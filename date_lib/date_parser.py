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
    log_head,
    OKCYAN,
    FAIL,
    OKGREEN,
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
import re
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
    def match_exp_arr(self, value, reg):
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
        elif self.match_exp_arr(value, reg):
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

    def parse(self, date_exp, date_str):
        reg_list = parse_element(date_exp)
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


def is_late_hour():
    now = datetime.now()
    is_late = now.hour >= 0 and now.hour <= 6
    return is_late


def noti_current_plan(plan_list):
    plan_detail = [plan.get("detail/String") for plan in plan_list]
    log(f"[当前计划]:{plan_detail}")

    if len(plan_list) == 0:
        log_error("plan is empty")
        return

    if is_late_hour():
        log_error("is late hour")
        return

    # [h, m, s, *ms] = re.split("[.:]", delta_time)
    msg = f"请注意,现在{plan_detail}"
    speak(msg)


wait_time = 10


def get_delta(plan_date, now):
    if plan_date is None:
        return None
    delta = plan_date - now
    return delta


def is_current_plan(left_seconds):
    if left_seconds < 0:
        return False

    if left_seconds <= wait_time:
        return True

    return False


def start_plan():
    plan_list = to_dict_list(dict_list)
    date_exp_list = [plan.get("dateExp/String") for plan in plan_list]
    date_time_list = parse_date_list(" ".join(date_exp_list))

    now = datetime.now()

    matched_plan_list = []
    for i in range(len(plan_list)):
        try:
            plan = plan_list[i]
            date_time = date_time_list[i]
            plan["date"] = date_time
            is_active = plan.get("active/String") != "N"
            plan_exp = plan.get("dateExp/String")
            plan_detail = plan.get("detail/String")
            delta = get_delta(date_time, now)
            msg = f"[{i}]:[{is_active}] => [{date_time}] => [{delta}] => [{plan_exp}] =>  {plan_detail}"

            if is_active:
                log_error(msg)
            else:
                log(msg)
        except:
            pass

    def sort_plan(plan):
        date = plan.get("date")
        if date is None:
            return -1
        return date.timestamp()

    sorted_list = sorted(plan_list, key=sort_plan)

    i = 1
    log(log_head * 3)
    log(log_head * 3)

    next_plan = None
    next_message = ""
    next_left_seconds = 0
    for plan in sorted_list:
        date_time = plan.get("date")
        is_active = plan.get("active/String") != "N"
        plan_exp = plan.get("dateExp/String")
        plan_detail = plan.get("detail/String")
        try:
            if date_time is None or not is_active:
                continue

            delta = get_delta(date_time, now)
            left_seconds = int(delta.total_seconds())

            if left_seconds < 0:
                continue

            is_current = is_current_plan(left_seconds)
            msg = f"[{i}]:[{is_active}] => [{date_time}] => [{delta}] => [{left_seconds}] => [{plan_exp}] =>  {plan_detail}"

            if left_seconds > 0 and next_plan is None:
                next_plan = plan
                next_message = msg
                next_left_seconds = left_seconds

            log_plan(msg, left_seconds)
            i += 1

            if is_current:
                log_error(f"[current-plan]{plan_detail}")
                matched_plan_list.append(plan)
        except Exception as e:
            log_error(f"[{plan_detail}]: {e}")

    if next_plan is not None:
        log(log_head * 3)
        log_plan(next_message, next_left_seconds)
        log(log_head * 3)

    noti_current_plan(matched_plan_list)


def log_plan(msg, left_seconds):
    in_hour = left_seconds > 0 and left_seconds < 60 * 60
    in_today = left_seconds > 0 and left_seconds < 60 * 60 * 24
    if in_hour:
        log(msg, FAIL)
    elif in_today:
        log(msg, OKGREEN)
    else:
        log_error(msg)


def start_plan_and_wait():
    while True:
        try:
            start_plan()
        except:
            pass
        finally:
            sleep(wait_time)


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
            parse_date(args.date_exp)
        else:
            date_exp = "*/*/*/[1-5]/[9-18]:0:0"
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
