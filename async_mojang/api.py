"""Public async API for Mojang services."""

import base64
import binascii
import json
import uuid
from typing import Any

import aiohttp

from async_mojang._http_client import _DEFAULT_MAX_ATTEMPTS, _HTTPClient
from async_mojang._types import UserProfile
from async_mojang._utils import _assert_valid_username, _parse_uuid
from async_mojang.errors import BadRequest, MalformedResponse, NotFound

_API_BASE_URL = "https://api.mojang.com"
_SESSIONSERVER_BASE_URL = "https://sessionserver.mojang.com"
_UUID_API_URL = "https://api.minecraftservices.com/minecraft/profile/lookup/name"

_MAX_BATCH = 10  # API limitation

# Mojang endpoints may return 400 or 404 for "player not found".
# We map both to None in lookup methods.
_NOT_FOUND_ERRORS = (NotFound, BadRequest)


class API:
    """Async Mojang API client.

    Example:
        async with API() as api:
            player = await api.get_uuid("Notch")
            profile = await api.get_profile(player)
    """

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        *,
        retry_on_ratelimit: bool = False,
        ratelimit_sleep_time: float = 60,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    ) -> None:
        self._http = _HTTPClient(
            session,
            retry_on_ratelimit=retry_on_ratelimit,
            ratelimit_sleep_time=ratelimit_sleep_time,
            max_attempts=max_attempts,
        )

    async def get_uuid(self, username: str) -> uuid.UUID | None:
        """Look up a player's UUID by username, or None if not found."""
        _assert_valid_username(username)
        try:
            data: dict[str, Any] = await self._http._get_json(
                f"{_UUID_API_URL}/{username}",
            )
        except _NOT_FOUND_ERRORS:
            return None

        try:
            raw = data["id"]
        except (KeyError, TypeError, AttributeError) as exc:
            raise MalformedResponse(
                detail=f"UUID lookup response missing 'id': {exc}",
            ) from exc

        return uuid.UUID(raw) if raw else None

    async def get_uuids(self, names: list[str]) -> dict[str, uuid.UUID]:
        """Batch-convert up to 10 usernames to UUIDs.

        The returned dict is keyed by the server-returned casing
        (e.g. input "notch" -> key "Notch").
        """
        if len(names) > _MAX_BATCH:
            raise ValueError(
                f"Mojang batch API accepts at most {_MAX_BATCH} names, got {len(names)}",
            )
        for name in names:
            _assert_valid_username(name)
        try:
            data: list[dict[str, Any]] = await self._http._post_json(
                f"{_API_BASE_URL}/profiles/minecraft",
                json=names,
            )
        except _NOT_FOUND_ERRORS:
            return {}
        try:
            return {entry["name"]: uuid.UUID(entry["id"]) for entry in data}
        except (TypeError, KeyError, ValueError) as exc:
            raise MalformedResponse(
                detail=f"Unexpected batch-lookup response shape: {exc}",
            ) from exc

    async def get_username(self, player: uuid.UUID | str) -> str | None:
        """Convert a UUID to its current username, or None if not found."""
        uid = _parse_uuid(player)
        try:
            data: dict[str, Any] = await self._http._get_json(
                f"{_SESSIONSERVER_BASE_URL}/session/minecraft/profile/{uid.hex}",
            )
        except _NOT_FOUND_ERRORS:
            return None
        try:
            return data["name"]
        except (KeyError, TypeError, AttributeError) as exc:
            raise MalformedResponse(
                detail=f"Profile response missing 'name': {exc}",
            ) from exc

    async def get_profile(self, player: uuid.UUID | str) -> UserProfile | None:
        """Full profile with decoded texture data, or None if not found."""
        uid = _parse_uuid(player)
        try:
            data: dict[str, Any] = await self._http._get_json(
                f"{_SESSIONSERVER_BASE_URL}/session/minecraft/profile/{uid.hex}",
            )
        except _NOT_FOUND_ERRORS:
            return None
        return _parse_profile(data)

    async def get_blocked_servers(self) -> list[str]:
        """SHA-1 hashes of blocked Minecraft servers."""
        text: str = await self._http._get_text(
            f"{_SESSIONSERVER_BASE_URL}/blockedservers"
        )
        return text.splitlines()

    async def close(self) -> None:
        """Close the underlying HTTP session."""
        await self._http.close()

    async def __aenter__(self) -> "API":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()


def _parse_profile(data: dict[str, Any]) -> UserProfile:
    """Decode the base64 textures blob into a UserProfile."""
    try:
        value = data["properties"][0]["value"]
        decoded: dict[str, Any] = json.loads(base64.b64decode(value))
    except (KeyError, IndexError, json.JSONDecodeError, binascii.Error) as exc:
        raise MalformedResponse(
            detail=f"Cannot decode profile textures: {exc}",
        ) from exc

    textures: dict[str, Any] = decoded.get("textures", {})
    skin: dict[str, Any] = textures.get("SKIN", {})

    try:
        return UserProfile(
            id=uuid.UUID(decoded["profileId"]),
            timestamp=decoded["timestamp"],
            name=decoded["profileName"],
            is_legacy_profile=bool(decoded.get("legacy")),
            skin_url=skin.get("url"),
            skin_variant=skin.get("metadata", {}).get("model", "classic"),
            cape_url=textures.get("CAPE", {}).get("url"),
        )
    except (KeyError, ValueError) as exc:
        raise MalformedResponse(
            detail=f"Profile payload missing or invalid field: {exc}",
        ) from exc
