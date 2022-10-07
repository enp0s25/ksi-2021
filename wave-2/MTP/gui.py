#!/usr/bin/env python3


import meme_transfer_protocol as mtp

from tkinter import BooleanVar, Checkbutton, Tk, Frame, Label, Entry, Button, Toplevel
from tkinter import Text
from tkinter.filedialog import askopenfilename
from typing import Tuple, Union

window = Tk()
window.title("MTP Client")

frame_entries = Frame(window, padx=10, pady=10)
frame_entries.pack()

l_ip = Label(frame_entries, text="IP:")
l_port = Label(frame_entries, text="port:")
l_nick = Label(frame_entries, text="nick:")
l_pass = Label(frame_entries, text="password:")
e_ip = Entry(frame_entries)
e_port = Entry(frame_entries)
e_nick = Entry(frame_entries)
e_pass = Entry(frame_entries)

l_ip.grid(row=0, column=0, sticky="w")
l_port.grid(row=1, column=0, sticky="w")
l_nick.grid(row=0, column=4, sticky="w")
l_pass.grid(row=1, column=4, sticky="w")
e_ip.grid(row=0, column=1, columnspan=3)
e_port.grid(row=1, column=1, columnspan=3)
e_nick.grid(row=0, column=5, columnspan=3)
e_pass.grid(row=1, column=5, columnspan=3)

frame_meme = Frame(window, padx=10)
frame_meme.pack()
var_nsfw = BooleanVar()
rb_nsfw = Checkbutton(frame_meme, variable=var_nsfw, onvalue=True,
                      offvalue=False, text="NSFW")
rb_nsfw.pack(anchor="w")
l_desc = Label(frame_meme, text="Description:")
l_desc.pack(anchor="w")
t_desc = Text(frame_meme, height=5, width=55)
t_desc.pack()
l_meme = Label(frame_meme, text="Meme")
l_meme.pack(anchor="w")
frame_file = Frame(frame_meme)
frame_file.pack(anchor="w")
b_file = Button(frame_file, text="Browse",
                command=lambda: l_file.configure(text=askopenfilename()))
b_file.pack(side="left")
l_file = Label(frame_file, text="")
l_file.pack(side="right")

frame_submit = Frame(window, padx=10, pady=10)
frame_submit.pack(side="right")
b_upload = Button(frame_submit, text="Submit", command=lambda: upload_meme())
b_upload.pack()


def show_msg(msg: str) -> None:
    '''
    Show toplevel window with message
    '''

    window1 = Toplevel(window)
    l_msg = Label(window1, text=msg, padx=5, pady=5)
    l_msg.pack()
    b_close = Button(window1, text="Ok", pady=4, 
                     command=lambda: window1.destroy())
    b_close.pack()

def check_entries() -> Union[None, Tuple[str, int, str, str]]:
    '''
    Validate data in entries and return them or highlight the problematic ones
    '''

    errors = False
    for entry in e_ip, e_port, e_nick, e_pass:
        entry['background'] = "white"

    ip = e_ip.get().strip()
    try:
        ints = map(int, ip.split("."))
        if len(tuple(ints)) != 4:
            e_ip['background'] = "#db6d6d"
            errors = True
        for i in ints:
            if i < 0 or i > 255:
                e_ip['background'] = "#db6d6d"
                errors = True
    except ValueError:
        e_ip['background'] = "#db6d6d"
        errors = True

    try:
        port = int(e_port.get().strip())
        if port > 65535:
            raise ValueError
    except ValueError:
        e_port['background'] = "#db6d6d"
        errors = True

    nick = e_nick.get().strip()
    if nick == "":
        e_nick['background'] = "#db6d6d"
        errors = True

    passw = e_pass.get().strip()
    if passw == "":
        e_pass['background'] = "#db6d6d"
        errors = True
    
    if errors:
        return None
    return (ip, port, nick, passw)

def upload_meme() -> None:
    '''
    acquire data and start meme transfer, display results
    '''

    entry_data = check_entries()
    if entry_data is None:
        show_msg("Error: Problem in these fields")
        return
    elif l_file['text'] == "":
        show_msg("Error: No file selected")
        return
    ip, port, nick, passw = entry_data
    desc = t_desc.get("1.0", "end-1c")
    isNSFW = var_nsfw.get()
    res = mtp.submit(ip, port, nick, (l_file['text'], desc, isNSFW, passw))
    if res:
        show_msg("Success!")
    else:
        show_msg("Error when sending meme!\nCheck console for more info")

window.mainloop()