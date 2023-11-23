import cv2 as cv
from ultralytics import YOLO
import torch
import os
import numpy as np
import time as time


def load_model():
    # Import model
    path = os.getcwd()[0:-4]
    # print(path)
    model = YOLO(path + "/Yolov8/model/best.pt")

    # Load image for first prediction
    path = os.getcwd()[0:-12]
    image = cv.imread(path + "imgs/out_11212.ppm")
    # t0 = time.time()
    # print("Avant 1ere prediction")
    model(image)
    # t1 = time.time() - t0
    # print("Apres 1ere prediction : ", t1)
    return model


def detect_ball(image, model):
    detect_ = False
    x = 0
    y = 0
    w = 0
    h = 0

    # Prediction
    # t0 = time.time()
    # print("Avant prediction")
    # results = model.predict(image, imgsz=(160, 120), device='cpu', max_det=1)
    results = model(image)
    # t1 = time.time()
    # print("Temps prediction : ", t1 - t0)

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
    # t2 = time.time()
    # print("Temps affichage : ", t2 - t1)
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


if __name__ == "__main__":
    model = load_model()
    path = os.getcwd()[0:-12]
    image = cv.imread(path + "imgs/out_11212.ppm")
    detect_ball(image, model)
