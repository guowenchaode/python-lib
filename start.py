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
    # read_file,
    # write_file,
    # format_json,
    # loop_dir,
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
    parser.add_argument(
        "--video_index", dest="video_index", required=False, help="video_index"
    )
    parser.add_argument(
        "--enable_plan", dest="enable_plan", required=False, help="enable_plan"
    )
    parser.add_argument(
        "--enable_video", dest="enable_video", required=False, help="enable_video"
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


import time

# from windows.task_list import save_active_title
from cam_lib.cam import start_cam
from threading import Thread

# from windows.pc_monitor import monite
# from windows.task_window import save_window_workspace
# from work_note_lib.work_note import save_work_note
from chrome_lib.chrome import get_last_history
from date_lib.date_parser import start_plan_and_wait

# from localtest_http_server_run import start_self_service


def run():
    try:
        pass
    # save_work_note
    # save_work_note()
    except Exception as e:
        traceback.print_exc()


def start_threads(video_index=1, enable_cam=True, enable_plan=True):
    if enable_cam:
        log("start cam thread")
        thread = Thread(target=start_cam, args=(video_index,))
        thread.start()

    if enable_plan:
        log("start plan thread")
        thread = Thread(target=start_plan_and_wait)
        thread.start()

    # thread = Thread(target=start_server)
    # thread.start()

    # thread = Thread(target=start_self_service)
    # thread.start()
    thread = Thread(target=monite_pc)
    thread.start()


def monite_pc(slp=60):
    while True:
        try:
            ## save active title
            log_error(f"[TASK] save task list")

            # save_active_title
            # save_active_title()

            # monite()

            last_url = get_last_history()

            log_error(f"[url]{last_url}")

        except print(0):
            pass
        finally:
            time.sleep(slp)


def main(video, enable_cam=True, enable_plan=True, slp=3):
    # START THREAD
    log(
        f"Start Main Thread, video={video} enable_cam={enable_cam} enable_plan={enable_plan}"
    )
    start_threads(video, enable_cam, enable_plan)
    while True:
        try:
            run()
        except print(0):
            pass
        finally:
            time.sleep(slp)


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
        elif args.action == "start":
            main(int(args.video_index), bool(args.enable_plan), bool(args.enable_video))
        else:
            # test(args.text)
            main(int(2), bool("True"), bool("True"))
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
