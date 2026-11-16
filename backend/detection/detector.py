from ultralytics import YOLO
import numpy as np
import torch
import ultralytics

RELEVANT_CLASSES = {
    "car_accident", "fire", "smoke", "flood",
    "person", "bicycle", "car", "motorcycle", "bus", "truck",
    "traffic light", "stop sign", "fire hydrant",
}


class YOLODetector:
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

    def detect(self, frame: np.ndarray) -> list[dict]:
        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            device=self.device,
            verbose=False,
        )

        detections = []
        if not results:
            return detections

        result = results[0]
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = self.model.names[class_id]

            if class_name not in RELEVANT_CLASSES:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "class_name": class_name,
                "confidence": float(box.conf[0]),
                "bbox": [int(x1), int(y1), int(x2), int(y2)],
            })

        return detections

    def raw_predict(self, frame: np.ndarray):
        return self.model.predict(
            source=frame,
            conf=self.confidence,
            device=self.device,
            verbose=False,
        )
