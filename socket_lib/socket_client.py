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
from threading import Thread

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


import socket

MESSAGE_END = "@#@#@#@#@#@#@#@#@#@#@#@#@#@#@#@#@"


def send_heart_beat(ip="192.168.3.137", port=2019):
    heart_beat_message = f"msg=heartbeat{MESSAGE_END}"
    send_message(heart_beat_message)


def send_message(message, ip="192.168.3.137", port=2019):
    thread = Thread(target=start_send_message, args=(message, ip, port))
    thread.start()


def start_send_message(message, ip="192.168.3.137", port=2019):
    try:
        log(f"start send message to server {ip}:{port}")
        ip_port = (ip, port)

        client = socket.socket()  # 创建一个套接字
        client.connect(ip_port)  # 连接目标IP的目标端口

        tmp = message.encode()
        client.send(tmp)

        data = client.recv(1024)  # 返回接收到的数据
        log(f"[server-message]:{data}")
        return data
    except Exception as e:
        traceback.print_exc()
    finally:
        log(f"send message completed!")


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
            send_heart_beat()
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
