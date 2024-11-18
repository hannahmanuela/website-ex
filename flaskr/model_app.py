from flask import Blueprint
from flask import flash, g, redirect, render_template, request, url_for, jsonify
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
import os

import torch
import torchvision.transforms as transforms
from torchvision.models import resnet18, ResNet18_Weights
from PIL import Image
import io

import ctypes

from . import add_deadline

bp = Blueprint("model_app", __name__)

libc = ctypes.CDLL(None, use_errno=True)


@bp.route("/")
@add_deadline(30, ["GET"])
def index():    
    return "welcome, please go somewhere else :)"


# Load the pre-trained ResNet-18 model
model = resnet18(weights=ResNet18_Weights.DEFAULT)
model.eval()  # Set the model to evaluation mode

# Define image preprocessing transformations
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Define the ImageNet class labels (you can extend this list or load it from a file)
LABELS = {idx: label for idx, label in enumerate(open('imagenet-simple-labels.json').read().splitlines())}

@bp.route('/paying-predict', methods=['POST'])
@add_deadline(180, methods=['POST'])
def paying_predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    return predict(file)


@bp.route('/free-predict', methods=['POST'])
@add_deadline(250, methods=['POST'])
def free_predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    return predict(file)



def predict(file):

    try:
        # Open the image from the request
        img = Image.open(io.BytesIO(file.read()))
        img = img.convert("RGB")

        print("read img")

        # Preprocess the image
        img_tensor = preprocess(img).unsqueeze(0)  # Add batch dimension

        print("processed img")

        # Run inference
        with torch.no_grad():
            outputs = model(img_tensor)
            _, predicted_class = torch.max(outputs, 1)
        
        print("did class")
        
        # Convert predicted class to label
        predicted_class_idx = predicted_class.item()

        print("got idx")

        # Return the result
        return jsonify({
            'predicted_class': predicted_class_idx,
            'label': LABELS.get(predicted_class_idx, 'Unknown'),
            'confidence': torch.nn.functional.softmax(outputs, dim=1).max().item()
        })

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 500