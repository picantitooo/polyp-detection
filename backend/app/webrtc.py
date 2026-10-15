
import asyncio
import logging
from contextlib import suppress
from fractions import Fraction
from time import perf_counter

import av
import cv2

from aiortc import (
    MediaStreamTrack,
    RTCPeerConnection,
    RTCSessionDescription,
)
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.inference.pipeline import PolypInferencePipeline


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webrtc", tags=["WebRTC"])

peer_connections: set[RTCPeerConnection] = set()

# Una instancia compartida para esta prueba local.
# No ejecutar inferencias concurrentes sobre ella.
pipeline: PolypInferencePipeline | None = None
pipeline_lock = asyncio.Lock()


def get_pipeline() -> PolypInferencePipeline:
    global pipeline

    if pipeline is None:
        pipeline = PolypInferencePipeline(
            confidence_threshold=0.25,
            crop_padding=0.15,
        )

        logger.info("Pipeline ONNX cargado correctamente")

    return pipeline


class OfferRequest(BaseModel):
    sdp: str
    type: str


class AnswerResponse(BaseModel):
    sdp: str
    type: str


class VideoInferenceTrack(MediaStreamTrack):
    """
    Recibe video continuamente y devuelve fotogramas
    procesados mediante YOLO26s + ConvNeXt-Tiny.

    Mantiene únicamente el fotograma más reciente.
    """

    kind = "video"

    def __init__(self, source: MediaStreamTrack):
        super().__init__()

        self.source = source
        self.latest_frame: av.VideoFrame | None = None
        self.new_frame = asyncio.Event()

        self.running = True
        self.frames_processed = 0

        self.reader_task = asyncio.create_task(
            self._read_frames()
        )

    async def _read_frames(self):
        """
        Consume continuamente la pista entrante.
        Los fotogramas antiguos se reemplazan.
        """
        try:
            while self.running:
                frame = await self.source.recv()

                self.latest_frame = frame
                self.new_frame.set()

        except asyncio.CancelledError:
            raise

        except Exception:
            logger.exception(
                "Finalizó la lectura del video entrante"
            )

        finally:
            self.running = False
            self.new_frame.set()

    async def recv(self):
        while self.running:
            await self.new_frame.wait()
            self.new_frame.clear()

            frame = self.latest_frame
            self.latest_frame = None

            if frame is None:
                continue

            image = frame.to_ndarray(format="bgr24")

            started = perf_counter()

            # ONNX Runtime es síncrono. Lo ejecutamos en
            # un hilo para no bloquear el event loop.
            async with pipeline_lock:
                result = await asyncio.to_thread(
                    get_pipeline().process_frame,
                    image,
                )

            self.frames_processed += 1

            if self.frames_processed % 20 == 0:
                elapsed_ms = (
                    perf_counter() - started
                ) * 1000

                logger.info(
                    "Inferencia WebRTC | frame=%d | "
                    "detecciones=%d | tiempo=%.1f ms",
                    self.frames_processed,
                    len(result.predictions),
                    elapsed_ms,
                )

            output = av.VideoFrame.from_ndarray(
                result.frame,
                format="bgr24",
            )

            # Conservar las marcas de tiempo originales.
            output.pts = frame.pts
            output.time_base = frame.time_base

            return output

        raise RuntimeError(
            "La pista de video ya no está activa."
        )

    def stop(self):
        if not self.running:
            return

        self.running = False
        self.new_frame.set()

        self.reader_task.cancel()

        super().stop()


@router.post("/offer", response_model=AnswerResponse)
async def offer(request: OfferRequest):
    if request.type != "offer":
        raise HTTPException(
            status_code=400,
            detail="Se esperaba una oferta WebRTC.",
        )

    pc = RTCPeerConnection()
    peer_connections.add(pc)

    inference_tracks: list[VideoInferenceTrack] = []

    logger.info("Nueva conexión WebRTC")

    async def cleanup():
        for track in inference_tracks:
            track.stop()

        await pc.close()
        peer_connections.discard(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(
            "Estado de conexión: %s",
            pc.connectionState,
        )

        if pc.connectionState in ("failed", "closed"):
            await cleanup()

    @pc.on("track")
    def on_track(track):
        logger.info("Pista recibida: %s", track.kind)

        if track.kind == "video":
            inference_track = VideoInferenceTrack(track)

            inference_tracks.append(inference_track)

            pc.addTrack(inference_track)

        @track.on("ended")
        async def on_ended():
            logger.info(
                "Pista finalizada: %s",
                track.kind,
            )

            if track.kind == "video":
                for inference_track in inference_tracks:
                    inference_track.stop()

    try:
        # Cargar modelos antes de negociar la conexión.
        # Esta carga es síncrona, pero ocurre una sola vez.
        await asyncio.to_thread(get_pipeline)

        remote_description = RTCSessionDescription(
            sdp=request.sdp,
            type=request.type,
        )

        await pc.setRemoteDescription(remote_description)

        answer = await pc.createAnswer()

        await pc.setLocalDescription(answer)

        while pc.iceGatheringState != "complete":
            await asyncio.sleep(0.1)

        if pc.localDescription is None:
            raise RuntimeError(
                "No se pudo generar la respuesta SDP."
            )

        return AnswerResponse(
            sdp=pc.localDescription.sdp,
            type=pc.localDescription.type,
        )

    except Exception:
        logger.exception(
            "Error estableciendo conexión WebRTC"
        )

        await cleanup()

        raise HTTPException(
            status_code=500,
            detail="Error estableciendo conexión WebRTC.",
        )


async def close_peer_connections():
    connections = list(peer_connections)

    await asyncio.gather(
        *(pc.close() for pc in connections),
        return_exceptions=True,
    )

    peer_connections.clear()
