from async_mojang._types import UserProfile
from async_mojang.api import API
from async_mojang.errors import (
    BadRequest,
    Forbidden,
    LoginFailure,
    MalformedResponse,
    MissingMinecraftLicense,
    MissingMinecraftProfile,
    MojangError,
    NotFound,
    ServerError,
    TooManyRequests,
    Unauthorized,
)

__all__ = [
    "API",
    "BadRequest",
    "Forbidden",
    "LoginFailure",
    "MalformedResponse",
    "MissingMinecraftLicense",
    "MissingMinecraftProfile",
    "MojangError",
    "NotFound",
    "ServerError",
    "TooManyRequests",
    "Unauthorized",
    "UserProfile",
]
