"""
mobilenet.py - MobileNetV2 classifier with transfer learning.

The previous from-scratch classifier was easy to overfit and often collapsed
to predicting one class. This version uses ImageNet features when available,
then fine-tunes the top MobileNetV2 layers at a lower learning rate.
"""

import os
import sys
os.environ["KERAS_BACKEND"] = "torch"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as CFG

import keras
from keras import Model, layers


def _build_base(input_shape):
    weights = "imagenet" if CFG.USE_IMAGENET_WEIGHTS else None
    try:
        return keras.applications.MobileNetV2(
            input_shape=input_shape,
            include_top=False,
            weights=weights,
            alpha=CFG.MOBILENET_ALPHA,
        )
    except Exception as exc:
        if weights is None:
            raise
        print(f"  [WARN] Could not load ImageNet weights: {exc}")
        print("  [WARN] Falling back to random MobileNetV2 weights.")
        return keras.applications.MobileNetV2(
            input_shape=input_shape,
            include_top=False,
            weights=None,
            alpha=CFG.MOBILENET_ALPHA,
        )


def build_mobilenet(input_shape=(CFG.IMG_SIZE, CFG.IMG_SIZE, CFG.IMG_CHANNELS),
                    num_classes=CFG.NUM_CLASSES):
    """Build a MobileNetV2 classifier for images normalized to [0, 1]."""
    inputs = layers.Input(shape=input_shape)

    x = layers.Rescaling(2.0, offset=-1.0)(inputs)
    base = _build_base(input_shape)
    base.trainable = False
    x = base(x, training=False)

    x = layers.GlobalAveragePooling2D()(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(0.35)(x)
    x = layers.Dense(256, activation="relu")(x)
    x = layers.Dropout(0.25)(x)
    outputs = layers.Dense(num_classes, activation="softmax", dtype="float32")(x)

    return Model(inputs, outputs, name="MobileNetV2_Transfer")


def compile_mobilenet(model, learning_rate=CFG.LEARNING_RATE):
    loss = keras.losses.SparseCategoricalCrossentropy()
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=loss,
        metrics=["accuracy"],
    )
    return model


def prepare_for_fine_tuning(model, fine_tune_at=CFG.FINE_TUNE_AT):
    """Unfreeze the upper MobileNetV2 layers and recompile with a small LR."""
    base = next((layer for layer in model.layers
                 if isinstance(layer, keras.Model)
                 and layer.name.startswith("mobilenetv2")), None)
    if base is None:
        return compile_mobilenet(model, CFG.FINE_TUNE_LEARNING_RATE)

    base.trainable = True
    for layer in base.layers[:fine_tune_at]:
        layer.trainable = False
    for layer in base.layers[fine_tune_at:]:
        if isinstance(layer, layers.BatchNormalization):
            layer.trainable = False

    return compile_mobilenet(model, CFG.FINE_TUNE_LEARNING_RATE)


def get_mobilenet():
    """Build, compile, and return the classifier."""
    return compile_mobilenet(build_mobilenet())


if __name__ == "__main__":
    m = get_mobilenet()
    m.summary()
    print(f"Total params: {m.count_params():,}")
