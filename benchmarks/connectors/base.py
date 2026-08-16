"""
base.py -- common interface every connector implements.

Keeping this interface tiny and uniform is what makes run_benchmark.py able
to drive every database (Bolt-based or not) through the same loop, and what
makes "same workload, same measurement code" true across the whole benchmark
instead of per-vendor special-casing creeping into the timing logic.
"""
from abc import ABC, abstractmethod


class GraphConnector(ABC):
    display_name: str = "unnamed"

    @abstractmethod
    def connect(self):
        """Open the connection/session. Raise on failure -- callers should
        not silently skip a database that failed to connect."""

    @abstractmethod
    def close(self):
        ...

    @abstractmethod
    def run(self, workload: dict, params: dict):
        """Execute one workload (the full dict from workloads.WORKLOADS,
        so a connector can either use workload['cypher'] directly or look
        workload['name'] up in its own translation table) with bound
        params, and fully consume the result -- drivers are often lazy,
        and the benchmark must force materialization so we're timing real
        work, not a generator handle."""

    @abstractmethod
    def bulk_load(self, dataset_dir: str):
        """Load the CSVs in dataset_dir using whatever bulk-import path is
        idiomatic and fastest for this database. Load time itself is
        reported as a separate metric (see results schema in README)."""

    @abstractmethod
    def wipe(self):
        """Delete all data so bulk_load starts from empty -- required for a
        fair, repeatable load-time measurement."""
