#!/usr/bin/env bash
# scripts/setup_all.sh -- one-time environment setup.
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example -- fill in your credentials before running benchmarks."
fi

python3 data/generate_dataset.py

echo ""
echo "Setup done. Next steps:"
echo "  1. Edit .env with your CognoDB / AuraDB / ArangoDB Oasis / FalkorDB credentials"
echo "  2. docker compose up -d memgraph neo4j-community   # self-hosted comparators"
echo "  3. ./scripts/run_all.sh"
