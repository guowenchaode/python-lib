# Example 7.6 MobileNet SSD Object Detection
# Modified based on:
# https://www.pyimagesearch.com/2017/09/18/real-time-object-detection-with-deep-learning-a
# import the necessary packages
import sys

sys.path.append(r"D:/Git/github/python-lib")

from py_lib.func import (
    log,
    log_error,
    sleep,
    seconds_to_hms,
    # read_file,
    write_file,
    dtl,
    d,
    # format_json,
    # loop_dir,
)

import numpy as np
import argparse
import imutils
import time
import cv2
from cam_lib.cam_qr import process_qr
from cam_lib.cam_hand import process_hand
import traceback
from event_lib.person_event import update_person, timer
from audio.speaker import speak

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


FRAME_WIDTH = 500
LINE_COLOR = [255, 255, 255]
LINE_HEIGHT = 20
MAX_WORKING_SECONDS = 60 * 60  # 1 HOUR

black_image = np.zeros(
    (FRAME_WIDTH, FRAME_WIDTH, 3), dtype=np.uint8
)  # 创建一个黑色图像

# Load the Haar cascade file
face_cascade = cv2.CascadeClassifier(
    r"D:\Git\github\python-lib\data\haar_cascade_files\haarcascade_frontalface_default.xml"
)

# Check if the cascade file has been loaded correctly
if face_cascade.empty():
    raise IOError("Unable to load the face cascade classifier xml file")

video_index = 1
total_person = ""


def read_frame(cap):
    (ret, frame) = cap.read()
    return frame


def wait_key(chr="q"):
    key = cv2.waitKey(1) & 0xFF
    return key == ord(chr)


IMAGE_PATH = r"D:\Share\cam\cam1.png"
last_message = ""


def process(frame):
    global black_image, total_person, last_message
    try:
        frame = imutils.resize(frame, width=FRAME_WIDTH)
        black_image = np.zeros((FRAME_WIDTH, FRAME_WIDTH, 3), dtype=np.uint8)
        process_object(frame, black_image)
        process_face(frame, black_image)
        process_qr(frame)
        hands = process_hand(frame, black_image)

        draw_objects(frame, hands)

        total_person = seconds_to_hms(timer.total_run_seconds)

        msg = f"Person: {total_person}"
        show_text(black_image, msg)

        if timer.total_run_seconds == 60 * 60:
            alert_message = "已经学习一小时，去休息一下"
            speak(alert_message)

        # cv2.imwrite(IMAGE_PATH, frame)
        if timer.total_run_seconds > 0 and last_message != msg:
            last_message = msg
            today = d()
            n = dtl()
            SHARE_LOG_PATH = f"D:/Share/cam/{today}.log"
            write_file(SHARE_LOG_PATH, f"\n{n}: {msg}")
    except:
        traceback.print_exc()
    finally:
        # cv2.namedWindow('Window with Menu', cv2.WINDOW_GUI_NORMAL)
        cv2.imshow("Video", black_image)


def process_face(frame, black_image):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_rects = face_cascade.detectMultiScale(gray, 1.3, 5)

    # Draw a rectangle around the face
    for x, y, w, h in face_rects:
        show_rectangle(black_image, (x, y), (x + w, y + h), "face")


last_object_names = ""


def process_object(frame, black_image):
    global last_object_names

    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(
        cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5
    )
    net.setInput(blob)
    detections = net.forward()

    object_names = ""
    for i in np.arange(0, detections.shape[2]):
        conf = detections[0, 0, i, 2]
        if conf > confidence:
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            object_name = CLASSES[idx]
            label = "{}: {:.2f}%".format(object_name, conf * 100)
            show_rectangle(
                black_image,
                (startX, startY),
                (endX, endY),
                label,
                COLORS[idx],
            )

            if object_name == "person":
                update_person()

            object_names = f"{object_names}-{object_name}"
    if object_names != last_object_names and object_names != "":
        log_error(f"[objects]{object_names}")
        last_object_names = object_names


def show_text(frame, label, x=0, y=20, color=(0, 255, 0), font_size=2):
    cv2.putText(frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, font_size)


def show_rectangle(
    frame, start_point, end_point, label="", color=(0, 255, 0), font_size=2
):
    global black_image
    (startX, startY) = start_point
    cv2.rectangle(frame, start_point, end_point, color, font_size)
    y = startY - 15 if startY - 15 > 15 else startY + 15
    show_text(frame, label, startX, y)


def draw_object(blank_img, obj):
    (startX, startY, endX, endY, label) = obj
    show_rectangle(blank_img, (startX, startY), (endX, endY), label)


def draw_objects(blank_img, objs):
    for i in range(len(objs)):
        obj = objs[i]
        draw_object(blank_img, obj)


def open_cam(cap):
    try:
        while True:
            frame = read_frame(cap)
            process(frame)
            if wait_key():
                return True
            time.sleep(0.3)
    except:
        traceback.print_exc()
        return False


def start_cam(video=video_index):
    while True:
        try:
            log(f"open cam {video}")
            cap = cv2.VideoCapture(video)
            success = open_cam(cap)
            if success:
                break
            cap.release()
            cv2.destroyAllWindows()
        except:
            traceback.print_exc()


if __name__ == "__main__":
    start_cam(1)
