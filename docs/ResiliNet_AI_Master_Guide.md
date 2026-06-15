# ResiliNet AI — Master README & Implementation Guide

> **Audience**: Developers comfortable with general programming, but new to Graph Databases, GraphRAG, and AI-augmented backends.
> **Goal**: By the end of this document, your team should understand *why* each piece of the stack exists, and have working boilerplate to launch every layer — database, backend, AI pipeline, web dashboard, and mobile app.

---

## Table of Contents

- **Part 1** — The Crash Course (Concepts: Graph DBs, GraphRAG, Data Flow)
- **Part 2** — Database & Backend (Neo4j Schema + FastAPI)
- **Part 3** — The AI & GraphRAG Pipeline
- **Part 4** — The Web Command Center (React)
- **Part 5** — The Mobile Field App (Flutter)

---

# Part 1: The Crash Course (The "What" and "Why")

## 1.1 What is a Graph Database, and why Neo4j instead of SQL?

A **graph database** stores data as two simple things:

- **Nodes** — the "things" in your system. Think of these as nouns: an `Incident`, a `Responder`, a `Hospital`, a `Location`.
- **Relationships (Edges)** — the connections *between* things. Think of these as verbs: a Responder `CAN_REACH` a Location, an Incident `LOCATED_AT` a Location, a Hospital `NEAR` a Location.

Both nodes and relationships can carry **properties** (key-value data). A `Responder` node might have `{name: "Unit Alpha-7", status: "AVAILABLE"}`. A `NEAR` relationship might have `{distanceMeters: 850}`.

That's it. There's no rigid table schema, no foreign keys, no junction tables. The connections themselves are stored as first-class data.

### Why this matters for disaster routing specifically

In a relational (SQL) database, "find the nearest available ambulance to this fire, that can also pass through roads that aren't currently blocked, and is within range of a hospital with free beds" requires **multiple JOINs across multiple tables** — `incidents JOIN locations JOIN responders JOIN road_segments JOIN hospitals JOIN bed_availability...`. Each JOIN is a separate table scan-and-match operation. As your question gets more relational ("responders who can reach X via roads that connect to Y"), the number of JOINs explodes, and so does the query time.

In Neo4j, that same question is a **graph traversal** — you start at the `Incident` node and *walk along relationships* outward (`MATCH (i:Incident)-[:LOCATED_AT]->(:Location)<-[:CAN_REACH]-(r:Responder)`). The cost of this walk depends on how many connections you traverse, **not** on the total size of the database. A city with 10 million road segments doesn't slow down a 3-hop query about one incident's immediate neighborhood.

| | SQL (Relational) | Neo4j (Graph) |
|---|---|---|
| Data model | Tables + foreign keys | Nodes + relationships |
| "Find connected things" | Multiple JOINs (slow as depth grows) | Graph traversal (fast regardless of total DB size) |
| Schema changes | Migrations, ALTER TABLE | Add new node/relationship types freely |
| Best for | Tabular, transactional data (orders, invoices) | Highly connected data (networks, routes, infrastructure) |

City infrastructure — roads, sensors, responders, hospitals, citizens — is *inherently* a network. Modeling it as a network instead of forcing it into tables is the whole point of using Neo4j here.

### Nodes and Edges, in plain English

```
(Incident: "Building Fire, Sector 7")
        |
        | LOCATED_AT
        v
(Location: 18.52°N, 73.85°E)
        ^
        | NEAR (distance: 850m)
        |
(Responder: "Unit Alpha-7", status: AVAILABLE)
```

- The parentheses `()` are **nodes**.
- The arrows with labels `-[:LOCATED_AT]->` are **relationships** — they have a direction and a type (the word in capitals).
- Both nodes and relationships can have extra properties attached (shown above as `status: AVAILABLE` or `distance: 850m`).

In Neo4j's query language, **Cypher**, this exact picture is written almost literally:

```cypher
(i:Incident {name: "Building Fire, Sector 7"})-[:LOCATED_AT]->(l:Location)<-[:NEAR {distanceMeters: 850}]-(r:Responder {name: "Unit Alpha-7"})
```

Cypher is intentionally drawn to *look like* the diagram — this is one of the biggest "aha" moments for newcomers.

---

## 1.2 What is GraphRAG, and how does it stop the AI from hallucinating dispatches?

**RAG (Retrieval-Augmented Generation)** is a pattern where, before asking an LLM to answer something, you first **retrieve relevant facts from your own data** and stuff those facts into the prompt. The LLM then answers *using the facts you gave it*, instead of relying purely on whatever it memorized during training.

**GraphRAG** is RAG where the retrieval step is a **graph traversal** instead of a plain document/vector search. Instead of "find documents similar to this text," we ask: *"Starting from this Incident node, walk outward and collect the Responders, Hospitals, and Infrastructure that are actually connected to it."*

### Why this prevents hallucinated dispatches

If you simply ask an LLM, *"A fire just started at coordinates X, which hospital and responder unit should be dispatched?"* — the LLM has **no idea** what responders or hospitals actually exist in your city's database. It might confidently invent a plausible-sounding but fictional "Unit Bravo-3" or "St. Mary's Hospital" that doesn't exist in your system. This is hallucination, and in an emergency dispatch system it's dangerous.

With GraphRAG, the flow becomes:

1. **Retrieve**: Run a Cypher query that finds the *real* hospitals and responders near this incident, with their *real* IDs, names, current status, and distances.
2. **Format**: Turn that result into a compact text block — e.g. `"Responder resp-001 'Unit Alpha-7' (Ambulance, AVAILABLE, 850m away)"`.
3. **Constrain**: Tell the LLM, explicitly in the system prompt, *"You may only reference entities by the exact IDs provided below. Do not invent IDs."*
4. **Generate**: The LLM's job becomes reasoning over a small, accurate, real-time list — not recalling facts from memory. It picks `resp-001` because it's the closest available unit *that we told it about*, not because it guessed a plausible-sounding name.

This shifts the LLM's role from "knowledge source" (error-prone) to "reasoning engine over verified data" (much safer) — which is the entire reason GraphRAG exists for high-stakes domains like emergency response.

---

## 1.3 The Overall Data Flow

Here's the full journey of a single incident report, end to end:

```
 [1] CITIZEN or IoT SENSOR
       |  (Flutter app or sensor firmware sends HTTP POST)
       v
 [2] FastAPI Backend  --  POST /report
       |  (validates payload, writes Incident + Location nodes to graph)
       v
 [3] Neo4j Knowledge Graph
       |  (Incident node now exists, connected to a Location)
       v
 [4] GraphRAG Retrieval (background task)
       |  (Cypher query: find nearby Responders + Infrastructure)
       v
 [5] Context Formatting
       |  (turn graph results into a text block)
       v
 [6] LLM (Claude / GPT via API)
       |  (system prompt + incident + graph context -> JSON response)
       |  { severity, dispatch_text, recommended_responder_id, ... }
       v
 [7] Write results back to Neo4j
       |  (update Incident node, create DISPATCHED_TO relationship)
       v
 [8] WebSocket Broadcast
       |
       +----------------------------------+
       v                                  v
 [9a] React Command Center          [9b] Flutter Field App
      (plots incident on Leaflet         (responder sees dispatch
       map in real time)                  appear on their device)
```

**The key architectural idea**: steps 1–3 are a normal "write to a database" flow. Steps 4–7 are the "AI brain" — and it's *sandwiched* between two database operations (read context, write results), which is what makes it GraphRAG rather than a bare LLM call. Step 8–9 is just "tell everyone who's listening that something changed," via WebSockets so the UI updates instantly without polling.

---

# Part 2: Database & Backend Implementation (Python/FastAPI & Neo4j)

## 2.1 Project Structure

```
resilinet-backend/
├── main.py            # FastAPI app, routes, WebSocket manager
├── database.py        # Neo4j driver connection
├── models.py           # Pydantic request/response models
├── graphrag.py          # Graph retrieval logic
├── llm_service.py        # LLM prompt + call + JSON parsing
├── requirements.txt
└── .env                 # secrets (never commit this)
```

## 2.2 requirements.txt

```text
fastapi==0.111.0
uvicorn[standard]==0.30.1
neo4j==5.21.0
pydantic==2.7.4
python-dotenv==1.0.1
anthropic==0.34.0
websockets==12.0
```

## 2.3 Neo4j Schema — Initial Cypher Setup

Run these statements once in the **Neo4j Browser** (or via `cypher-shell`) to set up constraints, indexes, and a small set of seed data so you have something to query against immediately.

### 2.3.1 Constraints & Indexes

```cypher
// ─────────────────────────────────────────────────────────────
// UNIQUENESS CONSTRAINTS
// These guarantee that, e.g., two Incident nodes can never share
// the same `id` — Neo4j will reject the second write.
// They also automatically create a fast lookup index on that property.
// ─────────────────────────────────────────────────────────────

CREATE CONSTRAINT incident_id_unique IF NOT EXISTS
FOR (i:Incident) REQUIRE i.id IS UNIQUE;

CREATE CONSTRAINT location_id_unique IF NOT EXISTS
FOR (l:Location) REQUIRE l.id IS UNIQUE;

CREATE CONSTRAINT responder_id_unique IF NOT EXISTS
FOR (r:Responder) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT infrastructure_id_unique IF NOT EXISTS
FOR (f:Infrastructure) REQUIRE f.id IS UNIQUE;

// ─────────────────────────────────────────────────────────────
// SPATIAL (POINT) INDEXES
// `coordinates` on Location and Infrastructure will store Neo4j's
// built-in `point()` type. A point index makes distance-based
// queries (point.distance) fast, which is exactly what our
// GraphRAG "find nearby responders/hospitals" query needs.
// ─────────────────────────────────────────────────────────────

CREATE POINT INDEX location_point_index IF NOT EXISTS
FOR (l:Location) ON (l.coordinates);

CREATE POINT INDEX infrastructure_point_index IF NOT EXISTS
FOR (f:Infrastructure) ON (f.coordinates);

CREATE POINT INDEX responder_point_index IF NOT EXISTS
FOR (r:Responder) ON (r.coordinates);
```

### 2.3.2 Seed Data — so you have something to test against

```cypher
// ─────────────────────────────────────────────────────────────
// INFRASTRUCTURE NODES
// `point({latitude: ..., longitude: ...})` is Neo4j's native
// geospatial type — it lets us later compute real distances
// with point.distance(a, b), which returns METERS.
// ─────────────────────────────────────────────────────────────

CREATE (:Infrastructure {
  id: "hosp-001",
  name: "City General Hospital",
  type: "Hospital",
  capacity: 50,                 // total bed capacity
  availableBeds: 12,            // current free beds
  coordinates: point({latitude: 18.5204, longitude: 73.8567})
});

CREATE (:Infrastructure {
  id: "hosp-002",
  name: "Riverside Medical Center",
  type: "Hospital",
  capacity: 30,
  availableBeds: 4,
  coordinates: point({latitude: 18.5390, longitude: 73.8480})
});

CREATE (:Infrastructure {
  id: "fire-001",
  name: "Central Fire Station",
  type: "FireStation",
  coordinates: point({latitude: 18.5300, longitude: 73.8500})
});

// ─────────────────────────────────────────────────────────────
// RESPONDER NODES
// `status` will be updated in real time as units are dispatched.
// ─────────────────────────────────────────────────────────────

CREATE (:Responder {
  id: "resp-001",
  name: "Unit Alpha-7",
  type: "Ambulance",
  status: "AVAILABLE",
  coordinates: point({latitude: 18.5210, longitude: 73.8550})
});

CREATE (:Responder {
  id: "resp-002",
  name: "Engine 12",
  type: "FireTruck",
  status: "AVAILABLE",
  coordinates: point({latitude: 18.5295, longitude: 73.8505})
});

CREATE (:Responder {
  id: "resp-003",
  name: "Unit Bravo-2",
  type: "Ambulance",
  status: "EN_ROUTE",
  coordinates: point({latitude: 18.5450, longitude: 73.8600})
});
```

### Why no relationship constraints?

Neo4j Community Edition does not support uniqueness constraints *on relationships* — only on node properties. That's fine: in this design, relationships like `LOCATED_AT`, `DISPATCHED_TO`, and `NEAR` are created/merged programmatically by the backend, so duplicates are controlled in application code (we use `MERGE` for that, shown below).

---

## 2.4 `database.py` — Connecting FastAPI to Neo4j

```python
# database.py
#
# This module owns ONE thing: the connection to Neo4j.
# We create a single "Driver" object when the app starts, and reuse it
# for every request. The driver is thread-safe and manages a pool of
# connections internally — you should NOT create a new driver per request.

import os
from neo4j import GraphDatabase, Driver

# Read connection details from environment variables.
# Defaults below match a local Neo4j Desktop / Docker instance.
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# This global variable will hold our single Driver instance.
# It starts as None and gets created by `connect_to_neo4j()` below.
driver: Driver | None = None


def connect_to_neo4j() -> None:
    """
    Create the Neo4j driver and verify connectivity.
    Called once, when the FastAPI app starts up.
    """
    global driver
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASSWORD),
    )
    # `verify_connectivity()` makes a real round-trip to Neo4j.
    # If credentials or the URI are wrong, this raises immediately —
    # far better than discovering it on the first user request.
    driver.verify_connectivity()
    print(f"Connected to Neo4j at {NEO4J_URI}")


def close_neo4j_connection() -> None:
    """
    Cleanly close the driver's connection pool.
    Called once, when the FastAPI app shuts down.
    """
    global driver
    if driver is not None:
        driver.close()
        print("Neo4j connection closed")


def get_driver() -> Driver:
    """
    Small helper so other modules don't need to import the global
    `driver` variable directly — they just call get_driver().
    """
    if driver is None:
        raise RuntimeError("Neo4j driver not initialized. Did the app start correctly?")
    return driver
```

---

## 2.5 `models.py` — Pydantic Request/Response Models

```python
# models.py
#
# Pydantic models define the SHAPE of data flowing in and out of our API.
# FastAPI uses these to automatically validate incoming JSON, and to
# auto-generate API documentation at /docs.

from pydantic import BaseModel, Field
from typing import Optional


class IncidentReport(BaseModel):
    """
    The JSON body the frontend/IoT sensor sends to POST /report.
    """

    # A human-readable description: "Smoke visible from 3rd floor window"
    description: str = Field(..., min_length=1, max_length=2000)

    # The category the reporter selected, e.g. "fire", "flood", "accident",
    # "structural_damage", "medical". Free text is allowed but these are
    # the categories our LLM prompt will be primed to expect.
    category: str

    # GPS coordinates of the incident.
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    # Optional: who/what reported this. "citizen_app", "iot_sensor_042", etc.
    source: Optional[str] = "citizen_app"


class IncidentResponse(BaseModel):
    """
    What we send back immediately after POST /report.
    Note: the AI classification happens ASYNCHRONOUSLY (in a background
    task), so this response does NOT include severity/dispatch yet —
    those arrive later via WebSocket.
    """

    status: str
    incident_id: str


class DispatchUpdate(BaseModel):
    """
    The shape of the message broadcast over WebSocket once the AI
    pipeline finishes processing an incident.
    """

    incident_id: str
    severity: str                 # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    dispatch_text: str             # human-readable instructions for responders
    recommended_responder_id: Optional[str] = None
    recommended_infrastructure_id: Optional[str] = None
    latitude: float
    longitude: float
    category: str
```

---

## 2.6 `main.py` — FastAPI App, `/report` Endpoint, and WebSocket Manager

```python
# main.py
#
# This is the entry point of our backend. It wires together:
#   - The FastAPI app itself
#   - Lifespan events (connect/disconnect Neo4j on startup/shutdown)
#   - CORS (so the React dev server can call us from a different port)
#   - The POST /report endpoint (writes incidents to the graph)
#   - A WebSocket endpoint that broadcasts AI dispatch results live

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from database import connect_to_neo4j, close_neo4j_connection, get_driver
from models import IncidentReport, IncidentResponse, DispatchUpdate
from graphrag import get_context_for_incident
from llm_service import classify_and_dispatch


# ─────────────────────────────────────────────────────────────
# LIFESPAN: code that runs ONCE at startup and ONCE at shutdown.
# This replaces the older @app.on_event("startup") style.
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    connect_to_neo4j()
    yield
    # --- SHUTDOWN ---
    close_neo4j_connection()


app = FastAPI(title="ResiliNet AI Backend", lifespan=lifespan)

# Allow the React dev server (typically http://localhost:5173 for Vite,
# or http://localhost:3000 for CRA) to call this API from the browser.
# In production, replace "*" with your real frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
# WEBSOCKET CONNECTION MANAGER
# Keeps a list of every currently-connected client (browser tabs,
# Flutter apps) so we can push a message to ALL of them at once
# whenever the AI finishes classifying a new incident.
# ─────────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        # A plain Python list of active WebSocket connections.
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        # `accept()` completes the WebSocket handshake.
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        # Remove a connection that has closed (browser tab closed, etc.)
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Send the same JSON payload to every connected client.
        # If a send fails (client disconnected without telling us),
        # we quietly drop that connection.
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)


# A single shared instance, used everywhere in this file.
manager = ConnectionManager()


# ─────────────────────────────────────────────────────────────
# CYPHER WRITE: create an Incident node + Location node + relationship
# ─────────────────────────────────────────────────────────────
def _create_incident_tx(tx, incident_id: str, report: IncidentReport):
    """
    A "transaction function" — Neo4j's Python driver runs this inside
    a managed transaction, automatically retrying on transient errors
    (e.g. brief network blips). This is the recommended pattern for
    all writes.
    """
    query = """
    // Create the Incident node with a unique generated ID.
    CREATE (i:Incident {
        id: $incident_id,
        description: $description,
        category: $category,
        source: $source,
        status: "PENDING_AI_REVIEW",
        createdAt: datetime()
    })

    // MERGE (not CREATE) the Location node: if a Location with these
    // exact coordinates already exists, reuse it instead of duplicating.
    // This keeps the graph clean when many incidents happen at the
    // same intersection, building, etc.
    MERGE (l:Location {
        id: $location_id
    })
    ON CREATE SET l.coordinates = point({latitude: $lat, longitude: $lng})

    // Connect the Incident to its Location.
    CREATE (i)-[:LOCATED_AT]->(l)

    RETURN i.id AS id
    """
    result = tx.run(
        query,
        incident_id=incident_id,
        description=report.description,
        category=report.category,
        source=report.source,
        # We derive a deterministic location ID from rounded coordinates
        # so nearby reports at the "same spot" reuse one Location node.
        location_id=f"loc-{round(report.latitude, 5)}-{round(report.longitude, 5)}",
        lat=report.latitude,
        lng=report.longitude,
    )
    return result.single()["id"]


# ─────────────────────────────────────────────────────────────
# CYPHER WRITE: store the AI's classification result back on the graph
# ─────────────────────────────────────────────────────────────
def _save_dispatch_result_tx(tx, incident_id: str, ai_result: dict):
    query = """
    MATCH (i:Incident {id: $incident_id})
    SET i.status = "DISPATCHED",
        i.severity = $severity,
        i.dispatchText = $dispatch_text

    // If the AI recommended a responder, link them to this incident
    // and flip their status so they don't get double-booked.
    WITH i
    OPTIONAL MATCH (r:Responder {id: $responder_id})
    FOREACH (_ IN CASE WHEN r IS NOT NULL THEN [1] ELSE [] END |
        MERGE (i)-[:DISPATCHED_TO]->(r)
        SET r.status = "EN_ROUTE"
    )
    """
    tx.run(
        query,
        incident_id=incident_id,
        severity=ai_result["severity"],
        dispatch_text=ai_result["dispatch_text"],
        responder_id=ai_result.get("recommended_responder_id"),
    )


# ─────────────────────────────────────────────────────────────
# ENDPOINT: POST /report
# ─────────────────────────────────────────────────────────────
@app.post("/report", response_model=IncidentResponse)
async def create_report(report: IncidentReport, background_tasks: BackgroundTasks):
    """
    Receives a new incident report, writes it to Neo4j immediately,
    and schedules the AI/GraphRAG pipeline to run AFTER this response
    is sent (so the citizen/sensor isn't kept waiting on an LLM call).
    """
    # Generate a unique ID for this incident.
    incident_id = f"inc-{uuid.uuid4().hex[:12]}"

    driver = get_driver()
    # `execute_write` opens a session, runs the transaction function,
    # and commits/retries as needed.
    with driver.session() as session:
        session.execute_write(_create_incident_tx, incident_id, report)

    # Queue the slow AI work to run after the HTTP response is returned.
    background_tasks.add_task(process_incident_with_ai, incident_id, report)

    return IncidentResponse(status="received", incident_id=incident_id)


# ─────────────────────────────────────────────────────────────
# BACKGROUND TASK: the GraphRAG + LLM pipeline (full detail in Part 3)
# ─────────────────────────────────────────────────────────────
async def process_incident_with_ai(incident_id: str, report: IncidentReport):
    driver = get_driver()

    # Step 1: GraphRAG retrieval — get nearby responders/hospitals as text.
    with driver.session() as session:
        graph_context = session.execute_read(get_context_for_incident, report)

    # Step 2: Send the incident + graph context to the LLM, get structured JSON back.
    ai_result = await classify_and_dispatch(report, graph_context)

    # Step 3: Write the AI's decision back into the graph.
    with driver.session() as session:
        session.execute_write(_save_dispatch_result_tx, incident_id, ai_result)

    # Step 4: Tell every connected dashboard/app about the new dispatch.
    update = DispatchUpdate(
        incident_id=incident_id,
        severity=ai_result["severity"],
        dispatch_text=ai_result["dispatch_text"],
        recommended_responder_id=ai_result.get("recommended_responder_id"),
        recommended_infrastructure_id=ai_result.get("recommended_infrastructure_id"),
        latitude=report.latitude,
        longitude=report.longitude,
        category=report.category,
    )
    await manager.broadcast(update.model_dump())


# ─────────────────────────────────────────────────────────────
# WEBSOCKET ENDPOINT: ws://<host>/ws/dispatches
# ─────────────────────────────────────────────────────────────
@app.websocket("/ws/dispatches")
async def dispatch_socket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # We don't expect the client to SEND us anything — this is a
        # one-way "server pushes updates" channel. We still need to
        # `await websocket.receive_text()` in a loop so FastAPI keeps
        # the connection open and we can detect disconnects.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/")
async def root():
    return {"service": "ResiliNet AI Backend", "status": "running"}
```

### Running it

```bash
# Start Neo4j (Docker example)
docker run -d \
  --name resilinet-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5

# Install dependencies and run FastAPI
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` — FastAPI auto-generates an interactive API explorer from your Pydantic models, where you can fire test `POST /report` requests immediately.

---

# Part 3: The AI & GraphRAG Pipeline

## 3.1 `graphrag.py` — Retrieving the Relevant Subgraph

This is the **"R" in GraphRAG**: given a new incident's coordinates, find the real responders and infrastructure near it, and turn that into plain text the LLM can read.

```python
# graphrag.py
#
# This module's job: given an incident's location, run a Cypher query
# that finds nearby Responders and Infrastructure, then format the
# results into a human-readable text block for the LLM prompt.

from models import IncidentReport


def get_context_for_incident(tx, report: IncidentReport) -> str:
    """
    A "transaction function" for execute_read.
    `tx` is provided automatically by the Neo4j driver.

    Strategy: use point.distance() to find everything within a
    radius (in meters) of the incident's coordinates, ordered by
    distance, and cap the results so the LLM prompt stays small.
    """

    incident_point_params = {
        "lat": report.latitude,
        "lng": report.longitude,
    }

    # ── Find nearby AVAILABLE responders, closest first ──────────────
    responder_query = """
    WITH point({latitude: $lat, longitude: $lng}) AS incidentPoint
    MATCH (r:Responder {status: "AVAILABLE"})
    WITH r, incidentPoint, point.distance(incidentPoint, r.coordinates) AS distanceMeters
    WHERE distanceMeters <= 10000          // within 10km
    RETURN r.id AS id, r.name AS name, r.type AS type,
           round(distanceMeters) AS distanceMeters
    ORDER BY distanceMeters ASC
    LIMIT 5
    """
    responders = list(tx.run(responder_query, **incident_point_params))

    # ── Find nearby Infrastructure (hospitals, fire stations), closest first ──
    infra_query = """
    WITH point({latitude: $lat, longitude: $lng}) AS incidentPoint
    MATCH (f:Infrastructure)
    WITH f, incidentPoint, point.distance(incidentPoint, f.coordinates) AS distanceMeters
    WHERE distanceMeters <= 10000
    RETURN f.id AS id, f.name AS name, f.type AS type,
           f.capacity AS capacity, f.availableBeds AS availableBeds,
           round(distanceMeters) AS distanceMeters
    ORDER BY distanceMeters ASC
    LIMIT 5
    """
    infrastructure = list(tx.run(infra_query, **incident_point_params))

    # ── Format everything into a single text block ───────────────────
    lines = []

    lines.append("NEARBY AVAILABLE RESPONDERS:")
    if responders:
        for row in responders:
            lines.append(
                f"- id={row['id']} | name=\"{row['name']}\" | type={row['type']} "
                f"| distance={row['distanceMeters']}m | status=AVAILABLE"
            )
    else:
        lines.append("- None found within 10km.")

    lines.append("")  # blank line separator
    lines.append("NEARBY INFRASTRUCTURE:")
    if infrastructure:
        for row in infrastructure:
            extra = ""
            if row["type"] == "Hospital":
                extra = f" | availableBeds={row['availableBeds']}/{row['capacity']}"
            lines.append(
                f"- id={row['id']} | name=\"{row['name']}\" | type={row['type']} "
                f"| distance={row['distanceMeters']}m{extra}"
            )
    else:
        lines.append("- None found within 10km.")

    return "\n".join(lines)
```

**Example output** of this function might look like:

```
NEARBY AVAILABLE RESPONDERS:
- id=resp-001 | name="Unit Alpha-7" | type=Ambulance | distance=820m | status=AVAILABLE
- id=resp-002 | name="Engine 12" | type=FireTruck | distance=1140m | status=AVAILABLE

NEARBY INFRASTRUCTURE:
- id=hosp-001 | name="City General Hospital" | type=Hospital | distance=1450m | availableBeds=12/50
- id=fire-001 | name="Central Fire Station" | type=FireStation | distance=950m
```

This is the *grounding* — the LLM will only ever choose from `resp-001`, `resp-002`, `hosp-001`, `fire-001`, etc., never an invented ID.

---

## 3.2 The System Prompt

This is the exact instruction set sent to the LLM on every classification call. Note how it (a) defines the output contract precisely, and (b) explicitly forbids inventing IDs.

```text
You are the AI dispatch coordinator for ResiliNet AI, an urban disaster
management platform. You will be given details about a newly reported
incident, plus a list of REAL responders and infrastructure currently
available near that incident, retrieved live from the city's knowledge
graph.

YOUR TASK:
1. Assess the severity of the incident based on its description and category.
2. Recommend ONE responder and, if relevant, ONE piece of infrastructure
   (e.g. a hospital) to dispatch — chosen ONLY from the lists provided.
3. Write a short, clear dispatch message for the responder to receive.

STRICT RULES:
- You MUST choose `recommended_responder_id` and
  `recommended_infrastructure_id` ONLY from the exact `id` values listed
  in the "NEARBY AVAILABLE RESPONDERS" / "NEARBY INFRASTRUCTURE" sections.
  If a section says "None found", set the corresponding field to null.
  NEVER invent, guess, or hallucinate an id that was not given to you.
- `severity` MUST be exactly one of: "LOW", "MEDIUM", "HIGH", "CRITICAL".
- `dispatch_text` should be 1-2 sentences, written as a direct instruction
  to the responder (e.g. "Proceed immediately to Sector 7 for a reported
  structural fire. Coordinate with Central Fire Station on arrival.").
- Respond with ONLY a single JSON object. No markdown, no code fences,
  no explanation text before or after the JSON.

OUTPUT FORMAT (exact keys, exact types):
{
  "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "recommended_responder_id": "<id from the list, or null>",
  "recommended_infrastructure_id": "<id from the list, or null>",
  "dispatch_text": "<string>",
  "reasoning": "<one sentence explaining the severity choice>"
}
```

---

## 3.3 `llm_service.py` — Calling the LLM and Parsing the Response

```python
# llm_service.py
#
# This module sends the incident + GraphRAG context to the LLM and
# parses the structured JSON it returns. We use Anthropic's Claude
# here; swapping to another provider only changes the API call itself —
# the prompt and parsing logic stay the same.

import json
import os
from anthropic import AsyncAnthropic

from models import IncidentReport

# The client reads ANTHROPIC_API_KEY from the environment automatically.
client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# The system prompt from section 3.2, stored as a constant so it's
# defined in exactly one place.
SYSTEM_PROMPT = """You are the AI dispatch coordinator for ResiliNet AI, an urban disaster
management platform. You will be given details about a newly reported
incident, plus a list of REAL responders and infrastructure currently
available near that incident, retrieved live from the city's knowledge
graph.

YOUR TASK:
1. Assess the severity of the incident based on its description and category.
2. Recommend ONE responder and, if relevant, ONE piece of infrastructure
   (e.g. a hospital) to dispatch — chosen ONLY from the lists provided.
3. Write a short, clear dispatch message for the responder to receive.

STRICT RULES:
- You MUST choose `recommended_responder_id` and
  `recommended_infrastructure_id` ONLY from the exact `id` values listed
  in the "NEARBY AVAILABLE RESPONDERS" / "NEARBY INFRASTRUCTURE" sections.
  If a section says "None found", set the corresponding field to null.
  NEVER invent, guess, or hallucinate an id that was not given to you.
- `severity` MUST be exactly one of: "LOW", "MEDIUM", "HIGH", "CRITICAL".
- `dispatch_text` should be 1-2 sentences, written as a direct instruction
  to the responder (e.g. "Proceed immediately to Sector 7 for a reported
  structural fire. Coordinate with Central Fire Station on arrival.").
- Respond with ONLY a single JSON object. No markdown, no code fences,
  no explanation text before or after the JSON.

OUTPUT FORMAT (exact keys, exact types):
{
  "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
  "recommended_responder_id": "<id from the list, or null>",
  "recommended_infrastructure_id": "<id from the list, or null>",
  "dispatch_text": "<string>",
  "reasoning": "<one sentence explaining the severity choice>"
}"""


async def classify_and_dispatch(report: IncidentReport, graph_context: str) -> dict:
    """
    Sends the incident details + GraphRAG context to the LLM and
    returns a parsed Python dict matching the OUTPUT FORMAT above.
    """

    # Build the user-facing message: the incident facts, then the
    # live graph data we retrieved in graphrag.py.
    user_message = f"""INCIDENT REPORT:
- Category: {report.category}
- Description: {report.description}
- Location: ({report.latitude}, {report.longitude})
- Source: {report.source}

{graph_context}

Based on the above, return the JSON object as specified."""

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_message},
        ],
    )

    # `response.content` is a list of content blocks; for a plain text
    # reply, the first block's `.text` holds the model's output.
    raw_text = response.content[0].text.strip()

    # Defensive parsing: even with strict instructions, models
    # sometimes wrap JSON in ```json fences. Strip those if present.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        # Fallback: if parsing fails entirely, return a safe default
        # so the pipeline doesn't crash — but flag it for human review.
        result = {
            "severity": "MEDIUM",
            "recommended_responder_id": None,
            "recommended_infrastructure_id": None,
            "dispatch_text": "AI response could not be parsed. Manual review required.",
            "reasoning": "JSON parse error.",
        }

    return result
```

### Why parse defensively?

LLMs are usually obedient to formatting instructions, but "usually" isn't "always." In a dispatch system, a malformed AI response should **never crash the pipeline or silently drop an incident** — it should degrade to a safe default (here, `MEDIUM` severity + "needs manual review") so a human dispatcher still sees it. This is a general pattern: *treat LLM output like untrusted user input, always validate, always have a fallback.*

---

# Part 4: The Web Command Center (React)

## 4.1 Project Structure

```
resilinet-frontend/
├── src/
│   ├── App.jsx
│   ├── useDispatchSocket.js
│   ├── MapView.jsx
│   └── main.jsx
├── package.json
└── index.html
```

Install dependencies:

```bash
npm create vite@latest resilinet-frontend -- --template react
cd resilinet-frontend
npm install leaflet react-leaflet
```

## 4.2 `useDispatchSocket.js` — The WebSocket Hook

```jsx
// useDispatchSocket.js
//
// A custom React hook that opens a WebSocket connection to our FastAPI
// backend and keeps a running list of dispatch updates in state.
// Any component that calls this hook gets live updates automatically.

import { useEffect, useRef, useState } from "react";

export function useDispatchSocket(url) {
  // `dispatches` holds every DispatchUpdate message received so far.
  const [dispatches, setDispatches] = useState([]);

  // `connectionStatus` lets the UI show "Connected" / "Disconnected".
  const [connectionStatus, setConnectionStatus] = useState("connecting");

  // We use a ref to hold the WebSocket instance so it persists across
  // re-renders without being recreated.
  const socketRef = useRef(null);

  useEffect(() => {
    // Open the connection when the component mounts.
    const socket = new WebSocket(url);
    socketRef.current = socket;

    socket.onopen = () => {
      setConnectionStatus("connected");
    };

    socket.onmessage = (event) => {
      // The backend sends JSON-encoded DispatchUpdate objects.
      const update = JSON.parse(event.data);

      // Prepend the newest dispatch so it appears at the top of any list.
      setDispatches((previous) => [update, ...previous]);
    };

    socket.onclose = () => {
      setConnectionStatus("disconnected");
    };

    socket.onerror = () => {
      setConnectionStatus("error");
    };

    // Cleanup: close the socket when the component unmounts, so we
    // don't leak connections when navigating away.
    return () => {
      socket.close();
    };
  }, [url]);

  return { dispatches, connectionStatus };
}
```

## 4.3 `MapView.jsx` — Plotting Incidents on a Leaflet Map

```jsx
// MapView.jsx
//
// Renders a Leaflet map and drops a colored marker for every dispatch
// we've received over the WebSocket. Marker color reflects severity.

import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Map each severity level to a color for the marker.
const SEVERITY_COLORS = {
  LOW: "#3b82f6",       // blue
  MEDIUM: "#f59e0b",    // amber
  HIGH: "#ef4444",      // red
  CRITICAL: "#7c2d12",  // dark red/brown
};

export default function MapView({ dispatches }) {
  // Center the map on the city's approximate center.
  // In production, this could come from a config/env value.
  const cityCenter = [18.5204, 73.8567];

  return (
    <MapContainer
      center={cityCenter}
      zoom={13}
      style={{ height: "100%", width: "100%" }}
    >
      {/* The base map tiles — OpenStreetMap is free and requires no API key */}
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution="&copy; OpenStreetMap contributors"
      />

      {/* One CircleMarker per dispatch we've received */}
      {dispatches.map((dispatch) => (
        <CircleMarker
          key={dispatch.incident_id}
          center={[dispatch.latitude, dispatch.longitude]}
          radius={10}
          pathOptions={{
            color: SEVERITY_COLORS[dispatch.severity] || "#6b7280",
            fillColor: SEVERITY_COLORS[dispatch.severity] || "#6b7280",
            fillOpacity: 0.7,
          }}
        >
          <Popup>
            <strong>{dispatch.category}</strong> — {dispatch.severity}
            <br />
            {dispatch.dispatch_text}
            <br />
            <em>Responder: {dispatch.recommended_responder_id ?? "Unassigned"}</em>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
```

## 4.4 `App.jsx` — The Main Dashboard

```jsx
// App.jsx
//
// The top-level dashboard component. It uses our WebSocket hook to get
// live dispatches, shows a connection status indicator, splits the
// screen into a map (left) and a scrolling incident feed (right).

import { useDispatchSocket } from "./useDispatchSocket";
import MapView from "./MapView";
import "./App.css";

// Point this at your FastAPI server's WebSocket endpoint.
const WS_URL = "ws://localhost:8000/ws/dispatches";

export default function App() {
  const { dispatches, connectionStatus } = useDispatchSocket(WS_URL);

  return (
    <div style={{ display: "flex", height: "100vh", flexDirection: "column" }}>
      {/* Header bar with connection status */}
      <header style={{ padding: "12px 20px", background: "#111827", color: "white" }}>
        <h1 style={{ margin: 0, fontSize: "18px" }}>ResiliNet AI — Command Center</h1>
        <span
          style={{
            fontSize: "12px",
            color: connectionStatus === "connected" ? "#22c55e" : "#ef4444",
          }}
        >
          ● {connectionStatus.toUpperCase()}
        </span>
      </header>

      {/* Main content: map + feed side by side */}
      <div style={{ display: "flex", flex: 1 }}>
        {/* Map takes most of the width */}
        <div style={{ flex: 3 }}>
          <MapView dispatches={dispatches} />
        </div>

        {/* Live incident feed in a scrollable sidebar */}
        <div style={{ flex: 1, overflowY: "auto", borderLeft: "1px solid #e5e7eb", padding: "12px" }}>
          <h2 style={{ fontSize: "14px", color: "#6b7280" }}>Live Dispatches</h2>
          {dispatches.length === 0 && <p>Waiting for incidents...</p>}
          {dispatches.map((d) => (
            <div
              key={d.incident_id}
              style={{
                marginBottom: "10px",
                padding: "10px",
                borderRadius: "6px",
                border: "1px solid #e5e7eb",
              }}
            >
              <strong>{d.severity}</strong> — {d.category}
              <p style={{ fontSize: "13px", margin: "4px 0" }}>{d.dispatch_text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

```jsx
// main.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

---

# Part 5: The Mobile Field App (Flutter)

## 5.1 Project Structure & Dependencies

```
resilinet_field_app/
├── lib/
│   ├── main.dart
│   ├── models/
│   │   └── dispatch.dart
│   ├── services/
│   │   └── dispatch_service.dart
│   ├── providers/
│   │   └── dispatch_provider.dart
│   └── screens/
│       └── dispatch_screen.dart
└── pubspec.yaml
```

`pubspec.yaml` dependencies:

```yaml
dependencies:
  flutter:
    sdk: flutter
  provider: ^6.1.2          # state management
  http: ^1.2.1               # REST calls
  web_socket_channel: ^2.4.0  # live updates
```

## 5.2 `models/dispatch.dart` — The Data Model

```dart
// models/dispatch.dart
//
// A plain Dart class representing one dispatch update, plus a
// `fromJson` factory constructor that converts the backend's JSON
// (matching our Python DispatchUpdate Pydantic model) into this object.

class Dispatch {
  final String incidentId;
  final String severity;
  final String dispatchText;
  final String? recommendedResponderId;
  final String? recommendedInfrastructureId;
  final double latitude;
  final double longitude;
  final String category;

  Dispatch({
    required this.incidentId,
    required this.severity,
    required this.dispatchText,
    required this.latitude,
    required this.longitude,
    required this.category,
    this.recommendedResponderId,
    this.recommendedInfrastructureId,
  });

  // Build a Dispatch from a decoded JSON map.
  factory Dispatch.fromJson(Map<String, dynamic> json) {
    return Dispatch(
      incidentId: json['incident_id'] as String,
      severity: json['severity'] as String,
      dispatchText: json['dispatch_text'] as String,
      recommendedResponderId: json['recommended_responder_id'] as String?,
      recommendedInfrastructureId: json['recommended_infrastructure_id'] as String?,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      category: json['category'] as String,
    );
  }
}
```

## 5.3 `services/dispatch_service.dart` — Fetching & Listening for Dispatches

```dart
// services/dispatch_service.dart
//
// This service is responsible for ALL communication with the backend:
//   1. fetchActiveDispatches() — a one-time REST call to load existing
//      dispatches when the app first opens.
//   2. connectToLiveUpdates() — opens a WebSocket and exposes a Stream
//      of new Dispatch objects as they arrive in real time.

import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

import '../models/dispatch.dart';

class DispatchService {
  // Base URL of the FastAPI backend.
  // On a physical device, replace "localhost" with your machine's
  // LAN IP (e.g. "192.168.1.42") so the phone can reach your laptop.
  static const String _baseUrl = "http://localhost:8000";
  static const String _wsUrl = "ws://localhost:8000/ws/dispatches";

  WebSocketChannel? _channel;

  /// One-time REST fetch of currently active dispatches.
  /// (Assumes the backend exposes a GET /dispatches endpoint returning
  /// a JSON array of DispatchUpdate-shaped objects — add this endpoint
  /// to main.py analogous to /report if you need historical data on
  /// app launch.)
  Future<List<Dispatch>> fetchActiveDispatches() async {
    final response = await http.get(Uri.parse('$_baseUrl/dispatches'));

    if (response.statusCode == 200) {
      // Decode the JSON array and map each element to a Dispatch object.
      final List<dynamic> jsonList = jsonDecode(response.body);
      return jsonList.map((item) => Dispatch.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load dispatches: ${response.statusCode}');
    }
  }

  /// Opens a WebSocket connection and returns a Stream that emits a
  /// new Dispatch object every time the backend broadcasts one.
  Stream<Dispatch> connectToLiveUpdates() {
    _channel = WebSocketChannel.connect(Uri.parse(_wsUrl));

    // `_channel.stream` emits raw JSON strings. We `map` each one
    // through json.decode + Dispatch.fromJson to get typed objects.
    return _channel!.stream.map((rawMessage) {
      final Map<String, dynamic> json = jsonDecode(rawMessage as String);
      return Dispatch.fromJson(json);
    });
  }

  /// Call this when the app closes or the user logs out, to avoid
  /// leaking the WebSocket connection.
  void dispose() {
    _channel?.sink.close();
  }
}
```

## 5.4 `providers/dispatch_provider.dart` — State Management for the Live Feed

```dart
// providers/dispatch_provider.dart
//
// We use the `provider` package with `ChangeNotifier`. This is the
// simplest state management approach that still supports a live,
// continuously-updating feed:
//
//   - The provider holds the single source of truth: a List<Dispatch>.
//   - It subscribes to the WebSocket stream from DispatchService.
//   - Every time a new Dispatch arrives, it's added to the list and
//     `notifyListeners()` is called.
//   - Any widget wrapped in a `Consumer<DispatchProvider>` (or using
//     `context.watch<DispatchProvider>()`) automatically rebuilds
//     ONLY when notifyListeners() fires — no manual setState needed,
//     and no unrelated widgets rebuild.

import 'package:flutter/foundation.dart';
import '../models/dispatch.dart';
import '../services/dispatch_service.dart';

class DispatchProvider extends ChangeNotifier {
  final DispatchService _service = DispatchService();

  // The list of dispatches currently known to the app, newest first.
  final List<Dispatch> _dispatches = [];
  List<Dispatch> get dispatches => List.unmodifiable(_dispatches);

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _error;
  String? get error => _error;

  /// Call once when the app starts: load existing dispatches via REST,
  /// then start listening for new ones via WebSocket.
  Future<void> initialize() async {
    _isLoading = true;
    notifyListeners();

    try {
      final initial = await _service.fetchActiveDispatches();
      _dispatches.addAll(initial);
    } catch (e) {
      // Non-fatal: if the REST call fails, we still proceed to listen
      // for live updates — the user just starts with an empty feed.
      _error = "Could not load history: $e";
    }

    _isLoading = false;
    notifyListeners();

    // Subscribe to the live WebSocket stream.
    _service.connectToLiveUpdates().listen(
      (newDispatch) {
        // Insert newest dispatch at the top of the list.
        _dispatches.insert(0, newDispatch);
        // This is the key call: it tells every widget listening to
        // this provider to rebuild with the updated list.
        notifyListeners();
      },
      onError: (err) {
        _error = "Live connection lost: $err";
        notifyListeners();
      },
    );
  }

  @override
  void dispose() {
    _service.dispose();
    super.dispose();
  }
}
```

## 5.5 `main.dart` — App Entry Point

```dart
// main.dart
//
// Wraps the entire app in a ChangeNotifierProvider, so any screen
// can access DispatchProvider via context.watch / context.read.

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'providers/dispatch_provider.dart';
import 'screens/dispatch_screen.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      // `..initialize()` uses Dart's cascade operator: create the
      // provider, then immediately call initialize() on it.
      create: (_) => DispatchProvider()..initialize(),
      child: const ResiliNetApp(),
    ),
  );
}

class ResiliNetApp extends StatelessWidget {
  const ResiliNetApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ResiliNet Field App',
      theme: ThemeData(primarySwatch: Colors.red, useMaterial3: true),
      home: const DispatchScreen(),
    );
  }
}
```

## 5.6 `screens/dispatch_screen.dart` — Displaying the Live Feed

```dart
// screens/dispatch_screen.dart
//
// Shows a scrolling list of dispatches, color-coded by severity.
// `Consumer<DispatchProvider>` rebuilds this list automatically
// whenever the provider calls notifyListeners() — e.g. when a new
// dispatch arrives over the WebSocket.

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/dispatch_provider.dart';
import '../models/dispatch.dart';

class DispatchScreen extends StatelessWidget {
  const DispatchScreen({super.key});

  // Map severity strings to colors, mirroring the React dashboard.
  Color _severityColor(String severity) {
    switch (severity) {
      case 'CRITICAL':
        return Colors.brown.shade900;
      case 'HIGH':
        return Colors.red;
      case 'MEDIUM':
        return Colors.orange;
      default:
        return Colors.blue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Active Dispatches')),
      // Consumer rebuilds ONLY this part of the tree on updates.
      body: Consumer<DispatchProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.dispatches.isEmpty) {
            return const Center(child: Text('No active dispatches.'));
          }

          return ListView.builder(
            itemCount: provider.dispatches.length,
            itemBuilder: (context, index) {
              final Dispatch d = provider.dispatches[index];
              return Card(
                margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: _severityColor(d.severity),
                    child: Text(
                      d.severity[0], // first letter: L, M, H, C
                      style: const TextStyle(color: Colors.white),
                    ),
                  ),
                  title: Text(d.category),
                  subtitle: Text(d.dispatchText),
                  trailing: Text(
                    d.recommendedResponderId ?? 'Unassigned',
                    style: const TextStyle(fontSize: 12),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
```

### Why `ChangeNotifier` + `Provider` for this specific requirement

The field app's core requirement is: **"a list that updates itself in real time as the server pushes new items, without the developer manually wiring rebuilds everywhere."** `ChangeNotifier` fits this precisely:

- The **WebSocket stream lives inside the provider**, not inside any widget — so it survives screen navigation and isn't tied to a widget's lifecycle.
- `notifyListeners()` is the *only* signal widgets need to care about. The provider doesn't know or care which widgets are listening.
- `Consumer<DispatchProvider>` scopes rebuilds to just the part of the tree that displays the list — the `AppBar`, `Scaffold`, etc. don't rebuild on every new dispatch.
- It avoids the alternative of passing a `StreamBuilder` + the raw `WebSocketChannel` down through widget constructors, which gets messy once you have more than one screen that needs the same live data (e.g. a map screen *and* a list screen both showing dispatches).

For a small app like this, `Provider` is the right amount of complexity — it's part of the official Flutter team's recommended state management approaches, with far less boilerplate than `Bloc` or `Riverpod` for a single shared live list.

---

## Closing Notes — Running the Full Stack Together

1. **Start Neo4j** (Docker command in Part 2) and run the schema/seed Cypher in the Neo4j Browser at `http://localhost:7474`.
2. **Start the backend**: `uvicorn main:app --reload --port 8000` (set `ANTHROPIC_API_KEY`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` in `.env` or your shell environment).
3. **Start the React dashboard**: `npm run dev` inside `resilinet-frontend`.
4. **Run the Flutter app**: `flutter run` — on a physical device, update `_baseUrl`/`_wsUrl` in `dispatch_service.dart` to your machine's LAN IP.
5. **Test it**: send a `POST /report` from `http://localhost:8000/docs` with a sample incident — within a few seconds you should see it appear on both the React map and (once you add the `/dispatches` GET endpoint) the Flutter feed.

From here, the natural next steps are: adding authentication, a `GET /dispatches` history endpoint, richer infrastructure types (roads, sensors, blocked routes), and expanding the GraphRAG query to consider multi-hop relationships like "responders who can reach this location via roads that aren't `BLOCKED`."
