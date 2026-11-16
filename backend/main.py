import sys
import os
import signal
import time
import cv2
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv()

from config.settings import settings
from tracking.tracker import ByteTrackWrapper
from evidence.capture import save_screenshot, CLASS_COLORS, DEFAULT_COLOR
from neo4j_client.database import connect as db_connect, close as db_close, get_driver
from neo4j_client.writer import save_detection_event, update_camera_status

CLASS_TO_EVENT = {
    "car_accident": "CAR_ACCIDENT",
    "fire": "FIRE_INCIDENT",
    "smoke": "SMOKE_HAZARD",
    "flood": "FLOOD_WARNING",
    "car": "VEHICLE_DETECTED",
    "truck": "VEHICLE_DETECTED",
    "bus": "VEHICLE_DETECTED",
    "motorcycle": "VEHICLE_DETECTED",
    "bicycle": "VEHICLE_DETECTED",
    "person": "PERSON_DETECTED",
}

WINDOW_NAME = f"ResiliNet — {settings.CAMERA_ID}"
_running = True


def _handle_sigint(sig, frame):
    global _running
    print("\nShutting down pipeline...")
    _running = False


signal.signal(signal.SIGINT, _handle_sigint)


def print_frame_summary(frame_num: int, tracked: list[dict]) -> None:
    if not tracked:
        return

    print(f"Frame {frame_num:04d} | {len(tracked)} object(s) tracked:")
    for obj in tracked:
        tid = obj["track_id"]
        cls = obj["class_name"]
        conf = obj["confidence"]
        bbox = obj["bbox"]
        print(f"  #{tid:<3} {cls:<14} conf={conf:.2f} bbox={bbox}")


def main() -> None:
    print(f"Starting camera stream: {settings.CAMERA_SOURCE} using {settings.YOLO_MODEL}")

    try:
        db_connect()
        update_camera_status(get_driver(), settings.CAMERA_ID, "ACTIVE")
        db_driver = get_driver()
    except Exception as exc:
        print(f"Neo4j connection skipped: {exc}")
        db_driver = None

    cap = cv2.VideoCapture(settings.CAMERA_SOURCE)
    if not cap.isOpened():
        print(f"Error: could not open camera source: {settings.CAMERA_SOURCE}")
        sys.exit(1)

    tracker = ByteTrackWrapper(
        model_name=settings.YOLO_MODEL,
        confidence=settings.CONFIDENCE_THRESHOLD,
    )

    frame_num = 0
    saved_count = 0

    while _running:
        ret, frame = cap.read()
        if not ret:
            break

        frame_num += 1
        if (frame_num - 1) % (settings.FRAME_SKIP + 1) != 0:
            continue

        tracked_objects = tracker.track(frame)
        print_frame_summary(frame_num, tracked_objects)

        if len(tracked_objects) >= settings.MIN_DETECTIONS_TO_SAVE:
            class_counts = {}
            for obj in tracked_objects:
                cls = obj["class_name"]
                class_counts[cls] = class_counts.get(cls, 0) + 1
            dominant_class = max(class_counts, key=class_counts.get)
            event_type = CLASS_TO_EVENT.get(dominant_class, "OBJECT_DETECTED")
            avg_confidence = sum(o["confidence"] for o in tracked_objects) / len(tracked_objects)

            evidence_path = save_screenshot(
                frame=frame,
                tracked_objects=tracked_objects,
                camera_id=settings.CAMERA_ID,
                event_type=event_type,
                evidence_dir=settings.EVIDENCE_DIR,
            )
            saved_count += 1

            if db_driver:
                track_ids = [o["track_id"] for o in tracked_objects]
                event_id = save_detection_event(
                    driver=db_driver,
                    camera_id=settings.CAMERA_ID,
                    event_type=event_type,
                    confidence=avg_confidence,
                    evidence_path=evidence_path,
                    track_ids=track_ids,
                )
                print(f"Event written to DB: {event_id}")

        preview = frame.copy()
        for obj in tracked_objects:
            x1, y1, x2, y2 = obj["bbox"]
            color = CLASS_COLORS.get(obj["class_name"], DEFAULT_COLOR)
            cv2.rectangle(preview, (x1, y1), (x2, y2), color, 2)
            label = f"#{obj['track_id']} {obj['class_name']} {int(obj['confidence'] * 100)}%"
            cv2.putText(
                preview,
                label,
                (x1, y1 - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
            )

        cv2.imshow(WINDOW_NAME, preview)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    print(f"Processed {frame_num} frames. Saved {saved_count} evidence screenshots.")
    cap.release()
    cv2.destroyAllWindows()

    if db_driver:
        update_camera_status(db_driver, settings.CAMERA_ID, "OFFLINE")
        db_close()


if __name__ == "__main__":
    main()
