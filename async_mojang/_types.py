import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class UserProfile:
    id: uuid.UUID
    timestamp: int
    name: str
    is_legacy_profile: bool
    skin_variant: str = "classic"
    skin_url: str | None = None
    cape_url: str | None = None
