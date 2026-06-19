#!/usr/bin/env python3
# main.py
#
# Phase 1 Pipeline Orchestrator
# ─────────────────────────────
# Flow per frame:
#   [Camera] → [ByteTrack + YOLOv8] → [Console output]
#                                    → [Evidence screenshot saved to disk]
#                                    → [DetectionEvent node written to Neo4j]
#
# This is the single entry point. Run with:
#   python main.py
#
# Press Q in the OpenCV preview window (or Ctrl+C in the terminal) to stop.

import sys
import signal
import time
import cv2
from dotenv import load_dotenv

load_dotenv()  # must be before any settings import

from config.settings       import settings
from tracking.tracker      import ByteTrackWrapper
from evidence.capture      import save_screenshot
from neo4j_client.database import connect as db_connect, close as db_close, get_driver
from neo4j_client.writer   import save_detection_event, update_camera_status

# ── CONSTANTS ────────────────────────────────────────────────────────────────

# Map class names to event type strings stored in Neo4j.
# Add more mappings here as the event engine grows in Phase 2.
CLASS_TO_EVENT = {
    "car":        "VEHICLE_DETECTED",
    "truck":      "VEHICLE_DETECTED",
    "bus":        "VEHICLE_DETECTED",
    "motorcycle": "VEHICLE_DETECTED",
    "bicycle":    "VEHICLE_DETECTED",
    "person":     "PERSON_DETECTED",
}

WINDOW_NAME = f"ResiliNet Phase 1 — {settings.CAMERA_ID}"


# ── GRACEFUL SHUTDOWN ─────────────────────────────────────────────────────────

_running = True

def _handle_sigint(sig, frame):
    global _running
    print("\n[MAIN] Interrupt received — shutting down …")
    _running = False

signal.signal(signal.SIGINT, _handle_sigint)


# ── CONSOLE PRINTER ───────────────────────────────────────────────────────────

def print_frame_summary(frame_num: int, tracked: list[dict]) -> None:
    """
    Pretty-print a per-frame detection summary to the console.

    Example output:
        ┌─ Frame 0042 ─ 3 object(s) detected ──────────────────┐
        │  #12  car         conf=0.91  bbox=[245, 130, 412, 290]
        │  #13  car         conf=0.78  bbox=[510, 145, 680, 305]
        │   #7  person      conf=0.85  bbox=[ 90, 200, 150, 450]
        └───────────────────────────────────────────────────────┘
    """
    if not tracked:
        # Print a short line for empty frames so the operator knows the
        # pipeline is running even when nothing is detected.
        print(f"  Frame {frame_num:04d} — no detections above threshold")
        return

    print(f"\n┌─ Frame {frame_num:04d} ─ {len(tracked)} object(s) detected {'─' * 30}┐")
    for obj in tracked:
        tid   = obj["track_id"]
        cls   = obj["class_name"]
        conf  = obj["confidence"]
        bbox  = obj["bbox"]
        print(f"│  #{tid:<4}  {cls:<12}  conf={conf:.2f}  bbox={bbox}")
    print(f"└{'─' * 55}┘")


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("  ResiliNet AI — Phase 1 CCTV Detection Pipeline")
    print("=" * 60)
    print(f"  Camera ID   : {settings.CAMERA_ID}")
    print(f"  Camera Name : {settings.CAMERA_NAME}")
    print(f"  Source      : {settings.CAMERA_SOURCE}")
    print(f"  YOLO Model  : {settings.YOLO_MODEL}")
    print(f"  Confidence  : {settings.CONFIDENCE_THRESHOLD}")
    print(f"  Evidence Dir: {settings.EVIDENCE_DIR}")
    print(f"  Frame Skip  : every {settings.FRAME_SKIP + 1} frame(s) processed")
    print("=" * 60)

    # ── 1. Connect to Neo4j ──────────────────────────────────
    try:
        db_connect()
        update_camera_status(get_driver(), settings.CAMERA_ID, "ACTIVE")
    except Exception as exc:
        print(f"[MAIN] WARNING: Neo4j unavailable — {exc}")
        print("[MAIN] Continuing in DB-less mode (detections printed only).")
        db_driver = None
    else:
        db_driver = get_driver()

    # ── 2. Open camera / video source ───────────────────────
    cap = cv2.VideoCapture(settings.CAMERA_SOURCE)
    if not cap.isOpened():
        print(f"[MAIN] ERROR: Could not open camera source: {settings.CAMERA_SOURCE}")
        sys.exit(1)

    fps_source = cap.get(cv2.CAP_PROP_FPS) or 30
    print(f"[MAIN] Stream opened — source FPS ≈ {fps_source:.1f}")
    print("[MAIN] Pipeline running — press Q in preview window or Ctrl+C to stop.\n")

    # ── 3. Initialise ByteTrack tracker ──────────────────────
    tracker = ByteTrackWrapper(
        model_name=settings.YOLO_MODEL,
        confidence=settings.CONFIDENCE_THRESHOLD,
    )

    # ── 4. Main processing loop ───────────────────────────────
    frame_num   = 0
    saved_count = 0

    while _running:
        ret, frame = cap.read()
        if not ret:
            print("[MAIN] Stream ended or frame read failed — exiting loop.")
            break

        frame_num += 1

        # Skip frames to reduce CPU/GPU load.
        # FRAME_SKIP=2 means: process frames 1, 4, 7, 10 …
        if (frame_num - 1) % (settings.FRAME_SKIP + 1) != 0:
            continue

        # ── 4a. Run YOLOv8 + ByteTrack ───────────────────────
        tracked_objects = tracker.track(frame)

        # ── 4b. Console output ───────────────────────────────
        print_frame_summary(frame_num, tracked_objects)

        # ── 4c. Save evidence + write to Neo4j ───────────────
        # Only trigger when there are enough detections to be meaningful.
        if len(tracked_objects) >= settings.MIN_DETECTIONS_TO_SAVE:

            # Determine dominant event type from tracked objects
            # (simple majority vote — Phase 2 will use richer logic)
            class_counts: dict[str, int] = {}
            for obj in tracked_objects:
                cls = obj["class_name"]
                class_counts[cls] = class_counts.get(cls, 0) + 1
            dominant_class = max(class_counts, key=class_counts.get)
            event_type = CLASS_TO_EVENT.get(dominant_class, "OBJECT_DETECTED")

            # Average confidence across all detections in this frame
            avg_confidence = sum(o["confidence"] for o in tracked_objects) / len(tracked_objects)

            # Save annotated screenshot to disk
            evidence_path = save_screenshot(
                frame=frame,
                tracked_objects=tracked_objects,
                camera_id=settings.CAMERA_ID,
                event_type=event_type,
                evidence_dir=settings.EVIDENCE_DIR,
            )
            saved_count += 1
            print(f"  [EVIDENCE] Screenshot saved → {evidence_path}")

            # Write DetectionEvent node to Neo4j
            if db_driver:
                track_ids = [o["track_id"] for o in tracked_objects]
                event_id  = save_detection_event(
                    driver=db_driver,
                    camera_id=settings.CAMERA_ID,
                    event_type=event_type,
                    confidence=avg_confidence,
                    evidence_path=evidence_path,
                    track_ids=track_ids,
                )
                print(f"  [DB]       DetectionEvent → {event_id}")

        # ── 4d. Show live preview window ─────────────────────
        # Draw bounding boxes on a preview copy (doesn't affect saved screenshots)
        preview = frame.copy()
        for obj in tracked_objects:
            x1, y1, x2, y2 = obj["bbox"]
            cv2.rectangle(preview, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                preview,
                f"#{obj['track_id']} {obj['class_name']}",
                (x1, y1 - 6),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
            )

        cv2.imshow(WINDOW_NAME, preview)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("[MAIN] Q pressed — stopping.")
            break

    # ── 5. Cleanup ────────────────────────────────────────────
    print(f"\n[MAIN] Processed {frame_num} frames | Saved {saved_count} screenshots")
    cap.release()
    cv2.destroyAllWindows()

    if db_driver:
        update_camera_status(db_driver, settings.CAMERA_ID, "OFFLINE")
        db_close()

    print("[MAIN] Pipeline shut down cleanly.")


if __name__ == "__main__":
    main()
