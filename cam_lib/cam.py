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

prototxt = r"D:\Git\github\python-lib\data\MobileNetSSD_deploy.prototxt"
model = r"D:\Git\github\python-lib\data\MobileNetSSD_deploy.caffemodel"
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

# Load the Haar cascade file
face_cascade = cv2.CascadeClassifier(
    r"D:\Git\github\python-lib\data\haar_cascade_files\haarcascade_frontalface_default.xml"
)

# Check if the cascade file has been loaded correctly
if face_cascade.empty():
    raise IOError("Unable to load the face cascade classifier xml file")


def process(frame):
    try:
        process_object(frame)
        process_face(frame)
        process_qr(frame)
    except Exception as e:
        traceback.print_exc()
        raise e


def process_face(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_rects = face_cascade.detectMultiScale(gray, 1.3, 5)

    # Draw a rectangle around the face
    for x, y, w, h in face_rects:
        show_rectangle(frame, (x, y), (x + w, y + h), "face")


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

            object_name = "{}: {:.2f}%".format(CLASSES[idx], conf * 100)
            show_rectangle(
                frame,
                (startX, startY),
                (endX, endY),
                object_name,
                COLORS[idx],
            )
    cv2.imshow("Video", frame)


def show_rectangle(
    frame, start_point, end_point, label="", color=(0, 255, 0), font_size=2
):
    (startX, startY) = start_point
    cv2.rectangle(frame, start_point, end_point, color, font_size)
    y = startY - 15 if startY - 15 > 15 else startY + 15
    cv2.putText(
        frame, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, font_size
    )


def open_cam(cap):
    success = True
    while True:
        (ret, frame) = cap.read()
        process(frame)
        # cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            success = False
            break
    # fps.stop()

    # print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
    # print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
    # do a bit of cleanup
    return success


def start_cam():
    while True:
        try:
            video_index = 1
            # vs = VideoStream(vf)
            cap = cv2.VideoCapture(video_index)
            # ret, frame=
            # fps = FPS().start()
            success = open_cam(cap)
            if not success:
                break
            cap.release()
            cv2.destroyAllWindows()
        except Exception as e:
            traceback.print_exc()


if __name__ == "__main__":
    start_cam()
