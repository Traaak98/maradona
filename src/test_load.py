import torch
from PIL import Image
import numpy as np

# Function to load the model
def load_model(model_path):
    model = torch.load(model_path)
    model.eval()  # Set the model to evaluation mode
    return model

# Function to preprocess the image before feeding it to the model
def preprocess_image(image_path):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((224, 224))  # Resize to the model's expected input size
    img = np.array(img).astype(np.float32) / 255.0  # Convert to a NumPy array and normalize
    img = np.transpose(img, (2, 0, 1))  # Transpose the image to (channels, height, width)
    img = np.expand_dims(img, axis=0)  # Add a batch dimension
    return torch.tensor(img)

# Load the model
model_path = "/media/apolline/B2C2CC8EC2CC586D/apolline/Ecole/ENSTA/M2/UE52-VS-IK/maradona/YOLODataset_simimages/Yolov8/best.pt"
model = load_model(model_path)

# Load the image and preprocess it
# image_path = "/media/apolline/B2C2CC8EC2CC586D/apolline/Ecole/ENSTA/M2/UE52-VS-IK/maradona/YOLODataset_simimages/data/Ball/images/val/naoreal_0126.png"
# input_image = preprocess_image(image_path)

# Run the model
# output = model(input_image)