"""Exception hierarchy for Mojang API errors."""


class MojangError(Exception):
    """Base error class for all library-related exceptions in this file.
    Essentially, this could be caught to handle any exceptions thrown from this library.
    """

    def __init__(
        self,
        status: int = 0,
        detail: str = "Unknown Mojang API error",
    ) -> None:
        self.status = status
        self.detail = detail
        msg = f"[HTTP {status}] {detail}" if status else detail
        super().__init__(msg)


class BadRequest(MojangError):
    """HTTP 400. The server could not process our request, likely due to an error of ours."""

    def __init__(self, *, status: int = 400, detail: str = "Bad request") -> None:
        super().__init__(status=status, detail=detail)


class Unauthorized(MojangError):
    """HTTP 401. We are not authorized to access the requested resource.
    This can occur due to an invalid or expired Bearer token.
    """

    def __init__(self, *, status: int = 401, detail: str = "Unauthorized") -> None:
        super().__init__(status=status, detail=detail)


class Forbidden(MojangError):
    """HTTP 403. We do not have permission to access the requested resource."""

    def __init__(self, *, status: int = 403, detail: str = "Forbidden") -> None:
        super().__init__(status=status, detail=detail)


class NotFound(MojangError):
    """HTTP 404. This resource does not exist."""

    def __init__(self, *, status: int = 404, detail: str = "Not found") -> None:
        super().__init__(status=status, detail=detail)


class TooManyRequests(MojangError):
    """HTTP 429. The server is ratelimiting us. Please wait for a bit before trying again."""

    def __init__(self, *, status: int = 429, detail: str = "Rate-limited") -> None:
        super().__init__(status=status, detail=detail)


class ServerError(MojangError):
    """HTTP 5xx. The server encountered an unexpected condition that prevented it from fulfilling the request."""

    def __init__(self, *, status: int = 500, detail: str = "Server error") -> None:
        super().__init__(status=status, detail=detail)


class MalformedResponse(MojangError):
    """Server returned 200 but the payload could not be parsed."""

    def __init__(self, detail: str = "Malformed response payload") -> None:
        super().__init__(status=0, detail=detail)


class LoginFailure(MojangError):
    """The login process failed for some reason. This can occur due to an incorrect email or password."""


class MissingMinecraftLicense(MojangError):
    """The Microsoft account is valid, but it is missing a Minecraft license."""


class MissingMinecraftProfile(MojangError):
    """The account has a Minecraft license, but it hasn't created a profile yet."""
