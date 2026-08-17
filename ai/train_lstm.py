"""Train LSTM classifier for AquaFlow dual-sensor windows."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import DATA_DIR, LABEL_PATH, LABELS, MODEL_PATH  # noqa: E402


def build_model(seq_len: int, n_features: int, n_classes: int):
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers

    model = keras.Sequential(
        [
            layers.Input(shape=(seq_len, n_features)),
            layers.Masking(mask_value=0.0),
            layers.LSTM(64, return_sequences=True),
            layers.Dropout(0.2),
            layers.LSTM(32),
            layers.Dense(32, activation="relu"),
            layers.Dropout(0.2),
            layers.Dense(n_classes, activation="softmax"),
        ]
    )
    model.compile(
        optimizer=keras.optimizers.Adam(1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main(epochs: int = 12, batch_size: int = 64):
    x_path = DATA_DIR / "lstm_X.npy"
    y_path = DATA_DIR / "lstm_y.npy"
    if not x_path.exists() or not y_path.exists():
        print("Dataset missing — generating...")
        from ai.generate_dataset import main as gen

        gen()

    X = np.load(x_path)
    y = np.load(y_path)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = build_model(X.shape[1], X.shape[2], len(LABELS))
    model.summary()
    history = model.fit(
        X_train,
        y_train,
        validation_split=0.15,
        epochs=epochs,
        batch_size=batch_size,
        verbose=1,
    )

    probs = model.predict(X_test, verbose=0)
    pred = probs.argmax(axis=1)
    print("\nClassification report:")
    print(classification_report(y_test, pred, target_names=LABELS))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, pred))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.save(MODEL_PATH)
    LABEL_PATH.write_text(json.dumps({"labels": LABELS}, indent=2))
    hist_path = MODEL_PATH.with_suffix(".history.json")
    hist_path.write_text(json.dumps({k: [float(x) for x in v] for k, v in history.history.items()}, indent=2))
    print(f"\nSaved model -> {MODEL_PATH}")
    print(f"Saved labels -> {LABEL_PATH}")


if __name__ == "__main__":
    main()
