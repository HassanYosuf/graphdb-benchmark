#!/usr/bin/env bash
# scripts/run_all.sh -- run the full benchmark suite against every
# configured target and regenerate results/summary.md + charts.
set -euo pipefail

source .venv/bin/activate 2>/dev/null || true
set -a; source .env 2>/dev/null || true; set +a

python3 -m benchmarks.run_benchmark --targets all --iterations "${ITERATIONS:-100}" --warmup "${WARMUP:-10}"
python3 -m benchmarks.generate_report

echo ""
echo "Done. See results/summary.md and results/charts/*.png"
