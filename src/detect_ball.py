import cv2 as cv
import os
from ultralytics import YOLO


def detect(image):
    detect_ = False
    x = 0
    y = 0
    w = 0
    h = 0

    # Import model
    path = os.path.dirname(__file__)[:-4]
    print("Load model")
    model = YOLO(path + "/YOLODataset_simimages/Yolov8/best.pt", task="detect")
    print("Model loaded")
    # Prediction
    results = model(image, device="cpu")

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


if __name__ == "__main__":
    path = os.path.dirname(__file__)[:-12]
    print(path)
    image = cv.imread(path + "imgs/out_11212.ppm")
    image, detect_, x, y, w, h = detect(image)
    cv.imshow("image", image)
    cv.waitKey(0)
    cv.destroyAllWindows()
