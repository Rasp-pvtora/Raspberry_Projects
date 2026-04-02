"""Train LSTM model from collected hand landmark data."""

import argparse
import os
import glob

import numpy as np


def load_data(data_dir: str, sequence_length: int = 30):
    """Load .npy landmark files organized by label subdirectories."""
    X, y = [], []
    labels = sorted(os.listdir(data_dir))
    labels = [l for l in labels if os.path.isdir(os.path.join(data_dir, l))]

    label_map = {label: idx for idx, label in enumerate(labels)}

    for label in labels:
        label_dir = os.path.join(data_dir, label)
        files = sorted(glob.glob(os.path.join(label_dir, "*.npy")))

        # Group files into sequences of sequence_length
        for i in range(0, len(files) - sequence_length + 1, sequence_length // 2):
            chunk = files[i:i + sequence_length]
            if len(chunk) < sequence_length:
                continue
            sequence = [np.load(f) for f in chunk]
            X.append(np.array(sequence))
            y.append(label_map[label])

    return np.array(X), np.array(y), labels


def build_model(input_shape, num_classes):
    """Build a 2-layer LSTM model."""
    import tensorflow as tf

    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(64, return_sequences=True, input_shape=input_shape),
        tf.keras.layers.LSTM(64),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(num_classes, activation="softmax"),
    ])

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def export_tflite(model, output_path: str):
    """Convert Keras model to TFLite format."""
    import tensorflow as tf

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    tflite_model = converter.convert()

    tflite_path = output_path + ".tflite"
    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"TFLite model saved: {tflite_path}")


def main():
    parser = argparse.ArgumentParser(description="Train LSTM sign classifier")
    parser.add_argument("--data-dir", required=True, help="Training data directory")
    parser.add_argument("--output", required=True, help="Output model path (without extension)")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--sequence-length", type=int, default=30)
    args = parser.parse_args()

    print("Loading data...")
    X, y, labels = load_data(args.data_dir, args.sequence_length)
    print(f"Loaded {len(X)} sequences, {len(labels)} classes")

    if len(X) == 0:
        print("ERROR: No valid sequences found. Need more data.")
        return

    # Split train / test
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"Train: {len(X_train)}, Test: {len(X_test)}")

    input_shape = (X_train.shape[1], X_train.shape[2])
    model = build_model(input_shape, len(labels))
    model.summary()

    model.fit(
        X_train, y_train,
        validation_data=(X_test, y_test),
        epochs=args.epochs,
        batch_size=args.batch_size,
    )

    # Evaluate
    loss, accuracy = model.evaluate(X_test, y_test)
    print(f"Test accuracy: {accuracy:.4f}")

    # Save
    h5_path = args.output + ".h5"
    model.save(h5_path)
    print(f"Keras model saved: {h5_path}")

    export_tflite(model, args.output)

    # Save labels
    labels_path = args.output + "_labels.txt"
    with open(labels_path, "w") as f:
        for label in labels:
            f.write(label + "\n")
    print(f"Labels saved: {labels_path}")


if __name__ == "__main__":
    main()
