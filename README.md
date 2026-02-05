```Async-Mojang``` is a Python package for accessing Mojang's services. This library can be used to convert UUIDs, get a profile's information, and more.

There is one component to this package:

- **Public API** - Used to parse information about Minecraft profiles and more. Authentication is not required.

## Installation

**Python 3.10 or higher is required.**

The easiest way to install the library is using `pip`. Just run the following console command:

```
pip install async-mojang
```

## **Public API Quickstart**

```py
import asyncio
import uuid

from async_mojang import API, MojangError, MalformedResponse

async def main():
    async with API() as api:
        # Username -> UUID
        player: uuid.UUID | None = await api.get_uuid("FroostySnoowman")
        print(player)            # 069a79f4-...  (uuid.UUID object)
        print(player.hex)        # 069a79f4...   (stripped, replaces get_stripped_uuid)

        # Batch lookup (up to 10 names)
        uuids: dict[str, uuid.UUID] = await api.get_uuids(["Notch", "jeb_"])
        print(uuids)

        # UUID -> Username (accepts uuid.UUID or str)
        username: str | None = await api.get_username(player)
        print(username)

        # Full profile with skin/cape info
        profile = await api.get_profile(player)
        print(profile)

        # Blocked server hashes
        blocked_servers = await api.get_blocked_servers()
        print(blocked_servers)

if __name__ == "__main__":
    asyncio.run(main())
```

## Error Handling

All exceptions inherit from `MojangError`, so you can catch everything with a single handler. `MalformedResponse` is raised when the server returns HTTP 200 but the payload cannot be parsed.

```py
from async_mojang import API, MojangError, MalformedResponse

async with API() as api:
    try:
        profile = await api.get_profile("some-uuid")
    except MalformedResponse:
        ...  # server returned unparseable data
    except MojangError as e:
        print(e.status, e.detail)
```

## Advanced Options

```py
api = API(
    retry_on_ratelimit=True,       # auto-retry on HTTP 429
    ratelimit_sleep_time=60,       # seconds to wait before retry
    max_attempts=5,                # max retries for transient 5xx errors
)
```
