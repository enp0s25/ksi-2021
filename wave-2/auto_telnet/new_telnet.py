#!/usr/bin/env python3


import socket
import sys


def main():
    NUMBERS = "0123456789"
    out = []
    cursor = 0
    saved_cursor = cursor
    cur_delta = 0

    hostname, port = sys.argv[1], int(sys.argv[2])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((hostname, port))

        while True:
            data = s.recv(1024)
            if data == b"":
                break
            # print(f"> {data}")
            data = data.replace(b"\x1B[1D*", b"")
            i = 0
            while i < len(data):
                if chr(data[i]) == "\x1B":
                    i += 1
                    if chr(data[i]) == "[":
                        i += 1
                        while chr(data[i]) in NUMBERS:
                            cur_delta = int(str(cur_delta) + chr(data[i]))
                            i += 1
                        # print(f"{chr(data[i])}:{cur_delta}")
                        if chr(data[i]) == "D":
                            cursor -= cur_delta
                            cur_delta = 0
                        elif chr(data[i]) == "C":
                            cursor += cur_delta
                            cur_delta = 0
                        else:
                            cur_delta = 0
                    elif chr(data[i]) == "7":
                        saved_cursor = cursor
                    elif chr(data[i]) == "8":
                        cursor = saved_cursor
                    else:
                        print(f"unknown code: {data[i]}")
                    i += 1
                    continue
                if cursor > len(out)-1:
                    out.append(chr(data[i]))
                    cursor += 1
                else:
                    # print(f"changing {cursor}")
                    out[cursor] = chr(data[i])
                    cursor += 1
                i += 1

        flag_start = "".join(out).find("KSI")
        print("".join(out)[flag_start:].rstrip())
        # sys.stdout.write(out[flag_start:].decode('utf-8'))


if __name__ == '__main__':
    main()