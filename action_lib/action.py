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
    load_object,
    exe_script,
    move_file,
    mkdirs,
    dt,
    is_string,
    loop_sys_path_dir,
    get_file_name,
    get_file_name_without_ext,
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


def _rec(name):
    return name.replace(" ", "_").replace(".rec", "")


def _act(name):
    return get_file_name(name).lower()


def _tri(name):
    return name.lower().replace(" ", "_").replace(".tri", "")


def is_system_trigger(trigger_id):
    return trigger_id.startswith("$$")


def is_action_trigger(trigger_id):
    return not trigger_id.startswith("$$")


def execute_script(action_id, receiver_id, bat_file):
    if not os.path.exists(bat_file):
        return ""

    out, err = exe_script(bat_file)
    now = dt()

    action_dir = f"{ACTION_HISTORY_DIR}/{action_id}/runs/{now}"
    path = f"{action_dir}/receivers/{receiver_id}.log"
    log(f"[action-history] {action_dir}")
    log(f"[action-receiver] {path}")

    content = f"OUT:\n{out}\n\nERROR:{err}"
    write_file(path, content)

    receiver_history_path = f"{RECEIVER_HISTORY_DIR}/{receiver_id}.log"
    receiver_log = f"{now}: [{action_id}]\n"
    write_file(receiver_history_path, receiver_log)


class action_receiver:
    def __init__(self, id):
        self.id = _rec(id)
        self.script = ""
        self.action = ""

    def execute(self):
        log(f"===> [RECEIVER][{self.id}] execute")
        if self.script != "":
            execute_script(self.action.id, self.id, self.script)


class action_trigger:
    def __init__(self, id):
        self.id = _tri(id)
        self.action = ""

    def is_matched(self):
        matched = True
        log(f"===> [TRIGGER][{self.id}] matched: {matched}")
        return matched


class action:
    def __init__(self, id, path="", simple=False):
        self.id = _act(id)
        self.trigger_list = []
        self.receiver_list = []
        self.is_simple = simple
        self.path = path

    def add_pending_trigger(self, trigger):
        trigger.action = self
        self.trigger_list.append(trigger)

    def add_receiver(self, receiver):
        receiver.action = self
        self.receiver_list.append(receiver)

    def contains(self, trigger):
        is_contain = False

        if self.is_simple:
            is_contain = trigger.id == self.id
        else:
            for tri in self.trigger_list:
                if trigger.id == tri.id:
                    is_contain = True

        log(f"==> [ACTION][{self.id}] contains {trigger.id}: {is_contain}")
        return is_contain

    def is_matched(self):
        matched = True

        if self.is_simple:
            return True
        else:
            for tri in self.trigger_list:
                if not tri.is_matched():
                    matched = False
                    break

        log(f"===> [ACTION][{self.id}] matched: {matched}")
        return matched

    def execute(self):
        log(f"===> [ACTION][{self.id}] execute")

        if self.is_simple:
            if os.path.exists(self.path):
                execute_script(self.id, self.id, self.path)
        else:
            for receiver in self.receiver_list:
                receiver.execute()


class action_manager:
    def __init__(self):
        self.action_list = []
        self.triggers = {}

    def get_related_action_list(self, trigger):
        log(f"=> [STEP-1] load related actions")
        matched_list = []
        for act in list(self.action_list):
            if act.contains(trigger):
                matched_list.append(act)

        return matched_list

    def get_matched_action_list(self, trigger):
        related_action_list = self.get_related_action_list(trigger)
        matched_list = []

        log(f"=> [STEP-2] load matched actions")
        for act in list(related_action_list):
            if act.is_matched():
                matched_list.append(act)

        return matched_list

    def execute(self, trigger):
        log(f"[TRIGGER]{trigger}")
        trigger_id = trigger.id

        if is_system_trigger(trigger_id):
            self.execute_system_actions(trigger)
        else:
            if trigger_id not in self.triggers:
                log_error(f"unkown trgger: [{trigger_id}]")
                return
            self.execute_actions(trigger)

    def execute_system_actions(self, trigger):
        trigger_id = trigger.id

        if SYSTEM_ACTION_RELOAD == trigger_id:
            reload()

    def execute_actions(self, trigger):
        matched_action_list = self.triggers[trigger.id]

        log(f"=> [STEP-3] execute matched actions")
        for act in matched_action_list:
            log(f"==> [ACTION] execute matched action [{act.id}]")
            act.execute()

    def append_action(self, act):
        self.action_list.append(act)

        if act.is_simple:
            if act.id not in self.triggers:
                self.triggers[act.id] = []
            self.triggers[act.id].append(act)
        else:
            for trigger in act.trigger_list:
                if trigger.id not in self.triggers:
                    self.triggers[trigger.id] = []
                self.triggers[trigger.id].append(act)  # load all window bat as action

    def load_bat_actions(self):
        def append_bat(file_path):
            file_name = get_file_name_without_ext(file_path)
            act = action(file_name, file_path, True)
            self.append_action(act)

        def is_bat_dir(dir_path):
            return (
                r"D:\__Share\script\windows"
                in dir_path
            )

        loop_sys_path_dir(is_bat_dir, append_bat, None, False)

    # load all actions
    def load_common_actions(self):
        actions = load_object(ACTIONS_DIR)
        for action_id, action_info in actions.items():
            act_path = f"{ACTIONS_DIR}/{action_id}"
            try:
                log_error(f"=> [ACTION] {action_id}")

                is_simple = is_string(action_info)
                act = action(action_id, act_path, is_simple)
                if not is_simple:
                    for trigger_id in action_info["trigger_list"].keys():
                        trigger = action_trigger(trigger_id)
                        log(f"==> [ACTION] [{action_id}]: [TRIGGER] {trigger.id}")
                        act.add_pending_trigger(trigger)

                    for receiver_id in action_info["receiver_list"].keys():
                        receiver = action_receiver(receiver_id)
                        receiver.script = f"{act_path}/receiver_list/{receiver_id}"
                        log(f"==> [ACTION] [{action_id}]: [RECEIVER] {receiver.id}")
                        act.add_receiver(receiver)
                self.append_action(act)  # MUST APPEND AFTER LOADED
            except Exception as e:
                traceback.print_exc()

    def load(self):
        log_error(f"==> [START-LOAD-ACTION]")
        self.reset()

        self.load_bat_actions()
        self.load_common_actions()

    def reset(self):
        self.action_list = []
        self.triggers = {}


"""
"""
SYSTEM_ACTION_RELOAD = "$$reload"

ACTION_HOME = r"D:\__Alex\__action"
ACTIONS_DIR = f"{ACTION_HOME}/actions"
ACTION_HISTORY = f"{ACTION_HOME}/.history"
ACTION_HISTORY_DIR = f"{ACTION_HISTORY}/actions"
TRIGGER_HISTORY_DIR = f"{ACTION_HISTORY}/triggers"
RECEIVER_HISTORY_DIR = f"{ACTION_HISTORY}/receivers"

PENDING_DIR = f"{ACTION_HISTORY}/pending"
PROCESSING_DIR = f"{ACTION_HISTORY}/processing"
COMPLETED_DIR = f"{ACTION_HISTORY}/completed"
FAILED_DIR = f"{ACTION_HISTORY}/failed"

manager = action_manager()

ACTION_DISK_FREE = "disk_free_is_less_than_10gb"

MIN_EVENT_IN_SECOND = 2


def execute(trigger):
    if isinstance(trigger, action_trigger):
        manager.execute(trigger)
    elif isinstance(trigger, str):
        manager.execute(action_trigger(trigger))


def execute_trigger(trigger_id):
    try:
        tri_path = f"{PENDING_DIR}/{trigger_id}"
        tri_path = move_action_file(tri_path, PROCESSING_DIR)
        trigger = action_trigger(trigger_id)
        execute(trigger)
        move_action_file(tri_path, COMPLETED_DIR)
    except Exception as e:
        traceback.print_exc()
        move_action_file(tri_path, FAILED_DIR)


def move_action_file(path, to_dir):
    return move_file(path, to_dir)


def add_pending_trigger(trigger_id):
    tri_path = f"{PENDING_DIR}/{trigger_id}"
    if os.path.exists(tri_path):
        log_error(f"[existed-trigger]: {tri_path}")
        return
    log_success(f"[add-trigger]: {tri_path}")
    write_file(tri_path, "")


def execute_triggers():
    files = list(os.listdir(PENDING_DIR))

    system_triggers = list(filter(is_system_trigger, files))
    action_triggers = list(filter(is_action_trigger, files))

    for trigger_id in system_triggers:
        execute_trigger(trigger_id)

    for trigger_id in action_triggers:
        t7 = Thread(target=execute_trigger, args=(trigger_id,))
        t7.start()


def start_action_manager():
    manager.load()
    while True:
        try:
            execute_triggers()
        except:
            pass
        time.sleep(1)


def reload():
    log_error("reload-action-manager")
    manager.load()


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
