
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.webrtc import (
    router as webrtc_router,
    close_peer_connections,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_peer_connections()


app = FastAPI(
    title="Polyp Detection API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webrtc_router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "polyp-detection-api",
    }
