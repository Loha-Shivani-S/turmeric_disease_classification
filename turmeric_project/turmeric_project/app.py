import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from predict import predict_image
import config as CFG

app = Flask(__name__)
# Enable CORS for all routes so the React frontend can call this API
CORS(app)

UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Run the prediction from the model
            result = predict_image(filepath, save_report=False)
            
            # Map Python classes to Frontend display names
            frontend_mapping = {
                "healthy": "Healthy Leaf",
                "leaf_spot": "Leaf Spot",
                "leaf_blotch": "Leaf Blotch",
                "dry_leaf": "Dry Leaf",
                "rhizome_healthy": "Healthy Rhizome",
                "rhizome_disease": "Rhizome Rot",
                "aphids": "Aphids"
            }
            
            frontend_disease = frontend_mapping.get(result['predicted_label'], result['predicted_label'])
            
            # Remove the temp file
            os.remove(filepath)
            
            return jsonify({
                "disease": frontend_disease,
                "confidence": result['confidence'],
                "severity": result['severity_label'],
                "coverage": result['disease_coverage'],
                "raw_result": result
            })
            
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌿 TurmeriCare ML Backend Started!")
    app.run(host='0.0.0.0', port=5000, debug=False)
