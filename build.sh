#!/bin/bash
set -e

echo "=== Installing Python dependencies ==="
pip install -r backend/requirements.txt

echo "=== Training ML model ==="
python train_model.py

echo "=== Installing frontend dependencies ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Build complete ==="
