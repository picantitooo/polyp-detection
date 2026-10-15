import asyncio
import logging
import time
import os

import av
import cv2
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, RTCRtpSender
from aiortc.mediastreams import MediaStreamError
from aiortc.codecs import h264 as aiortc_h264
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.inference.pipeline import PolypInferencePipeline

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)
router = APIRouter(prefix="/webrtc", tags=["WebRTC"])
peer_connections: set[RTCPeerConnection] = set()
active_tracks: set["VideoInferenceTrack"] = set()
pipeline: PolypInferencePipeline | None = None
pipeline_lock = asyncio.Lock()

METRICS_INTERVAL_SECONDS = 5.0
PREDICTION_TTL_SECONDS = 0.35
# "H264" para comparar calidad; "VP8" para regresar al comportamiento previo.
PREFERRED_VIDEO_CODEC = os.getenv("WEBRTC_VIDEO_CODEC", "H264").upper()
if PREFERRED_VIDEO_CODEC not in ("H264", "VP8"):
    raise ValueError("WEBRTC_VIDEO_CODEC debe ser H264 o VP8")

# Ajuste experimental para aiortc 1.15.0:
# H264Encoder.__init__ lee h264.DEFAULT_BITRATE cuando se crea el codificador.
# NO modifica MAX_BITRATE, ni fija una tasa constante, ni desactiva la
# estimación de ancho de banda de RTCRtpSender.
# Afecta a los codificadores H.264 creados en este proceso Python.
H264_INITIAL_BITRATE = int(os.getenv("WEBRTC_H264_INITIAL_BITRATE", "2500000"))
if not aiortc_h264.MIN_BITRATE <= H264_INITIAL_BITRATE <= aiortc_h264.MAX_BITRATE:
    raise ValueError(
        f"WEBRTC_H264_INITIAL_BITRATE debe estar entre "
        f"{aiortc_h264.MIN_BITRATE} y {aiortc_h264.MAX_BITRATE} bps"
    )
if PREFERRED_VIDEO_CODEC == "H264":
    aiortc_h264.DEFAULT_BITRATE = H264_INITIAL_BITRATE



def get_pipeline() -> PolypInferencePipeline:
    global pipeline
    if pipeline is None:
        logger.info("Cargando modelos ONNX...")
        pipeline = PolypInferencePipeline(
            confidence_threshold=0.25,
            crop_padding=0.15,
        )
        logger.info("Pipeline ONNX cargado")
    return pipeline


class OfferRequest(BaseModel):
    sdp: str
    type: str


class AnswerResponse(BaseModel):
    sdp: str
    type: str


class VideoInferenceTrack(MediaStreamTrack):
    """Video en tiempo real sin bloquear la salida esperando ONNX.

    Las cajas se dibujan sobre fotogramas posteriores durante un TTL breve.
    Esto es aproximado: no existe seguimiento de objetos entre inferencias.
    """

    kind = "video"

    def __init__(self, source: MediaStreamTrack):
        super().__init__()
        self.source = source
        self.running = True
        self.latest_frame: av.VideoFrame | None = None
        self.latest_frame_id = 0
        self.frame_event = asyncio.Event()
        self.inference_event = asyncio.Event()

        self.predictions = []
        self.prediction_updated_at = 0.0
        self.prediction_source_frame_id = -1

        self.received = 0
        self.sent = 0
        self.inferred = 0
        self.last_inference_ms = 0.0
        self.last_detection_count = 0
        self.input_width = 0
        self.input_height = 0
        self.output_width = 0
        self.output_height = 0
        self.inference_errors = 0

        self.reader_task = asyncio.create_task(self._read_frames())
        self.inference_task = asyncio.create_task(self._run_inference())
        active_tracks.add(self)

    async def _read_frames(self):
        try:
            while self.running:
                frame = await self.source.recv()
                self.latest_frame = frame
                self.latest_frame_id += 1
                self.received += 1
                self.input_width = frame.width
                self.input_height = frame.height
                self.frame_event.set()
                self.inference_event.set()
        except asyncio.CancelledError:
            raise
        except MediaStreamError:
            logger.info("Terminó la pista de video entrante")
        except Exception:
            logger.exception("Error recibiendo video")
        finally:
            self.stop()

    async def _run_inference(self):
        try:
            while self.running:
                await self.inference_event.wait()
                self.inference_event.clear()
                if not self.running:
                    break

                frame = self.latest_frame
                frame_id = self.latest_frame_id
                if frame is None:
                    continue

                try:
                    image = frame.to_ndarray(format="bgr24")
                    started = time.perf_counter()
                    async with pipeline_lock:
                        result = await asyncio.to_thread(
                            get_pipeline().process_frame, image
                        )
                    elapsed_ms = (time.perf_counter() - started) * 1000
                except asyncio.CancelledError:
                    raise
                except Exception:
                    self.inference_errors += 1
                    self.predictions = []
                    self.prediction_updated_at = 0.0
                    logger.exception("Error en inferencia ONNX")
                    await asyncio.sleep(0.2)
                    continue

                if not self.running:
                    break
                self.predictions = list(result.predictions)
                self.prediction_updated_at = time.monotonic()
                self.prediction_source_frame_id = frame_id
                self.last_detection_count = len(self.predictions)
                self.last_inference_ms = elapsed_ms
                self.inferred += 1
        except asyncio.CancelledError:
            raise

    def _annotate(self, image):
        age = time.monotonic() - self.prediction_updated_at
        if age > PREDICTION_TTL_SECONDS or not self.predictions:
            return image

        height, width = image.shape[:2]
        for prediction in self.predictions:
            det = prediction.detection
            cls = prediction.classification
            x1 = max(0, min(width - 1, int(det.x1)))
            y1 = max(0, min(height - 1, int(det.y1)))
            x2 = max(0, min(width - 1, int(det.x2)))
            y2 = max(0, min(height - 1, int(det.y2)))
            if x2 <= x1 or y2 <= y1:
                continue

            color = (0, 165, 255) if cls.label == "adenoma" else (0, 220, 80)
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            label = (
                f"{cls.label.upper()} {cls.confidence:.2f} "
                f"| DET {det.confidence:.2f}"
            )
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.45
            thickness = 1
            (tw, th), baseline = cv2.getTextSize(label, font, scale, thickness)
            top = max(0, y1 - th - baseline - 8)
            bottom = min(height - 1, top + th + baseline + 8)
            right = min(width - 1, x1 + tw + 8)
            cv2.rectangle(image, (x1, top), (right, bottom), color, -1)
            cv2.putText(
                image, label, (x1 + 4, min(height - 1, top + th + 3)),
                font, scale, (255, 255, 255), thickness, cv2.LINE_AA,
            )
        return image

    async def recv(self):
        while self.running:
            await self.frame_event.wait()
            self.frame_event.clear()
            if not self.running:
                break

            frame = self.latest_frame
            if frame is None:
                continue

            # Conversión y anotación local. La pista devuelve la marca temporal
            # original, de modo que WebRTC conserva la cadencia de la fuente.
            image = frame.to_ndarray(format="bgr24")
            self._annotate(image)
            output = av.VideoFrame.from_ndarray(image, format="bgr24")
            output.pts = frame.pts
            output.time_base = frame.time_base
            self.output_width = output.width
            self.output_height = output.height
            self.sent += 1
            return output

        raise MediaStreamError

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.frame_event.set()
        self.inference_event.set()
        self.reader_task.cancel()
        self.inference_task.cancel()
        active_tracks.discard(self)
        logger.info(
            "Pista detenida | RX=%d TX=%d IA=%d errores=%d",
            self.received, self.sent, self.inferred, self.inference_errors,
        )
        super().stop()


async def _wait_for_ice(pc: RTCPeerConnection):
    while pc.iceGatheringState != "complete":
        await asyncio.sleep(0.1)


async def _report_session_metrics(
    pc: RTCPeerConnection, tracks: list[VideoInferenceTrack], senders: list[RTCRtpSender]
):
    previous_time = time.monotonic()
    previous_counters = {}
    previous_outbound = {}
    try:
        while True:
            await asyncio.sleep(METRICS_INTERVAL_SECONDS)
            if pc.connectionState in ("closed", "failed"):
                return

            now = time.monotonic()
            elapsed = max(now - previous_time, 1e-6)
            previous_time = now

            for track in tracks:
                key = id(track)
                current = (track.received, track.sent, track.inferred)
                old = previous_counters.get(key, (0, 0, 0))
                previous_counters[key] = current
                rx, tx, ia = ((new - prev) / elapsed for new, prev in zip(current, old))
                logger.info(
                    "WEBRTC PIPELINE | RX=%.2f FPS | TX=%.2f FPS | "
                    "IA=%.2f FPS | ONNX=%.1f ms | detecciones=%d | "
                    "entrada=%dx%d | salida=%dx%d | errores=%d",
                    rx, tx, ia, track.last_inference_ms,
                    track.last_detection_count,
                    track.input_width, track.input_height,
                    track.output_width, track.output_height,
                    track.inference_errors,
                )

            # Diagnóstico del codificador REAL instanciado por aiortc.
            # __encoder es un atributo privado de aiortc 1.15.0: solo lectura.
            for sender in senders:
                encoder = getattr(sender, "_RTCRtpSender__encoder", None)
                if encoder is None:
                    logger.info("WEBRTC CODIFICADOR REAL | pendiente de inicialización")
                    continue
                codec_context = getattr(encoder, "codec", None)
                logger.info(
                    "WEBRTC CODIFICADOR REAL | clase=%s | objetivo=%s kbps | "
                    "codec_context=%s | bitrate_contexto=%s kbps",
                    type(encoder).__name__,
                    f"{encoder.target_bitrate / 1000:.0f}"
                    if hasattr(encoder, "target_bitrate") else "N/D",
                    getattr(codec_context, "name", "N/D"),
                    f"{codec_context.bit_rate / 1000:.0f}"
                    if codec_context is not None and getattr(codec_context, "bit_rate", None)
                    else "N/D",
                )

            try:
                stats = await pc.getStats()
                by_id = {stat.id: stat for stat in stats.values()}
                for stat in stats.values():
                    if getattr(stat, "type", None) != "outbound-rtp" or getattr(stat, "kind", getattr(stat, "mediaType", None)) != "video":
                        continue
                    codec = by_id.get(getattr(stat, "codecId", None))
                    codec_name = getattr(codec, "mimeType", "desconocido")
                    bytes_sent = getattr(stat, "bytesSent", None)
                    packets_sent = getattr(stat, "packetsSent", None)
                    old_bytes = previous_outbound.get(stat.id)
                    bitrate_kbps = (
                        (bytes_sent - old_bytes) * 8 / elapsed / 1000
                        if bytes_sent is not None and old_bytes is not None
                        else None
                    )
                    if bytes_sent is not None:
                        previous_outbound[stat.id] = bytes_sent
                    logger.info(
                        "WEBRTC ENCODER | codec=%s | bitrate=%s kbps | "
                        "bytes=%s | paquetes=%s",
                        codec_name,
                        f"{bitrate_kbps:.0f}" if bitrate_kbps is not None else "N/D",
                        bytes_sent if bytes_sent is not None else "N/D",
                        packets_sent if packets_sent is not None else "N/D",
                    )
            except Exception:
                logger.exception("No se pudieron leer las estadísticas WebRTC")
    except asyncio.CancelledError:
        raise


@router.post("/offer", response_model=AnswerResponse)
async def offer(request: OfferRequest):
    if request.type != "offer":
        raise HTTPException(status_code=400, detail="Se esperaba una oferta WebRTC.")

    pc = RTCPeerConnection()
    peer_connections.add(pc)
    session_tracks: list[VideoInferenceTrack] = []
    metrics_task: asyncio.Task | None = None
    cleanup_started = False

    async def cleanup():
        nonlocal cleanup_started
        if cleanup_started:
            return
        cleanup_started = True
        for track in session_tracks:
            track.stop()
        if metrics_task is not None:
            metrics_task.cancel()
        await pc.close()
        peer_connections.discard(pc)
        logger.info("Sesión WebRTC liberada")

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info("Estado WebRTC: %s", pc.connectionState)
        if pc.connectionState in ("failed", "closed"):
            await cleanup()

    @pc.on("track")
    def on_track(track):
        logger.info("Pista entrante: %s", track.kind)
        if track.kind == "video":
            processed = VideoInferenceTrack(track)
            session_tracks.append(processed)
            sender = pc.addTrack(processed)

            # Guardar el transceptor; la preferencia se aplicará después
            # de setRemoteDescription, cuando conozcamos la oferta real.
            logger.info("WEBRTC TRACK | transceptor de salida creado")

        @track.on("ended")
        async def on_ended():
            logger.info("Pista finalizada: %s", track.kind)
            if track.kind == "video":
                await cleanup()

    try:
        async with pipeline_lock:
            await asyncio.to_thread(get_pipeline)

        await pc.setRemoteDescription(
            RTCSessionDescription(
                sdp=request.sdp,
                type=request.type,
            )
        )

        # No alterar la oferta SDP del navegador: aiortc valida y negocia
        # los códecs. El encoder real se observa en las métricas.
        # La oferta del navegador suele tener DOS secciones m=video:
        # una para el video que envía y otra para el que recibe. La primera
        # puede seguir mostrando VP8 aunque nuestra pista de salida use H264.
        # Aplicar la preferencia solo al transceptor que ENVÍA la pista anotada.
        capabilities = RTCRtpSender.getCapabilities("video").codecs
        selected = [
            codec for codec in capabilities
            if codec.mimeType.lower() == f"video/{PREFERRED_VIDEO_CODEC.lower()}"
        ]
        if not selected:
            raise HTTPException(
                status_code=422,
                detail=f"El servidor no soporta {PREFERRED_VIDEO_CODEC}",
            )

        outgoing = [
            transceiver for transceiver in pc.getTransceivers()
            if transceiver.kind == "video"
            and transceiver.sender.track in session_tracks
        ]
        if not outgoing:
            raise RuntimeError("No se encontró el transceptor del video procesado")

        for transceiver in outgoing:
            transceiver.setCodecPreferences(selected)
            logger.info(
                "WEBRTC CODEC PREFERIDO | mid=%s | codec=%s | perfiles=%d",
                transceiver.mid, PREFERRED_VIDEO_CODEC, len(selected),
            )

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        await asyncio.wait_for(_wait_for_ice(pc), timeout=15)
        if pc.localDescription is None:
            raise RuntimeError("No se pudo generar la respuesta SDP")

        # Inspeccionar CADA sección de video, no solo la primera.
        # El orden de la primera sección no identifica necesariamente el
        # códec de la pista procesada que enviamos al navegador.
        sections = []
        current = None
        for line in pc.localDescription.sdp.splitlines():
            if line.startswith("m="):
                current = None
                if line.startswith("m=video "):
                    current = {
                        "payloads": line.split()[3:],
                        "mid": "?", "direction": "?", "codecs": {},
                    }
                    sections.append(current)
            elif current is not None:
                if line.startswith("a=mid:"):
                    current["mid"] = line[6:]
                elif line in ("a=sendonly", "a=recvonly", "a=sendrecv", "a=inactive"):
                    current["direction"] = line[2:]
                elif line.startswith("a=rtpmap:"):
                    fields = line[len("a=rtpmap:"):].split(" ", 1)
                    if len(fields) == 2:
                        current["codecs"][fields[0]] = fields[1].split("/")[0]

        for section in sections:
            codecs = [section["codecs"].get(pt, pt) for pt in section["payloads"]]
            logger.info(
                "WEBRTC SDP VIDEO | mid=%s | direccion=%s | codecs=%s",
                section["mid"], section["direction"], ",".join(codecs),
            )

        for transceiver in outgoing:
            matching = next(
                (section for section in sections if section["mid"] == transceiver.mid),
                None,
            )
            if matching is None:
                raise RuntimeError("No se encontró la sección SDP del video saliente")
            negotiated = [
                matching["codecs"].get(pt, "")
                for pt in matching["payloads"]
            ]
            logger.info(
                "WEBRTC CODEC SDP | mid=%s | codecs_disponibles=%s | "
                "seleccion_real_se_verifica_en_CODIFICADOR_REAL",
                transceiver.mid, ",".join(negotiated),
            )

        logger.info(
            "WEBRTC BITRATE CONFIG | codec_preferido=%s | "
            "h264_objetivo_inicial=%d kbps | "
            "h264_limites=%d-%d kbps | adaptación=habilitada",
            PREFERRED_VIDEO_CODEC,
            H264_INITIAL_BITRATE // 1000,
            aiortc_h264.MIN_BITRATE // 1000,
            aiortc_h264.MAX_BITRATE // 1000,
        )

        metrics_task = asyncio.create_task(
            _report_session_metrics(pc, session_tracks, [t.sender for t in outgoing])
        )
        return AnswerResponse(
            sdp=pc.localDescription.sdp,
            type=pc.localDescription.type,
        )
    except HTTPException:
        await cleanup()
        raise
    except Exception as exc:
        logger.exception("Error estableciendo WebRTC")
        await cleanup()
        raise HTTPException(
            status_code=500, detail="Error estableciendo conexión WebRTC."
        ) from exc


async def close_peer_connections():
    for track in list(active_tracks):
        track.stop()
    await asyncio.gather(
        *(pc.close() for pc in list(peer_connections)),
        return_exceptions=True,
    )
    peer_connections.clear()
    active_tracks.clear()
