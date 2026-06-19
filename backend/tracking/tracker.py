# tracking/tracker.py
#
# ByteTrack is built into Ultralytics — calling model.track() instead of
# model.predict() activates it automatically. This wrapper keeps the tracking
# logic in one place and returns a clean, typed list of tracked objects.
#
# ByteTrack assigns each detected object a persistent integer track_id that
# survives across frames (even through brief occlusions). This is what lets
# the event engine later say "that same vehicle has been stationary for 30s."

import numpy as np
from ultralytics import YOLO
import torch
import ultralytics

RELEVANT_CLASSES = {
    "person", "bicycle", "car", "motorcycle", "bus", "truck",
    "traffic light", "stop sign", "fire hydrant",
}


class ByteTrackWrapper:
    """
    Wraps Ultralytics YOLOv8 + ByteTrack tracking.

    Using model.track() instead of model.predict() tells Ultralytics to
    run ByteTrack internally and attach a .id to each detected box.

    Args:
        model_name:  YOLOv8 weights file (auto-downloaded if not present).
        confidence:  Per-detection confidence threshold.
        device:      'cpu' | 'cuda' | 'mps' | None (auto).
        persist:     Keep tracker state across frames (MUST be True for
                     tracking to work — this is what maintains track IDs
                     between calls).
    """

    def __init__(self, model_name: str = "yolov8n.pt",
                 confidence: float = 0.45, device: str | None = None):
        self.confidence = confidence
        self.device     = device
        # Ensure torch will allow deserializing ultralytics DetectionModel
        # (PyTorch 2.6+ changed safe-loading defaults; allowlist if available)
        if hasattr(torch, 'serialization') and hasattr(torch.serialization, 'add_safe_globals'):
            try:
                torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])
            except Exception:
                pass

        # Monkeypatch torch.load to set weights_only=False by default so
        # older checkpoints with custom globals can be deserialized.
        if hasattr(torch, 'load'):
            _orig_torch_load = torch.load
            def _patched_torch_load(f, *args, **kwargs):
                if 'weights_only' not in kwargs:
                    kwargs['weights_only'] = False
                return _orig_torch_load(f, *args, **kwargs)
            torch.load = _patched_torch_load

        self.model      = YOLO(model_name)
        print(f"[TRACKER] ByteTrack ready — model={model_name}  conf≥{confidence}")

    def track(self, frame: np.ndarray) -> list[dict]:
        """
        Run YOLOv8 + ByteTrack on a single BGR frame.

        Returns a list of tracked objects, each a dict:
        {
            "track_id":    int,    # Persistent ID across frames (ByteTrack)
            "class_name":  str,    # e.g. "car"
            "confidence":  float,
            "bbox":        [x1, y1, x2, y2],
            "center":      (cx, cy),  # Pixel centroid — used for velocity calc
        }

        If a detection has no track_id (can happen on the very first frame),
        it is assigned track_id = -1 and still included.
        """
        # persist=True is critical: it tells Ultralytics to keep the tracker
        # state object alive between calls to this method.
        results = self.model.track(
            source=frame,
            conf=self.confidence,
            device=self.device,
            persist=True,    # ← DO NOT remove — tracker breaks without this
            verbose=False,
            tracker="bytetrack.yaml",  # Ultralytics ships this config file
        )

        tracked = []
        if not results:
            return tracked

        result = results[0]
        if result.boxes is None:
            return tracked

        for box in result.boxes:
            class_id   = int(box.cls[0])
            class_name = self.model.names[class_id]

            if class_name not in RELEVANT_CLASSES:
                continue

            # box.id is None if ByteTrack hasn't assigned an ID yet
            track_id = int(box.id[0]) if box.id is not None else -1

            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2

            tracked.append({
                "track_id":   track_id,
                "class_name": class_name,
                "confidence": round(float(box.conf[0]), 3),
                "bbox":       [x1, y1, x2, y2],
                "center":     (cx, cy),
            })

        return tracked
