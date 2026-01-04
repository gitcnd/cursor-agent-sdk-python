# Cursor Agent SDK for Python

A **claude-agent-sdk compatible** Python SDK that uses `cursor-agent` CLI as the backend. This allows code written for the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) to work with Cursor subscriptions instead.

## Why?

- **Use your Cursor subscription** - No need for separate Anthropic API keys
- **Compatible API** - Drop-in replacement for claude-agent-sdk in many cases
- **Same patterns** - Async iteration, message types, and options work the same way
- **Model flexibility** - Access to GPT-4, Claude, Grok, and other models via Cursor

## Installation

### From PyPI (when published)

```bash
pip install cursor-agent-sdk
```

### From GitHub

```bash
# Latest version
pip install git+https://github.com/cnd/cursor-agent-sdk-python.git

# Specific version/tag
pip install git+https://github.com/cnd/cursor-agent-sdk-python.git@v0.1.0

# Or clone and install locally
git clone https://github.com/cnd/cursor-agent-sdk-python.git
cd cursor-agent-sdk-python
pip install -e .
```

**Prerequisites:**
- Python 3.10+
- cursor-agent CLI installed: `curl https://cursor.com/install -fsS | bash`
- Active Cursor subscription

## Quick Start

```python
import anyio
from cursor_agent_sdk import query

async def main():
    async for message in query(prompt="What is 2 + 2?"):
        print(message)

anyio.run(main)
```

## Basic Usage

### Simple Query

```python
from cursor_agent_sdk import query, AssistantMessage, TextBlock

async for message in query(prompt="Explain Python decorators"):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                print(block.text)
```

### With Options

```python
from cursor_agent_sdk import query, CursorAgentOptions

options = CursorAgentOptions(
    model="gpt-4",  # Specify model
    cwd="/path/to/project",  # Working directory
    permission_mode="acceptEdits",  # Auto-approve file changes
)

async for message in query(prompt="Refactor this code", options=options):
    print(message)
```

### File Modifications

```python
options = CursorAgentOptions(
    permission_mode="acceptEdits",  # Maps to --force flag
    cwd="/path/to/project",
)

async for message in query(
    prompt="Add docstrings to all functions in main.py",
    options=options
):
    print(message)
```

### With MCP Tools

```python
options = CursorAgentOptions(
    browser=True,  # Enable browser MCP
    approve_mcps=True,  # Auto-approve MCP usage
)

async for message in query(
    prompt="Navigate to example.com and describe what you see",
    options=options
):
    print(message)
```

## API Compatibility with claude-agent-sdk

### Compatible Features

| Feature | cursor-agent-sdk | claude-agent-sdk |
|---------|------------------|------------------|
| `query()` function | ✅ | ✅ |
| `CursorAgentOptions` / `ClaudeAgentOptions` | ✅ | ✅ |
| `AssistantMessage`, `UserMessage`, etc. | ✅ | ✅ |
| `TextBlock`, `ToolUseBlock`, `ToolResultBlock` | ✅ | ✅ |
| `ResultMessage` with session_id | ✅ | ✅ |
| `SystemMessage` | ✅ | ✅ |
| Stream JSON output parsing | ✅ | ✅ |
| Model selection | ✅ | ✅ |
| Working directory (cwd) | ✅ | ✅ |
| Session resume | ✅ | ✅ |

### Differences

| Feature | cursor-agent-sdk | claude-agent-sdk |
|---------|------------------|------------------|
| Backend CLI | `cursor-agent` | `claude` |
| Hooks | ❌ Not supported | ✅ Supported |
| Custom MCP servers (SDK-defined) | ❌ Use .cursor/mcp.json | ✅ Supported |
| Subagents | ❌ Not supported | ✅ Supported |
| `ClaudeSDKClient` bidirectional | ❌ Not implemented | ✅ Supported |
| Streaming input mode | ❌ Not supported | ✅ Supported |
| Sandbox settings | Via `--sandbox` flag | Full SandboxSettings |

### Migration from claude-agent-sdk

For simple use cases, just change the import:

```python
# Before (claude-agent-sdk)
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

# After (cursor-agent-sdk)  
from cursor_agent_sdk import query, CursorAgentOptions, AssistantMessage, TextBlock
# Or use the alias:
from cursor_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock
```

## Configuration Options

### CursorAgentOptions

| Option | Type | Description | CLI Flag |
|--------|------|-------------|----------|
| `model` | `str` | Model to use (gpt-4, claude, grok, etc.) | `--model` |
| `permission_mode` | `str` | 'default', 'acceptEdits', 'bypassPermissions' | `--force` |
| `cwd` | `str \| Path` | Working directory | (cwd) |
| `cli_path` | `str \| Path` | Path to cursor-agent binary | - |
| `resume` | `str` | Session ID to resume | `--resume` |
| `system_prompt` | `str` | System prompt (prepended to prompt) | - |
| `env` | `dict` | Environment variables | - |
| `extra_args` | `dict` | Additional CLI arguments | (various) |

**Note**: cursor-agent v2025.09 supports a subset of features. MCP servers are 
automatically available based on your `.cursor/mcp.json` configuration.

## Message Types

### SystemMessage
Emitted once at session start with metadata:
```python
SystemMessage(
    subtype="init",
    data={
        "session_id": "...",
        "model": "Claude 4 Sonnet",
        "cwd": "/path/to/project",
    }
)
```

### UserMessage
Your input prompt:
```python
UserMessage(content="Your prompt text")
```

### AssistantMessage
Agent responses and tool calls:
```python
AssistantMessage(
    content=[TextBlock(text="Here's my response...")],
    model="gpt-4"
)
```

### ResultMessage
Final result with timing info:
```python
ResultMessage(
    subtype="success",
    duration_ms=1234,
    duration_api_ms=1234,
    is_error=False,
    session_id="...",
    result="Final response text"
)
```

## Error Handling

```python
from cursor_agent_sdk import (
    CursorSDKError,
    CLINotFoundError,
    CLIConnectionError,
    ProcessError,
    CLIJSONDecodeError,
)

try:
    async for message in query(prompt="Hello"):
        pass
except CLINotFoundError:
    print("Install cursor-agent: curl https://cursor.com/install -fsS | bash")
except ProcessError as e:
    print(f"Process failed with exit code: {e.exit_code}")
    print(f"Stderr: {e.stderr}")
except CLIJSONDecodeError as e:
    print(f"Failed to parse response: {e}")
```

## Examples

### Code Review Script

```python
import anyio
from cursor_agent_sdk import query, CursorAgentOptions, AssistantMessage, TextBlock

async def review_code():
    options = CursorAgentOptions(
        model="claude",
        cwd=".",
    )
    
    async for message in query(
        prompt="Review the code in src/ for potential bugs and improvements",
        options=options
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)

anyio.run(review_code)
```

### File Generation with Auto-Approval

```python
async def generate_tests():
    options = CursorAgentOptions(
        permission_mode="acceptEdits",
        cwd="/path/to/project",
    )
    
    async for message in query(
        prompt="Generate pytest tests for all functions in utils.py",
        options=options
    ):
        print(message)

anyio.run(generate_tests)
```

## License

MIT License - see LICENSE file for details.

## Related Projects

- [claude-agent-sdk-python](https://github.com/anthropics/claude-agent-sdk-python) - The official Claude Agent SDK
- [cursor-agent](https://cursor.com/docs/cli) - The Cursor Agent CLI
