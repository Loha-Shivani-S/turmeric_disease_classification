"""
unet.py — UNet Segmentation Model built from scratch
Encoder-Decoder with skip connections. No pretrained weights.
"""

import os, sys
os.environ["KERAS_BACKEND"] = "torch"
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as CFG

import keras
from keras import layers, Model, ops
from keras import backend as K


# ─────────────────────────────────────────────────────────────
# Building blocks
# ─────────────────────────────────────────────────────────────

def conv_block(x, filters, dropout=0.0):
    """Two conv layers with BN + ReLU."""
    x = layers.Conv2D(filters, 3, padding='same', use_bias=False,
                      kernel_initializer='he_normal')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    if dropout > 0:
        x = layers.Dropout(dropout)(x)
    x = layers.Conv2D(filters, 3, padding='same', use_bias=False,
                      kernel_initializer='he_normal')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    return x


def encoder_block(x, filters, dropout=0.0):
    skip = conv_block(x, filters, dropout)
    pool = layers.MaxPooling2D(2)(skip)
    return skip, pool


def decoder_block(x, skip, filters):
    x = layers.UpSampling2D(size=2, interpolation='nearest')(x)
    x = layers.Conv2D(filters, 3, padding='same', use_bias=False,
                      kernel_initializer='he_normal')(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation('relu')(x)
    x = layers.Concatenate()([x, skip])
    x = conv_block(x, filters)
    return x


# ─────────────────────────────────────────────────────────────
# UNet model
# ─────────────────────────────────────────────────────────────

def build_unet(input_shape=(CFG.IMG_SIZE, CFG.IMG_SIZE, CFG.IMG_CHANNELS),
               num_classes=CFG.NUM_CLASSES,
               base_filters=CFG.UNET_BASE_FILTERS):
    """
    UNet from scratch.
    Encoder: [64 → 128 → 256 → 512]
    Bottleneck: 1024
    Decoder: [512 → 256 → 128 → 64]
    Output: softmax over num_classes per pixel
    """
    inputs = layers.Input(shape=input_shape)

    # Encoder
    s1, p1 = encoder_block(inputs, base_filters)
    s2, p2 = encoder_block(p1, base_filters * 2)
    s3, p3 = encoder_block(p2, base_filters * 4, dropout=0.2)
    s4, p4 = encoder_block(p3, base_filters * 8, dropout=0.2)

    # Bottleneck
    b = conv_block(p4, base_filters * 16, dropout=0.3)

    # Decoder
    d4 = decoder_block(b,  s4, base_filters * 8)
    d3 = decoder_block(d4, s3, base_filters * 4)
    d2 = decoder_block(d3, s2, base_filters * 2)
    d1 = decoder_block(d2, s1, base_filters)

    # Output
    outputs = layers.Conv2D(num_classes, 1, activation='softmax')(d1)

    model = Model(inputs, outputs, name='UNet_Scratch')
    return model


# ─────────────────────────────────────────────────────────────
# Loss: combined Dice + Categorical Cross-Entropy
# ─────────────────────────────────────────────────────────────

def dice_loss(y_true, y_pred, smooth=1e-6):
    """Dice loss for segmentation. Works with 1D/2D reshaped tensors."""
    num_classes = CFG.NUM_CLASSES
    y_true_oh = ops.one_hot(ops.cast(y_true, "int32"), num_classes)
    y_true_oh = ops.cast(y_true_oh, "float32")
    y_pred_f  = ops.cast(y_pred, "float32")

    intersection = ops.sum(y_true_oh * y_pred_f, axis=0)
    dice = (2.0 * intersection + smooth) / (
        ops.sum(y_true_oh, axis=0) + ops.sum(y_pred_f, axis=0) + smooth
    )
    return 1.0 - ops.mean(dice)


def combined_loss(y_true, y_pred):
    """50% Dice + 50% Sparse Categorical Cross-Entropy with contiguous tensor layout."""
    num_classes = CFG.NUM_CLASSES
    y_true_flat = ops.reshape(y_true, (-1,))
    y_pred_flat = ops.reshape(y_pred, (-1, num_classes))

    cce = keras.losses.sparse_categorical_crossentropy(y_true_flat, y_pred_flat)
    dl  = dice_loss(y_true_flat, y_pred_flat)
    return 0.5 * ops.mean(cce) + 0.5 * dl


def mean_iou_metric(num_classes=CFG.NUM_CLASSES):
    """Mean IoU metric compatible with sparse labels."""
    miou = keras.metrics.MeanIoU(num_classes=num_classes)
    def _metric(y_true, y_pred):
        y_pred_cls = ops.argmax(y_pred, axis=-1)
        miou.reset_state()
        miou.update_state(ops.reshape(y_true, (-1,)), ops.reshape(y_pred_cls, (-1,)))
        return miou.result()
    _metric.__name__ = 'mean_iou'
    return _metric


def get_unet():
    """Build, compile and return UNet model."""
    model = build_unet()
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=CFG.LEARNING_RATE),
        loss=combined_loss,
        metrics=['accuracy', mean_iou_metric()]
    )
    return model


if __name__ == '__main__':
    m = get_unet()
    m.summary()
    print(f"Total params: {m.count_params():,}")
