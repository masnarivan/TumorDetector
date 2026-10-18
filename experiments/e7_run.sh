#!/bin/sh
# E7: the three variants one after the other (each runs its three seeds in parallel), then the comparison.
set -e
for name in balanced balanced+group_dro balanced+stat_mix; do
  recipe=$(echo "$name" | tr '+' ',')
  uv run td task=train_head "head.recipe=[$recipe]" mil.register=false \
    "mil.report_dir=data/reports/experiments/e7/$name"
done
uv run python experiments/e7_compare.py
