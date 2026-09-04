#!/usr/bin/env bash
set -euo pipefail

# Local helper script to build a single-file executable with PyInstaller
# Usage: ./scripts/pyinstaller_build.sh [--name transfile] [--onefile]

NAME=transfile
ONEFILE=--onefile
ENTRY=scripts/transfile_server.py

while [[ ${#} -gt 0 ]]; do
  case "$1" in
    --name) NAME="$2"; shift 2;;
    --no-onefile) ONEFILE=; shift 1;;
    --entry) ENTRY="$2"; shift 2;;
    --help) echo "Usage: $0 [--name <name>] [--no-onefile] [--entry <script>]"; exit 0;;
    *) shift 1;;
  esac
done

python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m pip install .

rm -rf build dist "${NAME}".spec
pyinstaller ${ONEFILE} --name "${NAME}" "${ENTRY}"

echo "Built: dist/${NAME} (or dist/${NAME}.exe on Windows)."