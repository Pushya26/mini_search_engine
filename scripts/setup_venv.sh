#!/usr/bin/env bash
# Creates and bootstraps the Python virtual environment (Unix/macOS).
# Usage: ./scripts/setup_venv.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Creating virtual environment in .venv ..."
python3 -m venv .venv

echo "Activating .venv ..."
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Upgrading pip ..."
python -m pip install --upgrade pip

echo "Installing dependencies ..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo ""
echo "Done. Activate the venv with:"
echo "  source .venv/bin/activate"
