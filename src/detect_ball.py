import cv2 as cv
from ultralytics import YOLO
import os

def detect(image):
    detect_ = False
    x = 0
    y = 0
    w = 0
    h = 0

    # Import model
    path = os.path.dirname(__file__)[:-4]
    model = YOLO(path + "/best.pt")

    # Prediction
    results = model(image)

    # Affichage
    if results[0].boxes:
        detect_ = True
        for box in results[0].boxes:
            x = box.xywh[0][0]
            y = box.xywh[0][1]
            w = box.xywh[0][2]
            h = box.xywh[0][3]
            cv.rectangle(image, (int(x - w / 2), int(y + h / 2)), (int(x + w / 2), int(y - h / 2)), (0, 255, 0),
                         2)

    return image, detect_, x, y, w, h
