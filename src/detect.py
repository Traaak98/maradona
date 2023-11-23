import cv2 as cv
from ultralytics import YOLO
import os
import numpy as np


def load_model():
    # Import model
    path = os.path.dirname(__file__)[:-4]
    print(path)
    model = YOLO(path + "/Yolov8/model/best.pt")
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
        for result in results:
            nb_detection = result.boxes.shape[0]
            for i in range(nb_detection):
                cls = int(result.boxes.cls[i].item())
                name = result.names[cls]
                if name == "ball":
                    x = result.boxes.xywh[0][0]
                    y = result.boxes.xywh[0][1]
                    w = result.boxes.xywh[0][2]
                    h = result.boxes.xywh[0][3]
                    cv.rectangle(image, (int(x - w / 2), int(y + h / 2)), (int(x + w / 2), int(y - h / 2)), (0, 255, 0),
                                 2)

    return image, detect_, x, y, w, h


def detect_goal(image, model):
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
        for result in results:
            nb_detection = result.boxes.shape[0]
            for i in range(nb_detection):
                cls = int(result.boxes.cls[i].item())
                name = result.names[cls]
                if name == "goal_corner":
                    x = np.append(x, result.boxes.xywh[0][0])
                    y = np.append(y, result.boxes.xywh[0][1])
                    w = np.append(w, result.boxes.xywh[0][2])
                    h = np.append(h, result.boxes.xywh[0][3])
                    cv.rectangle(image, (int(result.boxes.xywh[0][0] - result.boxes.xywh[0][2] / 2), int(result.boxes.xywh[0][1] + result.boxes.xywh[0][3] / 2)), (int(result.boxes.xywh[0][0] + result.boxes.xywh[0][2] / 2), int(result.boxes.xywh[0][1] - result.boxes.xywh[0][3] / 2)), (0, 255, 0),
                                 2)

    return image, detect_, x, y, w, h
