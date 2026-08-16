#!/usr/bin/env python3
"""
generate_report.py

Reads every results/raw/*.json produced by run_benchmark.py and produces:
  - results/summary.md           a plain markdown table (p50/p95/p99 + load time)
  - results/charts/*.png         one bar chart per workload, all targets side by side

Run this after run_benchmark.py has produced results for all targets you
want compared. It intentionally does NOT compute a single "winner" score --
different workloads matter differently depending on your access pattern,
and collapsing five databases into one number is exactly the kind of
methodology shortcut this assignment asks us not to take.
"""
import glob
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
RAW_DIR = os.path.join(RESULTS_DIR, "raw")
CHARTS_DIR = os.path.join(RESULTS_DIR, "charts")


def load_all_results():
    results = {}
    for path in sorted(glob.glob(os.path.join(RAW_DIR, "*.json"))):
        with open(path) as f:
            data = json.load(f)
        results[data["target"]] = data
    return results


def write_summary_md(results):
    lines = ["# Benchmark Summary", ""]
    lines.append(f"Targets: {', '.join(r['display_name'] for r in results.values())}")
    lines.append("")
    lines.append("## Load time & connection time")
    lines.append("")
    lines.append("| Target | Connect (ms) | Bulk load (s) |")
    lines.append("|---|---|---|")
    for key, r in results.items():
        lines.append(f"| {r['display_name']} | {r['connect_time_ms']} | {r['load_time_s']} |")
    lines.append("")

    all_workload_names = sorted({wl for r in results.values() for wl in r["workloads"]})
    for wl_name in all_workload_names:
        lines.append(f"## {wl_name}")
        lines.append("")
        lines.append("| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |")
        lines.append("|---|---|---|---|---|---|---|")
        for key, r in results.items():
            wl = r["workloads"].get(wl_name)
            if not wl:
                lines.append(f"| {r['display_name']} | - | - | - | - | - | - |")
                continue
            lines.append(
                f"| {r['display_name']} | {wl.get('n')} | {wl.get('errors')} | "
                f"{wl.get('p50_ms')} | {wl.get('p95_ms')} | {wl.get('p99_ms')} | {wl.get('throughput_qps')} |"
            )
        lines.append("")

    out_path = os.path.join(RESULTS_DIR, "summary.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {out_path}")


def make_charts(results):
    os.makedirs(CHARTS_DIR, exist_ok=True)
    all_workload_names = sorted({wl for r in results.values() for wl in r["workloads"]})

    for wl_name in all_workload_names:
        names, p50s, p95s = [], [], []
        for key, r in results.items():
            wl = r["workloads"].get(wl_name)
            if not wl or wl.get("p50_ms") is None:
                continue
            names.append(r["display_name"])
            p50s.append(wl["p50_ms"])
            p95s.append(wl["p95_ms"])

        if not names:
            continue

        x = range(len(names))
        fig, ax = plt.subplots(figsize=(8, 4.5))
        width = 0.35
        ax.bar([i - width / 2 for i in x], p50s, width, label="p50")
        ax.bar([i + width / 2 for i in x], p95s, width, label="p95")
        ax.set_ylabel("Latency (ms)")
        ax.set_title(wl_name)
        ax.set_xticks(list(x))
        ax.set_xticklabels(names, rotation=25, ha="right")
        ax.legend()
        fig.tight_layout()
        out_path = os.path.join(CHARTS_DIR, f"{wl_name}.png")
        fig.savefig(out_path, dpi=120)
        plt.close(fig)
        print(f"wrote {out_path}")


def main():
    results = load_all_results()
    if not results:
        print(f"No results found in {RAW_DIR} -- run run_benchmark.py first.")
        return
    write_summary_md(results)
    make_charts(results)


if __name__ == "__main__":
    main()
