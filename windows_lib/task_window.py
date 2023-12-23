########################################
# TOP #
########################################
############## TOP IMPORT FUNC #########
import sys

sys.path.append(r"D:/Git/github/python-lib")

from py_lib.func import (
    log,
    log_error,
    sleep,
    read_file,
    load_object,
    dict_to_object,
    mkdirs,
    format_file_name,
    write_file,
    format_json,
    loop_dir,
)

########################################

import argparse
import os
import time
import traceback
from datetime import datetime

############### SAMPLE ################
# time.sleep(1)


########################################
def build_arg_parser():
    parser = argparse.ArgumentParser(description="Action")
    parser.add_argument("--action", dest="action", required=False, help="action")
    parser.add_argument("--text", dest="text", required=False, help="text")
    parser.add_argument("--window", dest="window", required=False, help="window")
    parser.add_argument("--width", dest="width", required=False, help="width")
    parser.add_argument("--height", dest="height", required=False, help="height")
    parser.add_argument("--x", dest="x", required=False, help="x")
    parser.add_argument("--y", dest="y", required=False, help="y")
    parser.add_argument(
        "--workspace", dest="workspace", required=False, help="workspace"
    )
    args, left = parser.parse_known_args()
    return args


def test(txt):
    log(txt)


########################################
# BODY #
########################################
"""
INPUT YOUR SCRIPT HERE
"""


import win32gui

WINDOW_DATA_PATH = r"D:\__Alex\config\workspace"

window_index = {}

DIS_X = 80
DIS_Y = -60

DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 500

DEFAULT_TITLE = "__default"


def get_window_index(key):
    index = window_index.get(key)
    if index is None:
        index = 0
    else:
        index += 1

    window_index[key] = index

    return index


def format_name(name):
    return name.replace("|", "^").replace(":", "^").replace("/", "^")


def get_config(window_config, title):
    current_name = ""

    title_configs = window_config.get("title")
    group_configs = window_config.get("group")

    if title_configs is None:
        title_configs = {}

    if group_configs is None:
        group_configs = {}

    # check from title
    for name in title_configs.keys():
        if format_name(name.lower()) == format_name(title.lower()):
            config = title_configs.get(name)
            return (config, name)

    for name in title_configs.keys():
        if format_name(name.lower()) in format_name(title.lower()):
            config = title_configs.get(name)
            return (config, name)

    # check from group
    for group in group_configs.keys():
        group_config = group_configs.get(group)
        names = get(group_config, "names", [])

        for name in names:
            if format_name(name.lower()) in format_name(title.lower()):
                current_name = group
                config = window_config.get(name)
                return (group_config, group)

    return (None, None)


def process_window(window, window_config):
    try:
        (x, y, end_x, end_y) = win32gui.GetWindowRect(window)
        width = end_x - x
        height = end_y - y

        title = win32gui.GetWindowText(window)

        if "Cmder" in title:
            pass

        ignore_list = window_config.get("ignore")

        if ignore_list is None:
            ignore_list = []

        if title == "" or width <= 100 or height <= 100 or x > 4000:
            log_error(f"invalid size: {title}")
            return
        if title.lower() in ignore_list:
            log_error(f"ignored title: {title}")
            return

        log(f"[{title}]: location: ({x},{y})\tsize: ({width},{height})")

        title = format_file_name(title)

        config, current_name = get_config(window_config, title)

        is_default = False

        # set default window if big window
        if width > 1000 and config is None:
            is_default = True
            config, current_name = get_config(window_config, DEFAULT_TITLE)
        if config is None:
            return

        index = get_window_index(current_name)

        ## for same title or group it will reset window as trace
        _x = parse_as_int(config, "x", x) + index * DIS_X
        _y = parse_as_int(config, "y", y) + index * DIS_Y
        _width = parse_as_int(config, "width", DEFAULT_WIDTH)
        _height = parse_as_int(config, "height", DEFAULT_HEIGHT)

        info = f"[{title}]: to_location: ({_x},{_y})\tto_size: ({_width},{_height})"

        if is_default:
            info += f" [DEFAULT]"
        log_error(info)
        win32gui.MoveWindow(window, _x, _y, _width, _height, True)
    except Exception as e:
        traceback.print_exc()


def parse_as_int(config, name, default):
    i = config.get(name)
    if i is None:
        return default
    else:
        return int(i.strip())


def load_window_workspace(workspace="default"):
    log(f"load workspace {workspace}")
    config_path = f"{WINDOW_DATA_PATH}/{workspace}/config"
    if not os.path.exists(config_path):
        config_path = f"{WINDOW_DATA_PATH}/default/config"
    window_config = load_object(config_path)
    win32gui.EnumWindows(process_window, window_config)


def save_window_workspace(workspace="current"):
    log(f"save workspace {workspace}")
    config_path = f"{WINDOW_DATA_PATH}/{workspace}/config"
    if not os.path.exists(config_path):
        config_path = f"{WINDOW_DATA_PATH}/default/config"

    CURRENT_TITLE_WORKSPACE_PATH = f"{config_path}\\title"

    # delete_dir(CURRENT_TITLE_WORKSPACE_PATH)

    window_config = load_object(config_path)
    window_config["name"] = workspace

    win32gui.EnumWindows(save_window, window_config)


def set_window(window_title, width, height, x=0, y=0):
    window_config = {
        "title": window_title,
        "width": int(width),
        "height": int(height),
        "x": int(x),
        "y": int(y),
    }
    dct = dict_to_object(**window_config)
    win32gui.EnumWindows(load_window, dct)


def load_window(window, window_config):
    try:
        title = win32gui.GetWindowText(window)

        if title.strip() == "":
            return

        log(f"==>{title}")

        if window_config.title.lower() not in title.lower():
            return

        win32gui.MoveWindow(
            window,
            window_config.x,
            window_config.y,
            window_config.width,
            window_config.height,
            True,
        )

    except Exception as e:
        traceback.print_exc()


def save_window(window, window_config):
    try:
        (x, y, end_x, end_y) = win32gui.GetWindowRect(window)
        width = end_x - x
        height = end_y - y

        title = win32gui.GetWindowText(window)
        ignore_list = window_config.get("ignore")

        if "Code" in title:
            pass

        if ignore_list is None:
            ignore_list = []

        if (
            title == ""
            or title in ignore_list
            or width <= 100
            or height <= 100
            or x > 4000
        ):
            return

        if title.lower() in ignore_list:
            return

        title = format_file_name(title)
        # process Visual Studio Code
        if "- Visual Studio Code" in title:
            arr = title.split(" - ")
            title = f"{arr[1]} - {arr[2]}"
        elif "Microsoft Teams" in title:
            title = "Microsoft Teams"
        elif " Chrome" in title:
            title = " Chrome"

        log(f"[{title}]: location: ({x},{y})\tsize: ({width},{height})")

        workspace = window_config["name"]
        config_path = f"{WINDOW_DATA_PATH}/{workspace}/config"

        window_title_dir = f"{config_path}\\title\\{title}"

        mkdirs(window_title_dir)

        x_path = f"{window_title_dir}\\x"
        y_path = f"{window_title_dir}\\y"
        width_path = f"{window_title_dir}\\width"
        height_path = f"{window_title_dir}\\height"

        write_file(x_path, f"{x}", False)
        write_file(y_path, f"{y}", False)
        write_file(width_path, f"{width}", False)
        write_file(height_path, f"{height}", False)

    except Exception as e:
        traceback.print_exc()


########################################
########################################

# BOTTOM #
########################################
if __name__ == "__main__":
    try:
        start = datetime.now()
        args = build_arg_parser()
        log(f"__dir__: {__file__}")
        log(f"### [start-try]: action=[{args.action}]")
        ###########################################
        if args.action == "test":
            test(args.text)
        elif args.action == "set-window":
            set_window(args.window, args.width, args.height, args.x, args.y)
        elif args.action == "set-windows":
            load_window_workspace(args.workspace)
        elif args.action == "save-windows":
            save_window_workspace(args.workspace)
        else:
            # test(args.text)
            save_window_workspace()
        ###########################################
        end = datetime.now()
        inter = end - start
        log(f"### [end-try]: [{inter}]")
    except:
        traceback.print_exc()
    finally:
        fine = datetime.now()
        inter = fine - start
        log(f"### [finally]: [{inter}]")
