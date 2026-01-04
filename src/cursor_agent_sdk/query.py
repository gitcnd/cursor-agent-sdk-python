"""Query function for one-shot interactions with Cursor Agent."""

import os
from collections.abc import AsyncIterator
from typing import Any

from .transport import SubprocessCLITransport
from .types import CursorAgentOptions, Message


async def query(
    *,
    prompt: str,
    options: CursorAgentOptions | None = None,
) -> AsyncIterator[Message]:
    """
    Query Cursor Agent for one-shot interactions.

    This function provides a claude_agent_sdk-compatible interface for
    cursor-agent CLI. It spawns cursor-agent as a subprocess and yields
    messages as they are generated.

    Args:
        prompt: The prompt to send to the agent.
        options: Optional configuration (defaults to CursorAgentOptions() if None).
                 Set options.permission_mode to control tool execution:
                 - 'default': CLI prompts for dangerous tools
                 - 'acceptEdits': Auto-accept file edits (uses --force)
                 - 'bypassPermissions': Allow all tools (uses --force)
                 Set options.cwd for working directory.
                 Set options.model to specify the model.

    Yields:
        Messages from the conversation (SystemMessage, UserMessage,
        AssistantMessage, ResultMessage)

    Example - Simple query:
        ```python
        async for message in query(prompt="What is the capital of France?"):
            print(message)
        ```

    Example - With options:
        ```python
        async for message in query(
            prompt="Create a Python web server",
            options=CursorAgentOptions(
                model="gpt-4",
                cwd="/home/user/project"
            )
        ):
            print(message)
        ```

    Example - With file modifications:
        ```python
        async for message in query(
            prompt="Refactor this code to use async/await",
            options=CursorAgentOptions(
                permission_mode="acceptEdits",
                cwd="/home/user/project"
            )
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
        ```
    """
    if options is None:
        options = CursorAgentOptions()

    os.environ["CURSOR_AGENT_SDK_ENTRYPOINT"] = "sdk-py"

    transport = SubprocessCLITransport(prompt=prompt, options=options)

    try:
        await transport.connect()

        async for message in transport.read_messages():
            yield message

    finally:
        await transport.close()
