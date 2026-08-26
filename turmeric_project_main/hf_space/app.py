import spaces
import os
import sys
import numpy as np
import cv2
import gradio as gr

# Ensure project root is in python path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ["KERAS_BACKEND"] = "torch"
import keras

classes_to_patch = [
    keras.layers.Layer,
    keras.layers.Dense,
    keras.layers.BatchNormalization,
    keras.layers.Conv2D,
    keras.layers.DepthwiseConv2D
]

for cls in classes_to_patch:
    orig_fn = cls.__init__
    def make_patched(fn):
        def patched(self, *args, **kwargs):
            kwargs.pop('renorm', None)
            kwargs.pop('renorm_clipping', None)
            kwargs.pop('renorm_momentum', None)
            kwargs.pop('quantization_config', None)
            fn(self, *args, **kwargs)
        return patched
    cls.__init__ = make_patched(orig_fn)

import config as CFG

# Auto-download model weights from Hugging Face if missing
HF_REPO_ID = "loni-lolita/turmeric-disease-model"
MODEL_FILENAME = "mobilenet_final.keras"

def download_model_if_needed():
    os.makedirs(CFG.MODEL_DIR, exist_ok=True)
    clf_path = os.path.join(CFG.MODEL_DIR, MODEL_FILENAME)
    if os.path.exists(clf_path):
        print(f"  ✓ Model already exists at: {clf_path}")
        return

    print(f"  Downloading model from Hugging Face: {HF_REPO_ID}/{MODEL_FILENAME} to {CFG.MODEL_DIR}")
    try:
        from huggingface_hub import hf_hub_download
        downloaded_path = hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=MODEL_FILENAME,
            local_dir=CFG.MODEL_DIR
        )
        print(f"  ✓ Model downloaded to: {downloaded_path}")
    except Exception as e:
        print(f"  ✗ Model download failed: {e}")

download_model_if_needed()

from predict import predict_image

@spaces.GPU
def predict(image):
    if image is None:
        return {"error": "No image uploaded"}
    temp_path = os.path.join(ROOT, "temp_gradio_input.jpg")
    try:
        if isinstance(image, np.ndarray):
            cv2.imwrite(temp_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        else:
            image.save(temp_path)
            
        res = predict_image(temp_path, save_report=False)
        frontend_mapping = {
            "healthy":          "Healthy Leaf",
            "leaf_spot":        "Leaf Spot",
            "leaf_blotch":      "Leaf Blotch",
            "dry_leaf":         "Dry Leaf",
            "rhizome_healthy":  "Healthy Rhizome",
            "rhizome_disease":  "Rhizome Rot",
            "aphids":           "Aphids"
        }
        disease = frontend_mapping.get(res['predicted_label'], res['predicted_label'])
        return {
            "disease":    disease,
            "confidence": float(res['confidence']),
            "severity":   res['severity_label'],
            "coverage":   float(res['disease_coverage']),
            "raw_result": res
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

demo = gr.Interface(
    fn=predict,
    inputs=gr.Image(type="numpy", label="Upload Turmeric Leaf Image"),
    outputs=gr.JSON(label="Prediction Result"),
    title="TurmeriCare ML Disease Classification API",
    description="Fast AI Disease Diagnosis API for Turmeric Plants"
)

demo.launch()
