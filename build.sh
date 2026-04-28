#!/bin/bash
set -e

echo "=== Installing Python dependencies ==="
pip install -r backend/requirements.txt

echo "=== Checking ML model ==="
if [ -f "Telugu_F&R_News/fake_news_model.pkl" ]; then
  echo "Model already exists, skipping training."
else
  echo "Training ML model..."
  python train_model.py
fi

echo "=== Installing frontend dependencies ==="
cd frontend
npm install
npm run build
cd ..

echo "=== Build complete ==="
