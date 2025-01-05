########################################
# TOP #
########################################
############## TOP IMPORT FUNC #########
import sys

sys.path.append(r"D:/Git/github/python-lib")

from py_lib.func import (
    log,
    log_error,
    log_success,
    sleep,
    read_file,
    write_file,
    format_json,
    loop_dir,
    now,
    dtl,
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

import sys
from action_lib.action import add_pending_trigger

from cvzone.HandTrackingModule import HandDetector

detector = HandDetector(
    staticMode=False, maxHands=2, modelComplexity=1, detectionCon=0.5, minTrackCon=0.5
)

HAND_LEFT = "Left"
HAND_RIGHT = "Right"

CAM_HAND = "CAM-HAND"
LEFT_HAND_CODE = ""
RIGHT_HAND_CODE = ""

LAST_LEFT_HAND_FINGER_COUNT = -1
LAST_RIGHT_HAND_FINGER_COUNT = -1

HAND_CODE = "Hand"

MIN_EVENT_IN_SECOND = 1

log_path = f"{__file__}.localtest.log"

event_start_date = None
event_end_date = None

start_event = False


def get_hand_detail(hand_info):
    lmList1 = hand_info["lmList"]  # List of 21 landmarks for the first hand
    bbox1 = hand_info[
        "bbox"
    ]  # Bounding box around the first hand (x,y,w,h coordinates)
    center1 = hand_info["center"]  # Center coordinates of the first hand
    handType1 = hand_info["type"]  # Type of the first hand ("Left" or "Right")

    # Count the number of fingers up for the first hand
    fingers1 = detector.fingersUp(hand_info)

    finger_count = fingers1.count(1)
    label = f"{handType1} Hand = {finger_count} Fingers"
    log(label)
    # event_message = f'{handType1}-{finger_count}'
    # fire_event('CAM', 'HAND', event_message)

    return (handType1, finger_count, bbox1)


def parse_cam_info(hand_type, finger_count, bbox1):
    global LEFT_HAND_CODE, RIGHT_HAND_CODE, event_start_date
    label = f"{hand_type} Hand = {finger_count} Fingers"
    (startX, startY, width, height) = bbox1

    hand_code = LEFT_HAND_CODE if hand_type == HAND_LEFT else RIGHT_HAND_CODE

    event_delta = get_event_delta(event_start_date)
    label = f"{label} [{event_delta}s] [{hand_code}]"
    return (startX, startY, startX + width, startY + height, label)


def process_hand_event(hand_type, finger_count, bbox1):
    global LEFT_HAND_CODE, RIGHT_HAND_CODE, LAST_LEFT_HAND_FINGER_COUNT, LAST_RIGHT_HAND_FINGER_COUNT

    if hand_type == HAND_LEFT and LAST_LEFT_HAND_FINGER_COUNT != finger_count:
        LEFT_HAND_CODE = f"{LEFT_HAND_CODE}{finger_count}"
        LAST_LEFT_HAND_FINGER_COUNT = finger_count
        log_success(f"LEFT_HAND_CODE: {LEFT_HAND_CODE}")

    if hand_type == HAND_RIGHT and LAST_RIGHT_HAND_FINGER_COUNT != finger_count:
        RIGHT_HAND_CODE = f"{RIGHT_HAND_CODE}{finger_count}"
        LAST_RIGHT_HAND_FINGER_COUNT = finger_count
        log_success(f"RIGHT_HAND_CODE: {RIGHT_HAND_CODE}")


def process_hand_info(hand_info):
    (hand_type, finger_count, bbox1) = get_hand_detail(hand_info)
    process_hand_event(hand_type, finger_count, bbox1)
    return parse_cam_info(hand_type, finger_count, bbox1)


def reset():
    global LEFT_HAND_CODE, RIGHT_HAND_CODE, LAST_LEFT_HAND_FINGER_COUNT, LAST_RIGHT_HAND_FINGER_COUNT, start_event, event_start_date, event_end_date
    LEFT_HAND_CODE = ""
    RIGHT_HAND_CODE = ""
    LAST_LEFT_HAND_FINGER_COUNT = -1
    LAST_RIGHT_HAND_FINGER_COUNT = -1
    start_event = False
    event_start_date = None
    event_end_date = None


def trigger_hand(hand_code):
    msg = dtl() + ": " + hand_code + "\n"
    write_file(log_path, msg)
    add_pending_trigger(hand_code)


def is_valid_date(event_start_date, event_end_date):
    total_seconds = get_event_delta(event_start_date, event_end_date)
    valid_date = total_seconds >= MIN_EVENT_IN_SECOND
    return valid_date


def get_event_delta(event_start_date, event_end_date=None):
    if event_start_date is None:
        return -1

    if event_end_date is None:
        event_end_date = now()

    date_delta = event_end_date - event_start_date
    total_seconds = date_delta.total_seconds()
    return int(total_seconds)


def fire_hand_event():
    global LEFT_HAND_CODE, RIGHT_HAND_CODE, event_end_date, event_start_date
    
    try:
        event_end_date = now()
        valid_event = is_valid_date(event_start_date, event_end_date)

        if not valid_event:
            return

        if LEFT_HAND_CODE == "" and RIGHT_HAND_CODE == "":
            return

        if RIGHT_HAND_CODE != "" and LEFT_HAND_CODE != "":
            trigger_hand(
                f"{HAND_CODE}-{HAND_LEFT}-{HAND_RIGHT}-{LEFT_HAND_CODE}-{RIGHT_HAND_CODE}"
            )
        elif LEFT_HAND_CODE != "":
            trigger_hand(f"{HAND_CODE}-{HAND_LEFT}-{LEFT_HAND_CODE}")
        elif RIGHT_HAND_CODE != "":
            trigger_hand(f"{HAND_CODE}-{HAND_RIGHT}-{RIGHT_HAND_CODE}")

    except Exception as e:
            traceback.print_exc()
    finally:
        reset()



def process_hand(frame, black_image):
    global start_event, event_start_date

    hands, img = detector.findHands(frame, draw=True, flipType=True)

    have_hands = hands is not None and len(hands) > 0

    # Check if any hands are detected
    hand0 = None
    hand1 = None

    # if not start and no hands will return
    if not start_event and not have_hands:
        return []

    # if have hands and not started will start event
    elif not start_event and have_hands:
        start_event = True
        event_start_date = now()
        log_success(f"start event: {event_start_date}")

    elif start_event and not have_hands:
        fire_hand_event()
        return []

    hand0 = process_hand_info(hands[0])

    if len(hands) == 2:
        hand1 = process_hand_info(hands[1])

    if hand0 and hand1:
        return [hand0, hand1]
    elif hand0:
        return [hand0]


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
