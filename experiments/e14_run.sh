#!/bin/sh
# E14: the 144 models (three seeds in parallel, one thread each), then the analysis.
# Resumable: models whose logits exist are skipped.
set -e
out="data/reports/experiments/e14"
mkdir -p "$out"
echo "$(date '+%F %T') E14 training: start"
for s in 0 1 2; do
  uv run python experiments/e14_new_centre.py train "$s" > "$out/train_s$s.log" 2>&1 &
done
wait
echo "$(date '+%F %T') E14 training: end"
uv run python experiments/e14_new_centre.py analyse
