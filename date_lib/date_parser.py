########################################
# TOP #
########################################
############## TOP IMPORT FUNC #########
import sys

sys.path.append(r"C:/Users/e531866/Desktop/_GUOZHENG/git/repository/python-lib/")

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


class plan_parser:
    def __init__(self):
        self.date = dt()

    # 12 ~ 12 True
    # 12 ~ [1, 12, 13] True
    # 12 ~ [1-10, 12] True
    # 12 ~ [1-10] True
    # 12 ~ * True
    def match_reg_arr(self, value, reg):
        # 12 ~ [1-10, 12] True
        reg = reg.replace("[", "").replace("]", "")
        num_arr = reg.split(",")
        for i in list(num_arr):
            if i == value:
                return True
            elif "-" in i and in_range(i, value):
                return True
        return False

    def match_element(self, value, reg):
        log(f"compare {value} ~ {reg}")
        if value == reg or reg == "*":
            log(f"{value} ~= {reg}")
            return True
        elif self.match_reg_arr(value, reg):
            return True
        return False

    def match_all(self, reg_list, date_list):
        for i in range(7):
            reg = reg_list[i]
            value = date_list[i]
            if not self.match_element(value, reg):
                return False
        return True

    def parse_next_date(self, reg_list, date_list):
        while not self.match_all(reg_list, date_list):
            pass
        log("success")
        return ""

    def parse(self, date_reg, date_str):
        reg_list = parse_element(date_reg)
        date_list = parse_element(date_str)
        next_date = self.parse_next_date(reg_list, date_list)


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
