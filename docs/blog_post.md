# We benchmarked CognoDB against four graph databases. Here's what "free tier" actually buys you.

*A field guide for anyone choosing a managed graph database on a budget —
and a template for not trusting benchmarks, including this one.*

---

Every graph database vendor's homepage says roughly the same thing: fast
traversals, no JOINs, point your driver at a URL and go. That pitch is
almost never wrong, and almost never the whole story either. The part that
actually decides whether your side project or your MVP survives contact
with real traffic is what happens on the smallest, cheapest instance you
can get — because that's the one you're actually going to run.

So instead of reading another "top 10 graph databases" listicle, we built
a small graph, wrote nine queries that mirror what a real app does with a
graph (look someone up, walk their network two hops, recommend something,
find a path, add data), and ran the exact same queries against five
databases sitting on the smallest tier each one offers: **CognoDB Cloud**,
**Memgraph**, **Neo4j Community**, **ArangoDB Oasis**, and **FalkorDB
Cloud**. (Neo4j AuraDB Free was going to be a sixth, single-most-direct
comparator, but its signup flow asked for billing details before it would
finish provisioning an instance — which broke this benchmark's own
"free tier, no credit card" rule, so it's left out of the results rather
than run on different terms than everything else here. The code supports
it end-to-end if you have, or are willing to set up, an Aura instance that
doesn't hit that wall.) Full methodology, all the code, and the raw
numbers are in [the repo](../README.md) — this post is the readable
version of that.

## Why "same resources" is the whole ballgame

The easiest way to win a database benchmark is to accidentally (or not)
compare a free tier against a bigger box. A burstable 0.5 vCPU / 256 MB
instance and a dedicated 4 vCPU / 16 GB instance are not the same product,
even if they run the same software — and yet "Database X is 8x faster
than Database Y" headlines routinely come from exactly that kind of
mismatch. We didn't want to write that headline by accident, so the first
rule of this benchmark was: **every database runs on its smallest tier,
every tier's specs are written down, and the dataset is sized to fit the
tightest one of the six.** Where a vendor doesn't let you dial in an exact
vCPU/RAM number for their free tier (looking at you, most managed clouds),
we say so instead of guessing.

## What we actually measured

Five databases, one dataset (7,000 people, 2,800 products, ~56,000
relationships — big enough to have real hub nodes and skewed degree
distributions, small enough to fit inside FalkorDB's real 100 MB free-tier
cap with room to spare, which turned out to be the tightest constraint in
the whole comparison, not CognoDB's), nine queries run identically
everywhere:

- a point lookup,
- a 1-hop and a 2-hop traversal ("friends of friends" — the query graph
  databases exist to make fast),
- a two-edge-type recommendation pattern,
- a bounded shortest path,
- two aggregations (one scoped to a user, one global),
- and two writes (create a node, create an edge).

For each one we logged p50/p95/p99 latency and throughput, plus load time
and connection setup time as their own separate numbers, because "how
long until my data is queryable" and "how fast is each query once it's
loaded" are different questions with different answers.

## What we found

The self-hosted engines won on raw query speed, and that's not a surprise
once you remember what "free tier" is buying on each side. Memgraph and
Neo4j Community — both running under a 0.5 vCPU / 256 MB Docker cap, but
on the same machine as the client — answered point lookups and 1-hop reads
in 1-4ms. (That 256 MB cap was set to match the *assignment brief's* stated
CognoDB spec; we later discovered CognoDB's real dashboard reports 512 MB,
so if anything the self-hosted numbers here are a *more* resource-starved
baseline than CognoDB itself, not an equal one — disclosed, not quietly
fixed, since fixing it means re-running everything.) CognoDB, ArangoDB
Oasis, and FalkorDB Cloud all sat in a narrow band regardless of query
shape: roughly 245-310ms for CognoDB and Oasis, ~35ms for FalkorDB, on
everything from a point lookup to a two-hop traversal. That flatness is the
tell — for those three, network round-trip to the provider's region is
doing most of the work in the number, not the query planner. If you're
picking a database to make *queries* fast, self-hosting next to your app
wins by construction; if you're picking a *managed* free tier, FalkorDB's
~35ms floor was the best of the three managed options we could complete
reliably.

Two results don't fit the "just network latency" story and are worth
flagging on their own. First, CognoDB's free instance didn't hold up under
sustained load on two of the nine workloads: `shortest_path_two_people`
completed only 1 of 100 iterations and `aggregation_spend_by_category`
completed 24 of 100, both failing with the connection dying mid-query
(`SSLEOFError` / `ConnectionResetError`). The identical Cypher, on the
identical driver, ran error-free on every other target including
self-hosted Neo4j Community — so this reads as the free instance itself
under load, not a query bug. Second, Memgraph — otherwise the fastest
thing in the whole comparison — fell off a cliff on exactly the two
multi-hop queries: `two_hop_friends_of_friends` at p50 12.1s and
`recommendation_bought_similar` at p50 2.3s, against sub-4ms for its own
point lookups and writes. The dataset's edges are generated with a
Pareto/Zipf skew to produce hub nodes on purpose, and these are the two
workloads that fan out through them — a plausible explanation, though we
didn't isolate it further within this benchmark's time budget.

Load time told a different story than query latency, and this is the
part that's easy to miss if you only look at p50s. FalkorDB had the
snappiest per-query latency of the managed clouds but the slowest bulk
load by far (231s, vs. CognoDB's 40s and Neo4j Community's 21s) — "fast
once loaded" and "fast to get data in" are genuinely different axes, and
a workload that reloads data often should weight the second one more than
these headline query numbers suggest.

A few things worth calling out regardless of which numbers land where:

**Network latency isn't zero, and we didn't pretend it was.** Every
managed provider here runs in a region you pick when you sign up, and the
client-observed latency in this benchmark includes real round-trip time to
that region. If you're picking a database for an app with users in a
specific place, the closest region beats the fastest engine more often
than people expect.

**"Free tier" doesn't mean "same free tier."** Some of these platforms
publish exact vCPU/RAM numbers for their smallest tier; some don't and
just say "shared" or "burstable." We wrote down what each one actually
tells you, rather than assuming parity where none is documented.

**No single number wins.** We didn't compute one composite score across
nine different query shapes, on purpose. A database that's excellent at
2-hop traversal and mediocre at global aggregation isn't "worse" — it's a
better fit for a social app than an analytics dashboard. If you take one
thing from this post, take that: the right benchmark for *your* database
choice is the one built from *your* queries, not ours. This repo is
structured so you can swap in your own dataset and workloads in an
afternoon — see `benchmarks/workloads.py`.

## Why we ran this on CognoDB in particular

CognoDB's whole pitch is compatibility: point the official Neo4j driver
at a `bolt+s://` URL with a username and password, and nothing else about
your code changes. That's a testable claim, not a marketing one — so we
tested it, using the same connector class, the same driver, and the same
query strings for CognoDB and self-hosted Neo4j Community
(`benchmarks/connectors/bolt_connector.py`). The same class also supports
Neo4j AuraDB with no code changes, for the same reason — it just isn't in
this run's results (see above). If a query behaves differently on CognoDB
than on Neo4j, it's a difference in the database, not in how we talked to
it.

## Try it yourself

This isn't a report you have to trust — it's a repo you can run. Clone
it, drop in your own free-tier credentials, and get your own numbers on
your own network in about twenty minutes:

```bash
git clone <this-repo-url>
cd graphdb-benchmark
./scripts/setup_all.sh
cp .env.example .env   # fill in your credentials
docker compose up -d memgraph neo4j-community
./scripts/run_all.sh
```

Whatever you find, we'd rather you find it yourself than take our word
for it. That's the point.
