########################################
# TOP #
########################################
############## TOP IMPORT FUNC #########
import sys

sys.path.append(r"D:/Git/github/python-lib")

from py_lib.func import (
    log,
    log_error,
    now,
    sleep,
    read_file,
    write_file,
    format_json,
    loop_dir,
    log_event,
    log,
    sleep,
    now,
    format_file_name,
    date_as_log,
    time_as_file,
    format_delta_date,
    log_event,
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
class EventTimer:

    def __init__(
        self,
        name,
        stop_interval_seconds=60,
        run_interval_seconds=60,
        on_stop=None,
        on_run=None,
    ):
        self.name = name
        self.stop_interval_seconds = stop_interval_seconds
        self.run_interval_seconds = run_interval_seconds
        self.start = now()
        self.count = 0
        self.last_time = None
        self.on_run = on_run
        self.on_stop = on_stop
        self.total_run_seconds = 0
        self.total_stop_seconds = 0

    def save(self, type, value):
        name = format_file_name(value)
        path = f"C:/Users/e531866/Desktop/_GUOZHENG/tree/data/event/{self.name}/{type}/{name}"
        os.makedirs(path)

    def save_stop(self, interval):
        date_path = date_as_log()
        time_path = time_as_file()
        interval = format_delta_date(interval)
        self.log(f"STOP", interval)
        path = f"C:/Users/e531866/Desktop/_GUOZHENG/tree/data/event/{self.name}/STOP/{date_path}/{time_path}-{interval}"
        os.makedirs(path)

    def save_run(self, interval):
        date_path = date_as_log()
        time_path = time_as_file()
        interval = format_delta_date(interval)
        self.log(f"RUN", interval)
        path = f"C:/Users/e531866/Desktop/_GUOZHENG/tree/data/event/{self.name}/RUN/{date_path}/{time_path}-{interval}"
        os.makedirs(path)

    def log(self, type, value):
        log(f"[Event-{self.name}] [{type}] {value}")

    def reset(self):
        self.start = now()
        self.last_time = None
        self.count = 0

    def receive(self):
        current = now()
        # self.log('Receive', current)
        if self.last_time is None:
            log_event(self.name, "START")
            self.last_time = now()
        else:
            interval = current - self.last_time
            interval_seconds = interval.total_seconds()

            if interval_seconds < 1:
                return
            # self.log('Interval', interval)
            if interval_seconds > self.stop_interval_seconds:
                log_event(self.name, "STOP")
                self.reset()
                # info = f'{current} == {interval}'.replace(':', '-')
                self.save_stop(interval)
                self.total_stop_seconds = interval_seconds

                if self.on_stop is None:
                    self.log("Stop", f"{interval} at {current}")
                else:
                    self.on_stop(interval)
                return
            log_event(self.name, "RECEIVE")
            self.last_time = current
        run_interval = current - self.start
        run_interval_seconds = run_interval.total_seconds()

        self.total_run_seconds = run_interval_seconds

        if int(run_interval_seconds) % self.run_interval_seconds == 0:
            self.save_run(run_interval)

        if self.on_run is not None:
            self.on_run(run_interval)

        self.log("Time", run_interval)
        self.count = self.count + 1


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
