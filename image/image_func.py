import os
from face_detect import detect_face
from person_detect import detect_person
from analysis import load_image
import shutil
import re


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


def load_date(path):
    info = load_image(path)

    date_info = info.get('date_info')

    if date_info is None or date_info == '':
        print('No date')
        return

    # move to image to date
    arr = date_info.split(' ')

    date = arr[0]

    return date_info, date


def load_and_move_file(path, root='X:\WD-PHONE\Image', copy=False):
    date_info, date = load_date(path)
    new_dir = f'{root}\__IMG\{date.replace(":","/")}'

    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    new_image_name = 'IMG_' + \
        date_info.replace(':', '').replace(' ', '_')+".jpg"

    new_image_path = f'{new_dir}/{new_image_name}'
    print(f'New Image Name:{new_image_path}')

    if os.path.exists(new_image_name):
        print('Existes')
        return

    if copy:
        shutil.copyfile(path, new_image_path)
    else:
        shutil.move(path, new_image_path)


def is_img_date_jpg(file_name):
    return False
    x = re.search("IMG_\d{8}_\d{6}.jpg", file_name)
    return x is not None


def get_date_from_img(file_name):
    year = file_name[4:8]
    month = file_name[8:10]
    day = file_name[10:12]
    return f'{year}/{month}/{day}'


def is_img(file_name):
    return '.jpg' in file_name.lower() or '.png' in file_name.lower()


def is_video(file_name):
    return '.mp4' in file_name.lower() or '.mov' in file_name.lower()


def move_img(path, file_name, root, copy):
    is_img = is_img_date_jpg(file_name)
    if is_img:
        date_dir = get_date_from_img(file_name)
        new_image_dir = f'{root}\__IMG\{date_dir}'

        if not os.path.exists(new_image_dir):
            os.makedirs(new_image_dir)

        new_image_path = f'{new_image_dir}/{file_name}'
        print(f'New Image Name:{new_image_path}')

        if os.path.exists(new_image_path):
            print('Existes')
            return
        if copy:
            shutil.copyfile(path, new_image_dir)
        else:
            shutil.move(path, new_image_dir)
    else:
        load_and_move_file(path, root, copy)


def move_vid(path, file_name, root, copy):
    date_info, date = load_date(path)
    # date_dir = get_date_from_img(file_name)

    date_dir = date.replace(':', '/')
    new_image_dir = f'{root}/__VID/{date_dir}'

    dup_image_dir = f'{root}/__VID_DUP/{date_dir}'

    if not os.path.exists(new_image_dir):
        os.makedirs(new_image_dir)

    new_image_path = f'{new_image_dir}/{file_name}'
    print(f'New Video Name:{new_image_path}')
    if os.path.exists(new_image_path):
        if not os.path.exists(dup_image_dir):
            os.makedirs(dup_image_dir)
        print('Existes')
        shutil.move(path, dup_image_dir)
        return

    if copy:
        shutil.copyfile(path, new_image_dir)
    else:
        shutil.move(path, new_image_dir)


def move_to_image_base_dir(dir, root='X:\WD-PHONE\Image', copy=False):
    children = os.listdir(dir)

    count = len(children)
    i = 0
    for file_name in children:
        i += 1
        try:
            path = f'{dir}/{file_name}'
            print(f'[{i}/{count}]: {path}')

            if os.path.isdir(path):
                move_to_image_base_dir(path, root, copy)
            elif is_img(file_name):
                move_img(path, file_name, root, copy)
            elif is_video(file_name):
                move_vid(path, file_name, root, copy)

        except Exception as e:
            print(e)


def clear_empty_dir(dir):
    try:
        children = os.listdir(dir)
        count = len(children)

        if count == 0:
            print(f'delete empty dir: {dir}')
            os.rmdir(dir)
            return

        for file_name in children:
            path = f'{dir}/{file_name}'
            if os.path.isdir(path):
                clear_empty_dir(path)

        children = os.listdir(dir)
        count = len(children)

        if count == 0:
            print(f'delete empty dir: {dir}')
            os.rmdir(dir)
    except:
        pass


# person_dir = r'X:\WD-PHONE\Camera\person'
# no_face_dir = r'X:\WD-PHONE\Camera\no-person-face'
# no_person_dir = r'X:\WD-PHONE\Camera\no-person'
dir = r'X:\WD-PHONE\Camera'
dir = r'X:\WD-PHONE\Camera\person-face'
dir = r'X:\WD-PHONE\Camera\person'
dir = r'X:\WD-PHONE\Camera\no-person-face'
dir = r'X:\WD-PHONE\Image\person'
dir = r'X:\WD-PHONE\Image\no-person'
dir = r'F:\phone\HW\DCIM\Camera'
dir = r'F:\phone\HW\Pictures\WeiXin'
# move_person_image(dir)
# move_no_person_face_image(dir, no_face_dir)
# move_no_person_image(dir, no_person_dir)


dir = r'R:\Image\__All\2022\05\17'
dir = r'F:\phone\HW\Pictures\Screenshots'

root = r'E:\Image'
dir = r'E:\Image\__VID'
dir = r'E:\Phone'
# dir = r'E:\Image\__All\2011\11\20'

# dir = r'E:\Phone\MT02\DCIM'

dir = f'F:\phone'
root = r"R:\Image"
root = r"F:\Image"


dir = f'J:\Phone'
root = r"J:\Image"


dir = r'N:\backup\备份\备份\LO我和老婆VE'
root = r'N:\Image'


dir = r'R:\Phone'
dir = r'S:/'

root = r'H:\Image'
dir = r'H:\MT02\DCIM'


root = r'H:\Image'
dir = r'F:\内部存储\DCIM\Camera'

move_to_image_base_dir(dir, root, True)

dir = r'K:/'
# clear_empty_dir(dir)


# is_img = is_img_date_jpg('IMG_20180115_061147.jpg')
# print(is_img)

# file_name = 'IMG_20180115_061147.jpg'
# print(get_date_from_img(file_name))
