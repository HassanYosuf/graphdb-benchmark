"""
registry.py -- the list of databases under test.

Adding a database to the benchmark means adding one entry here (plus a
connector class if it's a new protocol family). Every entry is skipped
gracefully with a clear message if its required env vars aren't set, so
`--targets all` works even if you've only configured some of the five.
"""
from .bolt_connector import BoltConnector


def build_registry():
    registry = {}

    def try_add(key, factory):
        try:
            registry[key] = factory()
        except RuntimeError as e:
            registry[key] = None
            registry.setdefault("_skip_reasons", {})[key] = str(e)

    try_add("cognodb", lambda: BoltConnector(
        "CognoDB Cloud", "COGNODB_URI", "COGNODB_USER", "COGNODB_PASSWORD"))

    try_add("neo4j_aura", lambda: BoltConnector(
        "Neo4j AuraDB Free", "NEO4J_AURA_URI", "NEO4J_AURA_USER", "NEO4J_AURA_PASSWORD"))

    try_add("memgraph", lambda: BoltConnector(
        "Memgraph (self-hosted, capped)", "MEMGRAPH_URI", "MEMGRAPH_USER", "MEMGRAPH_PASSWORD",
        # Memgraph has no database named "neo4j" (the BoltConnector default) --
        # it doesn't support Neo4j-style multi-database routing, so passing
        # None lets the driver omit the database name and use Memgraph's own
        # default instead of erroring with "unknown database neo4j".
        database=None,
        cypher_overrides={
            # Two Memgraph dialect differences from the shared Cypher, both
            # confirmed by testing directly against the container:
            # 1. No shortestPath() function -- Memgraph expresses "shortest
            #    path up to depth N" via a *BFS quantifier on the
            #    relationship pattern instead.
            # 2. No length() function for paths (use size() instead), and
            #    "hops" is apparently a reserved word in Memgraph's grammar
            #    ("RETURN ... AS hops" fails to parse; "AS numhops" is fine)
            #    -- neither issue affects any other target, which all use
            #    plain length(p) AS hops without incident.
            "shortest_path_two_people": (
                "MATCH p = (a:Person {id: $pid})-[:FOLLOWS *BFS..6]-(b:Person {id: $prod_id}) "
                "RETURN size(p) AS numhops"
            ),
        }))

    try_add("neo4j_community", lambda: BoltConnector(
        "Neo4j Community (self-hosted, capped)", "NEO4J_COMMUNITY_URI",
        "NEO4J_COMMUNITY_USER", "NEO4J_COMMUNITY_PASSWORD"))

    try:
        from .arangodb_connector import ArangoConnector
        try_add("arangodb", ArangoConnector)
    except ImportError:
        registry["arangodb"] = None
        registry.setdefault("_skip_reasons", {})["arangodb"] = "python-arango not installed"

    try:
        from .falkordb_connector import FalkorConnector
        try_add("falkordb", FalkorConnector)
    except ImportError:
        registry["falkordb"] = None
        registry.setdefault("_skip_reasons", {})["falkordb"] = "falkordb package not installed"

    return registry
