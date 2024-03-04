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
    schedule,
    dt,
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
from tkinter import *
from tkinter.ttk import *
from threading import Thread

current_dir = os.path.dirname(os.path.realpath(__file__))

MESSAGE_FILE = f"{current_dir}/message.localtest.txt"


def load_message():
    return read_file(MESSAGE_FILE)


def save_message(message):
    return write_file(MESSAGE_FILE, message, False)


def create_tk(x, y):
    floating_window = Tk()
    # floating_window.geometry('+0+0')
    floating_window.geometry(f"+{x}+{y}")
    floating_window.attributes("-topmost", True)
    floating_window.wm_overrideredirect(True)
    return floating_window


# infinite loop
class message_window:
    # def __init__(self, x=-955, y=1080, font_size=30):
    def __init__(self, x=0, y=0, font_size=20):
        self.l1 = ""
        self.time = dt()
        self.message = load_message()
        self.stop = False
        self.x = x
        self.y = y
        self.font_size = font_size

    def on_enter(self, arg1):
        # update_message(f"hover: {arg1}")
        self.root.withdraw()
        schedule(3, lambda n: self.root.deiconify())

    def show_window(self):
        self.root = create_tk(self.x, self.y)

        style = Style()
        style.configure(
            "BW.TLabel",
            foreground="#f00",
            background="black",
            # width=500,
            font=("Times New Roman", self.font_size, ""),
        )

        self.l1 = Label(text="Test", style="BW.TLabel")
        self.l1.bind("<Enter>", self.on_enter)
        self.l1.pack()

        mainloop()

    def update_datetime(self):
        while not self.stop:
            try:
                self.time = dtl()
                self.update()
            except Exception as e:
                traceback.print_exc()
            finally:
                time.sleep(1)

    def start_update(self):
        t1 = Thread(target=self.update_datetime)
        t1.start()

    def show(self):
        self.start_update()
        self.show_window()

    def set_message(self, message):
        log(f"update message: {message}")
        self.message = message

    def update(self):
        if isinstance(self.l1, Label):
            self.message = load_message()
            self.l1["text"] = f"{self.time}: {self.message}"


window = ""


def show_message(x=0, y=0):
    global window
    window = message_window(x, y)
    window.show()


def update_message(message):
    save_message(message)
    if isinstance(window, message_window):
        window.set_message(message)
        return True
    return False


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
        elif args.action == "update_message":
            update_message(args.text)
        else:
            show_message()
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
