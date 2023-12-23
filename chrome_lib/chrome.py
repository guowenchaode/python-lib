########################################
# TOP #
########################################
############## TOP IMPORT FUNC #########
import sys

sys.path.append(r"D:/Git/github/python-lib")

from py_lib.func import log, log_block, copy

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
import chrome_bookmarks
import sqlite3
import subprocess

CHROME_HISTORY_PATH = (
    r"C:\Users\Alex\AppData\Local\Google\Chrome\User Data\Default\History"
)


def show_dirs():
    for folder in chrome_bookmarks.folders:
        log_block(folder.folders, folder.name)


def open_url(path):
    for folder in chrome_bookmarks.folders:
        pass


def copy_history(to_path=f"{CHROME_HISTORY_PATH}.temp"):
    if os.path.exists(to_path):
        os.remove(to_path)
    copy(CHROME_HISTORY_PATH, to_path)
    return to_path


def get_last_history():
    lst = get_history_list(1)
    return lst[0]


def get_history_list(last_count=5):
    history_path = copy_history()
    con = sqlite3.connect(history_path)
    cursor = con.cursor()
    cursor.execute("SELECT * FROM urls order by last_visit_time desc")
    history_list = cursor.fetchall()

    his_list = []
    for i in range(last_count):
        history = history_list[i]
        url = history[1]
        log(f"[{i}] {url}")
        his_list.append(url)

    return his_list


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
        else:
            test(args.text)
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
