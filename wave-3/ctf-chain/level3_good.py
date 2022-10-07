#!/usr/bin/env python3

from Crypto.Cipher import DES
from itertools import product

KEY1 = b"\x00\xf1"
KEY3 = b"Kar"

pattern = "Karlík".encode("utf-8")


pw_gen = product(range(0,255), repeat=3)
with open('prisonerDetails', "rb") as f:
    details_full = f.read()
    details = details_full[:64]
    f.close()

for password in pw_gen:
    # print(password)
    key = KEY1 + bytes(password) + KEY3
    obj = DES.new(key, DES.MODE_ECB)
    result = obj.decrypt(details)

    if pattern in result:
        r2 = obj.decrypt(details_full)
        try:
            s = r2.decode('utf-8')
            print(s)
        except Exception as e:
            print(e)
