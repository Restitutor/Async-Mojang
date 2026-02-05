import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any, NoReturn, TypeVar

import aiohttp

from async_mojang.errors import (
    BadRequest,
    Forbidden,
    MalformedResponse,
    MojangError,
    NotFound,
    ServerError,
    TooManyRequests,
    Unauthorized,
)

_log = logging.getLogger(__name__)

_T = TypeVar("_T")

_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/105.0.0.0 Safari/537.36"
)

# Status -> exception class
_STATUS_TO_ERROR: dict[int, type[MojangError]] = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    429: TooManyRequests,
}

_DEFAULT_MAX_ATTEMPTS = 3


class _HTTPClient:
    __slots__ = (
        "_max_attempts",
        "_owns_session",
        "_retry",
        "_retry_delay",
        "_session",
    )

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        *,
        retry_on_ratelimit: bool = False,
        ratelimit_sleep_time: float = 60,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    ) -> None:
        if max_attempts < 1:
            raise ValueError(f"max_attempts must be at least 1, got {max_attempts}")
        self._owns_session = session is None
        self._session = session or aiohttp.ClientSession(
            headers={"User-Agent": _DEFAULT_UA},
        )
        self._retry = retry_on_ratelimit
        self._retry_delay = ratelimit_sleep_time
        self._max_attempts = max_attempts

    async def _get_json(self, url: str, **kwargs: Any) -> Any:
        """GET and return parsed JSON."""
        return await self._request(
            "GET",
            url,
            lambda r: r.json(),
            **kwargs,
        )

    async def _post_json(self, url: str, **kwargs: Any) -> Any:
        """POST and return parsed JSON."""
        return await self._request(
            "POST",
            url,
            lambda r: r.json(),
            **kwargs,
        )

    async def _get_text(self, url: str, **kwargs: Any) -> str:
        """GET and return plain text."""
        return await self._request(
            "GET",
            url,
            lambda r: r.text(),
            **kwargs,
        )

    async def _request(
        self,
        method: str,
        url: str,
        deserialize: Callable[[aiohttp.ClientResponse], Awaitable[_T]],
        **kwargs: Any,
    ) -> _T:
        for attempt in range(1, self._max_attempts + 1):
            async with self._session.request(method, url, **kwargs) as resp:
                _log.debug(
                    "API %s %s -> %d (attempt %d)",
                    method,
                    url,
                    resp.status,
                    attempt,
                )
                if resp.ok:
                    try:
                        return await deserialize(resp)
                    except (json.JSONDecodeError, aiohttp.ContentTypeError) as exc:
                        raise MalformedResponse(
                            detail=f"Failed to deserialize {method} {url}: {exc}",
                        ) from exc
                if await self._maybe_retry(resp, attempt):
                    continue
                await self._raise_for_status(resp)

    async def _maybe_retry(
        self,
        resp: aiohttp.ClientResponse,
        attempt: int,
    ) -> bool:
        """Retry on 429 (if enabled) or transient 5xx.

        429 uses the configured retry delay (default 60s).
        Transient 5xx (502, 503, 504) use exponential backoff.
        """
        if attempt >= self._max_attempts:
            return False

        await resp.read()  # drain body before retry

        if resp.status == 429 and self._retry:
            _log.warning(
                "Rate-limited (attempt %d/%d). Sleeping %ss.",
                attempt,
                self._max_attempts,
                self._retry_delay,
            )
            await asyncio.sleep(self._retry_delay)
            return True

        if resp.status in (502, 503, 504):
            delay = 2 ** (attempt - 1)
            _log.warning(
                "Transient server error %d (attempt %d/%d). Retrying in %ds.",
                resp.status,
                attempt,
                self._max_attempts,
                delay,
            )
            await asyncio.sleep(delay)
            return True

        return False

    @staticmethod
    async def _raise_for_status(resp: aiohttp.ClientResponse) -> NoReturn:
        """Map a non-2xx response to the appropriate exception. Always raises."""
        try:
            error_data = await resp.json()
            detail = (
                error_data.get("errorMessage")
                or error_data.get("error")
                or f"HTTP {resp.status}"
            )
        except (json.JSONDecodeError, aiohttp.ContentTypeError):
            detail = f"HTTP {resp.status} {resp.reason or 'error'} for {resp.url.path}"

        if exc_cls := _STATUS_TO_ERROR.get(resp.status):
            raise exc_cls(status=resp.status, detail=detail)

        if resp.status >= 500:
            raise ServerError(status=resp.status, detail=detail)

        raise MojangError(status=resp.status, detail=detail)

    async def close(self) -> None:
        """Close the session if we created it."""
        if self._owns_session and not self._session.closed:
            await self._session.close()
