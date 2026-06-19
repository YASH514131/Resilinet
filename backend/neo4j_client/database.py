# neo4j_client/database.py
#
# Owns the single Neo4j Driver instance for the Phase 1 pipeline.
# Call connect() once at startup, get_driver() everywhere else.

import os
from neo4j import GraphDatabase, Driver

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

_driver: Driver | None = None


def connect() -> None:
    """Create and verify the Neo4j driver. Call once at app start."""
    global _driver
    _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    _driver.verify_connectivity()
    print(f"[DB] Connected to Neo4j at {NEO4J_URI}")


def close() -> None:
    """Close the driver's connection pool. Call once at app shutdown."""
    global _driver
    if _driver:
        _driver.close()
        print("[DB] Neo4j connection closed")


def get_driver() -> Driver:
    """Return the shared driver instance."""
    if _driver is None:
        raise RuntimeError("Neo4j driver not initialised — call connect() first")
    return _driver
