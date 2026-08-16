"""
falkordb_connector.py

FalkorDB speaks Cypher too (via GRAPH.QUERY over the Redis protocol), so the
query strings from workloads.py are reused almost verbatim -- the only
translation needed is because FalkorDB's `shortestPath` support and
parameter-binding syntax differ slightly from Neo4j's. Those specific
deviations are marked inline below; everything else is character-for-character
the same Cypher as every Bolt target runs.
"""
import os
from time import perf_counter
from falkordb import FalkorDB
from .base import GraphConnector

# Only the two workloads that need any change from the shared Cypher text.
# Every other workload name maps straight through to workloads.WORKLOADS.
FALKOR_OVERRIDES = {
    "shortest_path_two_people": (
        # FalkorDB requires a and b to be fully resolved (via an explicit
        # WITH) before they can be referenced inside allShortestPaths --
        # unlike Neo4j, which accepts them bound directly in the same MATCH.
        "MATCH (a:Person {id: $pid}), (b:Person {id: $prod_id}) "
        "WITH a, b "
        "MATCH p = allShortestPaths((a)-[:FOLLOWS*..6]->(b)) "
        "RETURN length(p) AS hops LIMIT 1"
    ),
}


class FalkorConnector(GraphConnector):
    display_name = "FalkorDB Cloud"

    def __init__(self):
        self.host = os.environ.get("FALKOR_HOST")
        self.port = int(os.environ.get("FALKOR_PORT", "6379"))
        self.username = os.environ.get("FALKOR_USER") or None
        self.password = os.environ.get("FALKOR_PASSWORD")
        self.graph_name = os.environ.get("FALKOR_GRAPH", "benchmark")
        self.db = None
        self.graph = None
        if not self.host:
            raise RuntimeError("FalkorDB: missing FALKOR_HOST in environment.")

    def connect(self):
        # socket_connect_timeout: an unreachable or misconfigured (e.g. wrong
        # TLS setting) endpoint otherwise hangs indefinitely instead of
        # failing fast. socket_timeout is deliberately generous (not the
        # tight per-query benchmark timing -- that's measured client-side in
        # run_benchmark.py): a 500-row batch CREATE against a shared
        # free-tier instance can legitimately take longer than a plain query,
        # and a too-tight socket_timeout here previously aborted bulk_load
        # outright ("Timeout reading from socket") on a batch that was still
        # making progress, not actually stuck.
        self.db = FalkorDB(
            host=self.host, port=self.port, username=self.username, password=self.password,
            socket_connect_timeout=10, socket_timeout=120,
        )
        self.graph = self.db.select_graph(self.graph_name)
        # matches the UNIQUE constraint (index) the Bolt connector creates on
        # Person.id/Product.id -- without this, id lookups below are a full
        # label scan on FalkorDB but an index seek on every Bolt target.
        # try/except: FalkorDB errors on re-creating an existing index, and
        # this connect() call can run again against an already-indexed graph.
        for q in ("CREATE INDEX FOR (p:Person) ON (p.id)", "CREATE INDEX FOR (p:Product) ON (p.id)"):
            try:
                self.graph.query(q)
            except Exception:
                pass

    def close(self):
        pass

    def run(self, workload: dict, params: dict):
        cypher = FALKOR_OVERRIDES.get(workload["name"], workload["cypher"])
        result = self.graph.query(cypher, params)
        return result.result_set

    def wipe(self):
        try:
            self.graph.delete()
        except Exception:
            pass

    def bulk_load(self, dataset_dir: str):
        import csv as csvmod
        t0 = perf_counter()

        def batch_create_nodes(path, label, row_fn, batch_size=500):
            with open(path) as f:
                reader = csvmod.DictReader(f)
                batch = [row_fn(r) for r in reader]
            for i in range(0, len(batch), batch_size):
                chunk = batch[i:i + batch_size]
                self.graph.query(
                    f"UNWIND $rows AS row CREATE (n:{label}) SET n = row", {"rows": chunk}
                )

        def batch_create_edges(path, from_label, to_label, rel_type, extra_fn=None, batch_size=200):
            with open(path) as f:
                reader = csvmod.DictReader(f)
                batch = []
                for r in reader:
                    item = {"a": int(r[":START_ID"]), "b": int(r[":END_ID"])}
                    if extra_fn:
                        item["props"] = extra_fn(r)
                    batch.append(item)
            for i in range(0, len(batch), batch_size):
                chunk = batch[i:i + batch_size]
                if extra_fn:
                    self.graph.query(
                        f"UNWIND $rows AS row MATCH (a:{from_label} {{id: row.a}}), (b:{to_label} {{id: row.b}}) "
                        f"CREATE (a)-[r:{rel_type}]->(b) SET r = row.props",
                        {"rows": chunk},
                    )
                else:
                    self.graph.query(
                        f"UNWIND $rows AS row MATCH (a:{from_label} {{id: row.a}}), (b:{to_label} {{id: row.b}}) "
                        f"CREATE (a)-[:{rel_type}]->(b)",
                        {"rows": chunk},
                    )

        batch_create_nodes(f"{dataset_dir}/persons.csv", "Person",
                            lambda r: {"id": int(r["id:ID"]), "name": r["name"],
                                       "age": int(r["age:int"]), "country": r["country"]})
        batch_create_nodes(f"{dataset_dir}/products.csv", "Product",
                            lambda r: {"id": int(r["id:ID"]), "name": r["name"],
                                       "category": r["category"], "price": float(r["price:float"])})
        batch_create_edges(f"{dataset_dir}/follows.csv", "Person", "Person", "FOLLOWS")
        batch_create_edges(f"{dataset_dir}/purchased.csv", "Person", "Product", "PURCHASED",
                            extra_fn=lambda r: {"ts": r["ts"], "amount": float(r["amount:float"])})
        batch_create_edges(f"{dataset_dir}/similar_to.csv", "Product", "Product", "SIMILAR_TO")

        return perf_counter() - t0
