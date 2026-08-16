#!/usr/bin/env python3
"""
run_benchmark.py

Runs the shared workload suite (workloads.py) against every configured
target and writes one JSON file per target to results/raw/.

Usage:
    python -m benchmarks.run_benchmark --targets all
    python -m benchmarks.run_benchmark --targets cognodb,neo4j_aura
    python -m benchmarks.run_benchmark --targets cognodb --iterations 200 --warmup 20

Methodology notes (see README for the full writeup):
  - Every target gets the same iteration count, warmup count, and random
    seed sequence for parameter generation, so query selectivity is
    identical run to run and target to target.
  - Warmup iterations execute and discard results before timing starts, to
    avoid unfairly penalizing databases with cold-cache-on-first-query
    behavior (e.g. free-tier instances that pause/hibernate).
  - We measure end-to-end wall-clock latency from the client: connection
    setup time is excluded (measured once, separately, and reported), but
    network RTT to each provider's region is NOT excluded and NOT
    equalized across providers -- this is disclosed as a limitation in
    README, not hidden. A benchmark that pretends network latency doesn't
    exist would not be honest.
  - Load time (bulk import of the fixed dataset) is measured once per
    target as its own metric, separate from per-query latency.
"""
import argparse
import json
import os
import random
import statistics
import sys
from datetime import datetime, timezone
from time import perf_counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from benchmarks.workloads import get_workloads
from benchmarks.connectors.registry import build_registry

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", "raw")
DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "dataset")

SEED = 20260814  # fixed -> identical parameter sequence across every target


def percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * (p / 100)
    f, c = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def run_target(key, connector, iterations, warmup, do_load, skip_writes):
    print(f"\n=== {connector.display_name} ({key}) ===")
    t0 = perf_counter()
    connector.connect()
    connect_time = perf_counter() - t0
    print(f"  connected in {connect_time*1000:.1f} ms")

    load_time = None
    if do_load:
        print("  wiping existing data...")
        connector.wipe()
        print("  bulk loading dataset...")
        load_time = connector.bulk_load(DATASET_DIR)
        print(f"  loaded in {load_time:.2f} s")

    workloads = get_workloads()
    per_workload_results = {}

    for wl in workloads:
        if skip_writes and wl["category"] == "write":
            continue
        # Warmup uses a different (but still fixed, still identical across
        # every target) seed than the timed run. Reusing SEED for both would
        # make the timed run's first `warmup` iterations replay the exact
        # same params as warmup -- harmless for reads, but for
        # write_create_person it means the timed run immediately re-creates
        # the same ids warmup just created, producing unique-constraint
        # errors (or silent duplicates on targets that don't enforce
        # uniqueness) that have nothing to do with the database being
        # measured.
        rng = random.Random(SEED - 1)
        latencies_ms = []

        for i in range(warmup):
            params = wl["params_fn"](rng)
            try:
                connector.run(wl, params)
            except Exception as e:
                print(f"  [warmup error] {wl['name']}: {e}")

        rng = random.Random(SEED)  # same param sequence for every target's timed run
        errors = 0
        for i in range(iterations):
            params = wl["params_fn"](rng)
            start = perf_counter()
            try:
                connector.run(wl, params)
                latencies_ms.append((perf_counter() - start) * 1000)
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  [error] {wl['name']}: {e}")

        latencies_ms.sort()
        if latencies_ms:
            summary = {
                "n": len(latencies_ms),
                "errors": errors,
                "mean_ms": round(statistics.mean(latencies_ms), 3),
                "p50_ms": round(percentile(latencies_ms, 50), 3),
                "p95_ms": round(percentile(latencies_ms, 95), 3),
                "p99_ms": round(percentile(latencies_ms, 99), 3),
                "min_ms": round(min(latencies_ms), 3),
                "max_ms": round(max(latencies_ms), 3),
                "throughput_qps": round(len(latencies_ms) / (sum(latencies_ms) / 1000), 2) if sum(latencies_ms) else None,
            }
        else:
            summary = {"n": 0, "errors": errors, "note": "all iterations failed"}
        per_workload_results[wl["name"]] = summary
        print(f"  {wl['name']:35s} p50={summary.get('p50_ms')}ms  p95={summary.get('p95_ms')}ms  errors={errors}")

    connector.close()

    return {
        "target": key,
        "display_name": connector.display_name,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "connect_time_ms": round(connect_time * 1000, 2),
        "load_time_s": round(load_time, 2) if load_time is not None else None,
        "iterations": iterations,
        "warmup": warmup,
        "workloads": per_workload_results,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="all", help="comma-separated target keys, or 'all'")
    ap.add_argument("--iterations", type=int, default=100)
    ap.add_argument("--warmup", type=int, default=10)
    ap.add_argument("--no-load", action="store_true", help="skip wipe+bulk_load, benchmark existing data")
    ap.add_argument("--skip-writes", action="store_true", help="skip write_* workloads (repeatable read-only runs)")
    args = ap.parse_args()

    os.makedirs(RESULTS_DIR, exist_ok=True)
    registry = build_registry()
    skip_reasons = registry.pop("_skip_reasons", {})

    requested = list(registry.keys()) if args.targets == "all" else args.targets.split(",")

    for key in requested:
        connector = registry.get(key)
        if connector is None:
            reason = skip_reasons.get(key, "not configured")
            print(f"\n=== SKIPPING {key}: {reason} ===")
            continue
        try:
            result = run_target(key, connector, args.iterations, args.warmup,
                                 do_load=not args.no_load, skip_writes=args.skip_writes)
            out_path = os.path.join(RESULTS_DIR, f"{key}.json")
            with open(out_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"  -> wrote {out_path}")
        except Exception as e:
            print(f"\n=== {key} FAILED: {e} ===")


if __name__ == "__main__":
    main()
