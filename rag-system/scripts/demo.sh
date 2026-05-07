#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <API_BASE_URL> <PDF_PATH> [QUESTION]"
  echo "Example: $0 http://localhost:8000 ./sample.pdf 'What are the key obligations?'"
  exit 1
fi

API_BASE_URL="$1"
PDF_PATH="$2"
QUESTION="${3:-Summarize the core policy points from the document.}"

curl -s -X POST "${API_BASE_URL}/documents/upload" \
  -F "files=@${PDF_PATH}" | jq

echo

curl -s -X POST "${API_BASE_URL}/qa/ask" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"${QUESTION}\", \"top_k\": 6}" | jq
