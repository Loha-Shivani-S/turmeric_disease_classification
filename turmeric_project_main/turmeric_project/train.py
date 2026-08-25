"""
train.py — Full training pipeline
Loads YOUR dataset → trains MobileNet → saves model → full metrics report

Usage:
    python train.py
"""

import os, sys, time
os.environ["KERAS_BACKEND"] = "torch"
import numpy as np
import warnings
warnings.filterwarnings('ignore')

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import config as CFG
from utils.dataloader import (
    load_full_dataset, generate_seg_masks_from_labels,
    make_classification_dataset, compute_class_weights
)
from utils.metrics import (
    confusion_matrix, classification_metrics,
    plot_confusion_matrix,
    plot_training_history,
    export_metrics_to_excel
)

import keras
import torch
from keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
)

def setup_accelerator():
    """Enable Torch GPU acceleration settings when a GPU is available."""
    print(f"  Keras backend: {keras.backend.backend()}")
    if not torch.cuda.is_available():
        message = (
            "PyTorch did not detect a CUDA GPU.\n"
            "Run gpu_check.py to confirm the PyTorch/CUDA environment."
        )
        if getattr(CFG, 'REQUIRE_GPU', False):
            raise RuntimeError(message)
        print(f"  Accelerator: CPU only ({message})")
        return

    gpu_count = torch.cuda.device_count()
    print(f"  Accelerator: {gpu_count} CUDA GPU(s) detected by PyTorch")
    for i in range(gpu_count):
        print(f"    - {torch.cuda.get_device_name(i)}")

    if CFG.MIXED_PRECISION:
        keras.config.set_dtype_policy('mixed_float16')
        print("  Mixed precision: enabled")


# ─────────────────────────────────────────────────────────────
# Callbacks
# ─────────────────────────────────────────────────────────────

def get_callbacks(model_name, monitor='val_loss', mode='auto'):
    os.makedirs(CFG.MODEL_DIR, exist_ok=True)
    ckpt_path = os.path.join(CFG.MODEL_DIR, f'{model_name}_best.keras')
    return [
        EarlyStopping(monitor=monitor, patience=6,
                      restore_best_weights=True, verbose=1),
        ReduceLROnPlateau(monitor=monitor, factor=0.5,
                          patience=3, min_lr=1e-6, verbose=1),
        ModelCheckpoint(ckpt_path, monitor=monitor, mode=mode,
                        save_best_only=True, verbose=0),
    ]


def print_classification_report(clf, class_names=CFG.CLASS_NAMES):
    W = 70
    print(f"\n{'='*W}")
    print("  CLASSIFICATION METRICS")
    print(f"{'-'*W}")
    print(f"  {'Class':<18} {'Precision':>10} {'Recall':>10} {'F1':>10} "
          f"{'Specificity':>12} {'Support':>8}")
    print(f"{'-'*W}")
    for i, name in enumerate(class_names):
        print(f"  {name:<18} {clf['precision'][i]:>10.4f} {clf['recall'][i]:>10.4f} "
              f"{clf['f1'][i]:>10.4f} {clf['specificity'][i]:>12.4f} "
              f"{clf['support'][i]:>8.0f}")
    print(f"{'-'*W}")
    print(f"  {'Macro Avg':<18} {clf['macro_precision']:>10.4f} "
          f"{clf['macro_recall']:>10.4f} {clf['macro_f1']:>10.4f}")
    print(f"  {'Weighted Avg':<18} {clf['weighted_precision']:>10.4f} "
          f"{clf['weighted_recall']:>10.4f} {clf['weighted_f1']:>10.4f}")
    print(f"{'-'*W}")
    print(f"  Accuracy : {clf['accuracy']:.4f}   MCC : {clf['mcc']:.4f}   "
          f"Kappa : {clf['kappa']:.4f}")
    print(f"{'='*W}")


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    np.random.seed(CFG.RANDOM_SEED)
    keras.utils.set_random_seed(CFG.RANDOM_SEED)
    setup_accelerator()

    print("\n" + "█"*65)
    print("  TURMERIC DISEASE DETECTION — TRAINING PIPELINE")
    print("  Heuristic Segmentation + MobileNet Classification")
    print("  MobileNetV2 transfer learning + PyTorch CUDA backend.")
    print("█"*65)

    # ── 1. Load dataset ───────────────────────────────────────
    print("\n[1/5] Loading dataset...")
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = load_full_dataset()

    # Auto-generate segmentation masks from images
    print("  Generating segmentation masks from images...")
    y_seg_train = generate_seg_masks_from_labels(X_train, y_train)
    y_seg_val   = generate_seg_masks_from_labels(X_val,   y_val)
    y_seg_test  = generate_seg_masks_from_labels(X_test,  y_test)
    print(f"  Seg masks: train={y_seg_train.shape} val={y_seg_val.shape} test={y_seg_test.shape}")

    train_clf_ds = make_classification_dataset(X_train, y_train, training=True)
    val_clf_ds   = make_classification_dataset(X_val, y_val, training=False)
    test_clf_ds  = make_classification_dataset(X_test, y_test, training=False)

    class_weights = compute_class_weights(y_train)
    print(f"  Class weights: {class_weights}")

    # ── 2. Build models ───────────────────────────────────────
    print("\n[2/5] Building models...")
    from models.mobilenet import get_mobilenet, prepare_for_fine_tuning
    from models.unet import get_unet

    clf_model = get_mobilenet()
    print(f"  MobileNet   params: {clf_model.count_params():>12,}")

    unet_model = None
    if CFG.TRAIN_UNET:
        unet_model = get_unet()
        print(f"  UNet        params: {unet_model.count_params():>12,}")

    # ── 3. Segmentation setup ─────────────────────────────────
    if CFG.TRAIN_UNET:
        print(f"\n[3/5] Training UNet segmentation model ({CFG.UNET_EPOCHS} epochs max)...")
        unet_hist = unet_model.fit(
            X_train, y_seg_train,
            validation_data=(X_val, y_seg_val),
            epochs=CFG.UNET_EPOCHS,
            batch_size=CFG.BATCH_SIZE,
            callbacks=get_callbacks('unet', monitor='val_loss', mode='min'),
            verbose=1
        )
        unet_path = os.path.join(CFG.MODEL_DIR, 'unet_final.keras')
        unet_model.save(unet_path)
        print(f"  UNet saved → {unet_path}")

        plot_training_history(
            unet_hist.history, title='UNet',
            save_path=os.path.join(CFG.RESULTS_DIR, 'unet_history.png')
        )
    else:
        print("\n[3/5] Using heuristic segmentation masks (no UNet training).")

    # ── 4. Train MobileNet ────────────────────────────────────
    print(f"\n[4/5] Training MobileNet classifier ({CFG.CLF_EPOCHS} epochs max)...")
    warmup_epochs = max(3, CFG.CLF_EPOCHS // 3)
    fine_tune_epochs = max(CFG.CLF_EPOCHS - warmup_epochs, 0)
    clf_hist = clf_model.fit(
        train_clf_ds[0], train_clf_ds[1],
        validation_data=val_clf_ds,
        epochs=warmup_epochs,
        batch_size=CFG.BATCH_SIZE,
        class_weight=class_weights,
        callbacks=get_callbacks('mobilenet_warmup',
                                monitor='val_accuracy', mode='max'),
        verbose=1
    )
    if fine_tune_epochs > 0:
        print(f"\n[4/5] Fine-tuning MobileNetV2 ({fine_tune_epochs} epochs max)...")
        prepare_for_fine_tuning(clf_model)
        fine_hist = clf_model.fit(
            train_clf_ds[0], train_clf_ds[1],
            validation_data=val_clf_ds,
            initial_epoch=warmup_epochs,
            epochs=CFG.CLF_EPOCHS,
            batch_size=CFG.BATCH_SIZE,
            class_weight=class_weights,
            callbacks=get_callbacks('mobilenet',
                                    monitor='val_accuracy', mode='max'),
            verbose=1
        )
        for key, values in fine_hist.history.items():
            clf_hist.history.setdefault(key, []).extend(values)

    # ── 5. Save final models ──────────────────────────────────
    clf_path  = os.path.join(CFG.MODEL_DIR, 'mobilenet_final.keras')
    clf_model.save(clf_path)
    print(f"\n  Models saved:")
    print(f"    {clf_path}")

    # ── 6. Evaluate on test set ───────────────────────────────
    print("\n[5/5] Evaluating on test set...")

    clf_probs  = clf_model.predict(test_clf_ds[0], batch_size=CFG.BATCH_SIZE, verbose=0)
    clf_preds  = np.argmax(clf_probs, axis=-1)

    cm   = confusion_matrix(y_test, clf_preds)
    clf  = classification_metrics(cm)
    print_classification_report(clf)
    print("  Note: segmentation metrics are skipped because segmentation is")
    print("  heuristic-only in the current pipeline, not a learned model.")

    # ── 7. Save plots, JSON and Excel reports ──────────────────
    print("  Generating plots, metrics.json, and metrics_report.xlsx...")
    os.makedirs(CFG.RESULTS_DIR, exist_ok=True)
    export_metrics_to_excel(clf, cm, os.path.join(CFG.RESULTS_DIR, 'metrics_report.xlsx'))
    import json
    metrics_json_path = os.path.join(CFG.RESULTS_DIR, 'metrics.json')
    metrics_dict = {
        'accuracy': float(clf['accuracy']),
        'macro_precision': float(clf['macro_precision']),
        'macro_recall': float(clf['macro_recall']),
        'macro_f1': float(clf['macro_f1']),
        'weighted_precision': float(clf['weighted_precision']),
        'weighted_recall': float(clf['weighted_recall']),
        'weighted_f1': float(clf['weighted_f1']),
        'mcc': float(clf['mcc']),
        'kappa': float(clf['kappa']),
        'per_class': {
            CFG.CLASS_NAMES[i]: {
                'precision': float(clf['precision'][i]),
                'recall': float(clf['recall'][i]),
                'f1': float(clf['f1'][i]),
                'specificity': float(clf['specificity'][i]),
                'support': int(clf['support'][i]),
            } for i in range(len(CFG.CLASS_NAMES))
        }
    }
    with open(metrics_json_path, 'w', encoding='utf-8') as f:
        json.dump(metrics_dict, f, indent=2)
    print(f"  Saved raw metrics → {metrics_json_path}")

    plot_confusion_matrix(
        cm, save_path=os.path.join(CFG.RESULTS_DIR, 'confusion_matrix.png'))
    plot_training_history(
        clf_hist.history, title='MobileNet',
        save_path=os.path.join(CFG.RESULTS_DIR, 'mobilenet_history.png'))

    elapsed = time.time() - t0
    print(f"\n{'═'*65}")
    print(f"  TRAINING COMPLETE — {elapsed:.1f}s")
    print(f"  Results  → {os.path.abspath(CFG.RESULTS_DIR)}/")
    print(f"  Models   → {os.path.abspath(CFG.MODEL_DIR)}/")
    print(f"{'═'*65}\n")


if __name__ == '__main__':
    main()
