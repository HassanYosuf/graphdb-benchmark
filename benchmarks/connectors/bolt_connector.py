"""
bolt_connector.py

One connector class reused for every database that speaks Bolt + Cypher:
CognoDB Cloud, Neo4j AuraDB Free, Memgraph, and self-hosted Neo4j Community.
This is deliberate: CognoDB's whole pitch is "point the official Neo4j
driver at our bolt+s:// URI, nothing else changes" -- so using the literal
same driver, same connector class, and same query strings for all four is
the fairest possible test of that claim. Any behavioral difference measured
between them is a difference in the database, not in how we talked to it.

Connection details come from environment variables (see .env.example) so no
credentials are ever hard-coded or committed.
"""
import os
from neo4j import GraphDatabase
from .base import GraphConnector


class BoltConnector(GraphConnector):
    def __init__(self, display_name: str, uri_env: str, user_env: str, pass_env: str,
                 database: str = "neo4j", cypher_overrides: dict = None):
        self.display_name = display_name
        self.uri = os.environ.get(uri_env)
        self.user = os.environ.get(user_env, "neo4j")
        self.password = os.environ.get(pass_env)
        self.database = database
        # Per-workload-name Cypher overrides for targets whose dialect
        # deviates from Neo4j's on a specific query -- e.g. Memgraph doesn't
        # implement the shortestPath() function (see registry.py). Empty by
        # default: every other Bolt target runs the exact same query string.
        self.cypher_overrides = cypher_overrides or {}
        self.driver = None
        if not self.uri:
            raise RuntimeError(
                f"{display_name}: missing {uri_env} in environment. "
                f"Copy .env.example to .env and fill in your credentials."
            )

    def connect(self):
        # self-hosted no-auth targets (e.g. default Memgraph docker config)
        # leave the password unset -- pass no auth rather than ("user", "").
        auth = (self.user, self.password) if self.password else None
        self.driver = GraphDatabase.driver(self.uri, auth=auth)
        self.driver.verify_connectivity()

    def close(self):
        if self.driver:
            self.driver.close()

    def run(self, workload: dict, params: dict):
        cypher = self.cypher_overrides.get(workload["name"], workload["cypher"])
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, params)
            return list(result)  # force materialization

    def wipe(self):
        with self.driver.session(database=self.database) as session:
            # batched delete -- a single MATCH ()-[r]->() DELETE r, n on a
            # 256MB-RAM instance can blow past memory; APOC periodic iterate
            # isn't guaranteed available on every target, so we page it
            # manually in pure Cypher instead.
            while True:
                result = session.run(
                    "MATCH (n) WITH n LIMIT 2000 DETACH DELETE n RETURN count(n) AS c"
                )
                deleted = result.single()["c"]
                if deleted == 0:
                    break

    def bulk_load(self, dataset_dir: str):
        import csv as csvmod
        from time import perf_counter

        t0 = perf_counter()
        with self.driver.session(database=self.database) as session:
            self._create_unique_constraint(session, "person_id", "Person")
            self._create_unique_constraint(session, "product_id", "Product")

            self._load_nodes(session, f"{dataset_dir}/persons.csv", "Person",
                              lambda row: {"id": int(row["id:ID"]), "name": row["name"],
                                           "age": int(row["age:int"]), "country": row["country"]})
            self._load_nodes(session, f"{dataset_dir}/products.csv", "Product",
                              lambda row: {"id": int(row["id:ID"]), "name": row["name"],
                                           "category": row["category"], "price": float(row["price:float"])})
            self._load_edges(session, f"{dataset_dir}/follows.csv", "Person", "Person", "FOLLOWS")
            self._load_edges(session, f"{dataset_dir}/purchased.csv", "Person", "Product", "PURCHASED",
                              extra=lambda row: {"ts": row["ts"], "amount": float(row["amount:float"])})
            self._load_edges(session, f"{dataset_dir}/similar_to.csv", "Product", "Product", "SIMILAR_TO")
        return perf_counter() - t0

    @staticmethod
    def _create_unique_constraint(session, name, label):
        # Neo4j 5 / CognoDB syntax first; Memgraph doesn't understand
        # "CREATE CONSTRAINT <name> IF NOT EXISTS FOR ... REQUIRE ... IS
        # UNIQUE" (no named constraints, uses ON/ASSERT instead of
        # FOR/REQUIRE) so fall back to its syntax on parse failure. Both
        # branches end up with the same effective index/constraint, so
        # every target still gets the same fair "id lookups are indexed"
        # guarantee.
        try:
            session.run(
                f"CREATE CONSTRAINT {name} IF NOT EXISTS FOR (p:{label}) REQUIRE p.id IS UNIQUE"
            )
        except Exception:
            try:
                session.run(f"CREATE CONSTRAINT ON (p:{label}) ASSERT p.id IS UNIQUE")
            except Exception:
                pass  # already exists from a previous run

    @staticmethod
    def _load_nodes(session, path, label, row_to_props, batch_size=500):
        import csv as csvmod
        with open(path) as f:
            reader = csvmod.DictReader(f)
            batch = []
            for row in reader:
                batch.append(row_to_props(row))
                if len(batch) >= batch_size:
                    session.run(
                        f"UNWIND $rows AS row CREATE (n:{label}) SET n = row", rows=batch
                    )
                    batch = []
            if batch:
                session.run(f"UNWIND $rows AS row CREATE (n:{label}) SET n = row", rows=batch)

    @staticmethod
    def _load_edges(session, path, from_label, to_label, rel_type, extra=None, batch_size=500):
        import csv as csvmod
        with open(path) as f:
            reader = csvmod.DictReader(f)
            batch = []
            for row in reader:
                item = {"a": int(row[":START_ID"]), "b": int(row[":END_ID"])}
                if extra:
                    item["props"] = extra(row)
                batch.append(item)
                if len(batch) >= batch_size:
                    BoltConnector._flush_edges(session, batch, from_label, to_label, rel_type, extra is not None)
                    batch = []
            if batch:
                BoltConnector._flush_edges(session, batch, from_label, to_label, rel_type, extra is not None)

    @staticmethod
    def _flush_edges(session, batch, from_label, to_label, rel_type, has_props):
        if has_props:
            session.run(
                f"UNWIND $rows AS row "
                f"MATCH (a:{from_label} {{id: row.a}}), (b:{to_label} {{id: row.b}}) "
                f"CREATE (a)-[r:{rel_type}]->(b) SET r = row.props",
                rows=batch,
            )
        else:
            session.run(
                f"UNWIND $rows AS row "
                f"MATCH (a:{from_label} {{id: row.a}}), (b:{to_label} {{id: row.b}}) "
                f"CREATE (a)-[:{rel_type}]->(b)",
                rows=batch,
            )
