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
    get_delta_time_by_str,
    OKCYAN,
    FAIL,
    OKGREEN,
    loop_dir,
    to_json,
    copy_file,
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
from socket_lib.socket_client import send_heart_beat

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
from ui_lib.message_window import update_message


current_dir = os.path.dirname(os.path.realpath(__file__))

MESSAGE_FILE = f"{current_dir}/last-plan.localtest.txt"


def load_last_plan():
    return read_file(MESSAGE_FILE)


def save_last_plan(message):
    return write_file(MESSAGE_FILE, message, False)


def parse_date_list_java(reg_list):
    command = f"java utils.function.DateParser {reg_list}"
    rs, e = execute(command)
    result = to_json(rs)
    return result


def parse_date(reg):
    command = f"java utils.function.DateParser {reg}"
    rs, e = execute(command)
    dt = datetime.strptime(rs, "%Y/%m/%d %H:%M:%S")
    return dt


plan_file = r"D:\Share\plan.csv"
dict_list_bak = r"D:\Share\plan.csv.bak"


def is_late_hour():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    is_late = hour >= 22 or hour <= 5 or (hour == 6 and minute <= 59)
    return is_late


def speak_message(msg):
    if is_late_hour():
        log(f"[plan]:is late hour")
        return

    speak(msg)


def update_plan_message(next_plan):
    plan_detail = next_plan.get("detail/String")
    date_time = next_plan.get("date")
    delta = get_delta_time_by_str(date_time)
    msg = f"请做好准备,{delta}后,{plan_detail}"
    update_message(f"{msg}")


def noti_next_plan(next_plan):
    plan_detail = next_plan.get("detail/String")
    date_time = next_plan.get("date")
    delta = get_delta_time_by_str(date_time)
    log(f"[下一计划]:{plan_detail}")
    msg = f"请做好准备,{delta}后,{plan_detail}"
    speak_message(msg)
    update_plan_message(next_plan)


def noti_current_plan(plan_list):
    plan_detail = [plan.get("detail/String") for plan in plan_list]
    log(f"[当前计划]:{plan_detail}")

    if len(plan_list) == 0:
        log_error("plan is empty")
        return

    msg = f"请注意,现在{plan_detail},{plan_detail}"
    update_message(msg)
    speak_message(msg)


wait_time = 30
current_phone = "Honor Magic 2"


def get_delta(plan_date, now):
    if plan_date is None:
        return None
    delta = plan_date - now
    return delta


def is_current_plan(left_seconds):
    if left_seconds <= wait_time:
        return True

    return False


last_alert_message = ""


def start_plan():
    global last_alert_message

    plan_list = to_dict_list(plan_file)
    date_exp_list = [plan.get("dateExp/String") for plan in plan_list]
    date_list_info = parse_date_list_java(" ".join(date_exp_list))
    date_time_list = date_list_info.get("planInfos")

    now = date_list_info.get("now")

    matched_plan_list = []
    for i in range(len(plan_list)):
        try:
            plan = plan_list[i]
            date_info = date_time_list[i]
            plan["date"] = date_info.get("value")
            plan["left_seconds"] = date_info.get("comment")
        except:
            pass

    def sort_plan(plan):
        date = plan.get("date")
        if date is None:
            return -1
        return date

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
        phone = plan.get("phone/String")
        left_seconds = plan.get("left_seconds")

        try:
            if (
                date_time is None
                or not is_active
                or left_seconds is None
                or (phone is not None and phone != "" and phone != current_phone)
            ):
                continue

            left_seconds = int(left_seconds)

            if left_seconds < 0:
                continue

            is_current = is_current_plan(left_seconds)
            delta = get_delta_time_by_str(date_time)
            msg = f"[{i}]\t[{date_time}]\t[{delta}]\t\t==> {plan_detail}"
            # msg = f"[{i}] [{left_seconds}] => [{delta}] => [{date_time}] => [{plan_exp}] =>  {plan_detail}"

            if left_seconds > 0 and next_plan is None:
                next_plan = plan
                next_message = msg
                next_detail = plan_detail
                next_left_seconds = left_seconds

            log_plan(msg, left_seconds)
            i += 1

            if is_current:
                log_error(f"[current-plan]{plan_detail}")
                matched_plan_list.append(plan)
        except Exception as e:
            log_error(f"[{plan_detail}]: {e}")

    if len(matched_plan_list) > 0:
        noti_current_plan(matched_plan_list)
        last_alert_message = ""
    elif next_plan is not None:
        log(log_head * 3)
        log_plan(next_message, next_left_seconds)
        log(log_head * 3)
        update_plan_message(next_plan)
        if last_alert_message != next_detail:
            log_error(f"[plan-updated] [{last_alert_message}] != [{next_detail}] ")
            log(log_head * 3)
            noti_next_plan(next_plan)
            last_alert_message = next_detail
            save_last_plan(last_alert_message)


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
            # if is_late_hour():
            #     log_error("is late hour")
            # else:
            start_plan()
            copy_file(plan_file, f"{plan_file}.bak")
        except:
            pass
        finally:
            # send_heart_beat()
            log(f"wait {wait_time} seconds")
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
