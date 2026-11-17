"""Configuración de ejecución; no carga modelos ni modifica la inferencia."""

import os
from pathlib import Path
from urllib.parse import urlsplit


# Mantener las rutas locales existentes cuando no hay configuración de contenedor.
MODEL_DIR = Path(
    os.environ.get("POLYP_MODEL_DIR")
    or Path(__file__).resolve().parents[2] / "models"
)


def parse_cors_origins(value: str) -> list[str]:
    origins = list(dict.fromkeys(origin.strip() for origin in value.split(",") if origin.strip()))
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or "*" in origin
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("CORS_ALLOWED_ORIGINS requiere orígenes HTTP(S) sin rutas ni comodines")
        # También rechazar puertos malformados o fuera de rango.
        _ = parsed.port
    return origins


# Una variable definida pero vacía deshabilita CORS; localhost solo es el valor de desarrollo.
CORS_ALLOWED_ORIGINS = parse_cors_origins(
    os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
)


# Optional: without either value local WebRTC continues without TURN.
TURN_URL = os.environ.get("TURN_URL", "").strip()
TURN_SHARED_SECRET = os.environ.get("TURN_SHARED_SECRET", "")
TURN_CREDENTIAL_TTL_SECONDS = int(os.environ.get("TURN_CREDENTIAL_TTL_SECONDS", "3600"))
if TURN_CREDENTIAL_TTL_SECONDS <= 0:
    raise ValueError("TURN_CREDENTIAL_TTL_SECONDS debe ser positivo")
if TURN_URL and not TURN_URL.startswith(("turn:", "turns:")):
    raise ValueError("TURN_URL debe ser una URL TURN")
