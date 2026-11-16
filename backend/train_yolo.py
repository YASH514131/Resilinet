import os
import shutil
import torch
import ultralytics
from ultralytics import YOLO

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


def train_model():
    model = YOLO("yolov8m.pt")
    device = 0 if torch.cuda.is_available() else "cpu"
    data_yaml = os.path.abspath("backend/datasets/unified_incidents/data.yaml")

    if not os.path.exists(data_yaml):
        print(f"Data config not found: {data_yaml}")
        return

    results = model.train(
        data=data_yaml,
        epochs=50,
        imgsz=640,
        batch=8 if device == 0 else 4,
        device=device,
        workers=4,
        optimizer="auto",
        lr0=0.01,
        lrf=0.01,
        cos_lr=True,
        patience=15,
        mosaic=1.0,
        mixup=0.15,
        fliplr=0.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        project="runs/incident_detector",
        name="yolov8m_production",
        save=True,
        plots=True,
        exist_ok=True
    )

    best_weights = os.path.join("runs", "incident_detector", "yolov8m_production", "weights", "best.pt")
    target_clean_path = os.path.join("backend", "incident_yolov8n.pt")
    target_medium_path = os.path.join("backend", "incident_yolov8m.pt")

    if os.path.exists(best_weights):
        shutil.copy2(best_weights, target_clean_path)
        shutil.copy2(best_weights, target_medium_path)
        print(f"Saved weights to {target_medium_path}")
    return results


if __name__ == "__main__":
    train_model()
