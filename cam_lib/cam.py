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
from cam_lib.cam_qr import process_qr
import traceback

prototxt = r"D:\Git\github\python-lib\MobileNetSSD_deploy.prototxt"
model = r"D:\Git\github\python-lib\MobileNetSSD_deploy.caffemodel"
confidence = 0.9
CLASSES = [
    "background",
    "aeroplane",
    "bicycle",
    "bird",
    "boat",
    "bottle",
    "bus",
    "car",
    "cat",
    "chair",
    "cow",
    "diningtable",
    "dog",
    "horse",
    "motorbike",
    "person",
    "pottedplant",
    "sheep",
    "sofa",
    "train",
    "tvmonitor",
]
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))
net = cv2.dnn.readNetFromCaffe(prototxt, model)


def process(frame):
    try:
        process_object(frame)
        process_qr(frame)
    except Exception as e:
        traceback.print_exc()
        raise e


def process_object(frame):
    frame = imutils.resize(frame, width=800)
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5
    )
    net.setInput(blob)
    detections = net.forward()
    for i in np.arange(0, detections.shape[2]):
        conf = detections[0, 0, i, 2]
        if conf > confidence:
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
            label = "{}: {:.2f}%".format(CLASSES[idx], conf * 100)
            cv2.rectangle(frame, (startX, startY), (endX, endY), COLORS[idx], 2)
            y = startY - 15 if startY - 15 > 15 else startY + 15
            cv2.putText(
                frame, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2
            )
    cv2.imshow("Frame", frame)


def open_cam(fps, vs):
    success = True
    while True:
        frame = vs.read()
        process(frame)
        key = cv2.waitKey(1) & 0xFF
        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            success = False
            break
        fps.update()
    fps.stop()
    print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
    print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
    # do a bit of cleanup
    cv2.destroyAllWindows()
    vs.stop()
    return success


def start_cam():
    while True:
        try:
            vf = 1
            vs = VideoStream(vf).start()
            fps = FPS().start()
            if not open_cam(fps, vs):
                break
        except Exception as e:
            pass
            # traceback.print_exc()


if __name__ == "__main__":
    start_cam()
