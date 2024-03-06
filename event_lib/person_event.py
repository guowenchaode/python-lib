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
from windows_lib.notification import noti
from event_lib.event import EventTimer

EVENT_NAME = "CAM/PERSON"
stop_interval_seconds = 60 * 2
run_interval_seconds = 60 * 20
on_stop = lambda inter: noti(f"Leave: {inter}")
on_run = lambda inter: noti(f"Start: {inter}")

timer = EventTimer(
    name=EVENT_NAME,
    stop_interval_seconds=stop_interval_seconds,
    run_interval_seconds=run_interval_seconds,
    on_stop=on_stop,
    on_run=on_run,
)


def update_person():
    timer.receive()


def get_total_run_seconds():
    return timer.total_run_seconds


def get_total_stop_seconds():
    return timer.total_stop_seconds


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
            update_person()
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
