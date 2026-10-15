
import argparse
import csv
import sys
from pathlib import Path
from time import perf_counter

import cv2


# Permite ejecutar este archivo directamente desde backend/.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.inference.pipeline import PolypInferencePipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prueba de inferencia ONNX sobre video."
    )

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Ruta del video de entrada.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Ruta del video MP4 de salida.",
    )

    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Umbral de confianza de YOLO26s.",
    )

    parser.add_argument(
        "--start",
        type=float,
        default=0.0,
        help="Segundo desde el que comienza el procesamiento.",
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Duración máxima del fragmento en segundos.",
    )

    parser.add_argument(
        "--max-frames",
        type=int,
        default=None,
        help="Número máximo de fotogramas que se procesarán.",
    )

    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Ruta opcional para exportar predicciones y métricas.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if not args.input.is_file():
        raise FileNotFoundError(
            f"No se encontró el video: {args.input}"
        )

    if args.start < 0:
        raise ValueError("--start no puede ser negativo.")

    if args.duration is not None and args.duration <= 0:
        raise ValueError("--duration debe ser mayor que cero.")

    if args.max_frames is not None and args.max_frames <= 0:
        raise ValueError("--max-frames debe ser mayor que cero.")

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if args.csv is not None:
        args.csv.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    capture = cv2.VideoCapture(str(args.input))

    if not capture.isOpened():
        raise RuntimeError(
            f"No se pudo abrir el video: {args.input}"
        )

    fps = capture.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        capture.release()
        raise RuntimeError(
            "No se pudo determinar el FPS del video."
        )

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if width <= 0 or height <= 0:
        capture.release()
        raise RuntimeError("Resolución de video inválida.")

    # Ubicarse en el segundo solicitado.
    start_frame = int(args.start * fps)

    capture.set(
        cv2.CAP_PROP_POS_FRAMES,
        start_frame,
    )

    # Calcular límite de fotogramas.
    limits = []

    if args.duration is not None:
        limits.append(max(1, int(args.duration * fps)))

    if args.max_frames is not None:
        limits.append(args.max_frames)

    frame_limit = min(limits) if limits else None

    print("\n=== POLYP DETECTION MVP ===")
    print(f"Entrada: {args.input}")
    print(f"Salida: {args.output}")
    print(f"Resolución: {width}x{height}")
    print(f"FPS original: {fps:.2f}")
    print(f"Inicio: {args.start:.2f} s")
    print(f"Confianza YOLO: {args.conf:.2f}")

    if frame_limit is not None:
        print(f"Máximo de fotogramas: {frame_limit}")

    print("\nCargando modelos ONNX...")

    pipeline = PolypInferencePipeline(
        confidence_threshold=args.conf,
        crop_padding=0.15,
    )

    # Conservamos la resolución y FPS originales.
    # El procesamiento puede tardar más que la duración del video.
    writer = cv2.VideoWriter(
        str(args.output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    if not writer.isOpened():
        capture.release()
        raise RuntimeError(
            "No se pudo inicializar el archivo MP4."
        )

    csv_file = None
    csv_writer = None

    if args.csv is not None:
        csv_file = args.csv.open(
            "w",
            newline="",
            encoding="utf-8",
        )

        csv_writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "frame",
                "timestamp_s",
                "detection_index",
                "x1",
                "y1",
                "x2",
                "y2",
                "detection_confidence",
                "classification",
                "classification_confidence",
                "adenoma_probability",
                "hyperplastic_probability",
                "detection_ms",
                "classification_ms",
                "total_ms",
            ],
        )

        csv_writer.writeheader()

    processed_frames = 0
    detected_regions = 0

    detection_times = []
    classification_times = []
    total_times = []

    started = perf_counter()

    print("\nProcesando video...\n")

    try:
        while True:
            if (
                frame_limit is not None
                and processed_frames >= frame_limit
            ):
                break

            success, frame = capture.read()

            if not success:
                break

            result = pipeline.process_frame(frame)

            writer.write(result.frame)

            processed_frames += 1
            detected_regions += len(result.predictions)

            detection_times.append(
                result.metrics.detection_ms
            )

            classification_times.append(
                result.metrics.classification_ms
            )

            total_times.append(
                result.metrics.total_ms
            )

            timestamp_s = (
                start_frame + processed_frames - 1
            ) / fps

            if csv_writer is not None:
                for index, prediction in enumerate(
                    result.predictions,
                    start=1,
                ):
                    d = prediction.detection
                    c = prediction.classification

                    csv_writer.writerow({
                        "frame": start_frame + processed_frames - 1,
                        "timestamp_s": round(timestamp_s, 3),
                        "detection_index": index,
                        "x1": d.x1,
                        "y1": d.y1,
                        "x2": d.x2,
                        "y2": d.y2,
                        "detection_confidence": d.confidence,
                        "classification": c.label,
                        "classification_confidence": c.confidence,
                        "adenoma_probability": c.adenoma_probability,
                        "hyperplastic_probability": c.hyperplastic_probability,
                        "detection_ms": result.metrics.detection_ms,
                        "classification_ms": result.metrics.classification_ms,
                        "total_ms": result.metrics.total_ms,
                    })

            if (
                processed_frames == 1
                or processed_frames % 25 == 0
            ):
                elapsed = perf_counter() - started

                processing_fps = (
                    processed_frames / elapsed
                    if elapsed > 0
                    else 0.0
                )

                print(
                    f"Frames: {processed_frames}"
                    f" | Regiones: {detected_regions}"
                    f" | FPS procesamiento: {processing_fps:.2f}"
                    f" | Último frame: {result.metrics.total_ms:.1f} ms",
                    flush=True,
                )

    finally:
        capture.release()
        writer.release()

        if csv_file is not None:
            csv_file.close()

    elapsed = perf_counter() - started

    if processed_frames == 0:
        raise RuntimeError(
            "No se procesaron fotogramas."
        )

    average_detection = (
        sum(detection_times) / processed_frames
    )

    average_classification = (
        sum(classification_times) / processed_frames
    )

    average_total = (
        sum(total_times) / processed_frames
    )

    processing_fps = (
        processed_frames / elapsed
        if elapsed > 0
        else 0.0
    )

    print("\n=== RESULTADOS ===")
    print(f"Fotogramas procesados: {processed_frames}")
    print(f"Regiones detectadas: {detected_regions}")
    print(f"Tiempo transcurrido: {elapsed:.2f} s")
    print(f"FPS de procesamiento: {processing_fps:.2f}")
    print(f"YOLO26s promedio: {average_detection:.2f} ms")
    print(f"ConvNeXt promedio: {average_classification:.2f} ms")
    print(f"Pipeline promedio: {average_total:.2f} ms")
    print(f"Video generado: {args.output}")

    if args.csv is not None:
        print(f"CSV generado: {args.csv}")


if __name__ == "__main__":
    main()
