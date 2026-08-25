"""
predict.py — Predict disease from a single unknown image
Loads saved trained models and returns:
  - Disease class name
  - Confidence scores for all classes
  - Segmentation overlay showing disease region
  - Saves a visual report and a simple sample output image

Usage:
    python predict.py path/to/your/image.jpg

    OR in Python:
        from predict import predict_image
        result = predict_image("path/to/image.jpg")
        print(result)
"""

import os, sys, argparse
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ["KERAS_BACKEND"] = "torch"
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import config as CFG
from utils.dataloader import generate_seg_masks_from_labels, apply_leaf_segmentation

# ── Palette ──────────────────────────────────────────────────
P = {
    'bg':    '#0d1117', 'card':   '#161b22',
    'text':  '#e6edf3', 'sub':    '#8b949e',
    'green': '#3fb950', 'yellow': '#d29922',
    'red':   '#f85149', 'blue':   '#58a6ff',
    'border':'#30363d',
}
CLASS_COLORS_RGB = [
    [63,  185,  80],   # healthy     → green
    [210, 153,  34],   # leaf_spot   → yellow
    [240, 136,  62],   # leaf_blotch → orange
    [248,  81,  73],   # dry_leaf    → red
    [88,  166, 255],   # rhizome_healthy -> blue
    [188, 140, 255],   # rhizome_disease -> purple
    [57,  211, 201],   # aphids -> teal
]
SEV_LABEL  = ['None', 'Mild', 'Moderate', 'Severe']
SEV_COLOR  = [P['green'], P['yellow'], P['yellow'], P['red']]


# ─────────────────────────────────────────────────────────────
# Load models (once, cached)
# ─────────────────────────────────────────────────────────────

_unet_model = None
_clf_model  = None


def load_models():
    global _unet_model, _clf_model
    if _clf_model is not None:
        return _unet_model, _clf_model

    import keras
    from models.unet import combined_loss, mean_iou_metric

    clf_path = os.path.join(CFG.MODEL_DIR, 'mobilenet_final.keras')
    unet_path = os.path.join(CFG.MODEL_DIR, 'unet_final.keras')

    if not os.path.exists(clf_path):
        print(f"\n  [WARNING] No classifier model found in '{CFG.MODEL_DIR}/'.")
        print("  Please run 'python train.py' first to train and save the classifier.")
        print(f"  Expected file: {clf_path}\n")
        sys.exit(1)

    print("  Loading saved classifier...")
    _clf_model = keras.saving.load_model(clf_path)
    if _clf_model.output_shape[-1] != CFG.NUM_CLASSES:
        raise ValueError(
            f"Classifier was trained for {_clf_model.output_shape[-1]} classes, "
            f"but config.py now has {CFG.NUM_CLASSES}. Run train.py again."
        )

    if os.path.exists(unet_path):
        print("  Loading saved UNet segmentation model...")
        custom_objects = {
            'combined_loss': combined_loss,
            'mean_iou': mean_iou_metric()
        }
        try:
            _unet_model = keras.saving.load_model(unet_path, custom_objects=custom_objects)
            print(f"  ✓ UNet loaded from:      {unet_path}")
        except Exception as e:
            print(f"  [Note] Could not load saved UNet ({e}). Using heuristic segmentation.")
            _unet_model = None
    else:
        _unet_model = None
        print("  Segmentation uses heuristic masks (no UNet model weights file).")

    print(f"  ✓ MobileNet loaded from: {clf_path}")
    return _unet_model, _clf_model


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def preprocess_image(img_path, img_size=CFG.IMG_SIZE):
    """Load and preprocess a single image for inference."""
    img_path = str(img_path)
    if not os.path.exists(img_path):
        raise FileNotFoundError(f"Image not found: {img_path}")

    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Cannot read image: {img_path}")

    img_rgb  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    original = img_rgb.copy()

    img_resized = cv2.resize(img_rgb, (img_size, img_size), interpolation=cv2.INTER_AREA)
    img_norm    = img_resized.astype(np.float32) / 255.0
    img_segmented, leaf_mask = apply_leaf_segmentation(img_norm)

    return img_norm, img_segmented, leaf_mask, original, img_resized


def overlay_segmentation(img_norm, seg_mask, alpha=0.45):
    """Blend segmentation mask over image as color overlay."""
    h, w = img_norm.shape[:2]
    color_layer = np.zeros((h, w, 3), dtype=np.float32)

    for c, color in enumerate(CLASS_COLORS_RGB[:CFG.NUM_CLASSES]):
        region = (seg_mask == c)
        for ch in range(3):
            color_layer[:, :, ch][region] = color[ch] / 255.0

    blended = img_norm * (1 - alpha) + color_layer * alpha
    return np.clip(blended, 0, 1)


def prediction_region(seg_mask, seg_probs, pred_class):
    """Return a visible boolean region for the predicted class."""
    region = (seg_mask == pred_class)
    min_pixels = max(16, int(seg_mask.size * 0.005))
    if region.sum() >= min_pixels:
        return region

    class_prob = seg_probs[:, :, pred_class]
    threshold = np.percentile(class_prob, 85)
    region = class_prob >= threshold
    return region


def make_masked_region(img_resized, region):
    """Keep the predicted region in color and gray out the rest."""
    img_float = img_resized.astype(np.float32) / 255.0
    gray = np.full_like(img_float, 0.58, dtype=np.float32)
    region_3c = region[:, :, np.newaxis]
    masked = np.where(region_3c, img_float, gray)
    return np.clip(masked, 0, 1)


def compute_severity(seg_mask, pred_class):
    """Estimate disease severity from segmentation mask coverage."""
    pred_name = CFG.CLASS_NAMES[pred_class]
    healthy_names = set(getattr(CFG, "HEALTHY_CLASS_NAMES", ("healthy",)))
    if pred_name in healthy_names or pred_name.endswith("_healthy"):
        return 0, 'None', 0.0
    total_px    = seg_mask.size
    disease_px  = (seg_mask == pred_class).sum()
    coverage    = disease_px / total_px

    if   coverage == 0.0:  return 0, 'None',     0.0
    elif coverage < 0.05:  return 1, 'Mild',      coverage
    elif coverage < 0.20:  return 2, 'Moderate',  coverage
    else:                  return 3, 'Severe',     coverage


# ─────────────────────────────────────────────────────────────
# Core prediction
# ─────────────────────────────────────────────────────────────

def predict_image(img_path, save_report=True, report_dir=None):
    """
    Predict disease class for a single image.

    Parameters:
        img_path   : str — path to the image file
        save_report: bool — save visual report PNG
        report_dir : str — where to save report (default: CFG.RESULTS_DIR)

    Returns:
        dict with keys:
            predicted_class   : int
            predicted_label   : str
            confidence        : float (0–1)
            all_scores        : dict {class_name: confidence}
            severity_level    : int (0–3)
            severity_label    : str
            disease_coverage  : float (% of image)
            report_path       : str or None
            sample_path       : str or None
    """
    if report_dir is None:
        report_dir = CFG.RESULTS_DIR
    os.makedirs(report_dir, exist_ok=True)

    # Load models
    unet_model, clf_model = load_models()

    # Preprocess
    img_norm, img_segmented, leaf_mask, original, img_resized = preprocess_image(img_path)
    batch = img_segmented[np.newaxis]  # (1, H, W, 3), segmentation first

    # MobileNet classification
    clf_probs  = clf_model.predict(batch, verbose=0)[0]  # (C,)
    pred_class = int(np.argmax(clf_probs))
    confidence = float(clf_probs[pred_class])

    # Segmentation mask (UNet model if available, else heuristic)
    if unet_model is not None:
        seg_probs = unet_model.predict(img_norm[np.newaxis], verbose=0)
        seg_mask = np.argmax(seg_probs[0], axis=-1)
    else:
        seg_mask = generate_seg_masks_from_labels(
            img_segmented[np.newaxis],
            np.array([pred_class], dtype=np.int32)
        )[0]
        seg_probs = np.eye(CFG.NUM_CLASSES, dtype=np.float32)[seg_mask][np.newaxis]

    # Severity
    sev_idx, sev_label, coverage = compute_severity(seg_mask, pred_class)

    # Build result dict
    result = {
        'predicted_class':  pred_class,
        'predicted_label':  CFG.CLASS_NAMES[pred_class],
        'confidence':       confidence,
        'all_scores':       {CFG.CLASS_NAMES[i]: float(clf_probs[i])
                             for i in range(CFG.NUM_CLASSES)},
        'severity_level':   sev_idx,
        'severity_label':   sev_label,
        'disease_coverage': float(coverage * 100),
        'report_path':      None,
        'sample_path':      None,
    }

    # Print to console
    _print_prediction(result)

    # Save visual report
    if save_report:
        fname = os.path.splitext(os.path.basename(img_path))[0]
        rpath = os.path.join(report_dir, f'prediction_{fname}.png')
        _save_visual_report(img_segmented, img_resized, original,
                            seg_mask, seg_probs[0], clf_probs,
                            result, img_path, rpath)
        result['report_path'] = rpath

        spath = os.path.join(report_dir, f'sample_{fname}.png')
        _save_output_sample(img_resized, seg_mask, seg_probs[0], result, spath)
        result['sample_path'] = spath

    return result


# ─────────────────────────────────────────────────────────────
# Visual report
# ─────────────────────────────────────────────────────────────

def _save_visual_report(img_norm, img_resized, original,
                        seg_mask, seg_probs, clf_probs,
                        result, img_path, save_path):
    """Save a 4-panel visual report for the prediction."""
    fig = plt.figure(figsize=(16, 9))
    fig.patch.set_facecolor(P['bg'])

    # Layout: 2 rows × 4 cols
    gs = fig.add_gridspec(2, 4, hspace=0.4, wspace=0.35,
                          left=0.04, right=0.96, top=0.88, bottom=0.08)

    # ── Panel 1: Original image ────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.imshow(img_resized)
    ax1.set_title('Input Image', color=P['text'], fontsize=10, fontweight='bold')
    ax1.axis('off')

    # ── Panel 2: Segmentation mask ────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    mask_rgb = np.zeros((*seg_mask.shape, 3), dtype=np.uint8)
    for c, color in enumerate(CLASS_COLORS_RGB[:CFG.NUM_CLASSES]):
        mask_rgb[seg_mask == c] = color
    ax2.imshow(mask_rgb)
    ax2.set_title('Heuristic Segmentation', color=P['text'], fontsize=10, fontweight='bold')
    ax2.axis('off')
    # Legend
    patches = [mpatches.Patch(color=[v/255 for v in CLASS_COLORS_RGB[i]],
                               label=CFG.CLASS_NAMES[i])
               for i in range(CFG.NUM_CLASSES)]
    ax2.legend(handles=patches, loc='lower center', fontsize=6,
               facecolor=P['card'], labelcolor=P['text'],
               framealpha=0.85, ncol=2, bbox_to_anchor=(0.5, -0.28))

    # ── Panel 3: Overlay ──────────────────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    overlay = overlay_segmentation(img_norm, seg_mask, alpha=0.5)
    ax3.imshow(overlay)
    ax3.set_title('Disease Overlay', color=P['text'], fontsize=10, fontweight='bold')
    ax3.axis('off')

    # ── Panel 4: Confidence bars ──────────────────────────
    ax4 = fig.add_subplot(gs[0, 3])
    ax4.set_facecolor(P['card'])
    for s in ax4.spines.values(): s.set_edgecolor(P['border'])
    yp   = np.arange(CFG.NUM_CLASSES)
    cols = [P['green'] if i == result['predicted_class'] else P['blue']
            for i in range(CFG.NUM_CLASSES)]
    bars = ax4.barh(yp, clf_probs * 100, color=cols, alpha=0.88)
    ax4.set_yticks(yp)
    ax4.set_yticklabels(CFG.CLASS_NAMES, fontsize=8, color=P['text'])
    ax4.set_xlabel('Confidence (%)', color=P['text'], fontsize=9)
    ax4.set_xlim(0, 115)
    ax4.set_title('Class Confidence', color=P['text'], fontsize=10, fontweight='bold')
    ax4.tick_params(colors=P['text'])
    ax4.xaxis.grid(True, color=P['border'], alpha=0.5)
    ax4.set_axisbelow(True)
    for b, v in zip(bars, clf_probs):
        ax4.text(v * 100 + 1, b.get_y() + b.get_height()/2,
                 f'{v:.1%}', va='center', fontsize=8, color=P['text'])

    # ── Panel 5 (bottom row): prediction card ─────────────
    ax5 = fig.add_subplot(gs[1, :])
    ax5.set_facecolor(P['card'])
    ax5.axis('off')
    for s in ax5.spines.values(): s.set_edgecolor(P['border'])

    pred_color = CLASS_COLORS_RGB[result['predicted_class']]
    pred_hex   = '#{:02x}{:02x}{:02x}'.format(*pred_color)
    sev_c      = SEV_COLOR[result['severity_level']]

    ax5.text(0.01, 0.75, 'PREDICTION:', transform=ax5.transAxes,
             fontsize=10, color=P['sub'], va='center')
    ax5.text(0.14, 0.75, result['predicted_label'].replace('_', ' ').title(),
             transform=ax5.transAxes, fontsize=18, fontweight='bold',
             color=pred_hex, va='center')

    ax5.text(0.38, 0.75, f"Confidence: {result['confidence']:.1%}",
             transform=ax5.transAxes, fontsize=13, color=P['text'], va='center')

    ax5.text(0.60, 0.75, f"Severity: ",
             transform=ax5.transAxes, fontsize=13, color=P['text'], va='center')
    ax5.text(0.72, 0.75, result['severity_label'],
             transform=ax5.transAxes, fontsize=13, fontweight='bold',
             color=sev_c, va='center')

    ax5.text(0.84, 0.75, f"Disease Coverage: {result['disease_coverage']:.1f}%",
             transform=ax5.transAxes, fontsize=11, color=P['sub'], va='center')

    # Score breakdown
    scores_txt = '  |  '.join(
        f"{n}: {s:.1%}" for n, s in result['all_scores'].items()
    )
    ax5.text(0.01, 0.25, scores_txt, transform=ax5.transAxes,
             fontsize=8, color=P['sub'], va='center')

    # Image filename
    ax5.text(0.01, 0.05, f"Image: {os.path.basename(img_path)}",
             transform=ax5.transAxes, fontsize=7, color=P['sub'], va='center')

    fig.suptitle('Turmeric Disease Detection Report',
                 fontsize=14, fontweight='bold', color=P['text'], y=0.97)

    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=P['bg'])
    print(f"  Visual report saved → {save_path}")
    plt.close()


def _save_output_sample(img_resized, seg_mask, seg_probs, result, save_path):
    """Save a simple Original / Predicted Mask / Masked Region image."""
    pred_class = result['predicted_class']
    pred_label = result['predicted_label'].replace('_', ' ').title()
    confidence = result['confidence'] * 100

    region = prediction_region(seg_mask, seg_probs, pred_class)
    mask_img = np.where(region, 0, 255).astype(np.uint8)
    masked_region = make_masked_region(img_resized, region)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.patch.set_facecolor('white')

    panels = [
        ('Original', img_resized, None),
        ('Predicted Mask', mask_img, 'gray'),
        ('Masked Region', masked_region, None),
    ]

    for ax, (title, image, cmap) in zip(axes, panels):
        if cmap:
            ax.imshow(image, cmap=cmap, vmin=0, vmax=255)
        else:
            ax.imshow(image)
        ax.set_title(title, fontsize=18, color='black', pad=10)
        ax.axis('off')

    fig.suptitle(
        f'Prediction: {pred_label} ({confidence:.1f}%)',
        fontsize=22,
        fontweight='bold',
        color='black',
        y=0.98
    )
    plt.subplots_adjust(left=0.02, right=0.98, top=0.85, bottom=0.06, wspace=0.08)
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"  Output sample saved → {save_path}")
    plt.close()


def _print_prediction(result):
    W = 55
    print(f"\n{'═'*W}")
    print(f"  DISEASE PREDICTION RESULT")
    print(f"{'─'*W}")
    print(f"  Predicted Disease  : {result['predicted_label'].replace('_',' ').title()}")
    print(f"  Confidence         : {result['confidence']:.2%}")
    print(f"  Severity           : {result['severity_label']}")
    print(f"  Disease Coverage   : {result['disease_coverage']:.1f}% of image")
    print(f"{'─'*W}")
    print(f"  All class scores:")
    for name, score in result['all_scores'].items():
        bar = '█' * int(score * 20)
        marker = ' ←' if name == result['predicted_label'] else ''
        print(f"    {name:<18} {score:>6.2%}  {bar}{marker}")
    print(f"{'═'*W}\n")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Turmeric Disease Predictor — provide an image path')
    parser.add_argument('image', type=str,
                        help='Path to the leaf image (JPG/PNG/etc.)')
    parser.add_argument('--no-report', action='store_true',
                        help='Skip saving the visual report')
    args = parser.parse_args()

    result = predict_image(
        args.image,
        save_report=not args.no_report,
        report_dir=CFG.RESULTS_DIR
    )
