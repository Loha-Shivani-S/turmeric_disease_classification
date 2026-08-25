FROM python:3.10-slim

# Set working directory
WORKDIR /code

# Install system dependencies required by OpenCV and image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt /code/requirements.txt

# Install PyTorch CPU and Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy all application code into container
COPY . /code/

# Create directory for uploads with appropriate permissions
RUN mkdir -p /code/temp_uploads /code/saved_models && chmod -R 777 /code/temp_uploads /code/saved_models

# Set environment variables for Keras Torch Backend
ENV KERAS_BACKEND=torch
ENV PORT=7860

# Expose Hugging Face default port 7860
EXPOSE 7860

# Start Gunicorn server on port 7860
CMD ["gunicorn", "--workers=1", "--threads=2", "--timeout=300", "--bind", "0.0.0.0:7860", "app:app"]
