import uuid


def _assert_valid_username(username: str) -> None:
    """Raise ValueError for usernames outside 3–16 ASCII characters."""
    if len(username) < 3 or len(username) > 16:
        raise ValueError(
            f"Invalid username {username!r}: must be between 3 and 16 characters",
        )
    if not username.isascii():
        raise ValueError(
            f"Invalid username {username!r}: contains non-ASCII characters",
        )


def _parse_uuid(value: uuid.UUID | str) -> uuid.UUID:
    """Coerce value to uuid.UUID, passing through UUIDs unchanged."""
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise ValueError(f"Invalid UUID: {value!r}") from exc
