
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


class KeyPresserThread(threading.Thread):
	def __init__(self, keys, interval=1.0, pause_event=None, stop_event=None, status_cb=None):
		super().__init__(daemon=True)
		self.keys = keys
		self.interval = interval
		self.pause_event = pause_event or threading.Event()
		self.stop_event = stop_event or threading.Event()
		self.status_cb = status_cb

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
				time.sleep(1)  # tiny gap between key down/up

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

	send_char = send_char_stub
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

	presser = KeyPresserThread(keys=keys, interval=interval_seconds, pause_event=pause_event, stop_event=stop_event, status_cb=update_status)
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

