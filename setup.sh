#!/bin/bash
set -euo pipefail

echo "=== MasterBlaster-Control Setup ==="

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

if [ ! -d "backend/MasterBlaster" ]; then
    echo "Submodule not initialized. Run: git submodule update --init --recursive"
    exit 1
fi

mkdir -p reports logs assets

echo "✓ Setup complete. Run with: python main.py"
echo "On first launch you will see the ethics dialog."
