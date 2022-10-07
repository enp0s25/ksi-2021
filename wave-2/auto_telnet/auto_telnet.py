#!/usr/bin/env python3


import socket
import sys

def f_1b(s):
    data = s.recv(1024)
    print(data.decode().rstrip())

def f_2a(s):
    data = b"Kolik"
    while True:
        data = s.recv(1024)
        # print(f"< {data.decode().rstrip()}")
        if data.decode().rstrip().startswith("KSI"):
            print(data.decode().rstrip())
            break
        question = data.decode().rstrip().split(" ")
        answer = int(question[2]) + int(question[4][:-1])
        s.sendall(str(answer).encode("utf-8"))
        # print(f"> {answer}")

def f_3a(s):
    NUMBERS = "0123456789"
    arr = []
    cursor = 0
    cur_delta = 0
    while True:
        data: bytes = s.recv(1024)
        if data == b"":
            break
        # if data[:6] == b"\x00\x1B[1D*":
        #     data = data[6:]
        data.replace(b"\x1B[1D*", b"")
        skip = 0
        for i in range(len(data)):
            if skip > 0:
                skip -= 1
                continue
            #print(data[i:i+2])
            if data[i:i+2] == b"\x1B[":
                i += 2
                skip += 2
                while chr(data[i]) in NUMBERS:
                    cur_delta = int(str(cur_delta) + chr(data[i]))
                    print(cur_delta)
                    i += 1
                    skip += 1
                if chr(data[i]) == "D":
                    cursor -= cur_delta
                    cur_delta = 0
                elif chr(data[i]) == "C":
                    cursor += cur_delta
                    cur_delta = 0
                skip += 1
            
            elif cursor > len(arr):
                arr.append(data[i])
                cursor += 1
            elif cursor < len(arr):
                arr[cursor] = data[i]
                cursor += 1

        print(f"< {data.decode().rstrip()}")
    print(arr)

def main():
    hostname, port = sys.argv[1], int(sys.argv[2])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((hostname, port))

        f_3a(s)

if __name__ == '__main__':
    main()