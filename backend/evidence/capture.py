# evidence/capture.py
#
# Saves annotated JPEG screenshots when a detection event fires.
# Draws bounding boxes, track IDs, class names, and confidence scores
# directly onto the frame before saving — so the saved image is
# self-explanatory when reviewed later.

import os
import time
import cv2
import numpy as np

# Colour palette per class (BGR format for OpenCV)
CLASS_COLORS = {
    "person":        (0,   165, 255),   # orange
    "car":           (0,   255,   0),   # green
    "truck":         (0,     0, 255),   # red
    "bus":           (255,   0, 255),   # magenta
    "motorcycle":    (255, 255,   0),   # cyan
    "bicycle":       (128, 255,   0),   # lime
    "traffic light": (0,   255, 255),   # yellow
    "stop sign":     (0,    64, 255),   # orange-red
    "fire hydrant":  (255,   0, 128),   # pink
}
DEFAULT_COLOR = (200, 200, 200)  # grey for any unlisted class


def save_screenshot(frame: np.ndarray, tracked_objects: list[dict],
                    camera_id: str, event_type: str,
                    evidence_dir: str = "./evidence_screenshots") -> str:
    """
    Draw bounding boxes + track IDs on the frame, then save as JPEG.

    Args:
        frame:           Raw BGR frame from OpenCV.
        tracked_objects: List of dicts from ByteTrackWrapper.track().
        camera_id:       Camera identifier (used in filename).
        event_type:      Event that triggered the screenshot (used in filename).
        evidence_dir:    Directory to write screenshots into.

    Returns:
        Full file path of the saved screenshot.
    """
    os.makedirs(evidence_dir, exist_ok=True)

    # Work on a copy so the original frame is never mutated
    annotated = frame.copy()

    for obj in tracked_objects:
        x1, y1, x2, y2 = obj["bbox"]
        track_id   = obj["track_id"]
        class_name = obj["class_name"]
        confidence = obj["confidence"]
        color      = CLASS_COLORS.get(class_name, DEFAULT_COLOR)

        # Draw bounding box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness=2)

        # Build label: "car #7  87%"
        label = f"{class_name} #{track_id}  {int(confidence * 100)}%"

        # Background pill for the label (so text is readable on any background)
        (text_w, text_h), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1
        )
        label_y = max(y1 - 6, text_h + 4)
        cv2.rectangle(
            annotated,
            (x1, label_y - text_h - 4),
            (x1 + text_w + 4, label_y + baseline),
            color,
            thickness=-1,  # filled
        )
        cv2.putText(
            annotated, label,
            (x1 + 2, label_y - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55, (0, 0, 0), thickness=1, lineType=cv2.LINE_AA,
        )

    # Overlay: camera ID + event type + timestamp in top-left corner
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    overlay_lines = [
        f"Camera: {camera_id}",
        f"Event:  {event_type}",
        f"Time:   {timestamp_str}",
    ]
    y_offset = 24
    for line in overlay_lines:
        cv2.putText(
            annotated, line,
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (255, 255, 255), 2, cv2.LINE_AA,
        )
        cv2.putText(
            annotated, line,
            (10, y_offset),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6, (0, 0, 0), 1, cv2.LINE_AA,
        )
        y_offset += 24

    # Filename: cam-001_PERSON_DETECTED_1718000000.jpg
    unix_ts  = int(time.time())
    filename = f"{camera_id}_{event_type}_{unix_ts}.jpg"
    filepath = os.path.join(evidence_dir, filename)

    # JPEG quality=92 balances file size vs. readability of bounding boxes
    cv2.imwrite(filepath, annotated, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return filepath
