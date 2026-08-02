#!/usr/bin/env bash
# Submit the checked-out suite to the eval API, poll to a terminal status,
# write scores to the step summary. Inputs via EVAL_* env (see action.yml).
set -euo pipefail

sha=$(git rev-parse HEAD)
scenarios=$(ls evals/scenarios | jq -R . | jq -sc .)
count=$(ls evals/scenarios | wc -l)
total=$((EVAL_BUDGET_PER_SCENARIO * count * EVAL_REPS))

body=$(jq -nc --arg sha "$sha" --argjson sc "$scenarios" \
  --arg model "$EVAL_MODEL" --argjson reps "$EVAL_REPS" --argjson t "$total" \
  '{model: $model, scenarios: $sc, data_source: {sha: $sha},
    reps: $reps, budget_tokens_total: $t}')

run=$(curl -sf -X POST "$EVAL_BASE_URL/runs" \
  -H "Ocp-Apim-Subscription-Key: $EVAL_API_KEY" \
  -H "Content-Type: application/json" -d "$body")
id=$(jq -r .id <<<"$run")
echo "submitted \`$id\` for \`$sha\` ($count scenario(s), $EVAL_REPS rep(s))" \
  >> "$GITHUB_STEP_SUMMARY"

for i in $(seq 1 60); do
  s=$(curl -sf -H "Ocp-Apim-Subscription-Key: $EVAL_API_KEY" \
    "$EVAL_BASE_URL/runs/$id" | jq -r .status)
  echo "[$i] $s"
  case "$s" in
    completed)
      {
        echo '### Eval scores'
        curl -sf -H "Ocp-Apim-Subscription-Key: $EVAL_API_KEY" \
          "$EVAL_BASE_URL/runs/$id/output-items" \
          | jq -r '.data[].cell | "- `\(.id)`: **\(.outcome.rubric_yes)/\(.outcome.rubric_total)** (stop: \(.process.stop_reason); scope violations: \(.process.scope_violations | length))"'
      } >> "$GITHUB_STEP_SUMMARY"
      exit 0;;
    failed)
      curl -sf -H "Ocp-Apim-Subscription-Key: $EVAL_API_KEY" \
        "$EVAL_BASE_URL/runs/$id" | jq . >> "$GITHUB_STEP_SUMMARY"
      echo "::error::eval run failed — see summary"; exit 1;;
  esac
  sleep 30
done
echo "::error::run not terminal after 30 minutes — the request record is durable; the next submission drains it"
exit 1
