"""Error types for Cursor Agent SDK."""


class CursorSDKError(Exception):
    """Base exception for Cursor SDK errors."""

    pass


class CLINotFoundError(CursorSDKError):
    """Raised when cursor-agent CLI is not found."""

    pass


class CLIConnectionError(CursorSDKError):
    """Raised when connection to CLI fails."""

    pass


class ProcessError(CursorSDKError):
    """Raised when the CLI process fails."""

    def __init__(self, message: str, exit_code: int = -1, stderr: str = ""):
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr = stderr


class CLIJSONDecodeError(CursorSDKError):
    """Raised when JSON parsing fails."""

    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(message)
        self.original_error = original_error
