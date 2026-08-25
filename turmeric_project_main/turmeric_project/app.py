import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Allow ALL origins explicitly (needed for Vercel → Render cross-origin calls)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"]
    }
})

# Handle preflight OPTIONS requests globally
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
        return response

UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ─────────────────────────────────────────────────────────────
# Auto-download model from Hugging Face if not present locally
# ─────────────────────────────────────────────────────────────
HF_REPO_ID = "loni-lolita/turmeric-disease-model"
MODEL_FILENAME = "mobilenet_final.keras"

def download_model_if_needed():
    """Download model from Hugging Face Hub if not already present locally."""
    clf_path = os.path.join("saved_models", MODEL_FILENAME)
    if os.path.exists(clf_path):
        print(f"  ✓ Model already exists at: {clf_path}")
        return

    print(f"  Downloading model from Hugging Face: {HF_REPO_ID}/{MODEL_FILENAME}")
    os.makedirs("saved_models", exist_ok=True)
    try:
        from huggingface_hub import hf_hub_download
        downloaded_path = hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=MODEL_FILENAME,
            local_dir="saved_models",
            local_dir_use_symlinks=False
        )
        print(f"  ✓ Model downloaded to: {downloaded_path}")
    except Exception as e:
        print(f"  ✗ Model download failed: {e}")
        raise RuntimeError(
            f"Could not download model from Hugging Face ({HF_REPO_ID}). "
            "Please ensure the repo is public and the file exists."
        ) from e

# Download model at server startup
download_model_if_needed()

# Now import predict (which loads the model)
from predict import predict_image
import config as CFG

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model': MODEL_FILENAME})

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        result = predict_image(filepath, save_report=False)

        # Map Python class names to user-friendly display names
        frontend_mapping = {
            "healthy":          "Healthy Leaf",
            "leaf_spot":        "Leaf Spot",
            "leaf_blotch":      "Leaf Blotch",
            "dry_leaf":         "Dry Leaf",
            "rhizome_healthy":  "Healthy Rhizome",
            "rhizome_disease":  "Rhizome Rot",
            "aphids":           "Aphids"
        }

        frontend_disease = frontend_mapping.get(
            result['predicted_label'], result['predicted_label']
        )

        os.remove(filepath)

        return jsonify({
            "disease":    frontend_disease,
            "confidence": result['confidence'],
            "severity":   result['severity_label'],
            "coverage":   result['disease_coverage'],
            "raw_result": result
        })

    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🌿 TurmeriCare ML Backend running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
