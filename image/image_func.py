import os
from face_detect import detect_face
from person_detect import detect_person
from analysis import load_image
import shutil


def move_no_person_image(dir, no_person_dir=r'X:\WD-PHONE\Image\no-person'):
    children = os.listdir(dir)

    count = len(children)
    i = 0
    for file_name in children:
        if not '.jpg' in file_name:
            continue

        path = f'{dir}/{file_name}'
        print(f'[{i}/{count}]: {path}')

        persons = detect_person(path)

        if not 'person' in persons:
            print(f'Not Found Person:{persons}')
            shutil.move(path, no_person_dir)

        i += 1


def move_person_image(dir, person_dir=r'X:\WD-PHONE\Image\person'):
    children = os.listdir(dir)

    count = len(children)
    i = 0
    for file_name in children:
        if not '.jpg' in file_name:
            continue

        path = f'{dir}/{file_name}'
        print(f'[{i}/{count}]: {path}')

        persons = detect_person(path)

        if 'person' in persons:
            print(f'Found Person:{persons}')
            shutil.move(path, person_dir)

        i += 1


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


def move_to_image_base_dir(dir):
    children = os.listdir(dir)

    count = len(children)
    i = 0
    for file_name in children:
        i += 1
        if not '.jpg' in file_name:
            continue

        path = f'{dir}/{file_name}'
        print(f'[{i}/{count}]: {path}')
        info = load_image(path)

        date_info = info.get('date_info')

        if date_info is None:
            continue

        # move to image to date
        date, time = date_info.split(' ')

        new_dir = f'X:\WD-PHONE\Image\__All\{date.replace(":","/")}'

        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        new_image_name = date_info.replace(':', '-').replace(' ', '+')+".jpg"

        new_image_path = f'{new_dir}/{new_image_name}'
        print(f'New Image Name:{new_image_path}')

        if os.path.exists(new_image_name):
            print('Existes')
            continue

        shutil.move(path, new_image_path)


# person_dir = r'X:\WD-PHONE\Camera\person'
# no_face_dir = r'X:\WD-PHONE\Camera\no-person-face'
# no_person_dir = r'X:\WD-PHONE\Camera\no-person'
dir = r'X:\WD-PHONE\Camera'
dir = r'X:\WD-PHONE\Camera\person-face'
dir = r'X:\WD-PHONE\Camera\person'
dir = r'X:\WD-PHONE\Camera\no-person-face'
dir = r'X:\WD-PHONE\Image\person'

# move_person_image(dir)
# move_no_person_face_image(dir, no_face_dir)
# move_no_person_image(dir, no_person_dir)
move_to_image_base_dir(dir)
