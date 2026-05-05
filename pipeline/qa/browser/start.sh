#!/bin/bash
# Fire-and-forget launcher for the full v2/uk QA run.
# Usage:
#   ./start.sh              # all 36 episodes, headless
#   ./start.sh 1-12         # range
#   ./start.sh 1,5,12       # list
#
# Detaches via nohup + disown — safe to close the terminal.
# Tells you where to look for the live log and final summary.

set -e
cd "$(dirname "$0")"

ARG="${1:-all}"
TS=$(date -u +%Y-%m-%d_%H-%M-%S)
RUN_LOG="reports/launch_${TS}.log"
mkdir -p reports

echo "Launching v2/uk QA run for episodes: ${ARG}"
nohup node run_full.mjs "${ARG}" > "${RUN_LOG}" 2>&1 &
PID=$!
disown $PID 2>/dev/null || true

echo "PID: ${PID}"
echo "Live log:    tail -f pipeline/qa/browser/${RUN_LOG}"
echo "When done:   pipeline/qa/browser/reports/qa_run_<latest>/summary.md"
echo
echo "Estimated runtime: ~10-15 min for all 36 episodes."
echo "Safe to close this terminal. The run continues in the background."
