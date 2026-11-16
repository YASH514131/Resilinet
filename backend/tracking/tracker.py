import numpy as np
import torch
import ultralytics
from ultralytics import YOLO

RELEVANT_CLASSES = {
    "car_accident", "fire", "smoke", "flood",
    "person", "bicycle", "car", "motorcycle", "bus", "truck",
    "traffic light", "stop sign", "fire hydrant",
}


class ByteTrackWrapper:
    def __init__(self, model_name: str = "backend/incident_yolov8m.pt",
                 confidence: float = 0.40, device: str | None = None):
        self.confidence = confidence
        self.device = device

        if hasattr(torch, 'serialization') and hasattr(torch.serialization, 'add_safe_globals'):
            try:
                torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])
            except Exception:
                pass

        if hasattr(torch, 'load'):
            _orig_torch_load = torch.load
            def _patched_torch_load(f, *args, **kwargs):
                if 'weights_only' not in kwargs:
                    kwargs['weights_only'] = False
                return _orig_torch_load(f, *args, **kwargs)
            torch.load = _patched_torch_load

        self.model = YOLO(model_name)

    def track(self, frame: np.ndarray) -> list[dict]:
        results = self.model.track(
            source=frame,
            conf=self.confidence,
            device=self.device,
            persist=True,
            verbose=False,
            tracker="bytetrack.yaml",
        )

        tracked = []
        if not results:
            return tracked

        result = results[0]
        if result.boxes is None:
            return tracked

        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]

            if class_name not in RELEVANT_CLASSES:
                continue

            track_id = int(box.id[0]) if box.id is not None else -1
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            tracked.append({
                "track_id": track_id,
                "class_name": class_name,
                "confidence": round(float(box.conf[0]), 3),
                "bbox": [x1, y1, x2, y2],
                "center": (cx, cy),
            })

        return tracked
