########################################
# TOP #
########################################
############## TOP IMPORT FUNC #########
import sys

sys.path.append(r"D:/Git/github/python-lib")

from py_lib.func import (
    log,
    dt,
    log_error,
    sleep,
    read_file,
    write_file,
    format_json,
    loop_dir,
    to_dict_list,
)

########################################

import argparse
import os
import time
import traceback
from datetime import datetime
from date_parser import parse_date

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
dict_list = "D:\__Alex\config\main\db\plan.csv"


def start_plan():
    plan_list = to_dict_list(dict_list)

    now = datetime.now()
    idx = 0
    date_reg_list = [plan.get("dateExp/String") for plan in plan_list]

    date_time_list = parse_date(date_reg_list)

    for date_reg in date_reg_list:
        try:
            idx += 1

            delta = date_time - now
            print(f"[{idx}]:{date_time} => {delta}")
        except:
            pass


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
            start_plan()
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
