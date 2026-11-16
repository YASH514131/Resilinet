import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")

    _raw_source: str = os.getenv("CAMERA_SOURCE", "0")
    if _raw_source.isdigit():
        CAMERA_SOURCE: int | str = int(_raw_source)
    else:
        if not os.path.isabs(_raw_source) and not _raw_source.startswith("rtsp://") and not _raw_source.startswith("http://"):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidate = os.path.join(base_dir, _raw_source.lstrip("./"))
            CAMERA_SOURCE = candidate if os.path.exists(candidate) else _raw_source
        else:
            CAMERA_SOURCE = _raw_source

    CAMERA_ID: str = os.getenv("CAMERA_ID", "cam-001")
    CAMERA_NAME: str = os.getenv("CAMERA_NAME", "Test Camera 1")
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.40"))

    _default_model = "incident_yolov8m.pt"
    _base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _cand1 = os.path.join(_base_dir, "incident_yolov8m.pt")
    _cand2 = os.path.join(_base_dir, "incident_yolov8n.pt")
    if os.path.exists(_cand1):
        _default_model = _cand1
    elif os.path.exists(_cand2):
        _default_model = _cand2
    else:
        _default_model = "yolov8m.pt"

    YOLO_MODEL: str = os.getenv("YOLO_MODEL", _default_model)
    EVIDENCE_DIR: str = os.getenv("EVIDENCE_DIR", "./evidence_screenshots")
    FRAME_SKIP: int = int(os.getenv("FRAME_SKIP", "2"))
    MIN_DETECTIONS_TO_SAVE: int = int(os.getenv("MIN_DETECTIONS_TO_SAVE", "1"))
    ONLY_SAVE_ACCIDENTS: bool = os.getenv("ONLY_SAVE_ACCIDENTS", "false").lower() in ("1", "true", "yes")


settings = Settings()
