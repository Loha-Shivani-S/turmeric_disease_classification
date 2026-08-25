"""
config.py — Central configuration for Turmeric Disease Detection
Edit DATASET_DIR to point to your dataset folder.
"""

import os
os.environ["KERAS_BACKEND"] = "torch"

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR  = os.path.join(BASE_DIR, "dataset")       # Root folder containing class sub-folders
MODEL_DIR    = os.path.join(BASE_DIR, "saved_models")  # Where trained weights are saved
RESULTS_DIR  = os.path.join(BASE_DIR, "results")       # Where plots/reports are saved

# ─────────────────────────────────────────────────────────────
# CLASS NAMES  (must match your folder names exactly)
# ─────────────────────────────────────────────────────────────
CLASS_NAMES = [
    "healthy",
    "leaf_spot",
    "leaf_blotch",
    "dry_leaf",
    "rhizome_healthy",
    "rhizome_disease",
    "aphids",
]
NUM_CLASSES = len(CLASS_NAMES)
HEALTHY_CLASS_NAMES = ("healthy", "rhizome_healthy")

# ─────────────────────────────────────────────────────────────
# IMAGE SETTINGS
# ─────────────────────────────────────────────────────────────
IMG_SIZE    = 224          # Resize all images to IMG_SIZE × IMG_SIZE
IMG_CHANNELS = 3

# ─────────────────────────────────────────────────────────────
# TRAINING SETTINGS
# ─────────────────────────────────────────────────────────────
BATCH_SIZE   = 16
CLF_EPOCHS   = 50          # MobileNet epochs
UNET_EPOCHS  = 25          # UNet epochs
TRAIN_UNET   = False       # Fast training: use instant heuristic segmentation (no UNet training)
LEARNING_RATE = 1e-3
FINE_TUNE_LEARNING_RATE = 1e-5
VAL_SPLIT    = 0.15        # 15% validation
TEST_SPLIT   = 0.15        # 15% test
RANDOM_SEED  = 42
REQUIRE_GPU = True         # Stop training if PyTorch/Keras cannot see a CUDA GPU
MIXED_PRECISION = True     # Uses Tensor Cores on supported NVIDIA GPUs

# ─────────────────────────────────────────────────────────────
# AUGMENTATION
# ─────────────────────────────────────────────────────────────
AUGMENT = True             # Enable data augmentation during training

# ─────────────────────────────────────────────────────────────
# MODEL
# ─────────────────────────────────────────────────────────────
MOBILENET_ALPHA = 1.0      # Width multiplier: 0.25 / 0.5 / 0.75 / 1.0
USE_IMAGENET_WEIGHTS = True
FINE_TUNE_AT = 100         # Unfreeze MobileNetV2 layers from this index after warmup
UNET_BASE_FILTERS = 48     # Enhanced filter capacity for UNet segmentation

# Auto-create dirs
for d in [MODEL_DIR, RESULTS_DIR]:
    os.makedirs(d, exist_ok=True)
