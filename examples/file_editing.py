#!/usr/bin/env python3
"""Example of file editing with cursor_agent_sdk."""

import anyio
from pathlib import Path
import tempfile

from cursor_agent_sdk import (
    AssistantMessage,
    CursorAgentOptions,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
    query,
)


async def edit_files_example():
    """Example showing file creation and editing."""

    # Create a temporary directory for this example
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Working in: {tmpdir}\n")

        options = CursorAgentOptions(
            permission_mode="acceptEdits",  # Auto-approve file changes
            cwd=tmpdir,
        )

        async for message in query(
            prompt="Create a simple Python hello world script called hello.py",
            options=options,
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"[Assistant] {block.text}")
                    elif isinstance(block, ToolUseBlock):
                        print(f"[Tool Call] {block.name}: {block.input}")
                    elif isinstance(block, ToolResultBlock):
                        print(f"[Tool Result] {block.content[:100]}...")

            elif isinstance(message, ResultMessage):
                print(f"\n[Done] Completed in {message.duration_ms}ms")

        # Check if the file was created
        hello_path = Path(tmpdir) / "hello.py"
        if hello_path.exists():
            print(f"\n=== Created file contents ===")
            print(hello_path.read_text())
        else:
            print("\nFile was not created (this is a demo)")


async def main():
    await edit_files_example()


if __name__ == "__main__":
    anyio.run(main)
