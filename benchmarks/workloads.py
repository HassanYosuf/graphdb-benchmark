"""
workloads.py

Query workloads run identically against every Cypher-compatible target
(CognoDB, Neo4j AuraDB, Memgraph, Neo4j Community self-hosted). This is the
core of the "same dataset, same workloads" fairness requirement: the exact
same query string, with the exact same bound parameters, is sent to every
database. Nothing is hand-tuned per vendor.

Each workload is a dict:
  name        -- short id, used in result filenames
  category    -- point_lookup | traversal | aggregation | write | mixed
  cypher      -- the query string
  params_fn   -- callable(rng) -> dict of bound params, re-rolled per iteration
                 so we're not just hitting one hot cached row every time
  read_only   -- bool, informs whether we run it against a read-replica-style
                 warm cache pass or treat it as a write that mutates state

ArangoDB (AQL) and FalkorDB (Redis protocol) cannot run these Cypher strings
verbatim -- see benchmarks/connectors/arangodb.py and falkordb.py for the
translated-but-semantically-equivalent versions of the SAME workloads
(same selectivity, same result shape, same number of hops). Any deliberate
translation choices are called out in README "Methodology > cross-language
query parity".
"""
import random


def _rand_person_id(rng):
    return {"pid": rng.randint(0, 4999)}


def _rand_product_id(rng):
    return {"pid": rng.randint(0, 1999)}


def _rand_person_and_product(rng):
    return {"pid": rng.randint(0, 4999), "prod_id": rng.randint(0, 1999)}


def _rand_write_person(rng):
    # ids above the loaded range so writes never collide with seed data or
    # each other across concurrent benchmark runs
    new_id = 900_000 + rng.randint(0, 10_000_000)
    return {"id": new_id, "name": f"bench_person_{new_id}", "age": rng.randint(18, 75)}


WORKLOADS = [
    {
        "name": "point_lookup_person",
        "category": "point_lookup",
        "cypher": "MATCH (p:Person {id: $pid}) RETURN p.name, p.age, p.country",
        "params_fn": _rand_person_id,
        "read_only": True,
    },
    {
        "name": "one_hop_who_they_follow",
        "category": "traversal",
        "cypher": (
            "MATCH (p:Person {id: $pid})-[:FOLLOWS]->(f:Person) "
            "RETURN f.id, f.name LIMIT 50"
        ),
        "params_fn": _rand_person_id,
        "read_only": True,
    },
    {
        "name": "two_hop_friends_of_friends",
        "category": "traversal",
        "cypher": (
            "MATCH (p:Person {id: $pid})-[:FOLLOWS]->()-[:FOLLOWS]->(fof:Person) "
            "WHERE fof.id <> $pid "
            "RETURN DISTINCT fof.id, fof.name LIMIT 50"
        ),
        "params_fn": _rand_person_id,
        "read_only": True,
    },
    {
        "name": "recommendation_bought_similar",
        "category": "traversal",
        "cypher": (
            "MATCH (p:Person {id: $pid})-[:PURCHASED]->(:Product)"
            "-[:SIMILAR_TO]->(rec:Product) "
            "RETURN DISTINCT rec.id, rec.name, rec.category LIMIT 20"
        ),
        "params_fn": _rand_person_id,
        "read_only": True,
    },
    {
        "name": "shortest_path_two_people",
        "category": "traversal",
        "cypher": (
            "MATCH p = shortestPath((a:Person {id: $pid})-[:FOLLOWS*..6]-(b:Person {id: $prod_id}))"
            " RETURN length(p) AS hops"
        ),
        # note: prod_id here is reused as a second person id 0-1999 range,
        # kept intentionally inside the hub-heavy low-id band so a path is
        # likely to exist within the hop limit on this synthetic graph
        "params_fn": _rand_person_and_product,
        "read_only": True,
    },
    {
        "name": "aggregation_spend_by_category",
        "category": "aggregation",
        "cypher": (
            "MATCH (p:Person {id: $pid})-[pu:PURCHASED]->(prod:Product) "
            "RETURN prod.category AS category, sum(pu.amount) AS total, count(*) AS n "
            "ORDER BY total DESC"
        ),
        "params_fn": _rand_person_id,
        "read_only": True,
    },
    {
        "name": "aggregation_top_products_global",
        "category": "aggregation",
        "cypher": (
            "MATCH (:Person)-[pu:PURCHASED]->(prod:Product) "
            "RETURN prod.category AS category, count(*) AS purchases, avg(pu.amount) AS avg_amount "
            "ORDER BY purchases DESC LIMIT 10"
        ),
        "params_fn": lambda rng: {},
        "read_only": True,
    },
    {
        "name": "write_create_person",
        "category": "write",
        "cypher": (
            "CREATE (p:Person {id: $id, name: $name, age: $age, country: 'IN'}) "
            "RETURN p.id"
        ),
        "params_fn": _rand_write_person,
        "read_only": False,
    },
    {
        "name": "write_create_follow_edge",
        "category": "write",
        "cypher": (
            "MATCH (a:Person {id: $pid}), (b:Person {id: $prod_id}) "
            "CREATE (a)-[:FOLLOWS]->(b)"
        ),
        "params_fn": _rand_person_and_product,
        "read_only": False,
    },
]


def get_workloads(categories=None):
    """Filter workloads by category list, or return all."""
    if categories is None:
        return WORKLOADS
    return [w for w in WORKLOADS if w["category"] in categories]
