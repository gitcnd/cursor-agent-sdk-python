"""Type definitions for Cursor Agent SDK.

These types are designed to be compatible with claude_agent_sdk types,
allowing easy migration between the two SDKs.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


# Permission modes - cursor-agent uses --force for auto-approval
PermissionMode = Literal["default", "acceptEdits", "bypassPermissions"]


@dataclass
class TextBlock:
    """Text content block."""

    text: str


@dataclass
class ToolUseBlock:
    """Tool use content block."""

    id: str
    name: str
    input: dict[str, Any]


@dataclass
class ToolResultBlock:
    """Tool result content block."""

    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None


ContentBlock = TextBlock | ToolUseBlock | ToolResultBlock


@dataclass
class UserMessage:
    """User message."""

    content: str | list[ContentBlock]
    uuid: str | None = None


@dataclass
class AssistantMessage:
    """Assistant message with content blocks."""

    content: list[ContentBlock]
    model: str
    parent_tool_use_id: str | None = None


@dataclass
class SystemMessage:
    """System message with metadata."""

    subtype: str
    data: dict[str, Any]


@dataclass
class ResultMessage:
    """Result message with session and timing information."""

    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    session_id: str
    result: str | None = None
    num_turns: int = 1
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None


Message = UserMessage | AssistantMessage | SystemMessage | ResultMessage


@dataclass
class CursorAgentOptions:
    """Configuration options for Cursor Agent SDK.

    These options map to cursor-agent CLI flags where possible.
    Some claude_agent_sdk options are not available in cursor-agent.
    """

    # Model selection
    model: str | None = None

    # Permission control
    # In cursor-agent: --force enables auto-approval
    permission_mode: PermissionMode | None = None

    # Working directory
    cwd: str | Path | None = None

    # CLI path (if not in PATH)
    cli_path: str | Path | None = None

    # Session management
    resume: str | None = None

    # Output format control (internal use)
    output_format: str = "stream-json"

    # Environment variables
    env: dict[str, str] = field(default_factory=dict)

    # System prompt (not directly supported by cursor-agent, but can be included in prompt)
    system_prompt: str | None = None

    # Allowed tools (for documentation - cursor-agent auto-discovers tools)
    allowed_tools: list[str] = field(default_factory=list)

    # Max buffer size for JSON parsing
    max_buffer_size: int | None = None

    # Extra CLI arguments
    extra_args: dict[str, str | None] = field(default_factory=dict)

    # Note: The following options from documentation may not be available in all
    # cursor-agent versions. They are kept for forward compatibility.
    # - browser: Enable browser MCP (not in v2025.09)
    # - sandbox: Sandbox mode (not in v2025.09)  
    # - approve_mcps: Auto-approve MCP tools (not in v2025.09)


# Alias for claude_agent_sdk compatibility
ClaudeAgentOptions = CursorAgentOptions
