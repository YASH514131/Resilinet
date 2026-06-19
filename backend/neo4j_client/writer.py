# neo4j_client/writer.py
#
# All Cypher writes for Phase 1: creating DetectionEvent nodes,
# linking them to the Camera, and updating Camera status.

import uuid
from datetime import datetime, timezone
from neo4j import Driver


def _write_detection_event_tx(tx, camera_id: str, event_type: str,
                               confidence: float, evidence_path: str,
                               track_ids: list[int]) -> str:
    """
    Transaction function that creates a DetectionEvent node and
    links it to the Camera that fired the event.

    Returns the new DetectionEvent id.
    """
    event_id = f"det-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    query = """
        // Create the DetectionEvent node
        CREATE (d:DetectionEvent {
            id:            $event_id,
            event_type:    $event_type,
            confidence:    $confidence,
            evidence_path: $evidence_path,
            track_ids:     $track_ids,
            triggered_at:  datetime($now),
            resolved_at:   null
        })

        // Optionally link it to an existing Camera (if present)
        WITH d
        OPTIONAL MATCH (c:Camera { id: $camera_id })
        FOREACH (_ IN CASE WHEN c IS NULL THEN [] ELSE [1] END |
            CREATE (d)-[:DETECTED_BY]->(c)
        )

        // Optionally link DetectionEvent to the Camera's Location (if present)
        WITH d
        OPTIONAL MATCH (c:Camera { id: $camera_id })-[:POSITIONED_AT]->(l:Location)
        FOREACH (_ IN CASE WHEN l IS NULL THEN [] ELSE [1] END |
            CREATE (d)-[:LOCATED_AT]->(l)
        )

        // Always return the newly-created DetectionEvent id
        RETURN d.id AS event_id
    """

    result = tx.run(
        query,
        event_id=event_id,
        event_type=event_type,
        confidence=round(confidence, 4),
        evidence_path=evidence_path,
        track_ids=[str(t) for t in track_ids],
        camera_id=camera_id,
        now=now,
    )
    return result.single()["event_id"]


def save_detection_event(driver: Driver, camera_id: str, event_type: str,
                          confidence: float, evidence_path: str,
                          track_ids: list[int]) -> str:
    """
    Public helper: opens a session, runs the write transaction,
    returns the created DetectionEvent id.
    """
    with driver.session() as session:
        event_id = session.execute_write(
            _write_detection_event_tx,
            camera_id, event_type, confidence, evidence_path, track_ids
        )
    print(f"[DB] DetectionEvent saved → id={event_id}  camera={camera_id}  type={event_type}")
    return event_id


def update_camera_status(driver: Driver, camera_id: str, status: str) -> None:
    """
    Set a Camera node's status property.
    status must be one of: ACTIVE | OFFLINE | MAINTENANCE
    """
    with driver.session() as session:
        session.run(
            "MATCH (c:Camera { id: $id }) SET c.status = $status",
            id=camera_id,
            status=status,
        )
    print(f"[DB] Camera {camera_id} status → {status}")
