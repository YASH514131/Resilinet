// ============================================================
// ResiliNet AI — Phase 1 CCTV Extension
// Neo4j Schema Setup: Camera Nodes + Seed Data
//
// Run these statements in order in the Neo4j Browser
// at http://localhost:7474  OR  via cypher-shell.
// ============================================================


// ── STEP 1: CONSTRAINTS ─────────────────────────────────────
//
// Guarantees no two Camera nodes share the same id.
// Also auto-creates a fast lookup index on Camera.id.

CREATE CONSTRAINT camera_id_unique IF NOT EXISTS
FOR (c:Camera) REQUIRE c.id IS UNIQUE;

// DetectionEvent uniqueness (used when Phase 1 writes events)
CREATE CONSTRAINT detection_event_id_unique IF NOT EXISTS
FOR (d:DetectionEvent) REQUIRE d.id IS UNIQUE;


// ── STEP 2: POINT INDEX FOR CAMERA LOCATION ─────────────────
//
// Cameras will be linked to Location nodes (which already have
// a point index from the base ResiliNet schema). No extra index
// needed here — the existing location_point_index covers it.
//
// If running this standalone (without the base ResiliNet schema),
// create the Location constraint + index first:

CREATE CONSTRAINT location_id_unique IF NOT EXISTS
FOR (l:Location) REQUIRE l.id IS UNIQUE;

CREATE POINT INDEX location_point_index IF NOT EXISTS
FOR (l:Location) ON (l.coordinates);


// ── STEP 3: SEED — LOCATION NODES ───────────────────────────
//
// Each camera needs a Location node to anchor it geographically.
// Using MERGE so re-running this script is safe (idempotent).

MERGE (l1:Location { id: "loc-18.5204-73.8567" })
ON CREATE SET l1.coordinates = point({ latitude: 18.5204, longitude: 73.8567 });

MERGE (l2:Location { id: "loc-18.5295-73.8505" })
ON CREATE SET l2.coordinates = point({ latitude: 18.5295, longitude: 73.8505 });

MERGE (l3:Location { id: "loc-18.5390-73.8480" })
ON CREATE SET l3.coordinates = point({ latitude: 18.5390, longitude: 73.8480 });


// ── STEP 4: SEED — CAMERA NODES ─────────────────────────────
//
// Properties:
//   id          — unique key, matches CAMERA_ID in .env
//   name        — human-readable label shown on dashboard
//   rtsp_url    — stream source (use "webcam:0" for local webcam)
//   status      — ACTIVE | OFFLINE | MAINTENANCE
//   fov_degrees — field of view (visual only, for future map overlays)
//   fps_target  — configured frame extraction rate
//   zone        — deployment zone label (free text, for filtering)

MERGE (c1:Camera { id: "cam-001" })
ON CREATE SET
  c1.name        = "Camera-01 (MG Road Junction)",
  c1.rtsp_url    = "webcam:0",
  c1.status      = "ACTIVE",
  c1.fov_degrees = 90.0,
  c1.fps_target  = 5,
  c1.zone        = "traffic";

MERGE (c2:Camera { id: "cam-002" })
ON CREATE SET
  c2.name        = "Camera-02 (Central Market)",
  c2.rtsp_url    = "rtsp://admin:password@192.168.1.65:554/stream",
  c2.status      = "ACTIVE",
  c2.fov_degrees = 120.0,
  c2.fps_target  = 5,
  c2.zone        = "crowd";

MERGE (c3:Camera { id: "cam-003" })
ON CREATE SET
  c3.name        = "Camera-03 (Riverside Bridge)",
  c3.rtsp_url    = "rtsp://admin:password@192.168.1.66:554/stream",
  c3.status      = "MAINTENANCE",
  c3.fov_degrees = 60.0,
  c3.fps_target  = 3,
  c3.zone        = "infrastructure";


// ── STEP 5: LINK CAMERAS TO LOCATIONS ───────────────────────
//
// POSITIONED_AT connects a Camera to its geographic Location.
// This is what the GraphRAG query uses to find cameras near an incident.

MATCH (c1:Camera { id: "cam-001" }), (l1:Location { id: "loc-18.5204-73.8567" })
MERGE (c1)-[:POSITIONED_AT]->(l1);

MATCH (c2:Camera { id: "cam-002" }), (l2:Location { id: "loc-18.5295-73.8505" })
MERGE (c2)-[:POSITIONED_AT]->(l2);

MATCH (c3:Camera { id: "cam-003" }), (l3:Location { id: "loc-18.5390-73.8480" })
MERGE (c3)-[:POSITIONED_AT]->(l3);


// ── STEP 6: VERIFY ──────────────────────────────────────────
//
// Run these to confirm everything looks right after seeding.

// Show all cameras with their locations:
// MATCH (c:Camera)-[:POSITIONED_AT]->(l:Location)
// RETURN c.id, c.name, c.status, c.zone, l.id
// ORDER BY c.id;

// Show all constraints:
// SHOW CONSTRAINTS;

// Show graph node counts:
// MATCH (n) RETURN labels(n) AS label, count(n) AS count ORDER BY label;
