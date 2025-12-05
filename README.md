# YOLO Fire Detection API

This project provides a RESTful API for detecting fire in images using YOLO (You Only Look Once) models. It is built with FastAPI and Ultralytics YOLO.

## Features

*   **Object Detection**: Utilizes YOLO models to detect fire in uploaded images.
*   **Result Annotation**: Automatically draws bounding boxes around detected objects and saves the annotated images.
*   **RESTful Interface**: Simple and efficient API endpoints for integration.
*   **Docker Support**: Containerized for easy deployment.

## Prerequisites

*   Python 3.10 or higher
*   Docker (optional, for containerized deployment)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd iot_api
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Model Setup:**
    Place your trained YOLO model file (e.g., `best.pt`) in the `models/` directory.
    *   Default path: `models/best.pt`
    *   This can be configured in `app/config.py` or via environment variables.

## Usage

### Running Locally

Start the application using Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

### Running with Docker

1.  **Build the Docker image:**
    ```bash
    docker build -t fire-detection-api .
    ```

2.  **Run the container:**
    ```bash
    docker run -p 8000:8000 fire-detection-api
    ```

## API Documentation

### POST /predict

Uploads an image for fire detection.

**Request:**
*   `file`: The image file to be analyzed (multipart/form-data).

**Response:**
Returns a JSON object containing:
*   `filename`: Name of the processed file.
*   `detections`: List of detected objects with bounding box coordinates and confidence scores.
*   `message`: Summary message.
*   `annotated_image_url`: URL to access the image with drawn bounding boxes.

**Example:**

```bash
curl -X POST "http://localhost:8000/predict" -F "file=@/path/to/image.jpg"
```

### Interactive Documentation

Access the interactive API documentation (Swagger UI) at:
`http://localhost:8000/docs`
