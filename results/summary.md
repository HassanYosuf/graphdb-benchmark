# Benchmark Summary

Targets: ArangoDB Oasis, CognoDB Cloud, FalkorDB Cloud, Memgraph (self-hosted, capped), Neo4j Community (self-hosted, capped)

## Load time & connection time

| Target | Connect (ms) | Bulk load (s) |
|---|---|---|
| ArangoDB Oasis | 3180.52 | 20.07 |
| CognoDB Cloud | 1339.95 | 39.72 |
| FalkorDB Cloud | 660.4 | 230.87 |
| Memgraph (self-hosted, capped) | 9.83 | 66.7 |
| Neo4j Community (self-hosted, capped) | 296.33 | 20.64 |

## aggregation_spend_by_category

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 267.599 | 352.167 | 356.382 | 3.48 |
| CognoDB Cloud | 24 | 76 | 250.978 | 328.843 | 1298.939 | 3.07 |
| FalkorDB Cloud | 100 | 0 | 35.816 | 37.287 | 38.116 | 27.77 |
| Memgraph (self-hosted, capped) | 100 | 0 | 3.243 | 5.263 | 36.051 | 205.1 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 1.689 | 6.706 | 65.407 | 244.48 |

## aggregation_top_products_global

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 1485.044 | 2149.922 | 3239.154 | 0.65 |
| CognoDB Cloud | 100 | 0 | 363.667 | 454.329 | 689.114 | 2.61 |
| FalkorDB Cloud | 100 | 0 | 49.849 | 52.349 | 56.717 | 19.86 |
| Memgraph (self-hosted, capped) | 100 | 0 | 5.212 | 31.682 | 43.343 | 129.72 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 18.653 | 90.677 | 251.5 | 27.13 |

## one_hop_who_they_follow

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 261.381 | 352.151 | 357.806 | 3.53 |
| CognoDB Cloud | 100 | 0 | 246.906 | 326.82 | 734.376 | 3.62 |
| FalkorDB Cloud | 100 | 0 | 34.497 | 36.693 | 42.589 | 28.63 |
| Memgraph (self-hosted, capped) | 100 | 0 | 3.997 | 35.23 | 41.777 | 163.46 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 1.784 | 67.468 | 74.356 | 149.0 |

## point_lookup_person

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 262.131 | 354.658 | 435.48 | 3.46 |
| CognoDB Cloud | 100 | 0 | 247.342 | 309.663 | 344.591 | 3.73 |
| FalkorDB Cloud | 100 | 0 | 34.476 | 40.118 | 41.774 | 28.34 |
| Memgraph (self-hosted, capped) | 100 | 0 | 1.615 | 2.109 | 2.163 | 606.47 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 1.943 | 57.039 | 63.645 | 171.79 |

## recommendation_bought_similar

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 261.965 | 346.209 | 356.106 | 3.48 |
| CognoDB Cloud | 100 | 0 | 248.723 | 326.989 | 360.354 | 3.62 |
| FalkorDB Cloud | 100 | 0 | 35.689 | 37.104 | 38.94 | 27.87 |
| Memgraph (self-hosted, capped) | 100 | 0 | 2325.457 | 2483.443 | 4612.36 | 0.42 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 2.25 | 61.903 | 70.884 | 140.14 |

## shortest_path_two_people

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 262.21 | 344.291 | 353.097 | 3.53 |
| CognoDB Cloud | 1 | 99 | 1499.606 | 1499.606 | 1499.606 | 0.67 |
| FalkorDB Cloud | 100 | 0 | 36.429 | 38.761 | 81.583 | 25.05 |
| Memgraph (self-hosted, capped) | 100 | 0 | 1.601 | 4.171 | 25.556 | 326.91 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 1.661 | 10.633 | 66.874 | 220.72 |

## two_hop_friends_of_friends

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 260.934 | 335.634 | 347.576 | 3.67 |
| CognoDB Cloud | 100 | 0 | 286.505 | 606.445 | 658.947 | 2.78 |
| FalkorDB Cloud | 100 | 0 | 34.711 | 36.709 | 39.694 | 28.48 |
| Memgraph (self-hosted, capped) | 100 | 0 | 12065.222 | 12306.734 | 12410.524 | 0.09 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 1.924 | 38.054 | 70.191 | 165.6 |

## write_create_follow_edge

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 306.509 | 359.63 | 409.204 | 3.35 |
| CognoDB Cloud | 100 | 0 | 270.152 | 361.585 | 362.926 | 3.49 |
| FalkorDB Cloud | 100 | 0 | 36.252 | 37.249 | 38.634 | 27.51 |
| Memgraph (self-hosted, capped) | 100 | 0 | 2.282 | 2.576 | 15.586 | 390.89 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 2.049 | 6.765 | 20.268 | 308.53 |

## write_create_person

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 257.427 | 357.615 | 358.946 | 3.55 |
| CognoDB Cloud | 100 | 0 | 253.289 | 359.924 | 362.353 | 3.62 |
| FalkorDB Cloud | 100 | 0 | 33.38 | 35.818 | 37.155 | 29.57 |
| Memgraph (self-hosted, capped) | 100 | 0 | 0.575 | 1.069 | 3.036 | 1469.69 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 2.287 | 54.306 | 66.773 | 156.71 |
