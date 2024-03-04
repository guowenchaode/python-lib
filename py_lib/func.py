import os
import shutil
import datetime
import requests
import win32clipboard
import traceback
import json
import time
import subprocess
import pandas as pd
import sys
import logging
from threading import Thread

KB = 1024
MB = KB * 1024
GB = MB * 1024


HEADER = "\033[95m"
OKBLUE = "\033[94m"
OKCYAN = "\033[96m"
OKGREEN = "\033[92m"
WARNING = "\033[93m"
FAIL = "\033[91m"
ENDC = "\033[0m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"


TIMEOUT = 100
FILE_MAX_LENGTH = 65

JIRA_ID = os.getenv("JIRA_ID")
JIRA_PW = os.getenv("JIRA_PW")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

jira_host = "https://statestreet-cloud.atlassian.net/browse"

DIR_CACHE = r"C:\Users\e531866\Desktop\_GUOZHENG\git\repository\alex_in_ssc\service_in_ssc\ui\cache"
sep = "-" * 50


log_head = "*********************"

sys.stdout.reconfigure(encoding="utf-8")

current_date = datetime.datetime.now().strftime("%Y-%m-%d")

# logging.basicConfig(
#     level=logging.INFO,
#     filename=f"D:\__cache\logs\{current_date}.log",
#     format="%(asctime)s [%(thread)d] [%(levelname)s]: %(message)s",
#     filemode="a",
# )


logger = logging.getLogger()
logger.setLevel(logging.INFO)
# 设置将日志输出到文件中，并且定义文件内容
now = datetime.datetime.now().strftime("%Y-%m-%d")
fileinfo = logging.FileHandler(f"D:\__cache\logs\{current_date}.log")
fileinfo.setLevel(logging.INFO)
# 设置将日志输出到控制台
controlshow = logging.StreamHandler()
controlshow.setLevel(logging.INFO)
# 设置日志的格式
formatter = logging.Formatter("%(asctime)s [%(thread)d] [%(levelname)s]: %(message)s")
fileinfo.setFormatter(formatter)
controlshow.setFormatter(formatter)

logger.addHandler(fileinfo)
logger.addHandler(controlshow)


# 记录日志信息
# logger.debug('debug message')
# logger.info('info message')
# logger.warning('warning message')
# logger.error('error message')
# logger.critical('critical message')


def copy(from_path, to_path):
    shutil.copy(from_path, to_path)


def mkdirs(dir):
    if not (os.path.exists(dir)):
        os.makedirs(dir)


def makedirs(dir, file):
    file_dir = f"{dir}/{format_file_name(file)}"
    mkdirs(file_dir)
    return file_dir


FILE_REP = ""


def format_file_name(name):
    name = str(name)
    name = (
        name.replace("<", " ")
        .replace(">", " ")
        .replace("\\", FILE_REP)
        .replace("/", FILE_REP)
        .replace(":", " ")
        .replace("*", " ")
        .replace("?", " ")
        .replace("|", FILE_REP)
        .replace('"', " ")
    )

    name = (
        name.replace("<EOM>", " ")
        .replace("\t", " ")
        .replace("\r", " ")
        .replace("\n", " ")
    )
    name = clear_lines(name)

    if len(name) > FILE_MAX_LENGTH:
        name = name[0 : FILE_MAX_LENGTH - 1]
    return name.strip()


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


def set_copied(text):
    # # set clipboard data
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(text)
    win32clipboard.CloseClipboard()


def get_copied():
    # get clipboard data
    win32clipboard.OpenClipboard()
    data = win32clipboard.GetClipboardData()
    win32clipboard.CloseClipboard()
    return data


def now():
    return datetime.datetime.now()


def d():
    d = datetime.datetime.now()
    dt_str = d.strftime("%Y-%m-%d")
    return dt_str


def dt():
    d = datetime.datetime.now()
    dt_str = d.strftime("%Y-%m-%d-%H.%M.%S")
    return dt_str


def dtl():
    d = datetime.datetime.now()
    dt_str = d.strftime("%Y-%m-%d %H:%M:%S")
    return dt_str


def read_file(path):
    try:
        return open(path, "r", encoding="utf-8").read()
    except:
        return ""


def write_file(path, content, append=True):
    try:
        dir = get_dir(path)

        if not os.path.exists(dir):
            mkdirs(dir)

        flg = "a" if append else "w"
        with open(path, flg, encoding="utf-8") as text_file:
            text_file.write(content)
    except Exception as e:
        traceback.print_exc()
        raise e


def exe_script(file_path):
    file_content = read_file(file_path)
    log_block(file_content, file_path)
    return exe_sh_output(file_content)


def exe_sh_output(args):
    log(f"[CALLING]{args}")
    process = subprocess.Popen(
        args, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )


def move_file(source, destination):
    filename = os.path.basename(source)
    dest = os.path.join(destination, filename)

    if not os.path.exists(source):
        log_error(f"[source-file-not-existed] [{source}]")
        return

    to_file = shutil.move(source, dest)
    log(f"[move_file] [{to_file}]")
    return to_file


def log_error(l):
    log(l, WARNING)


def log_success(l):
    log(l, OKGREEN)


def log(l=log_head, color=""):
    currentDT = datetime.datetime.now()
    dt = currentDT.strftime("%Y-%m-%d %H:%M:%S")
    # info = '\t'.join(l)
    l = str(l)
    message = f"{l}" if color == "" else f"{color}{l}{ENDC}"
    # logger.info(l)
    logger.info(message)
    # print(message)


def log_block(message, title=""):
    try:
        lg = message if is_string(message) else format_json(message)
        title = f"\n{sep} {title} {sep}"
        log(title)
        log(lg, WARNING, False)
        print(f"{sep}{sep}")
    except Exception as e:
        block = f"\n{sep} {title} {sep}\n{message}\n{sep}{sep}"
        log(block)
        # traceback.print_exc()


def is_string(o):
    return isinstance(o, str)


def get_file_name(file_path):
    return os.path.basename(file_path)


def format_json(obj):
    return json.dumps(obj, indent=4)


def sleep(second):
    time.sleep(second)


def loop_dir(dir, process_file=lambda x: x, process_dir=lambda x: x, print_file=True):
    if not os.path.exists(dir):
        log_error(f"Dir does not exits. {format_json(dir)}")
        return

    if os.path.isfile(dir):
        if print_file:
            log(f"[FILE]{dir}")
        process_file(dir)
        return
    for filename in os.listdir(dir):
        f = os.path.join(dir, filename)
        # checking if it is a file
        if os.path.isdir(f):
            loop_dir(dir=f, process_file=process_file, process_dir=process_dir)
        else:
            if print_file:
                log(f"[FILE]{f}")
            process_file(f)

    log(f"[DIR]{dir}")
    process_dir(dir)


def is_list(dir):
    list_path = f"{dir}/..list"
    return os.path.exists(list_path)


def is_obj_list(dir):
    list_path = f"{dir}/..object_list"
    return os.path.exists(list_path)


def load_object(file_path, print_file=False):
    is_list_dir = is_list(file_path)
    is_obj_list_dir = is_obj_list(file_path)
    obj = [] if is_list_dir else {}

    if os.path.isfile(file_path):
        return read_file(file_path)

    for file in os.listdir(file_path):
        if file.startswith(".."):
            continue

        if is_list_dir:
            obj.append(file)
            continue

        child_path = f"{file_path}/{file}"
        child_obj = load_object(child_path, print_file)

        # loading method
        if is_obj_list_dir:
            obj.append(child_obj)
        else:
            obj[file] = child_obj

    return obj


class dict_to_object:
    def __init__(self, **entries):
        self.__dict__.update(entries)


def last_line(s):
    arr = s.split("\n")
    return arr[len(arr) - 1]


def clear_lines(content, frm="  ", to=" "):
    while frm in content:
        content = content.replace(frm, to)
    return content


def execute(cmds):
    result = subprocess.run(cmds, capture_output=True)
    output = result.stdout.decode("utf-8")
    error = result.stderr.decode("utf-8")
    return f"{output}".strip(), f"{error}".strip()


def to_dict_list(pth):
    try:
        df = pd.read_csv(pth)
        json_data = df.to_json(orient="records")
        return json.loads(json_data)
    except:
        return None


def to_date_time(date_str, reg="%Y/%m/%d %H:%M:%S"):
    try:
        return datetime.datetime.strptime(date_str, reg)
    except:
        return None


def to_json(str):
    return json.loads(str)


def parse_delta_time(delta):
    (h, m, s) = delta.split(":")
    s = int(float(s))
    result = f",{h}小时,{m}分,{s}秒"

    result = result.replace(",0小时", "").replace(",0分", "").replace(",0秒", "")
    return result.replace(",", "")


def get_delta_time_by_str(date_time_str):
    delta = get_delta_time(to_date_time(date_time_str))
    delta = f"{delta}"
    result = ""
    if "," in delta:
        (days, times) = delta.split(", ")
        d = days.replace(" days", "")
        time_delta = parse_delta_time(times)
        result = f",{d}天{time_delta}".replace(",0天", "")

    else:
        result = parse_delta_time(delta)
    return result.replace(",", "")


def get_delta_time(date_time):
    return date_time - datetime.datetime.now()


def schedule(seconds, action):
    def run():
        time.sleep(seconds)
        if action is not None:
            action(None)

    t1 = Thread(target=run)
    t1.start()


def loop_sys_path_dir(
    path_filter=lambda x: True,
    process_file=lambda x: x,
    process_dir=lambda x: x,
    print_file=True,
):
    os_path = os.getenv("path")
    path_list = os_path.split(";")
    for path_dir in path_list:
        is_ignored = path_dir == "" or not path_filter(path_dir)
        if is_ignored:
            continue
        log(f"{path_dir}")
        loop_dir(path_dir, process_file, process_dir, print_file)


def get_file_name_without_ext(file_path):
    return os.Path(file_path).stem


def get_file_name(file_path):
    return os.path.basename(file_path)


def get_dir(file):
    return os.path.dirname(os.path.abspath(file))
