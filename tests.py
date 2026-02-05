"""Smoke tests against the live Mojang API."""

import asyncio

from async_mojang import API


async def main() -> None:
    async with API() as api:
        uid = await api.get_uuid("FroostySnoowman")
        print(f"UUID       : {uid}")

        if uid is not None:
            username = await api.get_username(uid)
            print(f"Username   : {username}")

            profile = await api.get_profile(uid)
            print(f"Profile    : {profile}")

        servers = await api.get_blocked_servers()
        print(f"Blocked    : {len(servers)} servers")


if __name__ == "__main__":
    asyncio.run(main())
