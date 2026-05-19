"""
dataloader.py
Loads turmeric images from folder structure:

    dataset/
        healthy/         img1.jpg, img2.jpg ...
        leaf_spot/       img1.jpg ...
        leaf_blotch/     ...
        dry_leaf/        ...
        rhizome_healthy/ ...
        rhizome_disease/ ...
        aphids/          ...

Returns numpy arrays ready for training.
No synthetic generation — uses YOUR images only.
"""

import os
import sys
os.environ["KERAS_BACKEND"] = "torch"
import numpy as np
import cv2
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as CFG


# ─────────────────────────────────────────────────────────────
# Image loading
# ─────────────────────────────────────────────────────────────

def load_image(path, img_size=CFG.IMG_SIZE):
    """Load and resize a single image. Returns float32 array in [0,1]."""
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Could not read image: {path}")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (img_size, img_size), interpolation=cv2.INTER_AREA)
    return img.astype(np.float32) / 255.0


def generate_leaf_mask(image):
    """Create a generic leaf mask from an RGB image in [0, 1]."""
    img_uint8 = (np.clip(image, 0.0, 1.0) * 255).astype(np.uint8)
    hsv = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2HSV)

    green_mask = cv2.inRange(
        hsv,
        np.array([25, 25, 20], dtype=np.uint8),
        np.array([100, 255, 255], dtype=np.uint8)
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel, iterations=1)

    if green_mask.sum() == 0:
        gray = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2GRAY)
        _, green_mask = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
        green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    return green_mask > 0


def apply_leaf_segmentation(image, background=0.35):
    """Keep the leaf region and gray out the background."""
    mask = generate_leaf_mask(image)
    bg = np.full_like(image, background, dtype=np.float32)
    segmented = np.where(mask[..., np.newaxis], image, bg)
    return np.clip(segmented, 0.0, 1.0), mask


def segment_images_for_classification(images):
    """Segment a batch of images before classification training/inference."""
    segmented = [apply_leaf_segmentation(img)[0] for img in images]
    return np.ascontiguousarray(np.array(segmented, dtype=np.float32))


def scan_dataset(dataset_dir, class_names):
    """
    Scan dataset folder. Returns list of (image_path, class_index) tuples.
    Prints a summary table of images found per class.
    """
    dataset_dir = Path(dataset_dir)
    if not dataset_dir.exists():
        raise FileNotFoundError(
            f"\n[ERROR] Dataset folder not found: {dataset_dir.resolve()}\n"
            f"Please set DATASET_DIR in config.py to your dataset root.\n"
            f"Expected structure:\n"
            f"  {dataset_dir}/\n"
            + "\n".join(f"    {c}/" for c in class_names)
        )

    samples = []
    print(f"\n{'─'*50}")
    print(f"  Scanning dataset: {dataset_dir.resolve()}")
    print(f"{'─'*50}")

    missing_or_empty = []
    for idx, cls in enumerate(class_names):
        cls_dir = dataset_dir / cls
        if not cls_dir.exists():
            print(f"  ⚠  {cls:<20} → folder not found, skipping")
            missing_or_empty.append(cls)
            continue

        imgs = sorted([
            p for p in cls_dir.iterdir()
            if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif')
        ])
        if not imgs:
            print(f"  ⚠  {cls:<20} → 0 images found")
            missing_or_empty.append(cls)
            continue

        for p in imgs:
            samples.append((p, idx))
        print(f"  ✓  {cls:<20} → {len(imgs):>4} images  (class {idx})")

    print(f"{'─'*50}")
    print(f"  Total: {len(samples)} images across {len(class_names)} classes")
    print(f"{'─'*50}\n")

    if missing_or_empty:
        raise RuntimeError(
            "Every configured class needs at least one image before training.\n"
            f"Missing or empty class folders: {missing_or_empty}\n"
            f"Add images under: {dataset_dir.resolve()}"
        )

    if not samples:
        raise RuntimeError(
            f"No images found in {dataset_dir}. "
            f"Check that your folder names match CLASS_NAMES in config.py:\n"
            f"  {class_names}"
        )
    return samples


# ─────────────────────────────────────────────────────────────
# Augmentation (from scratch, NumPy + OpenCV)
# ─────────────────────────────────────────────────────────────

def augment_image(img):
    """
    Apply random augmentations to a single image (H,W,3) float32 in [0,1].
    All operations done in NumPy/OpenCV — no external augmentation library.
    """
    h, w = img.shape[:2]
    img = (img * 255).astype(np.uint8)

    # Horizontal flip
    if np.random.rand() < 0.5:
        img = cv2.flip(img, 1)

    # Vertical flip
    if np.random.rand() < 0.3:
        img = cv2.flip(img, 0)

    # Random rotation ±20°
    if np.random.rand() < 0.5:
        angle = np.random.uniform(-20, 20)
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)

    # Random brightness/contrast
    if np.random.rand() < 0.5:
        alpha = np.random.uniform(0.7, 1.3)   # contrast
        beta  = np.random.randint(-30, 30)     # brightness
        img = np.clip(img.astype(np.float32) * alpha + beta, 0, 255).astype(np.uint8)

    # Random hue/saturation shift (helps with disease color variation)
    if np.random.rand() < 0.4:
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 0] = (hsv[:, :, 0] + np.random.uniform(-10, 10)) % 180
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * np.random.uniform(0.8, 1.2), 0, 255)
        img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

    # Random zoom (crop and resize back)
    if np.random.rand() < 0.3:
        scale = np.random.uniform(0.8, 1.0)
        nh, nw = int(h * scale), int(w * scale)
        y0 = np.random.randint(0, h - nh + 1)
        x0 = np.random.randint(0, w - nw + 1)
        img = cv2.resize(img[y0:y0+nh, x0:x0+nw], (w, h))

    # Gaussian blur (simulate out-of-focus)
    if np.random.rand() < 0.2:
        ksize = np.random.choice([3, 5])
        img = cv2.GaussianBlur(img, (ksize, ksize), 0)

    return img.astype(np.float32) / 255.0


# ─────────────────────────────────────────────────────────────
# Dataset split & load
# ─────────────────────────────────────────────────────────────

def split_samples(samples, val_ratio=CFG.VAL_SPLIT, test_ratio=CFG.TEST_SPLIT, seed=CFG.RANDOM_SEED):
    """Stratified split into train / val / test."""
    np.random.seed(seed)

    # Group by class
    from collections import defaultdict
    by_class = defaultdict(list)
    for path, label in samples:
        by_class[label].append((path, label))

    train_s, val_s, test_s = [], [], []
    for label, items in sorted(by_class.items()):
        n = len(items)
        idx = np.random.permutation(n)
        n_test = max(1, int(n * test_ratio))
        n_val  = max(1, int(n * val_ratio))

        test_s  += [items[i] for i in idx[:n_test]]
        val_s   += [items[i] for i in idx[n_test:n_test + n_val]]
        train_s += [items[i] for i in idx[n_test + n_val:]]

    np.random.shuffle(train_s)
    np.random.shuffle(val_s)
    np.random.shuffle(test_s)

    return train_s, val_s, test_s


def load_split(samples, augment=False, img_size=CFG.IMG_SIZE, verbose=True):
    """Load and optionally augment a list of (path, label) samples."""
    images, labels = [], []
    total = len(samples)
    for i, (path, label) in enumerate(samples):
        if verbose and (i + 1) % 100 == 0:
            print(f"    Loading {i+1}/{total}...", end='\r')
        try:
            img = load_image(path, img_size)
            if augment and CFG.AUGMENT:
                img = augment_image(img)
            images.append(img)
            labels.append(label)
        except Exception as e:
            print(f"\n    [WARN] Skipping {path}: {e}")

    if verbose:
        print(f"    Loaded {len(images)}/{total} images{'  ':20}")

    return np.array(images, dtype=np.float32), np.array(labels, dtype=np.int32)


def load_full_dataset(dataset_dir=CFG.DATASET_DIR,
                      class_names=CFG.CLASS_NAMES,
                      img_size=CFG.IMG_SIZE):
    """
    Master function: scan → split → load all three splits.
    Returns: (X_train, y_train), (X_val, y_val), (X_test, y_test)
    """
    samples = scan_dataset(dataset_dir, class_names)

    train_s, val_s, test_s = split_samples(samples)
    print(f"  Split → Train: {len(train_s)}  Val: {len(val_s)}  Test: {len(test_s)}")

    print("  Loading train set...")
    X_train, y_train = load_split(train_s, augment=False, img_size=img_size)
    print("  Loading val set...")
    X_val,   y_val   = load_split(val_s,   augment=False, img_size=img_size)
    print("  Loading test set...")
    X_test,  y_test  = load_split(test_s,  augment=False, img_size=img_size)

    print(f"\n  ✓ Dataset ready:")
    print(f"    X_train: {X_train.shape}  y_train: {y_train.shape}")
    print(f"    X_val  : {X_val.shape}  y_val  : {y_val.shape}")
    print(f"    X_test : {X_test.shape}  y_test : {y_test.shape}\n")

    return (X_train, y_train), (X_val, y_val), (X_test, y_test)


# ---------------------------------------------------------------------------
# Keras Torch-backend input helpers
# ---------------------------------------------------------------------------

def make_classification_dataset(images, labels, training=False,
                                batch_size=CFG.BATCH_SIZE):
    """Return contiguous arrays for Keras fit with the Torch backend."""
    images = segment_images_for_classification(images)
    if training and CFG.AUGMENT:
        images = np.array([augment_image(img) for img in images], dtype=np.float32)
    return np.ascontiguousarray(images), np.ascontiguousarray(labels)


def make_segmentation_dataset(images, masks, training=False,
                              batch_size=CFG.BATCH_SIZE):
    """Return contiguous arrays for Keras fit with the Torch backend."""
    return np.ascontiguousarray(images), np.ascontiguousarray(masks)


def compute_class_weights(labels, num_classes=CFG.NUM_CLASSES):
    """Balanced class weights to reduce one-class prediction collapse."""
    counts = np.bincount(labels.astype(np.int32), minlength=num_classes)
    total = counts.sum()
    weights = {}
    for cls_idx, count in enumerate(counts):
        weights[cls_idx] = float(total / (num_classes * count)) if count else 0.0
    return weights


# ─────────────────────────────────────────────────────────────
# Segmentation mask generation (auto from classification labels)
# ─────────────────────────────────────────────────────────────

def generate_seg_masks_from_labels(images, labels, img_size=CFG.IMG_SIZE,
                                   class_names=CFG.CLASS_NAMES):
    """
    Since you may not have pixel-level masks, we auto-generate them using
    color-based thresholding to segment the leaf region and mark disease areas.

    Returns seg_masks: (N, H, W) int32 array with class index per pixel.
    Healthy samples use their own healthy class index. Disease samples use
    healthy background pixels plus disease pixels marked as the class label.
    """
    N = len(images)
    masks = np.zeros((N, img_size, img_size), dtype=np.int32)
    healthy_names = set(getattr(CFG, "HEALTHY_CLASS_NAMES", ("healthy",)))
    healthy_indices = {
        i for i, name in enumerate(class_names)
        if name in healthy_names or name.endswith("_healthy")
    }
    default_healthy_idx = class_names.index("healthy") if "healthy" in class_names else 0
    rhizome_healthy_idx = (
        class_names.index("rhizome_healthy")
        if "rhizome_healthy" in class_names else default_healthy_idx
    )

    for i, (img, label) in enumerate(zip(images, labels)):
        label = int(label)
        label_name = class_names[label]
        img_uint8 = (img * 255).astype(np.uint8)

        # Convert to HSV for better color segmentation
        hsv = cv2.cvtColor(img_uint8, cv2.COLOR_RGB2HSV)

        # Segment leaf region (green hues: H=35-90 in OpenCV HSV)
        leaf_mask = cv2.inRange(hsv,
                                np.array([25, 30, 30]),
                                np.array([100, 255, 255]))

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        leaf_mask = cv2.morphologyEx(leaf_mask, cv2.MORPH_OPEN,  kernel, iterations=1)

        if label in healthy_indices:
            masks[i][leaf_mask > 0] = label
        else:
            # Disease: detect brownish/yellowish spots as disease region
            # Brown (disease): low saturation or brown hue
            disease_mask = cv2.inRange(hsv,
                                       np.array([5, 20, 20]),
                                       np.array([35, 255, 220]))
            # Yellow/necrotic
            yellow_mask  = cv2.inRange(hsv,
                                       np.array([20, 40, 100]),
                                       np.array([45, 255, 255]))
            combined = cv2.bitwise_or(disease_mask, yellow_mask)
            combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)

            bg_idx = rhizome_healthy_idx if label_name.startswith("rhizome_") else default_healthy_idx
            masks[i][leaf_mask > 0]  = bg_idx
            masks[i][combined > 0]   = label

    return masks


if __name__ == "__main__":
    # Quick test — will error if dataset folder doesn't exist yet
    try:
        (X_tr, y_tr), (X_val, y_val), (X_te, y_te) = load_full_dataset()
        print("Dataset loaded successfully!")
    except FileNotFoundError as e:
        print(e)
