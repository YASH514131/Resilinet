import os
import sys
import time
import argparse
import numpy as np
import torch
from pathlib import Path
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


def evaluate_dataset(model_path: str, data_yaml: str, split: str = "test", device: str = None, imgsz: int = 640):
    if not os.path.exists(data_yaml):
        print(f"Data config not found: {data_yaml}")
        return None

    model = YOLO(model_path)
    metrics = model.val(
        data=data_yaml,
        split=split,
        imgsz=imgsz,
        batch=16,
        conf=0.25,
        iou=0.6,
        device=device or ("cuda:0" if torch.cuda.is_available() else "cpu"),
        save_json=True,
        plots=True,
        verbose=True
    )

    mp = metrics.box.mp
    mr = metrics.box.mr
    map50 = metrics.box.map50
    map95 = metrics.box.map
    f1 = 2 * (mp * mr) / (mp + mr + 1e-16)

    print("-" * 50)
    print(f"Precision : {mp:.4f}")
    print(f"Recall    : {mr:.4f}")
    print(f"mAP@50    : {map50:.4f}")
    print(f"mAP@50-95 : {map95:.4f}")
    print(f"F1        : {f1:.4f}")
    print("-" * 50)

    names = model.names
    for cls_idx, class_name in names.items():
        if cls_idx < len(metrics.box.p):
            p = metrics.box.p[cls_idx]
            r = metrics.box.r[cls_idx]
            ap50 = metrics.box.ap50[cls_idx]
            ap = metrics.box.ap[cls_idx]
            print(f"{class_name:<16} P: {p:.3f}  R: {r:.3f}  mAP50: {ap50:.3f}  mAP: {ap:.3f}")
    return metrics


def benchmark_inference_speed(model_path: str, imgsz: int = 640, num_warmup: int = 20, num_runs: int = 100):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = YOLO(model_path)
    dummy_frame = np.random.randint(0, 255, (imgsz, imgsz, 3), dtype=np.uint8)

    for _ in range(num_warmup):
        _ = model.predict(dummy_frame, verbose=False, device=device)

    latencies = []
    for _ in range(num_runs):
        t0 = time.perf_counter()
        _ = model.predict(dummy_frame, verbose=False, device=device)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

    latencies = np.array(latencies)
    mean_lat = np.mean(latencies)
    fps = 1000.0 / mean_lat

    print("-" * 40)
    print(f"Mean Latency : {mean_lat:.2f} ms")
    print(f"Throughput   : {fps:.1f} FPS")
    print("-" * 40)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="backend/incident_yolov8m.pt")
    parser.add_argument("--data", type=str, default="backend/datasets/unified_incidents/data.yaml")
    parser.add_argument("--split", type=str, default="test")
    parser.add_argument("--benchmark-speed", action="store_true")
    args = parser.parse_args()

    if args.benchmark_speed:
        benchmark_inference_speed(args.model)
    else:
        evaluate_dataset(args.model, args.data, split=args.split)
