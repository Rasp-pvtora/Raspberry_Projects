#!/usr/bin/env bash
# train-model.sh — Train LSTM model from collected hand landmark data
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/data/training_data"
MODELS_DIR="$PROJECT_DIR/models"

echo "=== LSTM Model Training ==="

if [ ! -d "$DATA_DIR" ] || [ -z "$(ls -A "$DATA_DIR" 2>/dev/null)" ]; then
    echo "ERROR: No training data found in $DATA_DIR"
    echo "Collect data first by enabling DATA_COLLECTION_ENABLED=true"
    exit 1
fi

# Count samples
total=0
for label_dir in "$DATA_DIR"/*/; do
    count=$(find "$label_dir" -name "*.npy" | wc -l)
    label=$(basename "$label_dir")
    echo "  $label: $count samples"
    total=$((total + count))
done
echo "Total samples: $total"

if [ "$total" -lt 100 ]; then
    echo "WARNING: Very few samples. Recommend at least 100 per sign."
fi

# Run the Python training script
echo ""
echo "Starting training..."
python3 "$PROJECT_DIR/scripts/train_lstm.py" \
    --data-dir "$DATA_DIR" \
    --output "$MODELS_DIR/asl_lstm" \
    --epochs 50 \
    --batch-size 32

echo ""
echo "=== Training complete ==="
echo "Model saved to: $MODELS_DIR/asl_lstm.h5 and .tflite"
