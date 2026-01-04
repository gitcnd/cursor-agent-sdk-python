#!/usr/bin/env python3.10
"""Live test of cursor_agent_sdk with cursor-agent CLI."""

import anyio
import sys

from cursor_agent_sdk import (
    query,
    CursorAgentOptions,
    AssistantMessage,
    SystemMessage,
    ResultMessage,
    UserMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
)


async def test_query_about_tools():
    """Ask the agent about its available tools and MCP servers."""
    print("=" * 60)
    print("Testing cursor_agent_sdk - Querying about tools and MCP servers")
    print("=" * 60)
    print()

    options = CursorAgentOptions(
        cwd="/home/cnd/Downloads/cursor/vibe",
    )

    prompt = """Please tell me:
1. What tools do you have access to?
2. What MCP servers are available, and what tools do they provide?
3. What model are you running as?

Please be concise - just list the tools and MCP info, no lengthy explanations needed.
"""

    print(f"[PROMPT] {prompt}")
    print()
    print("-" * 60)

    try:
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, SystemMessage):
                print(f"[SYSTEM] subtype={message.subtype}")
                print(f"         session_id={message.data.get('session_id', 'N/A')}")
                print(f"         model={message.data.get('model', 'N/A')}")
                print()

            elif isinstance(message, UserMessage):
                content = message.content
                if isinstance(content, str):
                    preview = content[:100] + "..." if len(content) > 100 else content
                else:
                    preview = str(content)[:100]
                print(f"[USER] {preview}")
                print()

            elif isinstance(message, AssistantMessage):
                print(f"[ASSISTANT] (model={message.model})")
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                    elif isinstance(block, ToolUseBlock):
                        print(f"  [TOOL_USE] {block.name}: {block.input}")
                    elif isinstance(block, ToolResultBlock):
                        content = str(block.content)[:200] if block.content else ""
                        print(f"  [TOOL_RESULT] {content}...")
                print()

            elif isinstance(message, ResultMessage):
                print("-" * 60)
                print(f"[RESULT] subtype={message.subtype}")
                print(f"         duration_ms={message.duration_ms}")
                print(f"         session_id={message.session_id}")
                print(f"         is_error={message.is_error}")
                if message.result:
                    print(f"         result_preview={message.result[:200]}...")

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print()
    print("=" * 60)
    print("Test completed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit_code = anyio.run(test_query_about_tools)
    sys.exit(exit_code)
