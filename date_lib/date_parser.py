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
    to_date_time,
    to_dict_list,
    execute,
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
from xunfei_lib.tts import speak


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


def parse_date_list(reg_list):
    command = f"java utils.function.DateParser {reg_list}"
    rs, e = execute(command)
    reg_list = rs.split("==")
    dt_list = [to_date_time(reg) for reg in reg_list]
    return dt_list


def parse_date(reg):
    command = f"java utils.function.DateParser {reg}"
    rs, e = execute(command)
    dt = datetime.strptime(rs, "%Y/%m/%d %H:%M:%S")
    return dt
    # print(f"rs={rs}")
    # print(f"e={e}")


dict_list = "D:\__Alex\config\main\db\plan.csv"


def start_plan():
    plan_list = to_dict_list(dict_list)
    date_reg_list = [plan.get("dateExp/String") for plan in plan_list]
    date_time_list = parse_date_list(" ".join(date_reg_list))

    now = datetime.now()
    idx = 0
    for i in range(len(plan_list)):
        try:
            plan = plan_list[i]
            plan_detail = plan.get("detail/String")
            date_time = date_time_list[i]
            log(f"[{i}]:[{date_time}] {plan_detail}")

            if date_time is None:
                continue

            speak(plan_detail)

            delta = date_time - now
            left_seconds = delta.total_seconds()
            log(f"==>[{delta}] {plan_detail}")

            if left_seconds > 0 and left_seconds < 6000:
                log_error(f"==>[{delta}] {plan_detail}")
                speak(plan_detail)
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
        elif args.action == "parse_date":
            parse_date(args.date_reg)
        else:
            date_reg = "*/*/*/[1-5]/[9-18]:0:0"
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
