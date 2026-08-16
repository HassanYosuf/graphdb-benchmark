"""
arangodb_connector.py

ArangoDB doesn't speak Cypher, so this connector re-expresses each workload
in AQL. Translation rule followed throughout (documented here so it's
auditable, not hidden in the code): every AQL query returns the same shape
of result, walks the same number of hops, and applies the same filters as
the Cypher original in benchmarks/workloads.py -- no query is made cheaper
or more expensive on the ArangoDB side. Where AQL has no direct equivalent
(e.g. Cypher's shortestPath), we use ArangoDB's own shortest-path traversal
syntax rather than approximating with something slower/faster.

Collections: persons, products (document collections); follows, purchased,
similar_to (edge collections) -- mirrors the Bolt schema 1:1.
"""
import os
from time import perf_counter
from arango import ArangoClient
from .base import GraphConnector

AQL_WORKLOADS = {
    "point_lookup_person": (
        "FOR p IN persons FILTER p.id == @pid RETURN {name: p.name, age: p.age, country: p.country}"
    ),
    # `WITH <collection>` declarations below are required by ArangoDB's
    # cluster query optimizer for any traversal whose start vertex is
    # addressed by a computed id (CONCAT(...)) rather than a literal --
    # without it, AQL can't statically know which collections the traversal
    # touches and errors with "collection not known to traversal".
    "one_hop_who_they_follow": (
        "WITH persons "
        "FOR v IN 1..1 OUTBOUND CONCAT('persons/', @pid) follows LIMIT 50 RETURN {id: v.id, name: v.name}"
    ),
    "two_hop_friends_of_friends": (
        "WITH persons "
        "FOR v, e, p IN 2..2 OUTBOUND CONCAT('persons/', @pid) follows "
        "FILTER v.id != @pid LIMIT 50 RETURN DISTINCT {id: v.id, name: v.name}"
    ),
    "recommendation_bought_similar": (
        "WITH persons, products "
        "FOR v1 IN 1..1 OUTBOUND CONCAT('persons/', @pid) purchased "
        "FOR v2 IN 1..1 OUTBOUND v1._id similar_to "
        "LIMIT 20 RETURN DISTINCT {id: v2.id, name: v2.name, category: v2.category}"
    ),
    "shortest_path_two_people": (
        "WITH persons "
        "FOR path IN OUTBOUND SHORTEST_PATH CONCAT('persons/', @pid) TO CONCAT('persons/', @prod_id) follows "
        "RETURN LENGTH(path.edges)"
    ),
    "aggregation_spend_by_category": (
        "WITH persons, products "
        "FOR v, e IN 1..1 OUTBOUND CONCAT('persons/', @pid) purchased "
        "COLLECT category = v.category AGGREGATE total = SUM(e.amount), n = COUNT(1) "
        "SORT total DESC RETURN {category, total, n}"
    ),
    "aggregation_top_products_global": (
        "FOR e IN purchased "
        "LET prod = DOCUMENT(e._to) "
        "COLLECT category = prod.category AGGREGATE purchases = COUNT(1), avg_amount = AVG(e.amount) "
        "SORT purchases DESC LIMIT 10 RETURN {category, purchases, avg_amount}"
    ),
    "write_create_person": (
        "INSERT {id: @id, name: @name, age: @age, country: 'IN'} INTO persons RETURN NEW.id"
    ),
    "write_create_follow_edge": (
        "INSERT {_from: CONCAT('persons/', @pid), _to: CONCAT('persons/', @prod_id)} INTO follows"
    ),
}


class ArangoConnector(GraphConnector):
    display_name = "ArangoDB Oasis"

    def __init__(self):
        self.url = os.environ.get("ARANGO_URL")
        self.user = os.environ.get("ARANGO_USER", "root")
        self.password = os.environ.get("ARANGO_PASSWORD")
        self.db_name = os.environ.get("ARANGO_DB", "benchmark")
        self.client = None
        self.db = None
        if not self.url or not self.password:
            raise RuntimeError("ArangoDB: missing ARANGO_URL/ARANGO_PASSWORD in environment.")

    def connect(self):
        self.client = ArangoClient(hosts=self.url)
        sys_db = self.client.db("_system", username=self.user, password=self.password)
        if not sys_db.has_database(self.db_name):
            sys_db.create_database(self.db_name)
        self.db = self.client.db(self.db_name, username=self.user, password=self.password)
        for coll in ["persons", "products"]:
            if not self.db.has_collection(coll):
                self.db.create_collection(coll)
        for coll in ["follows", "purchased", "similar_to"]:
            if not self.db.has_collection(coll):
                self.db.create_collection(coll, edge=True)
        # matches the UNIQUE constraint (index) the Bolt connector creates on
        # Person.id/Product.id -- without this, every FILTER p.id == @pid
        # below is a full collection scan on ArangoDB but an index seek on
        # every Bolt target, which isn't a fair comparison.
        self.db.collection("persons").add_persistent_index(fields=["id"], unique=True)
        self.db.collection("products").add_persistent_index(fields=["id"], unique=True)

    def close(self):
        pass  # python-arango is stateless HTTP, nothing to close

    def run(self, workload: dict, params: dict):
        aql = AQL_WORKLOADS[workload["name"]]
        cursor = self.db.aql.execute(aql, bind_vars=params)
        return list(cursor)

    def wipe(self):
        for coll in ["persons", "products", "follows", "purchased", "similar_to"]:
            self.db.collection(coll).truncate()

    def bulk_load(self, dataset_dir: str):
        import csv as csvmod
        t0 = perf_counter()

        def load_docs(path, coll_name, row_fn):
            with open(path) as f:
                reader = csvmod.DictReader(f)
                docs = [row_fn(row) for row in reader]
            self.db.collection(coll_name).import_bulk(docs, on_duplicate="ignore")

        load_docs(f"{dataset_dir}/persons.csv", "persons",
                   lambda r: {"_key": r["id:ID"], "id": int(r["id:ID"]), "name": r["name"],
                              "age": int(r["age:int"]), "country": r["country"]})
        load_docs(f"{dataset_dir}/products.csv", "products",
                   lambda r: {"_key": r["id:ID"], "id": int(r["id:ID"]), "name": r["name"],
                              "category": r["category"], "price": float(r["price:float"])})
        load_docs(f"{dataset_dir}/follows.csv", "follows",
                   lambda r: {"_from": f"persons/{r[':START_ID']}", "_to": f"persons/{r[':END_ID']}"})
        load_docs(f"{dataset_dir}/purchased.csv", "purchased",
                   lambda r: {"_from": f"persons/{r[':START_ID']}", "_to": f"products/{r[':END_ID']}",
                              "ts": r["ts"], "amount": float(r["amount:float"])})
        load_docs(f"{dataset_dir}/similar_to.csv", "similar_to",
                   lambda r: {"_from": f"products/{r[':START_ID']}", "_to": f"products/{r[':END_ID']}"})

        return perf_counter() - t0
