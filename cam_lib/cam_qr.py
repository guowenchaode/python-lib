########################################
# TOP #
########################################
############## TOP IMPORT FUNC #########
import sys

sys.path.append(r"D:/Git/github/python-lib")

from py_lib.func import log, write_file, dt, set_copied

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
import cv2
from windows_lib.notification import noti

LOG_PATH = r"D:/__cache/qr_code/input.log"

last_data = ""


def process_qr(cam_frame):
    global last_data
    # detect and decode
    detector = cv2.QRCodeDetector()
    data, bbox, straight_qrcode = detector.detectAndDecode(cam_frame)
    # if there is a QR code

    if bbox is None or data == "":
        return

    if data == last_data:
        log(f"QRCode data: same data")
    else:
        set_copied(data)
        date_time = dt()
        msg = f"{date_time}:\t[{data}]\n"
        last_data = data
        log(f"QRCode data:\n{msg}")
        write_file(LOG_PATH, msg)
        noti("qr saved")


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
