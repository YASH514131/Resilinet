# config/settings.py
#
# Loads all configuration from environment variables (set via .env).
# Import `settings` anywhere in the project — never read os.getenv()
# directly in other modules.

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env file if present; harmless if file is missing


class Settings:
    # ── Neo4j ────────────────────────────────────────────────
    NEO4J_URI:      str   = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
    NEO4J_USER:     str   = os.getenv("NEO4J_USER",     "neo4j")
    NEO4J_PASSWORD: str   = os.getenv("NEO4J_PASSWORD", "password")

    # ── Camera ───────────────────────────────────────────────
    # CAMERA_SOURCE accepts: "0" (webcam), an int, or an RTSP URL string.
    _raw_source: str = os.getenv("CAMERA_SOURCE", "0")
    CAMERA_SOURCE: int | str = int(_raw_source) if _raw_source.isdigit() else _raw_source
    CAMERA_ID:   str = os.getenv("CAMERA_ID",   "cam-001")
    CAMERA_NAME: str = os.getenv("CAMERA_NAME", "Test Camera 1")

    # ── Detection ────────────────────────────────────────────
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))
    YOLO_MODEL:           str   = os.getenv("YOLO_MODEL", "yolov8n.pt")

    # ── Evidence storage ─────────────────────────────────────
    EVIDENCE_DIR: str = os.getenv("EVIDENCE_DIR", "./evidence_screenshots")

    # ── Pipeline tuning ──────────────────────────────────────
    # How many frames to skip between processed frames.
    # FRAME_SKIP=0 → process every frame (heavy on CPU/GPU)
    # FRAME_SKIP=2 → process 1 in every 3 frames (good default for 30fps input)
    FRAME_SKIP: int = int(os.getenv("FRAME_SKIP", "2"))

    # Minimum detections in a single frame to trigger a screenshot + DB write.
    # Keeps noise low — e.g. a lone person walking doesn't save to DB.
    MIN_DETECTIONS_TO_SAVE: int = int(os.getenv("MIN_DETECTIONS_TO_SAVE", "1"))

    # If true, only save/write frames that match the accident detection
    # heuristic. Default is false to preserve legacy behaviour.
    ONLY_SAVE_ACCIDENTS: bool = os.getenv("ONLY_SAVE_ACCIDENTS", "false").lower() in ("1", "true", "yes")


settings = Settings()
