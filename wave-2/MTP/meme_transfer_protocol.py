#!/usr/bin/env python3

# module that implements meme transfer protocol

import socket
import base64
import pynetstring

from queue import SimpleQueue
from typing import Tuple, Optional


class ConnectionHandler:
    '''
    MTP message handler
    '''

    def __init__(self, ip: str, port: int) -> None:
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((ip, port))
        self.queue = SimpleQueue()
    
    def send(self, data: str) -> None:
        self.conn.sendall(pynetstring.encode(data))
        # print(pynetstring.encode(data))
    
    def get(self) -> str:
        if self.queue.empty():
            self.recv()
        return self.queue.get()
    
    def recv(self) -> None:
        data = pynetstring.decode(self.conn.recv(1024))
        # print(data)
        for i in data:
            msg = i.decode('ascii')
            if msg.startswith("E"):
                raise ValueError("server responded with error: " + msg[2:])
            self.queue.put(msg)

    def close(self) -> None:
        self.conn.close()


def connect(ip: str, port: int, nick: str) -> Tuple[socket.socket, str, int]:
    '''
    Initial connection to MTP server

    returns connection socket, token, data channel port
    '''

    conn = ConnectionHandler(ip, port)
    conn.send("C MTP V:1.0")
    d_confirm = conn.get()
    if d_confirm != "S MTP V:1.0":
        conn.send("E server does not use MTP v1.0")
        raise ValueError("server does not support MTP 1.0")
    conn.send(f"C {nick}")
    token = conn.get()[2:]
    dc_port = int(conn.get()[2:])

    return conn, token, dc_port


def upload_meme(ip: str, port: int, meme_info: Tuple[str, str, bool, str],
                nick: str, token: str) -> Tuple[str, int]:
    '''
    Send meme with data through data channel
    
    meme info contains base64 encoded meme, description, isNSFW and password
    returns dtoken, transfer size
    '''

    conn = ConnectionHandler(ip, port)
    conn.send(f"C {nick}")

    token2 = conn.get()[2:]
    if token != token2:
        conn.send("E tokens don't match")
        raise ValueError("tokens don't match")
    print("tokens confirmed")
    

    meme_data_size = 0
    possible_reqs = ("REQ:meme", "REQ:description", "REQ:isNSFW", "REQ:password")
    for i in range(4):
        # what is server requesting
        req = conn.get()[2:]
        print(req)
        if req in possible_reqs:
            index = possible_reqs.index(req)

            if index == 0:
                # image -> base64
                with open(meme_info[0], "rb") as f:
                    b64img = base64.b64encode(f.read()).decode("ascii")
                    f.close()
                data_len = len(b64img)
                conn.send("C " + b64img)

            elif index == 2:
                # bool -> str
                if meme_info[2]:
                    nsfw_flag = "true"
                    data_len = 4
                else:
                    nsfw_flag = "false"
                    data_len = 5
                conn.send("C " + nsfw_flag)

            else:
                data_len = len(meme_info[index])
                conn.send("C " + meme_info[index])
        else:
            conn.send("E unknown data request")
            raise ValueError("unknown data request")

        meme_data_size += data_len
        ack_len = int(conn.get()[6:])
        if ack_len != data_len:
            conn.send("E data piece size mismatch")
            raise ValueError("data piece size mismatch")

    print("reqs done")
    dtoken = conn.get()[6:]
    conn.close()
    return dtoken, meme_data_size


def finish(conn: ConnectionHandler, dtoken: str, dsize: int) -> None:
    '''
    Finish communication with server
    '''

    ack_data = int(conn.get()[2:])
    if ack_data != dsize:
        conn.send("E data size mismatch")
        raise ValueError("data size mismatch")
    conn.send("C " + dtoken)
    fin_ack = conn.get()
    conn.close()
    print("connection closed successfully")


def submit(ip: str, port: int, nick: str,
           meme_info: Tuple[str, str, bool, str]) -> bool:
    '''
    Main function to submit meme to server

    returns False if an error is encountered
    '''

    try:
        conn, token, dc_port = connect(ip, port, nick)
        dtoken, dsize = upload_meme(ip, dc_port, meme_info, nick, token)
        finish(conn, dtoken, dsize)
        return True
    except ValueError as e:
        print(e)
        return False
