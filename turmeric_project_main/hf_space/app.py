import os
import sys
import numpy as np
import cv2
import gradio as gr
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

def process_file_and_predict(file_path):
    res = predict_image(file_path, save_report=False)
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

# Create FastAPI app with CORS enabled
app = FastAPI(title="TurmeriCare ML API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "Hugging Face Gradio + FastAPI Backend"}

@app.post("/predict")
async def api_predict(image: UploadFile = File(...)):
    temp_path = os.path.join(ROOT, "temp_hf_api_upload.jpg")
    try:
        contents = await image.read()
        with open(temp_path, "wb") as f:
            f.write(contents)
        result = process_file_and_predict(temp_path)
        return JSONResponse(content=result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def gradio_predict(img):
    if img is None:
        return {"error": "No image uploaded"}
    temp_path = os.path.join(ROOT, "temp_gradio_input.jpg")
    try:
        if isinstance(img, np.ndarray):
            cv2.imwrite(temp_path, cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        else:
            img.save(temp_path)
        return process_file_and_predict(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

demo = gr.Interface(
    fn=gradio_predict,
    inputs=gr.Image(type="numpy", label="Upload Turmeric Leaf Image"),
    outputs=gr.JSON(label="Prediction Result"),
    title="TurmeriCare ML Disease Classification API",
    description="Fast AI Disease Diagnosis API for Turmeric Plants"
)

# Mount Gradio app onto FastAPI root
app = gr.mount_gradio_app(app, demo, path="/ui")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
