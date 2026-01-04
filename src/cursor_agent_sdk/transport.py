"""Subprocess transport implementation using cursor-agent CLI."""

import json
import os
import platform
import shutil
from collections.abc import AsyncIterator
from contextlib import suppress
from pathlib import Path
from subprocess import PIPE
from typing import Any

import anyio
from anyio.abc import Process
from anyio.streams.text import TextReceiveStream

from ._errors import CLIConnectionError, CLIJSONDecodeError, CLINotFoundError, ProcessError
from .types import (
    AssistantMessage,
    CursorAgentOptions,
    Message,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

_DEFAULT_MAX_BUFFER_SIZE = 1024 * 1024  # 1MB buffer limit

# Default Windows cursor-agent location (community-patched Node.js version)
_DEFAULT_WINDOWS_CURSOR_AGENT_JS = Path.home() / "Downloads" / "cursor" / "vibe" / "cursor_agent_mod" / "2026.01.02-80e4d9b-windows" / "index.js"


class SubprocessCLITransport:
    """Subprocess transport using cursor-agent CLI."""

    def __init__(
        self,
        prompt: str,
        options: CursorAgentOptions,
    ):
        self._prompt = prompt
        self._options = options
        self._is_windows = platform.system() == "Windows"
        self._cli_path, self._is_node_js = self._find_cli(options.cli_path)
        self._cwd = str(options.cwd) if options.cwd else None
        self._process: Process | None = None
        self._stdout_stream: TextReceiveStream | None = None
        self._stderr_stream: TextReceiveStream | None = None
        self._ready = False
        self._exit_error: Exception | None = None
        self._max_buffer_size = (
            options.max_buffer_size
            if options.max_buffer_size is not None
            else _DEFAULT_MAX_BUFFER_SIZE
        )

    def _find_cli(self, cli_path_override: str | Path | None = None) -> tuple[str, bool]:
        """Find cursor-agent CLI binary or Node.js script.
        
        Returns:
            Tuple of (path, is_node_js) where is_node_js indicates if we need to run via node.
        """
        # If user provided a path, use it
        if cli_path_override:
            path_str = str(cli_path_override)
            # Check if it's a .js file (needs node to run)
            is_js = path_str.endswith(".js")
            return (path_str, is_js)

        # Check PATH first for cursor-agent binary/script
        if cli := shutil.which("cursor-agent"):
            return (cli, False)

        # Platform-specific locations
        if self._is_windows:
            # Windows: Look for the community-patched Node.js version
            windows_locations = [
                _DEFAULT_WINDOWS_CURSOR_AGENT_JS,
                Path.home() / "cursor-agent" / "index.js",
                Path("C:/cursor-agent/index.js"),
            ]
            
            for path in windows_locations:
                if path.exists() and path.is_file():
                    return (str(path), True)  # Node.js script
            
            # Also check for .cmd wrapper
            if cmd := shutil.which("cursor-agent.cmd"):
                return (cmd, False)
                
            raise CLINotFoundError(
                "cursor-agent not found on Windows.\n\n"
                "Option 1: Use the community-patched Windows version:\n"
                "  Download from: https://github.com/gitcnd/cursor-agent-cli-windows\n"
                f"  Expected at: {_DEFAULT_WINDOWS_CURSOR_AGENT_JS}\n\n"
                "Option 2: Provide the path via CursorAgentOptions:\n"
                "  CursorAgentOptions(cli_path='C:/path/to/index.js')\n"
            )
        else:
            # Linux/macOS: Look for native binary
            unix_locations = [
                Path.home() / ".local" / "bin" / "cursor-agent",
                Path("/usr/local/bin/cursor-agent"),
                Path.home() / ".cursor" / "bin" / "cursor-agent",
            ]

            for path in unix_locations:
                if path.exists() and path.is_file():
                    return (str(path), False)

            raise CLINotFoundError(
                "cursor-agent not found. Install with:\n"
                "  curl https://cursor.com/install -fsS | bash\n"
                "\nOr provide the path via CursorAgentOptions:\n"
                "  CursorAgentOptions(cli_path='/path/to/cursor-agent')"
            )

    def _build_command(self) -> list[str]:
        """Build CLI command with arguments."""
        # For Node.js scripts (Windows community patch), we need to run via node
        if self._is_node_js:
            # Find node executable
            node_path = shutil.which("node")
            if not node_path:
                raise CLINotFoundError(
                    "Node.js is required to run cursor-agent on Windows.\n"
                    "Install from: https://nodejs.org/\n"
                    "Or use: winget install OpenJS.NodeJS.LTS"
                )
            # Use --use-system-ca for proper SSL certificate handling
            cmd = [node_path, "--use-system-ca", self._cli_path]
        else:
            cmd = [self._cli_path]

        # Add common arguments
        cmd.extend([
            "--print",
            "--output-format", "stream-json",
        ])

        # Model selection
        if self._options.model:
            cmd.extend(["--model", self._options.model])

        # Permission mode -> --force flag
        if self._options.permission_mode in ("acceptEdits", "bypassPermissions"):
            cmd.append("--force")

        # Session resume
        if self._options.resume:
            cmd.extend(["--resume", self._options.resume])

        # Note: --browser, --sandbox, --approve-mcps are not valid in cursor-agent v2025.09
        # These options may be added in future versions
        # Workspace is controlled via cwd, not a CLI flag

        # Extra args
        for flag, value in self._options.extra_args.items():
            if value is None:
                cmd.append(f"--{flag}")
            else:
                cmd.extend([f"--{flag}", str(value)])

        # Add prompt as positional argument (agent command reads from stdin with -)
        cmd.extend(["agent", "-"])

        return cmd

    async def connect(self) -> None:
        """Start subprocess."""
        if self._process:
            return

        cmd = self._build_command()

        try:
            process_env = {
                **os.environ,
                **self._options.env,
            }

            if self._cwd:
                process_env["PWD"] = self._cwd

            self._process = await anyio.open_process(
                cmd,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
                cwd=self._cwd,
                env=process_env,
            )

            if self._process.stdout:
                self._stdout_stream = TextReceiveStream(self._process.stdout)

            if self._process.stderr:
                self._stderr_stream = TextReceiveStream(self._process.stderr)

            # Write prompt to stdin
            if self._process.stdin:
                # Prepend system prompt if provided
                full_prompt = self._prompt
                if self._options.system_prompt:
                    full_prompt = f"{self._options.system_prompt}\n\n{self._prompt}"

                await self._process.stdin.send(full_prompt.encode("utf-8"))
                await self._process.stdin.aclose()

            self._ready = True

        except FileNotFoundError as e:
            if self._cwd and not Path(self._cwd).exists():
                error = CLIConnectionError(f"Working directory does not exist: {self._cwd}")
                self._exit_error = error
                raise error from e
            error = CLINotFoundError(f"cursor-agent not found at: {self._cli_path}")
            self._exit_error = error
            raise error from e
        except Exception as e:
            error = CLIConnectionError(f"Failed to start cursor-agent: {e}")
            self._exit_error = error
            raise error from e

    async def close(self) -> None:
        """Close the transport and clean up resources."""
        if not self._process:
            self._ready = False
            return

        self._ready = False

        if self._process.returncode is None:
            with suppress(ProcessLookupError):
                self._process.terminate()
                with suppress(Exception):
                    await self._process.wait()

        self._process = None
        self._stdout_stream = None
        self._stderr_stream = None
        self._exit_error = None

    def _parse_event(self, data: dict[str, Any]) -> Message | None:
        """Parse a cursor-agent event into a Message type."""
        event_type = data.get("type")
        subtype = data.get("subtype")
        session_id = data.get("session_id", "")

        if event_type == "system":
            # System init event
            return SystemMessage(
                subtype=subtype or "init",
                data={
                    "session_id": session_id,
                    "model": data.get("model"),
                    "cwd": data.get("cwd"),
                    "apiKeySource": data.get("apiKeySource"),
                    "permissionMode": data.get("permissionMode"),
                },
            )

        elif event_type == "user":
            # User message
            message_data = data.get("message", {})
            content_list = message_data.get("content", [])
            if content_list and isinstance(content_list, list):
                text_content = content_list[0].get("text", "") if content_list else ""
            else:
                text_content = str(content_list)
            return UserMessage(content=text_content)

        elif event_type == "assistant":
            # Assistant message - note: stream-json may emit partial text fragments
            # Each assistant event contains a complete message segment between tool calls
            message_data = data.get("message", {})
            content_list = message_data.get("content", [])
            blocks: list[TextBlock | ToolUseBlock | ToolResultBlock] = []

            for item in content_list:
                if item.get("type") == "text":
                    text = item.get("text", "")
                    if text:  # Only emit if there's actual text
                        blocks.append(TextBlock(text=text))
                elif item.get("type") == "tool_use":
                    blocks.append(ToolUseBlock(
                        id=item.get("id", ""),
                        name=item.get("name", ""),
                        input=item.get("input", {}),
                    ))

            # Only return if we have content
            if blocks:
                return AssistantMessage(
                    content=blocks,
                    model=data.get("model", "unknown"),
                )
            return None

        elif event_type == "tool_call":
            # Tool call events - convert to ToolUseBlock or ToolResultBlock
            call_id = data.get("call_id", "")
            tool_call = data.get("tool_call", {})

            if subtype == "started":
                # Extract tool info from various formats
                tool_name = ""
                tool_input: dict[str, Any] = {}

                if "readToolCall" in tool_call:
                    tool_name = "Read"
                    tool_input = tool_call["readToolCall"].get("args", {})
                elif "writeToolCall" in tool_call:
                    tool_name = "Write"
                    tool_input = tool_call["writeToolCall"].get("args", {})
                elif "function" in tool_call:
                    tool_name = tool_call["function"].get("name", "")
                    args_str = tool_call["function"].get("arguments", "{}")
                    try:
                        tool_input = json.loads(args_str) if isinstance(args_str, str) else args_str
                    except json.JSONDecodeError:
                        tool_input = {"raw": args_str}

                # Return as an AssistantMessage with tool use
                return AssistantMessage(
                    content=[ToolUseBlock(id=call_id, name=tool_name, input=tool_input)],
                    model="unknown",
                )

            elif subtype == "completed":
                # Extract result
                result_content = ""

                if "readToolCall" in tool_call:
                    result = tool_call["readToolCall"].get("result", {})
                    success = result.get("success", {})
                    result_content = success.get("content", "")
                elif "writeToolCall" in tool_call:
                    result = tool_call["writeToolCall"].get("result", {})
                    success = result.get("success", {})
                    result_content = json.dumps(success)

                # Return as an AssistantMessage with tool result
                return AssistantMessage(
                    content=[ToolResultBlock(tool_use_id=call_id, content=result_content)],
                    model="unknown",
                )

        elif event_type == "result":
            # Final result
            return ResultMessage(
                subtype=subtype or "success",
                duration_ms=data.get("duration_ms", 0),
                duration_api_ms=data.get("duration_api_ms", 0),
                is_error=data.get("is_error", False),
                session_id=session_id,
                result=data.get("result"),
            )

        return None

    async def read_messages(self) -> AsyncIterator[Message]:
        """Read and parse messages from the transport."""
        if not self._process or not self._stdout_stream:
            raise CLIConnectionError("Not connected")

        json_buffer = ""

        try:
            async for line in self._stdout_stream:
                line_str = line.strip()
                if not line_str:
                    continue

                json_lines = line_str.split("\n")

                for json_line in json_lines:
                    json_line = json_line.strip()
                    if not json_line:
                        continue

                    json_buffer += json_line

                    if len(json_buffer) > self._max_buffer_size:
                        buffer_length = len(json_buffer)
                        json_buffer = ""
                        raise CLIJSONDecodeError(
                            f"JSON message exceeded maximum buffer size of {self._max_buffer_size} bytes",
                            ValueError(f"Buffer size {buffer_length} exceeds limit"),
                        )

                    try:
                        data = json.loads(json_buffer)
                        json_buffer = ""

                        message = self._parse_event(data)
                        if message:
                            yield message

                    except json.JSONDecodeError:
                        # Continue accumulating
                        continue

        except anyio.ClosedResourceError:
            pass
        except GeneratorExit:
            pass

        # Check process completion
        try:
            returncode = await self._process.wait()
        except Exception:
            returncode = -1

        if returncode is not None and returncode != 0:
            stderr_output = ""
            if self._stderr_stream:
                try:
                    async for line in self._stderr_stream:
                        stderr_output += line
                except Exception:
                    pass

            self._exit_error = ProcessError(
                f"cursor-agent failed with exit code {returncode}",
                exit_code=returncode,
                stderr=stderr_output,
            )
            raise self._exit_error

    def is_ready(self) -> bool:
        """Check if transport is ready for communication."""
        return self._ready
