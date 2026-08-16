# Benchmark Summary

Targets: ArangoDB Oasis, CognoDB Cloud, FalkorDB Cloud, Memgraph (self-hosted, capped), Neo4j Community (self-hosted, capped)

## Load time & connection time

| Target | Connect (ms) | Bulk load (s) |
|---|---|---|
| ArangoDB Oasis | 3302.91 | 12.58 |
| CognoDB Cloud | 1591.04 | 27.03 |
| FalkorDB Cloud | 694.01 | 119.18 |
| Memgraph (self-hosted, capped) | 7.6 | 31.64 |
| Neo4j Community (self-hosted, capped) | 130.75 | 7.73 |

## aggregation_spend_by_category

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 277.602 | 351.04 | 383.432 | 3.43 |
| CognoDB Cloud | 23 | 77 | 287.781 | 656.927 | 1329.755 | 2.81 |
| FalkorDB Cloud | 100 | 0 | 31.265 | 33.261 | 36.11 | 31.6 |
| Memgraph (self-hosted, capped) | 100 | 0 | 2.63 | 4.871 | 39.575 | 226.81 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 1.405 | 2.758 | 25.548 | 389.38 |

## aggregation_top_products_global

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 1060.915 | 1442.248 | 1485.255 | 0.94 |
| CognoDB Cloud | 100 | 0 | 304.621 | 372.115 | 408.743 | 3.19 |
| FalkorDB Cloud | 100 | 0 | 41.962 | 44.817 | 47.415 | 23.63 |
| Memgraph (self-hosted, capped) | 100 | 0 | 4.216 | 35.469 | 43.021 | 151.87 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 6.04 | 70.603 | 83.995 | 53.31 |

## one_hop_who_they_follow

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 267.271 | 345.86 | 372.739 | 3.49 |
| CognoDB Cloud | 100 | 0 | 241.107 | 311.366 | 341.535 | 3.92 |
| FalkorDB Cloud | 100 | 0 | 31.207 | 32.872 | 34.712 | 31.81 |
| Memgraph (self-hosted, capped) | 100 | 0 | 3.069 | 6.134 | 45.202 | 202.56 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 1.17 | 2.778 | 64.973 | 271.87 |

## point_lookup_person

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 268.183 | 349.702 | 371.336 | 3.46 |
| CognoDB Cloud | 100 | 0 | 245.273 | 330.901 | 350.489 | 3.75 |
| FalkorDB Cloud | 100 | 0 | 31.293 | 32.873 | 34.379 | 31.64 |
| Memgraph (self-hosted, capped) | 100 | 0 | 0.976 | 1.462 | 2.072 | 694.91 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 1.295 | 2.767 | 46.054 | 417.03 |

## recommendation_bought_similar

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 268.305 | 339.341 | 351.956 | 3.5 |
| CognoDB Cloud | 100 | 0 | 240.984 | 307.122 | 316.371 | 3.95 |
| FalkorDB Cloud | 100 | 0 | 31.379 | 33.534 | 36.236 | 30.68 |
| Memgraph (self-hosted, capped) | 100 | 0 | 1099.717 | 1193.617 | 1230.565 | 0.93 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 1.602 | 8.588 | 68.315 | 215.48 |

## shortest_path_two_people

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 267.157 | 348.896 | 387.502 | 3.46 |
| CognoDB Cloud | 2 | 98 | 992.09 | 1667.22 | 1727.231 | 1.01 |
| FalkorDB Cloud | 100 | 0 | 31.545 | 35.029 | 43.884 | 30.84 |
| Memgraph (self-hosted, capped) | 100 | 0 | 1.623 | 4.111 | 37.279 | 315.47 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 1.529 | 7.498 | 66.762 | 207.29 |

## two_hop_friends_of_friends

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 272.313 | 346.705 | 368.067 | 3.47 |
| CognoDB Cloud | 100 | 0 | 241.816 | 310.787 | 332.778 | 3.89 |
| FalkorDB Cloud | 100 | 0 | 31.047 | 33.385 | 35.0 | 31.75 |
| Memgraph (self-hosted, capped) | 100 | 0 | 5513.804 | 5934.717 | 6034.698 | 0.18 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 2.069 | 46.945 | 76.549 | 144.58 |

## write_create_follow_edge

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 305.558 | 357.917 | 361.123 | 3.4 |
| CognoDB Cloud | 100 | 0 | 249.063 | 321.521 | 355.098 | 3.8 |
| FalkorDB Cloud | 100 | 0 | 31.811 | 35.213 | 38.092 | 30.96 |
| Memgraph (self-hosted, capped) | 100 | 0 | 1.712 | 2.153 | 14.829 | 444.39 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 1.511 | 9.038 | 48.15 | 256.62 |

## write_create_person

| Target | n | errors | p50 (ms) | p95 (ms) | p99 (ms) | throughput (qps) |
|---|---|---|---|---|---|---|
| ArangoDB Oasis | 100 | 0 | 304.759 | 346.029 | 360.149 | 3.4 |
| CognoDB Cloud | 100 | 0 | 253.845 | 360.749 | 692.929 | 1.79 |
| FalkorDB Cloud | 100 | 0 | 30.57 | 32.385 | 35.622 | 32.34 |
| Memgraph (self-hosted, capped) | 100 | 0 | 0.471 | 0.58 | 0.675 | 2070.45 |
| Neo4j Community (self-hosted, capped) | 100 | 0 | 1.226 | 2.432 | 53.778 | 381.89 |
