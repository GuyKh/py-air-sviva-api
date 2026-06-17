class SvivaAirError(Exception):
    """Exception raised for errors in the Sviva Air API.

    Attributes:
        code: Error code (HTTP status or internal error code).
        error: Human-readable error description.
    """

    def __init__(self, code: int | str, error: str):
        self.code = code
        self.error = error
        super().__init__(f"(Code {self.code}): {self.error}")


class SvivaAirAuthError(SvivaAirError):
    """Exception raised for authentication errors."""

    def __init__(self, code: int | str, error: str):
        super().__init__(code, error)
