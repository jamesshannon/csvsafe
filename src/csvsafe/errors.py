"""CSVSafe error types."""


class CSVSafeError(Exception):
    """Application-level error with user-facing metadata."""

    def __init__(self, message: str, *, fatal: bool = True):
        super().__init__(message)
        self.message = message
        self.fatal = fatal
