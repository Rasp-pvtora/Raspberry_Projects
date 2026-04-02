#!/usr/bin/env bash
# download-models.sh — Download pre-trained models and TTS voices
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$PROJECT_DIR/models"

mkdir -p "$MODELS_DIR/piper"
mkdir -p "$MODELS_DIR/sign_dictionary"

echo "=== Model Download ==="

# Placeholder: download LSTM model files
# Replace these URLs with actual model hosting when models are trained
echo "NOTE: Pre-trained models are not yet available for download."
echo "Train your own model using: bash scripts/train-model.sh"
echo ""
echo "Expected model files:"
echo "  $MODELS_DIR/asl_lstm.tflite"
echo "  $MODELS_DIR/asl_lstm_labels.txt"
echo ""

# Create default label file for ASL alphabet
LABELS_FILE="$MODELS_DIR/asl_lstm_labels.txt"
if [ ! -f "$LABELS_FILE" ]; then
    echo "Creating default ASL alphabet labels..."
    for letter in A B C D E F G H I J K L M N O P Q R S T U V W X Y Z; do
        echo "$letter"
    done > "$LABELS_FILE"
    echo "Created: $LABELS_FILE"
fi

# Create sign dictionary index
DICT_INDEX="$MODELS_DIR/sign_dictionary/index.json"
if [ ! -f "$DICT_INDEX" ]; then
    echo "Creating default sign dictionary index..."
    echo '{' > "$DICT_INDEX"
    for letter in A B C D E F G H I J K L M N O P Q R S T U V W X Y Z; do
        lower=$(echo "$letter" | tr '[:upper:]' '[:lower:]')
        comma=","
        [ "$letter" = "Z" ] && comma=""
        echo "  \"$letter\": \"${lower}.png\"${comma}" >> "$DICT_INDEX"
    done
    echo '}' >> "$DICT_INDEX"
    echo "Created: $DICT_INDEX"
fi

# Download Piper TTS voice (optional)
if command -v piper &>/dev/null; then
    echo "Piper TTS is installed. Download voices from:"
    echo "  https://github.com/rhasspy/piper/blob/master/VOICES.md"
else
    echo "Piper TTS not installed. Install with: pip install piper-tts"
fi

echo ""
echo "=== Download complete ==="
