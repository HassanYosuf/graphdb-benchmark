#!/usr/bin/env python3
"""
generate_dataset.py

Generates a small, reproducible synthetic graph sized to fit the smallest
tier under test (CognoDB free c0: burstable 0.5 vCPU / 256 MB RAM / 1 GB disk).

Schema (a minimal social + e-commerce graph -- connected data, skewed degree
distribution, mix of node/edge types, mirrors the shape of common real-world
graph workloads without pretending to be a full LDBC SNB run):

  (:Person {id, name, age, country})
  (:Product {id, name, category, price})

  (:Person)-[:FOLLOWS]->(:Person)          # power-law-ish social graph
  (:Person)-[:PURCHASED {ts, amount}]->(:Product)
  (:Product)-[:SIMILAR_TO]->(:Product)

Sizing target: ~5,000 Person nodes, ~2,000 Product nodes, ~40,000 edges total.
On disk this is well under 50 MB as CSV / well under 1 GB as a loaded graph
with indexes, leaving headroom on the free tier. Change N_PERSONS / N_PRODUCTS
below to rescale -- but re-check against the smallest tier's disk limit
before you do (see README "Fairness & sizing").

Output: data/dataset/{persons.csv, products.csv, follows.csv, purchased.csv,
similar_to.csv} -- plain CSVs so every database's native bulk-import tool
(neo4j-admin, LOAD CSV, arangoimport, redis-cli, etc.) can consume the same
source data without a bespoke per-database generator.
"""
import csv
import random
import os

random.seed(1337)  # fixed seed -> byte-identical dataset across runs/reviewers

N_PERSONS = 5_000
N_PRODUCTS = 2_000
N_FOLLOWS = 20_000
N_PURCHASES = 15_000
N_SIMILAR = 5_000

COUNTRIES = ["IN", "US", "GB", "DE", "SG", "BR", "NG", "AU", "CA", "FR"]
CATEGORIES = ["electronics", "books", "apparel", "home", "sports", "toys", "grocery", "beauty"]

OUT_DIR = os.path.join(os.path.dirname(__file__), "dataset")


def zipf_id(n, alpha=1.4):
    """Skewed pick favoring low ids, to create realistic hub nodes (some
    Persons/Products with far more edges than others -- this is what makes
    2+ hop traversal queries meaningfully different from a uniform random
    graph)."""
    while True:
        x = int(random.paretovariate(alpha - 1))
        if 0 <= x < n:
            return x


def gen_persons(path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id:ID", "name", "age:int", "country"])
        for i in range(N_PERSONS):
            w.writerow([i, f"person_{i}", random.randint(18, 75), random.choice(COUNTRIES)])


def gen_products(path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id:ID", "name", "category", "price:float"])
        for i in range(N_PRODUCTS):
            w.writerow([i, f"product_{i}", random.choice(CATEGORIES), round(random.uniform(5, 500), 2)])


def gen_edges(path, header, n, left_n, right_n, extra_cols=None):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for _ in range(n):
            a = zipf_id(left_n)
            b = zipf_id(right_n)
            row = [a, b]
            if extra_cols:
                row += extra_cols()
            w.writerow(row)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    gen_persons(os.path.join(OUT_DIR, "persons.csv"))
    gen_products(os.path.join(OUT_DIR, "products.csv"))

    gen_edges(
        os.path.join(OUT_DIR, "follows.csv"),
        [":START_ID", ":END_ID"],
        N_FOLLOWS, N_PERSONS, N_PERSONS,
    )
    gen_edges(
        os.path.join(OUT_DIR, "purchased.csv"),
        [":START_ID", ":END_ID", "ts", "amount:float"],
        N_PURCHASES, N_PERSONS, N_PRODUCTS,
        extra_cols=lambda: [
            f"2026-{random.randint(1,8):02d}-{random.randint(1,28):02d}",
            round(random.uniform(5, 500), 2),
        ],
    )
    gen_edges(
        os.path.join(OUT_DIR, "similar_to.csv"),
        [":START_ID", ":END_ID"],
        N_SIMILAR, N_PRODUCTS, N_PRODUCTS,
    )

    total_edges = N_FOLLOWS + N_PURCHASES + N_SIMILAR
    print(f"Generated {N_PERSONS} Person, {N_PRODUCTS} Product nodes, {total_edges} edges")
    print(f"Output: {OUT_DIR}")


if __name__ == "__main__":
    main()
