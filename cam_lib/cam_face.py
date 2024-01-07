import sys

sys.path.append(
    r'C:\Users\e531866\Desktop\_GUOZHENG\git\repository\python-lib')

import cv2
from py_lib.func import log, now
# from windows.notification import noti
# from event_lib.person_event import update_person

path_haar_face = r'C:\Users\e531866\Desktop\_GUOZHENG\git\repository\python-lib\haar\haarcascade_frontalface_default.xml'


def putText(cam_frame, text, x, y):
    cv2.putText(cam_frame, text, (x + 10, y + 10), cv2.FONT_HERSHEY_SIMPLEX, 1,
                (255, 0, 255), 2)


def show_face(cam_frame, face):
    x, y, w, h = face
    cv2.rectangle(cam_frame, (x, y), (x + w, y + h), (255, 255, 0), 2)
    putText(cam_frame, '', x, y)


def process_face(cam_frame):
    cascade_classifier = cv2.CascadeClassifier(path_haar_face)
    gray_img = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2GRAY)
    faces = cascade_classifier.detectMultiScale(gray_img,
                                                scaleFactor=1.3,
                                                minNeighbors=5)
    face_list = []
    if len(faces) > 0:
        # update_person()
        pass

    for face in faces:
        # log('Found Face')
        show_face(cam_frame, face)
        x, y, w, h = face
        face_list.append((x, y, x + w, y + h, 'face'))
    return face_list