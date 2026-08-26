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
