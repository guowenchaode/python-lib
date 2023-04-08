import os
from face_detect import detect_face
import shutil


def move_no_person_face_image(dir, no_face_dir):
    children = os.listdir(dir)

    count = len(children)
    i = 0
    for file_name in children:
        if not '.jpg' in file_name:
            continue

        path = f'{dir}/{file_name}'
        print(f'[{i}/{count}]: {path}')

        faces = detect_face(path)

        if len(faces) == 0:
            print('No Face')
            shutil.move(path, no_face_dir)

        i += 1


dir = r'X:\WD-PHONE\Camera'
dir = r'X:\WD-PHONE\Camera\person-face'
no_face_dir = r'X:\WD-PHONE\Camera\no-person-face'
move_no_person_face_image(dir, no_face_dir)
