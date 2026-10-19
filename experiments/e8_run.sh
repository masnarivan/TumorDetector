#!/bin/sh
# E8: the two adversarial variants one after the other (each runs its three seeds in parallel), then the comparison.
# Resumable: a variant whose metrics.json exists is skipped (an interrupted variant is rerun from the start).
set -e
for name in balanced+adversarial balanced+adversarial_negatives; do
  out="data/reports/experiments/e8/$name"
  if [ -f "$out/metrics.json" ]; then
    echo "$(date '+%F %T') $name: done, skipped"
    continue
  fi
  echo "$(date '+%F %T') $name: start"
  recipe=$(echo "$name" | tr '+' ',')
  uv run td task=train_head "head.recipe=[$recipe]" mil.register=false "mil.report_dir=$out"
  echo "$(date '+%F %T') $name: end"
done
uv run python experiments/e8_compare.py
