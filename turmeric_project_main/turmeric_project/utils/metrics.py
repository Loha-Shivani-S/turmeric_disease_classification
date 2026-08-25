"""
metrics.py — All evaluation metrics + visualizations.
Confusion matrix, F1, Precision, Recall, Accuracy, IoU, Dice, MCC.
All computed from scratch using NumPy.
"""

import os, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as CFG

# ── Palette ───────────────────────────────────────────────────
P = {
    'bg':      '#0d1117', 'card':    '#161b22',
    'green':   '#3fb950', 'yellow':  '#d29922',
    'orange':  '#f0883e', 'red':     '#f85149',
    'blue':    '#58a6ff', 'purple':  '#bc8cff',
    'cyan':    '#39d353', 'text':    '#e6edf3',
    'subtext': '#8b949e', 'grid':    '#21262d',
    'border':  '#30363d',
}
CLASS_COLORS = [
    '#3fb950',  # healthy
    '#d29922',  # leaf_spot
    '#f0883e',  # leaf_blotch
    '#f85149',  # dry_leaf
    '#58a6ff',  # rhizome_healthy
    '#bc8cff',  # rhizome_disease
    '#39d3c9',  # aphids
]


# ─────────────────────────────────────────────────────────────
# Core metric computations (pure NumPy)
# ─────────────────────────────────────────────────────────────

def confusion_matrix(y_true, y_pred, n=CFG.NUM_CLASSES):
    cm = np.zeros((n, n), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        cm[int(t)][int(p)] += 1
    return cm


def classification_metrics(cm):
    """Compute all classification metrics from confusion matrix."""
    n   = cm.shape[0]
    out = {}

    total   = cm.sum()
    correct = np.trace(cm)
    out['accuracy'] = correct / total if total > 0 else 0.0

    precision = np.zeros(n)
    recall    = np.zeros(n)
    f1        = np.zeros(n)
    support   = cm.sum(axis=1)

    for c in range(n):
        tp = cm[c, c]
        fp = cm[:, c].sum() - tp
        fn = cm[c, :].sum() - tp
        p  = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        r  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        precision[c] = p
        recall[c]    = r
        f1[c]        = 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    out['precision'] = precision
    out['recall']    = recall
    out['f1']        = f1
    out['support']   = support

    # Macro averages
    out['macro_precision'] = precision.mean()
    out['macro_recall']    = recall.mean()
    out['macro_f1']        = f1.mean()

    # Weighted averages
    w = support / support.sum() if support.sum() > 0 else np.ones(n) / n
    out['weighted_precision'] = (precision * w).sum()
    out['weighted_recall']    = (recall * w).sum()
    out['weighted_f1']        = (f1 * w).sum()

    # Matthews Correlation Coefficient (multi-class)
    pk = cm.sum(axis=0)
    tk = cm.sum(axis=1)
    num = total * correct - (pk * tk).sum()
    den = np.sqrt(
        max((total**2 - (pk**2).sum()), 0) *
        max((total**2 - (tk**2).sum()), 0)
    )
    out['mcc'] = num / den if den > 0 else 0.0

    # Cohen's Kappa
    p_obs  = correct / total
    p_exp  = (pk * tk).sum() / (total ** 2) if total > 0 else 0.0
    out['kappa'] = (p_obs - p_exp) / (1 - p_exp) if (1 - p_exp) > 0 else 0.0

    # Specificity per class
    specificity = np.zeros(n)
    for c in range(n):
        tp = cm[c, c]
        fn = cm[c, :].sum() - tp
        fp = cm[:, c].sum() - tp
        tn = total - tp - fp - fn
        specificity[c] = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    out['specificity'] = specificity

    return out


def segmentation_metrics(y_true, y_pred, n=CFG.NUM_CLASSES):
    """IoU, Dice, pixel accuracy from pixel-wise label arrays."""
    out = {}
    iou  = np.zeros(n)
    dice = np.zeros(n)

    for c in range(n):
        t = (y_true == c)
        p = (y_pred == c)
        inter = (t & p).sum()
        union = (t | p).sum()
        iou[c]  = inter / union if union > 0 else 1.0
        denom   = t.sum() + p.sum()
        dice[c] = 2 * inter / denom if denom > 0 else 1.0

    out['iou']        = iou
    out['dice']       = dice
    out['mean_iou']   = iou.mean()
    out['mean_dice']  = dice.mean()
    out['pixel_acc']  = (y_true == y_pred).sum() / y_true.size

    return out


# ─────────────────────────────────────────────────────────────
# Text report
# ─────────────────────────────────────────────────────────────

def print_report(clf, seg, class_names=CFG.CLASS_NAMES):
    W = 70
    print(f"\n{'═'*W}")
    print(f"  CLASSIFICATION METRICS")
    print(f"{'─'*W}")
    print(f"  {'Class':<18} {'Precision':>10} {'Recall':>10} {'F1':>10} "
          f"{'Specificity':>12} {'Support':>8}")
    print(f"{'─'*W}")
    for i, name in enumerate(class_names):
        print(f"  {name:<18} {clf['precision'][i]:>10.4f} {clf['recall'][i]:>10.4f} "
              f"{clf['f1'][i]:>10.4f} {clf['specificity'][i]:>12.4f} "
              f"{clf['support'][i]:>8.0f}")
    print(f"{'─'*W}")
    print(f"  {'Macro Avg':<18} {clf['macro_precision']:>10.4f} "
          f"{clf['macro_recall']:>10.4f} {clf['macro_f1']:>10.4f}")
    print(f"  {'Weighted Avg':<18} {clf['weighted_precision']:>10.4f} "
          f"{clf['weighted_recall']:>10.4f} {clf['weighted_f1']:>10.4f}")
    print(f"{'─'*W}")
    print(f"  Accuracy : {clf['accuracy']:.4f}   MCC : {clf['mcc']:.4f}   "
          f"Kappa : {clf['kappa']:.4f}")
    print(f"{'═'*W}")

    print(f"\n{'═'*50}")
    print(f"  SEGMENTATION METRICS (Heuristic)")
    print(f"{'─'*50}")
    print(f"  {'Class':<18} {'IoU':>8} {'Dice':>8}")
    print(f"{'─'*50}")
    for i, name in enumerate(class_names):
        print(f"  {name:<18} {seg['iou'][i]:>8.4f} {seg['dice'][i]:>8.4f}")
    print(f"{'─'*50}")
    print(f"  {'Mean':<18} {seg['mean_iou']:>8.4f} {seg['mean_dice']:>8.4f}")
    print(f"  Pixel Accuracy : {seg['pixel_acc']:.4f}")
    print(f"{'═'*50}\n")


def export_metrics_to_excel(clf, cm, save_path, class_names=CFG.CLASS_NAMES):
    """Export all classification metrics and confusion matrix into an Excel (.xlsx) file."""
    import pandas as pd

    # Sheet 1: Overall Summary Scorecard
    summary_data = {
        "Metric": [
            "Overall Accuracy",
            "Macro Precision",
            "Macro Recall",
            "Macro F1-Score",
            "Weighted Precision",
            "Weighted Recall",
            "Weighted F1-Score",
            "Matthews Correlation (MCC)",
            "Cohen's Kappa",
        ],
        "Value": [
            clf['accuracy'],
            clf['macro_precision'],
            clf['macro_recall'],
            clf['macro_f1'],
            clf['weighted_precision'],
            clf['weighted_recall'],
            clf['weighted_f1'],
            clf['mcc'],
            clf['kappa'],
        ]
    }
    df_summary = pd.DataFrame(summary_data)

    # Sheet 2: Per-Class Classification Metrics
    per_class_data = {
        "Class Name": class_names,
        "Precision": clf['precision'],
        "Recall": clf['recall'],
        "F1-Score": clf['f1'],
        "Specificity": clf['specificity'],
        "Support (Sample Count)": clf['support'],
    }
    df_per_class = pd.DataFrame(per_class_data)

    # Sheet 3: Confusion Matrix
    df_cm = pd.DataFrame(cm, index=[f"True: {c}" for c in class_names], columns=[f"Pred: {c}" for c in class_names])

    # Write to Excel workbook with multiple sheets
    with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name='Summary Metrics', index=False)
        df_per_class.to_excel(writer, sheet_name='Per-Class Metrics', index=False)
        df_cm.to_excel(writer, sheet_name='Confusion Matrix')

    print(f"  Saved Excel metrics report → {save_path}")



# ─────────────────────────────────────────────────────────────
# Plots
# ─────────────────────────────────────────────────────────────

def _style_ax(ax):
    ax.set_facecolor(P['card'])
    for s in ax.spines.values():
        s.set_edgecolor(P['border'])
    ax.tick_params(colors=P['text'], labelsize=8)
    ax.xaxis.label.set_color(P['text'])
    ax.yaxis.label.set_color(P['text'])
    ax.title.set_color(P['text'])


def plot_confusion_matrix(cm, class_names=CFG.CLASS_NAMES, save_path=None):
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor(P['bg'])
    _style_ax(ax)

    row_s = cm.sum(axis=1, keepdims=True)
    row_s[row_s == 0] = 1
    cm_n  = cm / row_s

    im = ax.imshow(cm_n, cmap='YlOrRd', vmin=0, vmax=1, aspect='auto')
    cb = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.ax.tick_params(colors=P['text'])
    cb.outline.set_edgecolor(P['border'])

    for i in range(len(class_names)):
        for j in range(len(class_names)):
            tc = 'black' if cm_n[i, j] > 0.5 else P['text']
            ax.text(j, i, f"{cm[i,j]}\n({cm_n[i,j]:.0%})",
                    ha='center', va='center', fontsize=9,
                    color=tc, fontweight='bold')

    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=20, ha='right', fontsize=9, color=P['text'])
    ax.set_yticklabels(class_names, fontsize=9, color=P['text'])
    ax.set_xlabel('Predicted', fontsize=11, color=P['text'], labelpad=8)
    ax.set_ylabel('True Label', fontsize=11, color=P['text'], labelpad=8)
    ax.set_title('Confusion Matrix', fontsize=13, fontweight='bold', pad=12)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=P['bg'])
        print(f"  Saved → {save_path}")
    plt.close()


def plot_metrics_dashboard(clf, seg, class_names=CFG.CLASS_NAMES, save_path=None):
    fig = plt.figure(figsize=(18, 11))
    fig.patch.set_facecolor(P['bg'])
    gs  = GridSpec(2, 3, figure=fig, hspace=0.5, wspace=0.38)
    axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(3)]
    for ax in axes:
        _style_ax(ax)

    n   = len(class_names)
    x   = np.arange(n)
    bw  = 0.26
    cc  = CLASS_COLORS[:n]

    # 1. Precision / Recall / F1 grouped bar
    ax = axes[0]
    for i, (vals, label, col) in enumerate(zip(
            [clf['precision'], clf['recall'], clf['f1']],
            ['Precision', 'Recall', 'F1'],
            [P['blue'], P['green'], P['yellow']])):
        bars = ax.bar(x + (i - 1) * bw, vals, bw, label=label, color=col, alpha=0.88)
        for b in bars:
            h = b.get_height()
            if h > 0.05:
                ax.text(b.get_x() + b.get_width()/2, h + 0.02,
                        f'{h:.2f}', ha='center', va='bottom', fontsize=6.5, color=P['text'])
    ax.set_xticks(x)
    ax.set_xticklabels(class_names, fontsize=7.5, color=P['text'], rotation=12)
    ax.set_ylim(0, 1.2)
    ax.set_title('Per-Class Classification Metrics', fontsize=10, fontweight='bold')
    ax.legend(facecolor=P['card'], labelcolor=P['text'], fontsize=8, framealpha=0.8)
    ax.yaxis.grid(True, color=P['grid'], alpha=0.6, linewidth=0.7)
    ax.set_axisbelow(True)

    # 2. IoU per class
    ax = axes[1]
    bars = ax.bar(x, seg['iou'], color=cc, alpha=0.88)
    ax.set_xticks(x)
    ax.set_xticklabels(class_names, fontsize=7.5, color=P['text'], rotation=12)
    ax.set_ylim(0, 1.2)
    ax.set_title('IoU per Class (Heuristic Segmentation)', fontsize=10, fontweight='bold')
    ax.axhline(seg['mean_iou'], color=P['orange'], ls='--', lw=1.5,
               label=f"Mean IoU: {seg['mean_iou']:.3f}")
    ax.legend(facecolor=P['card'], labelcolor=P['text'], fontsize=8)
    ax.yaxis.grid(True, color=P['grid'], alpha=0.6, linewidth=0.7)
    ax.set_axisbelow(True)
    for b, v in zip(bars, seg['iou']):
        ax.text(b.get_x() + b.get_width()/2, v + 0.02,
                f'{v:.3f}', ha='center', va='bottom', fontsize=8, color=P['text'])

    # 3. Dice per class
    ax = axes[2]
    bars = ax.bar(x, seg['dice'], color=cc, alpha=0.88)
    ax.set_xticks(x)
    ax.set_xticklabels(class_names, fontsize=7.5, color=P['text'], rotation=12)
    ax.set_ylim(0, 1.2)
    ax.set_title('Dice Score per Class', fontsize=10, fontweight='bold')
    ax.axhline(seg['mean_dice'], color=P['purple'], ls='--', lw=1.5,
               label=f"Mean Dice: {seg['mean_dice']:.3f}")
    ax.legend(facecolor=P['card'], labelcolor=P['text'], fontsize=8)
    ax.yaxis.grid(True, color=P['grid'], alpha=0.6, linewidth=0.7)
    ax.set_axisbelow(True)
    for b, v in zip(bars, seg['dice']):
        ax.text(b.get_x() + b.get_width()/2, v + 0.02,
                f'{v:.3f}', ha='center', va='bottom', fontsize=8, color=P['text'])

    # 4. Summary scorecard
    ax = axes[3]
    ax.axis('off')
    ax.set_title('Summary Scorecard', fontsize=10, fontweight='bold',
                 color=P['text'], pad=6)
    rows = [
        ('Accuracy',            clf['accuracy']),
        ('Macro Precision',     clf['macro_precision']),
        ('Macro Recall',        clf['macro_recall']),
        ('Macro F1-Score',      clf['macro_f1']),
        ('Weighted F1',         clf['weighted_f1']),
        ('MCC',                 clf['mcc']),
        ('Cohen\'s Kappa',      clf['kappa']),
        ('Pixel Accuracy',      seg['pixel_acc']),
        ('Mean IoU (mIoU)',     seg['mean_iou']),
        ('Mean Dice',           seg['mean_dice']),
    ]
    for i, (label, val) in enumerate(rows):
        y = 0.94 - i * 0.094
        c = P['green'] if val >= 0.8 else P['yellow'] if val >= 0.6 else P['red']
        ax.text(0.04, y, label, transform=ax.transAxes,
                fontsize=9, color=P['subtext'], va='center')
        ax.text(0.97, y, f'{val:.4f}', transform=ax.transAxes,
                fontsize=10, color=c, va='center', ha='right', fontweight='bold')
        if i < len(rows) - 1:
            ax.axhline(y=y - 0.042, color=P['grid'], linewidth=0.5, alpha=0.6)

    # 5. F1 horizontal bar
    ax = axes[4]
    yp = np.arange(n)
    bars = ax.barh(yp, clf['f1'], color=cc, alpha=0.88)
    ax.set_xlim(0, 1.15)
    ax.set_yticks(yp)
    ax.set_yticklabels(class_names, fontsize=9, color=P['text'])
    ax.set_title('F1-Score per Class', fontsize=10, fontweight='bold')
    ax.xaxis.grid(True, color=P['grid'], alpha=0.6, linewidth=0.7)
    ax.set_axisbelow(True)
    for b in bars:
        w = b.get_width()
        ax.text(w + 0.01, b.get_y() + b.get_height()/2,
                f'{w:.4f}', va='center', fontsize=9, color=P['text'])

    # 6. Support distribution
    ax = axes[5]
    bars = ax.bar(x, clf['support'], color=cc, alpha=0.88)
    ax.set_xticks(x)
    ax.set_xticklabels(class_names, fontsize=7.5, color=P['text'], rotation=12)
    ax.set_title('Test Sample Distribution', fontsize=10, fontweight='bold')
    ax.yaxis.grid(True, color=P['grid'], alpha=0.6, linewidth=0.7)
    ax.set_axisbelow(True)
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width()/2, h + 0.3,
                str(int(h)), ha='center', va='bottom', fontsize=9, color=P['text'])

    fig.suptitle('Turmeric Disease Detection — Full Evaluation Report',
                 fontsize=14, fontweight='bold', color=P['text'], y=1.01)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=P['bg'])
        print(f"  Saved → {save_path}")
    plt.close()


def plot_training_history(history, title='', save_path=None):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.patch.set_facecolor(P['bg'])
    for ax in axes:
        _style_ax(ax)

    epochs = range(1, len(history.get('loss', [])) + 1)

    # Loss
    ax = axes[0]
    if 'loss'     in history: ax.plot(epochs, history['loss'],     color=P['blue'],   lw=2, label='Train',      marker='o', ms=3)
    if 'val_loss' in history: ax.plot(epochs, history['val_loss'], color=P['orange'], lw=2, label='Validation', marker='s', ms=3, ls='--')
    ax.set_title(f'{title} Loss', fontsize=12, fontweight='bold')
    ax.set_xlabel('Epoch'); ax.set_ylabel('Loss')
    ax.legend(facecolor=P['card'], labelcolor=P['text'])
    ax.yaxis.grid(True, color=P['grid'], alpha=0.5); ax.set_axisbelow(True)

    # Accuracy
    ax = axes[1]
    akey  = 'accuracy' if 'accuracy' in history else 'acc'
    vakey = 'val_accuracy' if 'val_accuracy' in history else 'val_acc'
    if akey  in history: ax.plot(epochs, history[akey],  color=P['green'],  lw=2, label='Train',      marker='o', ms=3)
    if vakey in history: ax.plot(epochs, history[vakey], color=P['yellow'], lw=2, label='Validation', marker='s', ms=3, ls='--')
    ax.set_title(f'{title} Accuracy', fontsize=12, fontweight='bold')
    ax.set_xlabel('Epoch'); ax.set_ylabel('Accuracy')
    ax.set_ylim(0, 1.05)
    ax.legend(facecolor=P['card'], labelcolor=P['text'])
    ax.yaxis.grid(True, color=P['grid'], alpha=0.5); ax.set_axisbelow(True)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor=P['bg'])
        print(f"  Saved → {save_path}")
    plt.close()
