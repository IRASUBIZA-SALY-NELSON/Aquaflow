#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || source .tmp-venv/bin/activate
python -m ai.generate_dataset
python -m ai.train_lstm
