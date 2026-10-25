#!/bin/sh
# E14: the 144 models (three seeds in parallel, one thread each), then the analysis.
#   sh experiments/e14_run.sh                E14, Phikon
#   sh experiments/e14_run.sh h_optimus_0    E14b, in data/reports/experiments/e14/h_optimus_0
# Resumable: models whose logits exist are skipped. Seed 0 stops if the control does not reproduce E6 / E17.
set -e
backbone="${1:-phikon}"
out="data/reports/experiments/e14"
[ "$backbone" = phikon ] || out="$out/$backbone"
mkdir -p "$out"
echo "$(date '+%F %T') E14 training ($backbone): start"
pids=""
for s in 0 1 2; do
  uv run python experiments/e14_new_centre.py train "$s" "$backbone" > "$out/train_s$s.log" 2>&1 &
  pids="$pids $!"
done
for p in $pids; do wait "$p"; done   # set -e: a failed seed (e.g. the control) stops before the analysis
echo "$(date '+%F %T') E14 training ($backbone): end"
uv run python experiments/e14_new_centre.py analyse "$backbone"
