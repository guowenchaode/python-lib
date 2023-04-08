# Example 7.6 MobileNet SSD Object Detection
# Modified based on:
# https://www.pyimagesearch.com/2017/09/18/real-time-object-detection-with-deep-learning-a
# import the necessary packages
from imutils.video import VideoStream
from imutils.video import FPS
import numpy as np
import argparse
import imutils
import time
import cv2

prototxt = r'D:\Git\github\python-lib\MobileNetSSD_deploy.prototxt'
model = r'D:\Git\github\python-lib\MobileNetSSD_deploy.caffemodel'
confidence = 0.8
CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
           "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
           "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
           "sofa", "train", "tvmonitor"]


def detect_person(image_path, show_image=False):
    COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))
    net = cv2.dnn.readNetFromCaffe(prototxt, model)
    frame = cv2.imread(image_path)

    frame = imutils.resize(frame, width=700)
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)),
                                 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()
    fps = FPS().start()

    types = []
    for i in np.arange(0, detections.shape[2]):
        conf = detections[0, 0, i, 2]
        if conf > confidence:
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            object_type = CLASSES[idx]
            conf = conf * 100
            label = "{}: {:.2f}%".format(object_type, conf)
            types.append(object_type)
            print(f'Found Object: [{label}]')

            if show_image:
                cv2.rectangle(frame, (startX, startY), (endX, endY),
                              COLORS[idx], 2)
                y = startY - 15 if startY - 15 > 15 else startY + 15
                cv2.putText(frame, label, (startX, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)
                cv2.imshow("Frame", frame)

    if show_image:
        fps.update()
        cv2.waitKey(0)
    return types


if __name__ == "__main__":
    image_path = r"X:\WD-PHONE\Camera\person-face/IMG_20220708_153326.jpg"
    detect_person(image_path, True)
