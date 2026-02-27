#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

if [[ -x "$REPO_ROOT/venv/bin/python3" ]]; then
  PYTHON_BIN="${PYTHON:-$REPO_ROOT/venv/bin/python3}"
else
  PYTHON_BIN="${PYTHON:-python3}"
fi

RUN_DATE="${RUN_DATE:-$(date +%F)}"
INPUT_CSV="${INPUT_CSV:-workspace/projects/mortgage-signals/test_input.csv}"
OUTPUT_DIR="${OUTPUT_DIR:-workspace/projects/mortgage-signals/outputs}"
LIMIT="${LIMIT:-20}"
TARGET_COMPLETE="${TARGET_COMPLETE:-5}"

if [[ ! -f "$INPUT_CSV" ]]; then
  echo "Input CSV not found: $INPUT_CSV"
  echo "Set INPUT_CSV=/path/to/input.csv and rerun."
  exit 1
fi

echo "Running MLO workflow test"
echo "Python: $PYTHON_BIN"
echo "Input:  $INPUT_CSV"
echo "Date:   $RUN_DATE"

"$PYTHON_BIN" -m workspace.agent.main \
  --workflow mlo \
  --input-csv "$INPUT_CSV" \
  --limit "$LIMIT" \
  --target-complete "$TARGET_COMPLETE" \
  --date "$RUN_DATE" \
  --output-dir "$OUTPUT_DIR"

CSV_FILE="$OUTPUT_DIR/mlo_leads_$RUN_DATE.csv"
SUMMARY_FILE="$OUTPUT_DIR/daily_summary_$RUN_DATE.md"

echo ""
echo "Done."
echo "CSV:     $CSV_FILE"
echo "Summary: $SUMMARY_FILE"
ls -lh "$CSV_FILE" "$SUMMARY_FILE"

