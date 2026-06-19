# ResiliNet AI — Phase 1 CCTV Detection Pipeline

> **Reference implementation** for the Smart CCTV Monitoring System.  
> This pipeline is the starting point for your team. It is intentionally minimal — every component is real and functional, but Phase 2 event logic, FastAPI integration, and the React/Flutter extensions are deliberately out of scope here.

---

## What This Pipeline Does

```
[Camera / Webcam / RTSP]
        │
        ▼
[YOLOv8n — Pretrained on COCO]   ← detects cars, trucks, persons, bikes …
        │
        ▼
[ByteTrack Tracker]               ← assigns persistent track IDs across frames
        │
        ├──▶ [Console Output]     ← frame-by-frame summary printed to terminal
        │
        ├──▶ [Evidence Screenshot]← annotated JPEG saved to ./evidence_screenshots/
        │
        └──▶ [Neo4j Write]        ← DetectionEvent node created, linked to Camera
```

No FastAPI, no LLM, no React, no Flutter. Just the **computer vision layer**, grounded in Neo4j. This is exactly what Phase 1 of the PRD specifies.

---

## Project Structure

```
phase1_pipeline/
├── main.py                     ← Entry point — run this
│
├── config/
│   └── settings.py             ← Loads all config from .env
│
├── detection/
│   └── detector.py             ← YOLOv8 inference wrapper (single-frame, no tracking)
│
├── tracking/
│   └── tracker.py              ← YOLOv8 + ByteTrack (what main.py actually uses)
│
├── evidence/
│   └── capture.py              ← Annotates frames + saves JPEG screenshots
│
├── neo4j/
│   ├── database.py             ← Driver connection (connect / close / get_driver)
│   ├── writer.py               ← Cypher writes: DetectionEvent nodes
│   └── schema_and_seed.cypher  ← Run once in Neo4j Browser to set up schema + seed data
│
├── evidence_screenshots/       ← Created automatically; screenshots land here
│
├── .env.example                ← Copy to .env and fill in your values
└── requirements.txt
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | 3.10 works but 3.11 is faster |
| Neo4j | 5.x | Docker command below; free Community Edition |
| GPU (optional) | CUDA 12.x | CPU mode works — slower per-camera FPS |
| Webcam or RTSP camera | — | USB webcam on `0` works for local testing |

---

## Setup — Step by Step

### 1. Clone and create a virtual environment

```bash
git clone <your-repo-url>
cd phase1_pipeline

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

On first run, `ultralytics` will **automatically download `yolov8n.pt`** (~6 MB) from the Ultralytics CDN. You do not need to download it manually.

> **GPU acceleration (optional):** If you have an NVIDIA GPU, install the CUDA-enabled PyTorch before the rest:
> ```bash
> pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
> pip install -r requirements.txt
> ```

### 3. Start Neo4j with Docker

```bash
docker run -d \
  --name resilinet-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

Wait ~10 seconds, then open **http://localhost:7474** in your browser.  
Log in with `neo4j / password`.

### 4. Run the Neo4j schema and seed data

In the Neo4j Browser query box, paste and run the contents of:

```
neo4j/schema_and_seed.cypher
```

This creates:
- Uniqueness constraints on `Camera.id` and `DetectionEvent.id`
- A point index on `Location.coordinates`
- 3 seed `Camera` nodes (`cam-001`, `cam-002`, `cam-003`)
- 3 seed `Location` nodes
- `POSITIONED_AT` relationships linking each camera to its location

**Verify it worked** by running this in the Neo4j Browser:

```cypher
MATCH (c:Camera)-[:POSITIONED_AT]->(l:Location)
RETURN c.id, c.name, c.status, c.zone, l.id
ORDER BY c.id;
```

You should see 3 rows.

### 5. Configure your environment

```bash
cp .env.example .env
```

Open `.env` and edit:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

EVIDENCE_DIR=./evidence_screenshots

# For a USB webcam:
CAMERA_SOURCE=0
CAMERA_ID=cam-001
CAMERA_NAME=Test Camera 1

# For an RTSP stream:
# CAMERA_SOURCE=rtsp://admin:password@192.168.1.64:554/stream
# CAMERA_ID=cam-002
# CAMERA_NAME=Camera-02 (Central Market)

CONFIDENCE_THRESHOLD=0.45
YOLO_MODEL=yolov8n.pt
FRAME_SKIP=2
MIN_DETECTIONS_TO_SAVE=1
```

### 6. Run the pipeline

```bash
python main.py
```

---

## What You'll See

### Terminal output

```
============================================================
  ResiliNet AI — Phase 1 CCTV Detection Pipeline
============================================================
  Camera ID   : cam-001
  Camera Name : Test Camera 1
  Source      : 0
  YOLO Model  : yolov8n.pt
  Confidence  : 0.45
  Evidence Dir: ./evidence_screenshots
  Frame Skip  : every 3 frame(s) processed
============================================================
[DB] Connected to Neo4j at bolt://localhost:7687
[DB] Camera cam-001 status → ACTIVE
[YOLO] Loaded model: yolov8n.pt  confidence≥0.45
[TRACKER] ByteTrack ready — model=yolov8n.pt  conf≥0.45
[MAIN] Stream opened — source FPS ≈ 30.0
[MAIN] Pipeline running — press Q in preview window or Ctrl+C to stop.

  Frame 0001 — no detections above threshold

┌─ Frame 0004 ─ 2 object(s) detected ──────────────────────────┐
│  #1   car          conf=0.91  bbox=[245, 130, 412, 290]
│  #2   person       conf=0.85  bbox=[ 90, 200, 150, 450]
└───────────────────────────────────────────────────────────────┘
  [EVIDENCE] Screenshot saved → ./evidence_screenshots/cam-001_VEHICLE_DETECTED_1718000042.jpg
  [DB]       DetectionEvent → det-3f8a1c72b901

┌─ Frame 0007 ─ 3 object(s) detected ──────────────────────────┐
│  #1   car          conf=0.89  bbox=[260, 132, 420, 292]
│  #2   person       conf=0.83  bbox=[ 92, 205, 153, 448]
│  #3   car          conf=0.74  bbox=[510, 145, 680, 305]
└───────────────────────────────────────────────────────────────┘
  [EVIDENCE] Screenshot saved → ./evidence_screenshots/cam-001_VEHICLE_DETECTED_1718000043.jpg
  [DB]       DetectionEvent → det-9c2b4e17d530
```

### OpenCV preview window

A live window titled **"ResiliNet Phase 1 — cam-001"** shows the camera feed with green bounding boxes and track IDs drawn in real time. Press **Q** to stop.

### Evidence screenshots

The `./evidence_screenshots/` folder fills with annotated JPEGs:

```
evidence_screenshots/
├── cam-001_VEHICLE_DETECTED_1718000042.jpg
├── cam-001_VEHICLE_DETECTED_1718000043.jpg
└── cam-001_PERSON_DETECTED_1718000055.jpg
```

Each image has:
- Coloured bounding boxes per class (car = green, person = orange, truck = red …)
- Label pills showing: `car #1  91%`
- Top-left overlay: Camera ID, Event Type, UTC timestamp

### Neo4j graph

After running, query your graph to see the written data:

```cypher
// All DetectionEvents with their camera and location
MATCH (d:DetectionEvent)-[:DETECTED_BY]->(c:Camera)-[:POSITIONED_AT]->(l:Location)
RETURN d.id, d.event_type, d.confidence, d.triggered_at,
       c.name, l.id
ORDER BY d.triggered_at DESC
LIMIT 20;
```

```cypher
// Count DetectionEvents per camera
MATCH (d:DetectionEvent)-[:DETECTED_BY]->(c:Camera)
RETURN c.id, c.name, count(d) AS total_events
ORDER BY total_events DESC;
```

---

## Neo4j Schema Reference

### Node Types

**`Camera`**
| Property | Type | Example |
|---|---|---|
| `id` | String (unique) | `cam-001` |
| `name` | String | `Camera-01 (MG Road Junction)` |
| `rtsp_url` | String | `webcam:0` or `rtsp://…` |
| `status` | String | `ACTIVE` \| `OFFLINE` \| `MAINTENANCE` |
| `fov_degrees` | Float | `90.0` |
| `fps_target` | Integer | `5` |
| `zone` | String | `traffic` \| `crowd` \| `infrastructure` |

**`DetectionEvent`**
| Property | Type | Example |
|---|---|---|
| `id` | String (unique) | `det-3f8a1c72b901` |
| `event_type` | String | `VEHICLE_DETECTED` \| `PERSON_DETECTED` |
| `confidence` | Float | `0.8750` |
| `evidence_path` | String | `./evidence_screenshots/cam-001_…jpg` |
| `track_ids` | String[] | `["1", "2", "3"]` |
| `triggered_at` | DateTime | `2025-06-19T10:32:00Z` |
| `resolved_at` | DateTime \| null | `null` (set in Phase 2) |

**`Location`**
| Property | Type | Example |
|---|---|---|
| `id` | String (unique) | `loc-18.5204-73.8567` |
| `coordinates` | Point | `point({latitude: 18.5204, longitude: 73.8567})` |

### Relationships

```
(Camera)-[:POSITIONED_AT]->(Location)
(DetectionEvent)-[:DETECTED_BY]->(Camera)
(DetectionEvent)-[:LOCATED_AT]->(Location)
```

### Visual graph (3-node pattern for one detection)

```
(DetectionEvent: det-3f8a1c72b901)
        │
        ├──[:DETECTED_BY]──► (Camera: cam-001)
        │                             │
        │                    [:POSITIONED_AT]
        │                             │
        └──[:LOCATED_AT]──────────────▼
                            (Location: loc-18.5204-73.8567)
```

---

## Configuration Reference

All settings live in `.env`. Full reference:

| Variable | Default | Description |
|---|---|---|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j bolt connection string |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `password` | Neo4j password |
| `CAMERA_SOURCE` | `0` | `0` for webcam, or RTSP URL |
| `CAMERA_ID` | `cam-001` | Must match an existing Camera node in Neo4j |
| `CAMERA_NAME` | `Test Camera 1` | Display label |
| `YOLO_MODEL` | `yolov8n.pt` | Nano=fastest; also: `yolov8s.pt` `yolov8m.pt` |
| `CONFIDENCE_THRESHOLD` | `0.45` | Detections below this are ignored |
| `EVIDENCE_DIR` | `./evidence_screenshots` | Where JPEGs are saved |
| `FRAME_SKIP` | `2` | Process 1 in every N+1 frames. `0` = every frame |
| `MIN_DETECTIONS_TO_SAVE` | `1` | Min objects in a frame to trigger screenshot + DB write |

---

## Choosing a YOLO Model

| Model | File | Speed | Accuracy | Recommended for |
|---|---|---|---|---|
| `yolov8n.pt` | ~6 MB | ★★★★★ | ★★☆☆☆ | CPU, Raspberry Pi, initial testing |
| `yolov8s.pt` | ~22 MB | ★★★★☆ | ★★★☆☆ | CPU with decent specs, or light GPU |
| `yolov8m.pt` | ~52 MB | ★★★☆☆ | ★★★★☆ | GPU recommended |
| `yolov8l.pt` | ~87 MB | ★★☆☆☆ | ★★★★★ | Dedicated GPU, production |

For Phase 1 testing, **`yolov8n.pt` (nano)** is the right choice. Switch to `yolov8s` or `yolov8m` once you have GPU infrastructure confirmed.

---

## Detected Classes

The pipeline filters YOLO's 80 COCO classes down to these CCTV-relevant ones:

| Class | Event Type Written to Neo4j | Bounding Box Colour |
|---|---|---|
| `car` | `VEHICLE_DETECTED` | Green |
| `truck` | `VEHICLE_DETECTED` | Red |
| `bus` | `VEHICLE_DETECTED` | Magenta |
| `motorcycle` | `VEHICLE_DETECTED` | Cyan |
| `bicycle` | `VEHICLE_DETECTED` | Lime |
| `person` | `PERSON_DETECTED` | Orange |
| `traffic light` | `OBJECT_DETECTED` | Yellow |
| `stop sign` | `OBJECT_DETECTED` | Orange-red |
| `fire hydrant` | `OBJECT_DETECTED` | Pink |

> **Phase 2 note:** The `CLASS_TO_EVENT` mapping in `main.py` and the event logic engine will expand this into `ACCIDENT_DETECTED`, `TRAFFIC_CONGESTION`, `CROWD_SURGE`, etc. based on track history — not just instantaneous class labels.

---

## Running Without Neo4j

If Neo4j is not running, the pipeline **does not crash**. It prints a warning and continues in DB-less mode:

```
[MAIN] WARNING: Neo4j unavailable — [Errno 111] Connection refused
[MAIN] Continuing in DB-less mode (detections printed only).
```

Console output and screenshot saving still work normally. This is useful for testing the vision layer in isolation before setting up the database.

---

## How ByteTrack Works (Plain English)

YOLO answers: **"what is in this frame?"** — but it treats every frame independently. Run it on 30 frames and you get 30 independent detection lists with no connection between them.

ByteTrack answers: **"which object in frame 31 is the same object as in frame 30?"** — it assigns each detected object a persistent integer `track_id` that follows it across frames, surviving brief occlusions (e.g. a car passing behind a lamppost).

This matters for Phase 2 event logic because:
- "A vehicle has been stationary for 30 seconds" requires knowing it's the **same** vehicle across 900 frames — that's `track_id` doing the work.
- "Two vehicles collided" requires detecting that `track_id=5` and `track_id=9` were moving and then both suddenly stopped near each other.

In Ultralytics, ByteTrack is activated by calling `model.track()` instead of `model.predict()`, with `persist=True`. That single flag is what connects detections across frames.

---

## Stopping the Pipeline

| Method | Effect |
|---|---|
| Press **Q** in the preview window | Graceful shutdown |
| **Ctrl+C** in the terminal | Graceful shutdown via SIGINT handler |
| Close the terminal | Abrupt stop — Neo4j camera status not updated to OFFLINE |

On graceful shutdown:
1. The camera's `status` is set to `OFFLINE` in Neo4j.
2. The OpenCV window closes.
3. The Neo4j driver connection pool closes cleanly.
4. A summary of frames processed and screenshots saved is printed.

---

## Troubleshooting

**`Could not open camera source: 0`**  
Your webcam is on a different index. Try `CAMERA_SOURCE=1` or `CAMERA_SOURCE=2` in `.env`.

**`Neo4j unavailable — Authentication failure`**  
Check `NEO4J_USER` and `NEO4J_PASSWORD` in `.env` match what you set in the Docker command.

**`Camera node not found` (no DetectionEvent created)**  
The `CAMERA_ID` in `.env` must match the `id` of an existing Camera node. Make sure you ran `schema_and_seed.cypher` first, or add your camera ID there.

**Very slow FPS on CPU**  
Increase `FRAME_SKIP` (e.g. `FRAME_SKIP=4` means 1 in 5 frames processed). Use `yolov8n.pt` (nano). Close other applications.

**`bytetrack.yaml not found`**  
Reinstall ultralytics: `pip install --upgrade ultralytics`. The config file ships with the package.

---

## What's NOT in Phase 1 (Coming in Phase 2+)

| Feature | Phase |
|---|---|
| Accident / congestion / crowd surge event rules | Phase 2 |
| Automatic POST to ResiliNet FastAPI `/report` | Phase 2 |
| Duplicate suppression (60s window) | Phase 2 |
| Camera marker on React Command Center map | Phase 3 |
| Evidence thumbnail in Flutter Field App | Phase 3 |
| GraphRAG camera context for LLM prompt | Phase 4 |
| Custom YOLO fine-tuning (waterlogging, drain blockage) | Phase 5 |

---

## Connecting to the Full ResiliNet Stack (Preview)

When Phase 2 is ready, the only change needed in this pipeline is adding one async call to `reporting/incident_reporter.py` at the point where a screenshot is saved. The Neo4j schema written here (Camera + DetectionEvent nodes) slots directly into the existing ResiliNet graph — no schema migration needed.

The Phase 2 call will look like:

```python
# Phase 2 addition in main.py — not needed yet
await incident_reporter.post(
    description=f"{settings.CAMERA_ID} detected {event_type} — {len(tracked_objects)} objects",
    category=EVENT_TO_CATEGORY[event_type],
    latitude=camera_lat,
    longitude=camera_lng,
    source=f"cctv_{settings.CAMERA_ID}",
)
```

Everything else — the GraphRAG retrieval, LLM dispatch, WebSocket broadcast, React map update, Flutter notification — happens automatically in the existing ResiliNet backend.

---

## File Checklist Before Running

```
✅  .env               (copied from .env.example and edited)
✅  Neo4j running      (docker ps shows resilinet-neo4j)
✅  schema_and_seed.cypher run in Neo4j Browser
✅  pip install -r requirements.txt complete
✅  Camera or webcam plugged in (if using CAMERA_SOURCE=0)
```

Then:

```bash
python main.py
```
