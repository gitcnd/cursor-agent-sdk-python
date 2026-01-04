"""Cursor Agent SDK for Python.

A claude-agent-sdk compatible interface that uses cursor-agent CLI as the backend.
This allows code written for claude-agent-sdk to work with Cursor subscriptions.

Example:
    import asyncio
    from cursor_agent_sdk import query, CursorAgentOptions

    async def main():
        async for message in query(prompt="What is 2 + 2?"):
            print(message)

    asyncio.run(main())
"""

from ._errors import (
    CursorSDKError,
    CLIConnectionError,
    CLIJSONDecodeError,
    CLINotFoundError,
    ProcessError,
)
from ._version import __version__
from .query import query
from .types import (
    AssistantMessage,
    ContentBlock,
    CursorAgentOptions,
    Message,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

# Aliases for claude_agent_sdk compatibility
ClaudeAgentOptions = CursorAgentOptions
ClaudeSDKError = CursorSDKError

__all__ = [
    # Main exports
    "query",
    "__version__",
    # Types (native names)
    "CursorAgentOptions",
    "UserMessage",
    "AssistantMessage",
    "SystemMessage",
    "ResultMessage",
    "Message",
    "TextBlock",
    "ToolUseBlock",
    "ToolResultBlock",
    "ContentBlock",
    # Compatibility aliases
    "ClaudeAgentOptions",
    "ClaudeSDKError",
    # Errors
    "CursorSDKError",
    "CLIConnectionError",
    "CLINotFoundError",
    "ProcessError",
    "CLIJSONDecodeError",
]
