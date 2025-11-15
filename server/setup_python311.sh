#!/usr/bin/env bash
# setup_python311.sh
# Usage: bash setup_python311.sh
# Installs Python 3.11, creates a venv, upgrades pip tooling and installs openai.
# Assumes Debian/Ubuntu. Requires sudo for apt installs.

set -euo pipefail

VENV_DIR="${HOME}/venvs/prolific-py311"
PYTHON_BIN="python3.11"

echo
echo "==> 1) Update apt and install prerequisites"
sudo apt update
sudo apt install -y software-properties-common apt-transport-https ca-certificates

echo
echo "==> 2) Add deadsnakes PPA (for newer Python) and update"
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update

echo
echo "==> 3) Install Python 3.11 and build deps"
sudo apt install -y "${PYTHON_BIN}" "${PYTHON_BIN}-venv" "${PYTHON_BIN}-dev" build-essential libssl-dev libffi-dev

# Create venv base folder if not exists
mkdir -p "$(dirname "${VENV_DIR}")"

echo
echo "==> 4) Create virtual environment at ${VENV_DIR}"
# Use explicit python3.11 binary to create venv
"${PYTHON_BIN}" -m venv "${VENV_DIR}"

echo
echo "==> 5) Activate venv for this script and upgrade packaging tools"
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate"
python -m pip install --upgrade pip setuptools wheel build

echo
echo "==> 6) Install openai package into venv"
pip install openai

echo
echo "==> Done."
echo
echo "IMPORTANT:"
echo " - The venv was created at: ${VENV_DIR}"
echo " - To use the venv in your current interactive shell run:"
echo "     source ${VENV_DIR}/bin/activate"
echo " - If you want this script to drop you into a new shell with the venv active, run:"
echo "     bash -i -c 'source ${VENV_DIR}/bin/activate; exec bash'"
echo
echo "Check versions:"
python --version
pip --version
pip show openai || true
