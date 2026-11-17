"""TURN REST credentials. Shared secrets and credentials must never be logged."""

import base64
import hashlib
import hmac
import secrets
import time

from app import config


def generate_turn_credentials(
    secret: str, ttl_seconds: int, *, now: float | None = None, identifier: str | None = None
) -> dict[str, str]:
    if ttl_seconds <= 0:
        raise ValueError("TURN credential TTL must be positive")
    expires = int(time.time() if now is None else now) + ttl_seconds
    username = f"{expires}:{identifier if identifier is not None else secrets.token_hex(16)}"
    credential = base64.b64encode(
        hmac.new(secret.encode(), username.encode(), hashlib.sha1).digest()
    ).decode("ascii")
    return {"username": username, "credential": credential}


def get_ice_servers() -> list[dict[str, str]]:
    if not config.TURN_URL or not config.TURN_SHARED_SECRET:
        return []
    return [{"urls": config.TURN_URL, **generate_turn_credentials(
        config.TURN_SHARED_SECRET, config.TURN_CREDENTIAL_TTL_SECONDS
    )}]
