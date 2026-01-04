#!/usr/bin/env python3
"""Quick start example for cursor_agent_sdk."""

import anyio

from cursor_agent_sdk import (
    AssistantMessage,
    CursorAgentOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    UserMessage,
    query,
)


async def simple_query():
    """Simple one-shot query example."""
    print("=== Simple Query ===\n")

    async for message in query(prompt="What is the capital of France?"):
        if isinstance(message, SystemMessage):
            print(f"[System] Session started: {message.data.get('session_id', 'N/A')}")
            print(f"[System] Model: {message.data.get('model', 'N/A')}")

        elif isinstance(message, UserMessage):
            print(f"[User] {message.content}")

        elif isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"[Assistant] {block.text}")

        elif isinstance(message, ResultMessage):
            print(f"\n[Result] Completed in {message.duration_ms}ms")
            print(f"[Result] Session: {message.session_id}")


async def query_with_options():
    """Query with custom options."""
    print("\n=== Query with Options ===\n")

    options = CursorAgentOptions(
        model="gpt-4",  # Or "claude", "grok", etc.
        # cwd="/path/to/project",  # Optional working directory
    )

    async for message in query(
        prompt="Explain Python async/await in one paragraph",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


async def main():
    """Run all examples."""
    await simple_query()
    await query_with_options()


if __name__ == "__main__":
    anyio.run(main)
