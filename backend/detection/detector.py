# detection/detector.py
#
# Thin wrapper around Ultralytics YOLOv8.
# Loads the pretrained model once and exposes a single detect() method
# that returns a clean list of detection dicts per frame.

from ultralytics import YOLO
import numpy as np
import torch
import ultralytics

# COCO class names that are relevant for urban CCTV monitoring.
# We filter out irrelevant classes (e.g. toothbrush, sandwich) to
# reduce noise. Add or remove class names here as needed.
RELEVANT_CLASSES = {
    "person", "bicycle", "car", "motorcycle", "bus", "truck",
    "traffic light", "stop sign", "fire hydrant",
}


class YOLODetector:
    """
    Pretrained YOLOv8 detector.

    Args:
        model_name: YOLOv8 model variant.
                    'yolov8n' = nano (fastest, least accurate) — good for CPU.
                    'yolov8s' = small  |  'yolov8m' = medium  |  'yolov8l' = large.
                    Weights are auto-downloaded from Ultralytics on first run.
        confidence: Minimum detection confidence threshold (0.0 – 1.0).
        device:     'cpu' | 'cuda' | 'mps' (Apple Silicon).
                    Pass None to auto-select (GPU if available, else CPU).
    """

    def __init__(self, model_name: str = "yolov8n.pt",
                 confidence: float = 0.45, device: str | None = None):
        self.confidence = confidence
        # Ensure torch will allow deserializing ultralytics DetectionModel
        # (PyTorch 2.6+ changed safe-loading defaults; allowlist if available)
        if hasattr(torch, 'serialization') and hasattr(torch.serialization, 'add_safe_globals'):
            try:
                torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])
            except Exception:
                pass

        # Some PyTorch versions also require passing `weights_only=False` to
        # `torch.load` when loading older checkpoints. Monkeypatch torch.load
        # to set weights_only=False by default for compatibility (trusted source).
        if hasattr(torch, 'load'):
            _orig_torch_load = torch.load
            def _patched_torch_load(f, *args, **kwargs):
                if 'weights_only' not in kwargs:
                    kwargs['weights_only'] = False
                return _orig_torch_load(f, *args, **kwargs)
            torch.load = _patched_torch_load

        self.model = YOLO(model_name)
        self.device = device  # None = auto
        print(f"[YOLO] Loaded model: {model_name}  confidence≥{confidence}")

    def detect(self, frame: np.ndarray) -> list[dict]:
        """
        Run inference on a single BGR frame (OpenCV format).

        Returns a list of detections, each a dict:
        {
            "class_name":  str,    # e.g. "car"
            "confidence":  float,  # e.g. 0.87
            "bbox":        [x1, y1, x2, y2],  # pixel coords
        }

        Note: ByteTrack is applied SEPARATELY in tracker.py using the
        raw YOLO Results object. This method is kept for standalone use
        (e.g. single-frame testing without tracking).
        """
        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            device=self.device,
            verbose=False,   # suppress per-frame console spam from YOLO
        )

        detections = []
        if not results:
            return detections

        result = results[0]  # single frame → single result
        for box in result.boxes:
            class_id   = int(box.cls[0])
            class_name = self.model.names[class_id]

            # Filter to relevant CCTV classes only
            if class_name not in RELEVANT_CLASSES:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            detections.append({
                "class_name": class_name,
                "confidence": float(box.conf[0]),
                "bbox":       [int(x1), int(y1), int(x2), int(y2)],
            })

        return detections

    def raw_predict(self, frame: np.ndarray):
        """
        Return raw Ultralytics Results object — used by ByteTrackWrapper
        in tracker.py so the tracker can access the internal tensor format
        it needs directly.
        """
        return self.model.predict(
            source=frame,
            conf=self.confidence,
            device=self.device,
            verbose=False,
        )
