import pytest
from server.src.database.neo4j_connector import Neo4jConnector

@pytest.fixture
def neo4j_connector():
    connector = Neo4jConnector(uri="bolt://localhost:7687", user="neo4j", password="password")
    yield connector
    connector.close()

def test_find_laundering_rings(neo4j_connector):
    # Assuming the database is seeded with known data for testing
    rings = neo4j_connector.find_laundering_rings()
    assert isinstance(rings, list)
    assert all(isinstance(ring, dict) for ring in rings)
    assert all('path' in ring for ring in rings)  # Check if each ring has a path key
    assert all(len(ring['path']) >= 3 for ring in rings)  # Ensure paths are of length 3 or more

def test_connection(neo4j_connector):
    assert neo4j_connector is not None
    assert neo4j_connector.session is not None

def test_invalid_query(neo4j_connector):
    with pytest.raises(Exception):
        neo4j_connector.run_query("INVALID CYPHER QUERY")  # Expecting an error on invalid query