"""
Simple GUI + background thread to send key presses in sequence 1,2,3,4,q

Behavior (from gamer.md):
1. Show a window
2. Automatically start a thread
3. Window has a button that toggles start/pause of the thread
4. Thread on each run performs key press operations
5. Each run presses keys '1','2','3','4','q' in order

This implementation targets Windows and uses ctypes to call WinAPI functions
so there are no external dependencies.
"""

import threading
import time
import ctypes
import sys
import tkinter as tk
from tkinter import ttk

pause_location = (500, 500)  # Example fixed position for mouse click


class KeyPresserThread(threading.Thread):
    def __init__(
        self,
        keys,
        interval=1.0,
        pause_event=None,
        stop_event=None,
        status_cb=None,
        click_pos=None,
    ):
        super().__init__(daemon=True)
        self.keys = keys
        self.interval = interval
        self.pause_event = pause_event or threading.Event()
        self.stop_event = stop_event or threading.Event()
        self.status_cb = status_cb
        # click_pos should be a tuple (x, y) in screen coordinates, or None to disable
        self.click_pos = click_pos

    def run(self):
        # Runs until stop_event is set. When not paused, presses the sequence then sleeps.
        while not self.stop_event.is_set():
            if self.pause_event.is_set():
                # paused: wait a short while and loop
                time.sleep(0.1)
                continue

            for k in self.keys:
                if self.stop_event.is_set() or self.pause_event.is_set():
                    break
                try:
                    send_char(k)
                    if self.status_cb:
                        self.status_cb(f"Sent: {k}")
                except Exception as e:
                    # Do not raise in thread; report via status callback
                    if self.status_cb:
                        self.status_cb(f"Error sending {k}: {e}")
                time.sleep(3)  # tiny gap between key down/up

                # after one full sequence, optionally move mouse and click once
                if self.click_pos and not (
                    self.stop_event.is_set() or self.pause_event.is_set()
                ):
                    x, y = self.click_pos
                    try:
                        mouse_move_and_click(x, y)
                        if self.status_cb:
                            self.status_cb(f"Clicked at: {x},{y}")
                    except Exception as e:
                        if self.status_cb:
                            self.status_cb(f"Error clicking: {e}")

            # after one full sequence, wait before next sequence
            slept = 0.0
            while slept < self.interval:
                if self.stop_event.is_set() or self.pause_event.is_set():
                    break
                time.sleep(0.1)
                slept += 0.1


# ------------------ Windows key sending helpers ------------------
if sys.platform != "win32":

    def send_char_stub(c):
        # non-windows fallback: just print
        print(f"[stub] would send: {c}")

    def mouse_move_and_click_stub(x, y):
        print(f"[stub] would move mouse to: {x},{y} and left-click")

    def get_mouse_pos_stub(root=None):
        # If we have a tkinter root, use it to get pointer position; otherwise return (0,0)
        if root is not None:
            try:
                return (root.winfo_pointerx(), root.winfo_pointery())
            except Exception:
                return (0, 0)
        return (0, 0)

    send_char = send_char_stub
    mouse_move_and_click = mouse_move_and_click_stub
    get_mouse_pos = get_mouse_pos_stub
else:
    # Use VkKeyScanA + keybd_event (available on Windows) via ctypes
    user32 = ctypes.windll.user32

    def send_char(c):
        """Send a single character to the system using keybd_event.

        This maps the character to a virtual-key code using VkKeyScanA and
        presses any modifier (Shift) if needed.
        """
        ch = ord(c)
        vk_and_shift = user32.VkKeyScanA(ch)
        vk = vk_and_shift & 0xFF
        shift_state = (vk_and_shift >> 8) & 0xFF

        # If VkKeyScanA returns -1, mapping failed.
        if vk_and_shift == -1:
            raise ValueError(f"Can't map character: {c}")

        # constants for keybd_event
        KEYEVENTF_KEYUP = 0x0002
        VK_SHIFT = 0x10

        # press shift if needed
        if shift_state & 0x01:
            user32.keybd_event(VK_SHIFT, 0, 0, 0)
            time.sleep(0.01)

        # press key
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)

        # release shift if we pressed it
        if shift_state & 0x01:
            time.sleep(0.01)
            user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)

    # mouse helpers using user32
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    def mouse_move_and_click(x1=0, y1=0):
        global pause_location
        x, y = pause_location
        # move then click left button
        user32.SetCursorPos(int(x), int(y))
        # small pause to ensure cursor moved
        time.sleep(0.02)
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.01)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    def get_mouse_pos(root=None):
        pt = POINT()
        if user32.GetCursorPos(ctypes.byref(pt)):
            return (pt.x, pt.y)
        return (0, 0)


def main():
    root = tk.Tk()
    root.title("Gamer Key Presser")
    root.geometry("360x140")

    status_var = tk.StringVar(value="Initializing...")
    running_var = tk.StringVar(value="Running")

    # events to control thread
    pause_event = threading.Event()  # when set => paused
    stop_event = threading.Event()

    def update_status(text):
        status_var.set(text)

    keys = ["1", "2", "3", "4", "q"]
    interval_seconds = 1.0

    click_position = (500, 500)  # e.g., (500, 500) to enable clicking at that position

    presser = KeyPresserThread(
        keys=keys,
        interval=interval_seconds,
        pause_event=pause_event,
        stop_event=stop_event,
        status_cb=update_status,
        click_pos=click_position,
    )
    presser.start()  # auto-start per requirement
    status_var.set("Thread started (auto)")

    def toggle_pause():
        if pause_event.is_set():
            pause_event.clear()
            btn_toggle.config(text="Pause")
            running_var.set("Running")
            status_var.set("Resumed")
        else:
            pause_event.set()
            btn_toggle.config(text="Start")
            running_var.set("Paused")
            status_var.set("Paused")
            # start polling mouse position while paused
            poll_mouse_pos()

    # Poll mouse position and update status while paused
    def poll_mouse_pos():
        global pause_location
        if not pause_event.is_set():
            return
        pause_location = get_mouse_pos(root)
        x, y = pause_location
        status_var.set(f"Paused - mouse: {x},{y}")
        # schedule next poll only while still paused
        if pause_event.is_set():
            root.after(200, poll_mouse_pos)

    def on_close():
        # stop thread cleanly
        stop_event.set()
        # if paused, unpause to allow thread to exit quicker
        pause_event.clear()
        # give the thread a moment
        presser.join(timeout=1.0)
        root.destroy()

    frm = ttk.Frame(root, padding=12)
    frm.pack(fill=tk.BOTH, expand=True)

    lbl_state = ttk.Label(frm, textvariable=running_var)
    lbl_state.pack(anchor=tk.W)

    lbl_status = ttk.Label(frm, textvariable=status_var, wraplength=340)
    lbl_status.pack(anchor=tk.W, pady=(6, 10))

    btn_toggle = ttk.Button(frm, text="Pause", command=toggle_pause)
    btn_toggle.pack(side=tk.LEFT)

    # Extra: a Quit button to stop cleanly
    btn_quit = ttk.Button(frm, text="Quit", command=on_close)
    btn_quit.pack(side=tk.RIGHT)

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
