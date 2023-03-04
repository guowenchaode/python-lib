import os
import threading
import tkinter as tk
import sys
import time
from PIL import ImageTk, Image

resolution = (960, 600)
Path = sys.argv[1]
Start = sys.argv[2]
Interval = 2
Index = 0

scaler = Image.ANTIALIAS

win = tk.Tk()
win_width = 1050
win_height = 650

sw = win.winfo_screenwidth()
sh = win.winfo_screenheight()
x = (sw - win_width) / 2
y = (sh - win_height) / 2

img_box_x = 0
img_box_y = 0
img_box_w = win_width
img_box_h = win_height-50
img_box_bg = '#ffffff'


win.title("电子相册")
win.geometry("%dx%d+%d+%d" % (win_width, win_height, x, y))

bg = tk.Label(win, bg='#DDDDDD')
bg.place(height=win_height, width=win_width, x=0, y=0)

img_in = Image.open(f"{Path}/{Start}")
w, h = img_in.size
size_new = ((int)(w * resolution[1] / h), resolution[1])
img_out = img_in.resize(size_new, scaler)
img = ImageTk.PhotoImage(img_out)
# img = ImageTk.PhotoImage(Image.open("load.jpg"))
panel = tk.Label(win, image=img)
panel.pack(side="bottom", fill="both", expand="yes")


def manual_img(e):
    global Index

    files = os.listdir(Path)
    i = 0
    for x in files:
        if not os.path.isfile(Path + '\%s' % x):
            break

        if i < Index:
            i += 1
            continue

        print('手动处理图片', x, Index)
        if not (x.endswith('.jpg') or x.endswith('.JPG')):
            i += 1
            Index += 1
            if Index >= len(files):
                Index = 0
            continue

        img_in = Image.open(Path + '\%s' % x)
        print(img_in)
        w, h = img_in.size
        size_new = ((int)(w * resolution[1] / h), resolution[1])
        img_out = img_in.resize(size_new, scaler)
        img2 = ImageTk.PhotoImage(img_out)
        # img2 = ImageTk.PhotoImage(Image.open(Path + '\%s' % x))
        panel.configure(image=img2)
        panel.image = img2
        Index += 1
        if Index >= len(files):
            Index = 0
        break


win.bind("<Button-1>", manual_img)



def image_change():
    global Index

    time.sleep(3)
    while True:
        files = os.listdir(Path)
        i = 0
        for x in files:
            if not os.path.isfile(Path + '\%s' % x):
                break

            if i < Index:
                i += 1
                continue

            print('show image', x, Index)
            if not (x.endswith('.jpg') or x.endswith('.JPG')):
                i += 1
                Index += 1
                if Index >= len(files):
                    Index = 0
                continue

            img_in = Image.open(Path + '\%s' % x)
            w, h = img_in.size
            size_new = ((int)(w * resolution[1] / h), resolution[1])
            img_out = img_in.resize(size_new, scaler)
            img2 = ImageTk.PhotoImage(img_out)
            # img2 = ImageTk.PhotoImage(Image.open(Path + '\%s' % x))
            panel.configure(image=img2)
            panel.image = img2
            Index += 1
            if Index >= len(files):
                Index = 0
            time.sleep(Interval)


def start_img():
    t = threading.Thread(target=image_change)
    t.start()


bt_start = tk.Button(win, text="start", command=start_img)
bt_start.place(x=img_box_x + img_box_w / 2, y=img_box_y + img_box_h + 20)

bt_stop = tk.Button(win, text="exit", command=win.quit)
bt_stop.place(x=img_box_x + img_box_w / 2-70, y=img_box_y + img_box_h + 20)

bt_manual = tk.Button(win, text="manu", command=manual_img)
bt_manual.place(x=img_box_x + img_box_w / 2-140, y=img_box_y + img_box_h + 20)


win.mainloop()
