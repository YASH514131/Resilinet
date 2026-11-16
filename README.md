# ResiliNet AI — Smart City Incident Detection & Emergency Response

> **Autonomous Real-Time Vision & Knowledge Graph System for Urban Disaster Management**  
> Powered by **YOLOv8-Medium**, **ByteTrack**, **Neo4j Graph Database**, and **GraphQL/FastAPI**, providing live incident dispatch across **React Command Center** and **Flutter Mobile Responders**.

---

## 📌 Executive Overview

ResiliNet AI monitors real-time urban CCTV feeds to automatically detect hazards, track emergency severity, and orchestrate immediate dispatch of nearby first responders (ambulances, police, fire units).

```
               [Live CCTV / RTSP / Video Stream]
                               │
                               ▼
        [YOLOv8-Medium Detection + ByteTrack Tracking]
            (Car Accidents, Fire, Smoke, Flood)
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
 [Evidence Screenshot Archive]           [Neo4j Knowledge Graph]
  (Annotated with Bounding Boxes)   (Location, Roadways, Emergency Units)
                                                  │
                                                  ▼
                                       [Shortest-Path Dispatch]
                                  (Nearest Police / Ambulance / Hospital)
                                                  │
                        ┌─────────────────────────┴─────────────────────────┐
                        ▼                                                   ▼
            [React Command Center]                              [Flutter Responder App]
            (Live City Map & Alerts)                            (Field Dispatch & Routing)
```

---

## 🏆 Computer Vision Model Evolution & Benchmark Report

Our computer vision engine underwent a 3-stage iterative optimization pipeline, culminating in our **Production YOLOv8-Medium** model trained on an **NVIDIA GeForce RTX 3050 6GB GPU**.

### 1. Training Progression: From Baseline to Production

| Metric | Stage 1: Initial YOLOv8-Nano (30 Epochs) | Stage 2: Optimized YOLOv8-Nano (50 Epochs) | Stage 3: Production YOLOv8-Medium (50 Epochs) | Overall Improvement |
| :--- | :---: | :---: | :---: | :---: |
| **Model Architecture** | Nano (3.0M params) | Nano (3.0M params) | **Medium (25.8M params)** | **+760% Capacity** |
| **Overall Precision ($P$)** | 69.1% | 73.7% | **82.2%** | 🟢 **+13.1% Increase** |
| **Overall Recall ($R$)** | 31.7% | 60.2% | **77.6%** | 🟢 **+144.8% Increase** |
| **Overall mAP@50** | 35.3% | 67.7% | **82.6%** | 🟢 **+134.0% Increase** |
| **mAP@50-95 (Box Fit)** | 20.1% | 42.9% | **55.8%** | 🟢 **+177.6% Increase** |
| **Inference Latency** | 2.8 ms (~263 FPS) | 2.8 ms (~263 FPS) | **13.1 ms (~71.4 FPS)** | 🟢 **Real-Time Edge Ready** |

---

### 2. Official Production Incident Benchmark (4-Class Incident Taxonomy)

> **Note on Casualty / Fall Detection**: The raw `fall_accident` dataset was audited and removed due to severe sequential annotation noise (upright pedestrians falsely indexed as falls). Casualty tracking is handled cleanly in Phase 2 via **ByteTrack temporal bounding-box aspect ratio ($W/H \ge 1.3$) and stationary velocity tracking**, eliminating false alarms.

| Incident Class | Precision ($P$) | Recall ($R$) | F1-Score | mAP@50 | mAP@50-95 | Production Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| 🚗 **Car Accident** | **83.6%** | **83.9%** | **83.7%** | **87.9%** | 49.8% | 🟢 **Production Grade** |
| 🌊 **Flood / Waterlogging** | **81.1%** | **81.0%** | **81.0%** | **83.8%** | 62.6% | 🟢 **Production Grade** |
| 🔥 **Fire** | **82.3%** | **76.3%** | **79.2%** | **82.4%** | 56.6% | 🟢 **Production Grade** |
| 💨 **Smoke Hazard** | **81.9%** | **69.1%** | **75.0%** | **76.3%** | 54.1% | 🟢 High Accuracy |
| **OVERALL INCIDENT ENGINE** | **82.2%** | **77.6%** | **79.7%** | **82.6%** | **55.8%** | 🟢 **Commercial Grade** |

---

### 3. Real-Time Detection Evidence Gallery

Below are real evidence frames captured automatically by ResiliNet AI during live stream CCTV processing, annotated with bounding boxes, event types, and confidence scores:

| 🚗 Car Accident Detection (`CAR_ACCIDENT`) | 🔥 Active Fire Incident (`FIRE_INCIDENT`) |
| :---: | :---: |
| <img src="assets/evidence/car_accident_evidence.jpg" alt="Car Accident Evidence" width="450"/> | <img src="assets/evidence/fire_incident_evidence.jpg" alt="Fire Incident Evidence" width="450"/> |
| *High-speed collision detection with vehicle bounding box* | *Active flame hazard detection on roadway / building* |

| 🌊 Urban Flood / Waterlogging (`FLOOD_WARNING`) | 💨 Smoke Hazard (`SMOKE_HAZARD`) |
| :---: | :---: |
| <img src="assets/evidence/flood_warning_evidence.jpg" alt="Flood Warning Evidence" width="450"/> | <img src="assets/evidence/smoke_hazard_evidence.jpg" alt="Smoke Hazard Evidence" width="450"/> |
| *Submerged roadway and high water accumulation warning* | *Dense smoke plume early warning prior to large combustion* |

---

### 4. Training Convergence & Confusion Matrix

| 📈 Loss Decay & Metric Growth Over 50 Epochs | 🎯 Multi-Class Confusion Matrix |
| :---: | :---: |
| <img src="assets/benchmarks/results.png" alt="Training Curves" width="450"/> | <img src="assets/benchmarks/confusion_matrix.png" alt="Confusion Matrix" width="450"/> |
| *Smooth convergence with Cosine Annealing scheduler* | *High diagonal activation proving low cross-class confusion* |

---

### 5. Edge Hardware & Real-Time Viability

- **Benchmarked Hardware**: NVIDIA GeForce RTX 3050 6GB Laptop GPU (PyTorch 2.5.1 + CUDA 12.1).
- **Latency Breakdown**:
  - Pre-process: `0.2 ms`
  - Model Inference: `13.1 ms`
  - ByteTrack & Post-process: `0.7 ms`
  - **Total Latency**: **`14.0 ms` per frame**
- **Throughput**: **~71.4 FPS**. Standard CCTV streams run at 25–30 FPS; our model processes **2 to 3 live 1080p camera streams concurrently** on a single laptop GPU.

---

## 🛠️ Project Structure

```text
Resilinet/
├── assets/
│   ├── evidence/                <-- Permanent README Demonstration Screenshots
│   │   ├── car_accident_evidence.jpg
│   │   ├── fire_incident_evidence.jpg
│   │   ├── flood_warning_evidence.jpg
│   │   └── smoke_hazard_evidence.jpg
│   └── benchmarks/              <-- Training Loss Curves & Confusion Matrices
│       ├── results.png
│       └── confusion_matrix.png
│
├── backend/
│   ├── incident_yolov8m.pt      <-- Active Production Model (YOLOv8-Medium, 52 MB)
│   ├── main.py                  <-- Live CCTV Pipeline Orchestrator
│   ├── evaluate_yolo.py         <-- Model Evaluation & Speed Benchmark Suite
│   ├── prepare_dataset.py       <-- Dataset Merger & Class Remapping Pipeline
│   ├── train_yolo.py            <-- High-Performance Model Training Suite
│   ├── accident.mp4             <-- Test CCTV Video 1 (Car Crash)
│   ├── accident_2.mp4           <-- Test CCTV Video 2 (Fire / Accident)
│   ├── config/
│   │   └── settings.py          <-- Centralized Environment Configuration
│   ├── detection/
│   │   └── detector.py          <-- Ultralytics YOLOv8 Inference Wrapper
│   ├── tracking/
│   │   └── tracker.py           <-- ByteTrack Multi-Object Persistent Tracker
│   ├── evidence/
│   │   └── capture.py           <-- Annotated Evidence Screenshot Generator
│   ├── neo4j_client/
│   │   ├── database.py          <-- Neo4j Driver Connection
│   │   └── writer.py            <-- Cypher Node & Edge Insertion Logic
│   └── evidence_screenshots/   <-- Saved Evidence Images
│
├── frontend-web/                <-- React Web Command Center Dashboard
├── frontend-mobile/             <-- Flutter Mobile First-Responder App
└── docs/                        <-- Master Architecture & Implementation Guides
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Environment Setup

```powershell
# Clone repository and enter backend
cd backend

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies with official NVIDIA CUDA acceleration
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

### 2. Run the Live Video Detection Pipeline

```powershell
python backend/main.py
```
- Opens a live OpenCV window (**`ResiliNet Phase 1 — cam-001`**) rendering color-coded bounding boxes and persistent track IDs:
  - 🔴 **Car Accident**
  - 🟠 **Fire**
  - ⚪ **Smoke**
  - 🔵 **Flood**
- Evidence screenshots are automatically saved to `backend/evidence_screenshots/`.
- Press **`Q`** to stop.

### 3. Run Benchmark Speed & Model Evaluation

```powershell
# 1. Benchmark GPU Latency & FPS
python backend/evaluate_yolo.py --benchmark-speed

# 2. Evaluate model Precision, Recall, and mAP against test split
python backend/evaluate_yolo.py --model backend/incident_yolov8m.pt --data backend/datasets/unified_incidents/data.yaml --split test
```

### 4. (Optional) Retrain or Fine-Tune Model

```powershell
# Merge and remap datasets into unified 4-class taxonomy
python backend/prepare_dataset.py

# Train YOLOv8-Medium with Cosine Annealing, Mosaic, and Mixup
python backend/train_yolo.py
```

---

## 🌐 Next Steps: Graph-RAG Emergency Dispatch

1. **Incident Trigger**: When an incident detection exceeds confidence threshold (`0.40`), an event is written to Neo4j.
2. **Spatial Graph Lookup**: Queries the road network topology for nearest emergency services:
   ```cypher
   MATCH (i:Incident {id: $incident_id})-[:LOCATED_AT]->(loc:Location)
   MATCH (r:Responder {status: "AVAILABLE"})-[:NEAR]->(loc)
   RETURN r.name, r.type, r.distanceMeters
   ORDER BY r.distanceMeters ASC
   LIMIT 3
   ```
3. **Dispatch Payload**: Relayed via GraphQL to the **React Command Dashboard** and **Flutter Mobile Responder App**.
