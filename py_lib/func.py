import os
import shutil
import datetime
import requests

KB = 1024
MB = KB * 1024
GB = MB * 1024


def log_error(l=""):
    log(l)


def log(l=""):
    now = datetime.datetime.now()
    dt = now.strftime("%Y-%m-%d %H:%M:%S")
    l = str(l)
    print(f"{dt}\t{l}")


def file_size_info(path):
    size = os.path.getsize(path)

    gb = int(size / GB)
    mb = int((size % GB) / MB)
    kb = int((size % MB) / KB)
    b = int(size % KB)

    info = ""

    if gb > 0:
        info += f"{gb}GB "

    if mb > 0:
        info += f"{mb}MB "

    if kb > 0:
        info += f"{kb}KB "

    info += f"{b}B"

    return info


def move_to_dir(dir, dir_root, target_root, copy=False):
    children = os.listdir(dir)

    count = len(children)
    i = 0
    for file_name in children:
        i += 1
        try:
            path = f"{dir}/{file_name}"
            print(f"[{i}/{count}]: {path}")

            if os.path.isdir(path):
                if "node_modules" == file_name or "Program Files" == file_name:
                    continue
                move_to_dir(path, dir_root, target_root, copy)
            else:
                ref_path = dir.replace(dir_root, "")
                target_dir = f"{target_root}/{ref_path}"

                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                if copy:
                    shutil.copyfile(path, target_dir)
                else:
                    shutil.move(path, target_dir)
        except Exception as e:
            print(e)


def clear_empty_dir(dir):
    try:
        print(f"check dir: {dir}")
        children = os.listdir(dir)
        count = len(children)

        if count == 0:
            print(f"delete empty dir: {dir}")
            os.rmdir(dir)
            return

        for file_name in children:
            path = f"{dir}/{file_name}"
            if os.path.isdir(path):
                clear_empty_dir(path)

        children = os.listdir(dir)
        count = len(children)

        if count == 0:
            print(f"delete empty dir: {dir}")
            os.rmdir(dir)
    except:
        pass


# dir = r'E:\Image'
# target_dir = r'H:\Image'

# move_to_dir(dir, dir, target_dir, True)

# dir = r'E:/'
# clear_empty_dir(dir)


def http_post(url, data={}):
    # log(f"[http_post] {url}")
    user = ""
    session = requests.Session()
    # session.proxies = PROXYS
    # auth = requests.auth.HTTPBasicAuth(username=user, password=api_key)
    response = session.post(url, json=data, verify=False)
    # log(f"[http_post] code=[{response.status_code}]")
    return response
