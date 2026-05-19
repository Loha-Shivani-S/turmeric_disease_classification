# 🌿 Turmeric Disease Detection
### UNet Segmentation + MobileNet Classification — Trained on YOUR Dataset

---

## 📁 Project Structure

```
turmeric_project/
├── config.py               ← ⚙️  EDIT THIS FIRST (paths, settings)
├── train.py                ← 🏋️  Run to train both models
├── predict.py              ← 🔍  Run to predict a single image
│
├── models/
│   ├── unet.py             ← UNet segmentation (from scratch)
│   └── mobilenet.py        ← MobileNet V1 classifier (from scratch)
│
├── utils/
│   ├── dataloader.py       ← Loads your dataset, augments, splits
│   └── metrics.py          ← Confusion matrix, F1, IoU, Dice etc.
│
├── saved_models/           ← Auto-created: trained model weights saved here
├── results/                ← Auto-created: plots + prediction reports here
└── requirements.txt
```

---

## 🚀 Quick Start

### Step 1 — Install requirements
```bash
pip install -r requirements.txt
```

### Step 2 — Organise your dataset
```
dataset/
    healthy/
        img001.jpg
        img002.jpg
        ...
    leaf_spot/
        img001.jpg
        ...
    leaf_blotch/
        ...
    dry_leaf/
        ...
    rhizome_rot/
        ...
```

### Step 3 — Edit config.py
```python
DATASET_DIR = "dataset"    # ← Path to your dataset root folder
```

### Step 4 — Train
```bash
python train.py
```
This will:
- Load all images from your folders
- Split into Train / Validation / Test (70% / 15% / 15%)
- Apply data augmentation on the training set
- Train UNet (segmentation) + MobileNet (classification) from scratch
- Save best model weights to `saved_models/`
- Evaluate on the test set and print full metrics
- Save plots to `results/`

### Step 5 — Predict an unknown image
```bash
python predict.py path/to/unknown_leaf.jpg
```
Output:
```
═══════════════════════════════════════════════════════
  DISEASE PREDICTION RESULT
───────────────────────────────────────────────────────
  Predicted Disease  : Leaf Spot
  Confidence         : 94.72%
  Severity           : Moderate
  Disease Coverage   : 12.3% of image
───────────────────────────────────────────────────────
  All class scores:
    healthy            2.15%  ████
    leaf_spot         94.72%  ██████████████████████ ←
    leaf_blotch        1.83%  ███
    dry_leaf           0.73%  █
    rhizome_rot        0.57%  █
═══════════════════════════════════════════════════════
```
A visual report PNG is also saved to `results/prediction_<filename>.png`

---

## 📊 Metrics Generated After Training

| Metric | Description |
|--------|-------------|
| **Accuracy** | Overall correct / total |
| **Precision** | TP / (TP + FP) per class |
| **Recall** | TP / (TP + FN) per class |
| **F1-Score** | Harmonic mean of Precision & Recall |
| **Specificity** | TN / (TN + FP) per class |
| **MCC** | Matthews Correlation Coefficient |
| **Cohen's Kappa** | Agreement above chance |
| **IoU** | Intersection over Union per class (UNet) |
| **Dice Score** | 2×TP / (2×TP+FP+FN) per class (UNet) |
| **Pixel Accuracy** | Correct pixels / total pixels (UNet) |

### Output files in `results/`:
| File | Contents |
|------|---------|
| `confusion_matrix.png` | Normalized confusion matrix |
| `metrics_dashboard.png` | Full 6-panel metrics dashboard |
| `mobilenet_history.png` | MobileNet loss/accuracy curves |
| `unet_history.png` | UNet loss/accuracy curves |
| `prediction_<name>.png` | Visual report per predicted image |

---

## ⚙️ Configuration Options (`config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `DATASET_DIR` | `"dataset"` | Root folder of your images |
| `CLASS_NAMES` | 5 classes | Must match your folder names exactly |
| `IMG_SIZE` | `224` | Resize images to this (pixels) |
| `BATCH_SIZE` | `16` | Training batch size |
| `CLF_EPOCHS` | `30` | Max epochs for MobileNet |
| `UNET_EPOCHS` | `20` | Max epochs for UNet |
| `LEARNING_RATE` | `1e-3` | Initial learning rate |
| `MOBILENET_ALPHA` | `1.0` | Width: 0.25 / 0.5 / 0.75 / 1.0 |
| `AUGMENT` | `True` | Enable data augmentation |

---

## 🏗️ Architecture Details

### MobileNet V1 (Classification)
- Standard Conv (32, /2) → 13 Depthwise-Separable blocks → GlobalAvgPool → Dense(512) → Softmax
- Filters: 64 → 128 → 256 → 512 → 1024
- Loss: Sparse Categorical Cross-Entropy with label smoothing

### UNet (Segmentation)
- Encoder: 4 stages [64 → 128 → 256 → 512] + MaxPool
- Bottleneck: 1024 filters
- Decoder: 4 upsampling stages + skip connections
- Loss: Dice + Sparse Categorical Cross-Entropy (50/50)

---

## 🔄 Using in Python code
```python
from predict import predict_image

result = predict_image("leaf.jpg")
print(result['predicted_label'])   # "leaf_spot"
print(result['confidence'])        # 0.9472
print(result['severity_label'])    # "Moderate"
print(result['all_scores'])        # dict of all class probabilities
```
