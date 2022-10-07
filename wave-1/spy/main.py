#!/usr/bin/env python3

import tkinter
import tkinter.filedialog

# create window and canvas
window = tkinter.Tk()
window.title("Orwell GPS v0.4")
can = tkinter.Canvas(window, width=800, height=800)
can.pack(side="right", padx=5, pady=5)
bg_img = tkinter.PhotoImage(file="map.gif")
can.create_image(400, 400, image=bg_img, tag="bg")

# create widgets on left panel
label1 = tkinter.Label(window, text="Orwell GPS 0.4", font="arial 18", pady=25)
label1.pack()
time_label = tkinter.Label(window, text="", font="arial 14")
time_label.pack()

# playback control widgets
pb_ctl_grid = tkinter.Frame(pady=10)
pb_ctl_grid.pack()
# if unable to load button icons, use text instead
try:
    img_pb_start = tkinter.PhotoImage(file="icons/start.png")
    img_pb_prev = tkinter.PhotoImage(file="icons/speed_down.png")
    img_pb_play = tkinter.PhotoImage(file="icons/play_pause.png")
    img_pb_stop = tkinter.PhotoImage(file="icons/stop.png")
    img_pb_next = tkinter.PhotoImage(file="icons/speed_up.png")
    img_pb_end = tkinter.PhotoImage(file="icons/end.png")
    t_pb_start, t_pb_prev, t_pb_play, = None, None, None
    t_pb_stop, t_pb_next, t_pb_end = None, None, None
except tkinter.TclError:
    print("unable to load icons")
    img_pb_start, img_pb_prev, img_pb_play, = None, None, None
    img_pb_stop, img_pb_next, img_pb_end = None, None, None
    t_pb_start = "Start"
    t_pb_prev = "Speed -"
    t_pb_play = "Play/Pause"
    t_pb_stop = "Stop"
    t_pb_next = "Speed +"
    t_pb_end = "End"

# construct buttons
btn_pb_start = tkinter.Button(pb_ctl_grid,
                              text=t_pb_start,
                              image=img_pb_start,
                              command=lambda:
                              reset())
btn_pb_start.grid(row=1, column=1)
btn_pb_prev = tkinter.Button(pb_ctl_grid,
                             text=t_pb_prev,
                             image=img_pb_prev,
                             command=lambda:
                             speedy_slider.set(speedy_slider.get()+8))
btn_pb_prev.grid(row=1, column=2)
btn_pb_play = tkinter.Button(pb_ctl_grid,
                             text=t_pb_play,
                             image=img_pb_play,
                             command=lambda: toggle_play())
btn_pb_play.grid(row=1, column=3)
btn_pb_stop = tkinter.Button(pb_ctl_grid,
                             text=t_pb_stop,
                             image=img_pb_stop,
                             command=lambda: stop())
btn_pb_stop.grid(row=1, column=4)
btn_pb_next = tkinter.Button(pb_ctl_grid,
                             text=t_pb_next,
                             image=img_pb_next,
                             command=lambda:
                             speedy_slider.set(speedy_slider.get()-8))
btn_pb_next.grid(row=1, column=5)
btn_pb_end = tkinter.Button(pb_ctl_grid,
                            text=t_pb_end,
                            image=img_pb_end,
                            command=lambda:
                            draw_instant())
btn_pb_end.grid(row=1, column=6)
scale_pb = tkinter.Scale(pb_ctl_grid,
                         from_=0,
                         orient="horizontal",
                         showvalue=False,
                         length=200)
scale_pb.grid(row=2, column=1, columnspan=6)

speedy_label = tkinter.Label(window, text="speed")
speedy_label.pack()
speedy_slider = tkinter.Scale(window,
                              orient="horizontal",
                              from_=160,
                              to=1,
                              showvalue=False,
                              length=160)
speedy_slider.set(80)
speedy_slider.pack()
connect_pts = tkinter.BooleanVar()
checkbox_connect = tkinter.Checkbutton(window,
                                       variable=connect_pts,
                                       onvalue=True,
                                       offvalue=False,
                                       text="draw path")
checkbox_connect.select()
checkbox_connect.pack()
btn_openfile = tkinter.Button(window,
                              text="Open log file",
                              command=lambda:
                              load_gps(tkinter.filedialog.askopenfilename()))
btn_openfile.pack()

# map offsets
offset_y1 = 4913.118
offset_x1 = 1635.682
offset_y2 = 4912.460
offset_x2 = 1636.690

# dict to store global variables
options = {
    "play": True,
    "old_pos": None,
    "run": True,
    "gps_data": None
}


# button callbacks
def toggle_play() -> None:
    options['play'] = not options['play']


def stop() -> None:
    options['play'] = False
    options['old_pos'] = None
    can.delete("path")


def reset() -> None:
    options['play'] = False
    options['old_pos'] = None
    can.delete("path")
    can.delete("person")
    scale_pb.set(0)


def draw_line(line, num_line) -> None:
    data = line.split(",")
    can.delete("person")
    time_label['text'] = f"{data[1][0:2]}:{data[1][2:4]}:{data[1][4:6]} UTC"

    x = ((float(data[4])-offset_x1) / (offset_x2-offset_x1) * 800)
    y = -((float(data[2])-offset_y1) / (offset_y1-offset_y2) * 800)

    # connect old position with new, avoid drawing if the positions
    # are from sentences that are too far from each other to avoid
    # skipping positions
    if options['old_pos'] is not None:
        if connect_pts.get():
            if abs(options['old_pos'][2] - num_line) < 2:
                can.create_line(options['old_pos'][0],
                                options['old_pos'][1],
                                x,
                                y,
                                tag="path")
    can.create_oval(x - 3, y - 3, x + 3, y + 3, fill="red", tag="person")
    options['old_pos'] = (x, y, num_line)


def draw_instant() -> None:
    """
    draw full path instantly
    """

    options['play'] = False
    options['old_pos'] = None
    can.delete("path")
    can.delete("person")
    for i in range(len(options['gps_data'])):
        draw_line(options['gps_data'][i], i)
    scale_pb.set(i)
    can.update()


def validate_data(line) -> bool:
    """
    check checksum of NMEA sentence
    """

    data = line[1:].split("*")
    checksum = 0
    for letter in bytes(data[0], "utf-8"):
        checksum ^= letter
    if str(hex(checksum)).upper()[2:] == data[1]:
        return True
    print("error on line: " + line)
    return False


def load_gps(filename) -> bool:
    """
    load GPS data from file

    GPS data are stored in options['gps_data']
    return True if successful, otherwise return False
    """
    if filename == ():
        return
    try:
        with open(filename, "r") as f:
            data = f.read().split('\n')
            f.close()
    except FileNotFoundError:
        print("could not open file")
        return False
    gps_data = []
    for i in data:
        if i.startswith("$GPGGA"):
            if validate_data(i):
                gps_data.append(i)
    scale_pb['to'] = len(gps_data)
    options['gps_data'] = gps_data
    scale_pb.set(0)
    return True


def tick() -> None:
    """
    main function of the program

    responsible for drawing things on map
    """

    # check if we are supposed to draw
    gps_data = options['gps_data']
    if gps_data is None:
        return
    num_line = scale_pb.get()
    if num_line >= len(gps_data):
        return
    if options['play']:
        scale_pb.set(num_line + 1)

    line = gps_data[num_line]
    draw_line(line, num_line)
    can.update()


if not load_gps("log.txt"):
    print("failed to open default file log.txt")

# mainloop of application
while options['run']:
    window.after(int(speedy_slider.get()**1/2))
    window.update()
    tick()
