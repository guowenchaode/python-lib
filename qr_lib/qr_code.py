########################################
# TOP #
########################################
############## TOP IMPORT FUNC #########
import sys

sys.path.append(r"D:\Git\github\python-lib")

from py_lib.func import log, get_copied, dt, read_file

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
    parser.add_argument("--file", dest="file", required=False, help="file")
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

import qrcode

MAX_LENGTH = 1500


def file_to_code(file_path):
    txt = read_file(file_path)
    return txt_to_code(txt)


def txt_to_code(txt=""):
    if txt.strip() == "":
        txt = get_copied()
    if len(txt) > MAX_LENGTH:
        txt = txt[:MAX_LENGTH]
    txt = txt.replace("	", "	")
    qr = qrcode.QRCode(version=1, box_size=1, border=5)
    qr.add_data(txt)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    now = dt()
    img_path = f"D:/__cache/qr_code/{now}.png"
    img.save(img_path)
    command = f"start {img_path}"
    os.system(command)


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
        elif args.action == "file_to_code":
            file_to_code(args.file)
        elif args.action == "txt_to_code":
            txt_to_code(args.text)
        else:
            # path = "D:\Git\github\python-lib\qr_lib\qr_code.py.jpg"
            txt_to_code()
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
