"""Tests for cursor_agent_sdk types."""

import pytest

from cursor_agent_sdk import (
    AssistantMessage,
    CursorAgentOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)


def test_text_block():
    """Test TextBlock creation."""
    block = TextBlock(text="Hello, world!")
    assert block.text == "Hello, world!"


def test_tool_use_block():
    """Test ToolUseBlock creation."""
    block = ToolUseBlock(
        id="tool_123",
        name="Write",
        input={"path": "test.py", "content": "print('hi')"},
    )
    assert block.id == "tool_123"
    assert block.name == "Write"
    assert block.input["path"] == "test.py"


def test_tool_result_block():
    """Test ToolResultBlock creation."""
    block = ToolResultBlock(
        tool_use_id="tool_123",
        content="File written successfully",
        is_error=False,
    )
    assert block.tool_use_id == "tool_123"
    assert block.content == "File written successfully"
    assert block.is_error is False


def test_user_message():
    """Test UserMessage creation."""
    msg = UserMessage(content="What is 2 + 2?")
    assert msg.content == "What is 2 + 2?"
    assert msg.uuid is None


def test_assistant_message():
    """Test AssistantMessage creation."""
    msg = AssistantMessage(
        content=[TextBlock(text="The answer is 4")],
        model="gpt-4",
    )
    assert len(msg.content) == 1
    assert isinstance(msg.content[0], TextBlock)
    assert msg.content[0].text == "The answer is 4"
    assert msg.model == "gpt-4"


def test_system_message():
    """Test SystemMessage creation."""
    msg = SystemMessage(
        subtype="init",
        data={"session_id": "abc123", "model": "claude"},
    )
    assert msg.subtype == "init"
    assert msg.data["session_id"] == "abc123"


def test_result_message():
    """Test ResultMessage creation."""
    msg = ResultMessage(
        subtype="success",
        duration_ms=1000,
        duration_api_ms=950,
        is_error=False,
        session_id="session_123",
        result="Task completed",
    )
    assert msg.subtype == "success"
    assert msg.duration_ms == 1000
    assert msg.is_error is False
    assert msg.session_id == "session_123"


def test_cursor_agent_options_defaults():
    """Test CursorAgentOptions default values."""
    options = CursorAgentOptions()
    assert options.model is None
    assert options.permission_mode is None
    assert options.cwd is None
    assert options.output_format == "stream-json"


def test_cursor_agent_options_with_values():
    """Test CursorAgentOptions with custom values."""
    options = CursorAgentOptions(
        model="gpt-4",
        permission_mode="acceptEdits",
        cwd="/path/to/project",
        extra_args={"verbose": None},
    )
    assert options.model == "gpt-4"
    assert options.permission_mode == "acceptEdits"
    assert options.cwd == "/path/to/project"
    assert options.extra_args == {"verbose": None}
