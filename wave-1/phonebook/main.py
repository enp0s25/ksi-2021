#!/usr/bin/env python3


# import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.ttk import OptionMenu, Treeview, Style
from tkinter import StringVar, Tk, Entry, Toplevel, Label, Frame
from tkinter import Scrollbar, Button, Checkbutton, BooleanVar
import json
import re
import datetime
from typing import Any, Dict, List, Tuple, Union


_globals = {
    "db_file": ""
    }

detached: List[str] = []
columns = ["name", "birthday", "email", "phone", "note"]

REGEX_EMAIL = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
REGEX_PHONE = r"^[+]?[ ]*(\d+[ ]*)+$"
REGEX_BDAY1 = r"^\d+-\d+-\d+$"
REGEX_BDAY2 = r"^\d+-\d+$"


window = Tk()
window.title("Phonebook")

# build main window widgets
frame_ppl = Frame(window, padx=10, pady=10)
frame_ppl.pack(side='right', anchor="n")

table_scroll = Scrollbar(frame_ppl)
table_scroll.pack(side="right", fill="y")

table = Treeview(frame_ppl,
                 height=20,
                 yscrollcommand=table_scroll.set,
                 xscrollcommand=table_scroll.set)
table.pack()

table_scroll.config(command=table.yview_scroll)

style = Style()
style.configure("Treeview.Heading", font=("Monospace", 12, "bold"))
style.configure("Treeview", font=("Monospace", 11))

table['columns'] = columns
table.column("#0", width=0,  stretch="no")
for col in columns:
    table.heading(col, text=col)
    table.column(col, width=200)


# widgets on left side
contacts_label = Label(window,
                       text="Contacts",
                       font="Monospace 14",
                       padx=10,
                       pady=10)
contacts_label.pack()

search_bar = Entry(window)
search_bar.pack()

btn_open_contacts = Button(window,
                           text="Open DB",
                           font="Monospace 11",
                           command=lambda:
                           load_db(askopenfilename()))
btn_open_contacts.pack()

btn_new = Button(window,
                 text="New",
                 font="Monospace 11",
                 command=lambda: new_contact_prompt())
btn_new.pack()
btn_edit = Button(window,
                  text="Edit",
                  font="Monospace 11",
                  state="disabled",
                  command=lambda: edit_contact_prompt())
btn_edit.pack()
btn_delete = Button(window,
                    text="Delete",
                    font="Monospace 11",
                    state="disabled",
                    command=lambda: table.delete(*table.selection()))
btn_delete.pack()

sort_by_var = StringVar()
sort_by_var.set("A-Z")
sort_by = OptionMenu(window, sort_by_var, "A-Z", "A-Z", "Z-A")
sort_by.pack()

vcard_export = Button(window,
                      text="Export vCard",
                      font="Monospace 11",
                      state="disabled",
                      command=lambda: export_vcard())
vcard_export.pack()
vcard_import = Button(window,
                      text="Import vCard",
                      font="Monospace 11",
                      command=lambda: import_vcard())
vcard_import.pack()

show_col_vars: List[BooleanVar] = []
for i in columns:
    ch_button_var = BooleanVar()
    ch_button_var.set(True)
    Checkbutton(window,
                variable=ch_button_var,
                onvalue=True,
                offvalue=False,
                text=i).pack()
    show_col_vars.append(ch_button_var)


def load_db(filename: str) -> None:
    '''load contacts from file into table'''

    has_birthday: List[Tuple[str, Union[None, int]]] = []
    today = datetime.date.today()
    # return if open file dialog was cancelled
    if filename == ():
        return
    try:
        with open(filename, "r") as f:
            contacts = json.load(f)
            f.close()
    except FileNotFoundError:
        print("file "+filename+" doesn't exist")
        return

    _globals['db_file'] = filename

    for item in table.get_children():
        table.delete(item)

    for col in table['columns']:
        width = min(max(map(lambda x: len(x[col]), contacts)) * 10, 300)
        table.column(col, width=width)
        table.heading(col, text=col)

    sort_by_var.set("A-Z")
    contacts.sort(key=lambda x: x['name'].lower())

    for i in range(len(contacts)):
        row_vals: List[str] = []
        # check birthday
        if contacts[i]['birthday'] != "":
            year = None
            bd_tuple = list(map(int, contacts[i]['birthday'].split("-")))
            if len(bd_tuple) == 3:
                year = bd_tuple.pop(0)
            if bd_tuple[0] == today.month and bd_tuple[1] == today.day:
                has_birthday.append((contacts[i]['name'], year))
        for j in range(len(columns)):
            row_vals.append(contacts[i][columns[j]])
        table.insert(parent="", index="end", iid=i, values=row_vals)
    table['displaycolumns'] = columns[:]

    display_bdays(has_birthday, today.year)


def display_bdays(birthdays: List[Tuple[str, Union[None, int]]],
                  year: int) -> None:
    '''create window that shows people who have birthday today'''

    if len(birthdays) == 0:
        return
    bday_window = Toplevel(window)
    bday_window.title("Todays birthdays")
    bday_label = Label(bday_window,
                       text="Todays birthdays",
                       font="Monospace 12 bold",
                       padx=10,
                       pady=10)
    bday_label.pack()
    for person in birthdays:
        text = person[0]
        # if year is specified also show age
        if person[1] is not None:
            text += f" ({year - person[1]})"
        Label(bday_window, text=text, font="Monospace 10").pack()
    exit_button = Button(bday_window,
                         text="Ok",
                         font="Monospace 11",
                         command=bday_window.destroy)
    exit_button.pack()


def export_vcard() -> None:
    '''export single contact as vCard 3.0 file'''

    name, bday, email, phone, note = table.item(table.selection())['values']
    vcard_out = "BEGIN:VCARD\nVERSION:3.0\n"
    vcard_out += "N:" + ";".join(name.split()) + "\n"
    vcard_out += "FN:" + name + "\n"
    if bday != "":
        vcard_out += "BDAY:" + bday + "\n"
    if email != "":
        vcard_out += "EMAIL:" + email + "\n"
    if phone != "":
        vcard_out += "TEL:" + phone + "\n"
    if note != "":
        vcard_out += "NOTE:" + note + "\n"
    vcard_out += "END:VCARD"

    filename = asksaveasfilename()
    if filename == ():
        return
    with open(filename, "w") as f:
        f.write(vcard_out)
        f.close()


def import_vcard() -> None:
    '''import single contact as vCard 3.0 file'''

    filename = askopenfilename()
    if filename == ():
        return
    with open(filename, "r") as f:
        card = f.readlines()
        f.close()
    name, bday, email, phone, note = "", "", "", "", ""
    if card[0].strip() == "BEGIN:VCARD" and card[1].strip() == "VERSION:3.0":
        for line in card:
            if line.startswith("FN:"):
                name = line[3:].strip()
            elif line.startswith("BDAY:"):
                bday = line[5:].strip()
            elif line.startswith("EMAIL:"):
                email = line[6:].strip()
            elif line.startswith("TEL:"):
                phone = line[4:].strip()
            elif line.startswith("NOTE:"):
                note = line[5:].strip()
        if name == "":
            print("could not find name in vCard")
            return
        if len(table.get_children()) == 0:
            i = 0
        else:
            i = max(map(int, table.get_children())) + 1
        row_vals = [name, bday, email, phone, note]
        table.insert(parent="", index="end", iid=i, values=row_vals)
        sort_contacts()
    else:
        print("not valid vCard")


def show_columns(*args: Any) -> None:
    '''change which columns should be visible in table'''

    showcolumns = columns[:]
    for i in range(len(columns)):
        if not show_col_vars[i].get():
            showcolumns.remove(columns[i])
    table['displaycolumns'] = showcolumns


def sort_contacts(*args: Any) -> None:
    '''sort contacts in table by name'''

    mode = sort_by_var.get()
    contacts: List[Tuple[str, Dict]] = []
    for i in table.get_children():
        contacts.append((i, table.item(i)))
    if mode == "A-Z":
        contacts.sort(key=lambda x: x[1]['values'][0].lower())
    else:
        contacts.sort(key=lambda x: x[1]['values'][0].lower(), reverse=True)
    for i in range(len(contacts)):
        table.move(contacts[i][0], "", i)


def check_selected() -> None:
    '''enable or disable buttons based on number of selected contacts'''

    selected = table.selection()
    if len(selected) == 0:
        btn_delete['state'] = "disabled"
        btn_edit['state'] = "disabled"
        vcard_export['state'] = "disabled"
    elif len(selected) == 1:
        btn_delete['state'] = "normal"
        btn_edit['state'] = "normal"
        vcard_export['state'] = "normal"
    else:
        btn_delete['state'] = "normal"
        btn_edit['state'] = "disabled"
        vcard_export['state'] = "disabled"


def mk_window(values: List, sel_contact: Dict) -> None:
    '''make toplevel window for adding/editing contact'''

    if values == []:
        is_new_contact = True
    else:
        is_new_contact = False
    window1 = Toplevel(window)
    if is_new_contact:
        window1.title("New contact")
        callback_func = new_contact
        window_name = Label(window1,
                            text="New contact",
                            font="Monospace 12 bold",
                            pady=5)
    else:
        window1.title("Edit contact")
        callback_func = edit_contact
        window_name = Label(window1,
                            text="Edit contact",
                            font="Monospace 12 bold",
                            pady=5)
    window_name.pack()
    error_label = Label(window1,
                        text="",
                        fg="#ff0000",
                        font="Monospace 10")
    error_label.pack()
    frame_person_info = Frame(window1)
    frame_person_info.pack()

    l_name = Label(frame_person_info, text="Name: *")
    l_bday = Label(frame_person_info, text="Birthday:")
    l_email = Label(frame_person_info, text="Email: **")
    l_phone = Label(frame_person_info, text="Phone: **")
    l_note = Label(frame_person_info, text="Note:")
    e_name = Entry(frame_person_info)
    e_bday = Entry(frame_person_info)
    e_email = Entry(frame_person_info)
    e_phone = Entry(frame_person_info)
    e_note = Entry(frame_person_info)

    l_name.grid(row=0, column=0, sticky="w")
    e_name.grid(row=0, column=1)
    l_bday.grid(row=1, column=0, sticky="w")
    e_bday.grid(row=1, column=1)
    l_email.grid(row=2, column=0, sticky="w")
    e_email.grid(row=2, column=1)
    l_phone.grid(row=3, column=0, sticky="w")
    e_phone.grid(row=3, column=1)
    l_note.grid(row=4, column=0, sticky="w")
    e_note.grid(row=4, column=1)

    entries = (e_name, e_bday, e_email, e_phone, e_note)

    if not is_new_contact:
        for i in range(len(entries)):
            entries[i].insert(0, values[i])

    btn_submit = Button(window1,
                        text="Submit",
                        font="Monospace 11",
                        command=lambda:
                        callback_func(window1,
                                      entries,
                                      error_label,
                                      sel_contact))
    btn_submit.pack()


def new_contact_prompt() -> None:
    mk_window([], {})


def edit_contact_prompt() -> None:
    selected_contact = table.item(table.selection())
    mk_window(selected_contact['values'], selected_contact)


def check_entries(entries: Tuple[Entry, ...]) -> bool:
    '''validate entries in add/edit contact toplevel window'''

    name, bday, email, phone, note = map(lambda x: x.get(), entries)

    month_days = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

    # reset BGs and err label
    for entry in entries:
        entry['background'] = "white"

    errors = False

    if name == "":
        entries[0]['background'] = "#db6d6d"
        errors = True

    if email != "" and not re.match(REGEX_EMAIL, email):
        entries[2]['background'] = "#db6d6d"
        errors = True

    if phone != "" and not re.match(REGEX_PHONE, phone):
        entries[3]['background'] = "#db6d6d"
        errors = True

    if bday != "":
        bd_error = False
        if not re.match(REGEX_BDAY1, bday) and not re.match(REGEX_BDAY2, bday):
            bd_error = True

        else:
            if len(bday.split("-")) == 3:
                year, month, day = map(int, bday.split("-"))
                if year == 0:
                    bd_error = True
            elif len(bday.split("-")) == 2:
                month, day = map(int, bday.split("-"))

            if month == 0 or day == 0:
                bd_error = True
            if day > month_days[month-1]:
                bd_error = True

        if bd_error:
            entries[1]['background'] = "#db6d6d"
            errors = True

    return errors


def edit_contact(window1: Toplevel,
                 entries: Tuple[Entry, ...],
                 err_label: Label,
                 sel_contact: Dict) -> None:
    name, bday, email, phone, note = map(lambda x: x.get(), entries)
    err_label['text'] = ""

# DEBUG
    if phone != "":
        phone += " "

    errors = check_entries(entries)

    if errors:
        err_label['text'] = "Errors on these fields: "
    else:
        window1.destroy()
        table.item(table.selection(),
                   values=[name, bday, email, phone, note])
    sort_contacts()


def new_contact(window1: Toplevel,
                entries: Tuple[Entry, ...],
                err_label: Label,
                sel_contact: Dict) -> None:
    name, bday, email, phone, note = map(lambda x: x.get(), entries)
    err_label['text'] = ""

    errors = check_entries(entries)

    if errors:
        err_label['text'] = "Errors on these fields: "
    else:
        window1.destroy()
        if len(table.get_children()) == 0:
            i = 0
        else:
            i = max(map(int, table.get_children())) + 1
        row_vals = [name, bday, email, phone, note]
        table.insert(parent="", index="end", iid=i, values=row_vals)
    sort_contacts()


def save_contacts() -> None:
    out_arr = []
    for i in table.get_children():
        row = table.item(i)['values']
        out_arr.append({
                        "name": row[0],
                        "birthday": row[1],
                        "email": row[2],
                        "phone": str(row[3]),
                        "note": row[4]
                       })
    if _globals["db_file"] == "":
        new_name = asksaveasfilename()
        if new_name == ():
            return
        _globals["db_file"] = new_name
    with open(_globals["db_file"], "w") as f:
        json.dump(out_arr, f)
        f.close()
    print("Saved!")


def search() -> None:
    name = search_bar.get().lower()
    for i in table.get_children():
        item_values = table.item(i)['values']
        if name not in item_values[0].lower():
            detached.append(i)
            table.detach(i)
    for i in detached:
        item_values = table.item(i)['values']
        if name in item_values[0].lower():
            table.reattach(i, '', i)
    sort_contacts()


# binds
table.bind("<Button-1>", lambda x: window.after(2, check_selected))
search_bar.bind("<Key>", lambda x: window.after(2, search))
window.bind_all("<Control-s>", lambda x: save_contacts())

sort_by_var.trace("w", sort_contacts)
for i in show_col_vars:
    i.trace("w", show_columns)


window.update()
load_db("contacts.json")

window.mainloop()
