import os
import time
import cv2
import numpy as np

CLASS_COLORS = {
    "car_accident": (0, 0, 255),
    "fire": (0, 69, 255),
    "smoke": (180, 180, 180),
    "flood": (255, 191, 0),
    "person": (0, 165, 255),
    "car": (0, 255, 0),
    "truck": (0, 0, 255),
    "bus": (255, 0, 255),
    "motorcycle": (255, 255, 0),
    "bicycle": (128, 255, 0),
    "traffic light": (0, 255, 255),
    "stop sign": (0, 64, 255),
    "fire hydrant": (255, 0, 128),
}
DEFAULT_COLOR = (200, 200, 200)


def save_screenshot(frame: np.ndarray, tracked_objects: list[dict],
                    camera_id: str, event_type: str,
                    evidence_dir: str = "./evidence_screenshots") -> str:
    os.makedirs(evidence_dir, exist_ok=True)
    annotated = frame.copy()

    for obj in tracked_objects:
        x1, y1, x2, y2 = obj["bbox"]
        track_id = obj["track_id"]
        class_name = obj["class_name"]
        confidence = obj["confidence"]
        color = CLASS_COLORS.get(class_name, DEFAULT_COLOR)

        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, thickness=2)
        label = f"{class_name} #{track_id} {int(confidence * 100)}%"

        (text_w, text_h), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1
        )
        label_y = max(y1 - 6, text_h + 4)
        cv2.rectangle(
            annotated,
            (x1, label_y - text_h - 4),
            (x1 + text_w + 4, label_y + baseline),
            color,
            thickness=-1,
        )
        cv2.putText(
            annotated, label,
            (x1 + 2, label_y - 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55, (0, 0, 0), thickness=1, lineType=cv2.LINE_AA,
        )

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

    unix_ts = int(time.time())
    filename = f"{camera_id}_{event_type}_{unix_ts}.jpg"
    filepath = os.path.join(evidence_dir, filename)

    cv2.imwrite(filepath, annotated, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return filepath
