import cv2 as cv
from ultralytics import YOLO
import os
import numpy as np


def load_model():
    # Import model
    path = os.path.dirname(__file__)[:-4]
    model = YOLO(path + "/best.pt")
    return model


def detect_ball(image, model):
    detect_ = False
    x = 0
    y = 0
    w = 0
    h = 0

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


def detetc_ball(image, model):
    detect_ = False
    x = np.array([])
    y = np.array([])
    w = np.array([])
    h = np.array([])

    # Prediction
    results = model(image)

    # Affichage
    if results[0].boxes:
        detect_ = True
        for box in results[0].boxes:
            x = np.append(x, box.xywh[0][0])
            y = np.append(y, box.xywh[0][1])
            w = np.append(w, box.xywh[0][2])
            h = np.append(h, box.xywh[0][3])
            cv.rectangle(image, (int(x - w / 2), int(y + h / 2)), (int(x + w / 2), int(y - h / 2)), (0, 255, 0),
                         2)

    return image, detect_, x, y, w, h
