#!/usr/bin/env python3

'''
========================
=- ZIPUU cracker v1.0 -=
========================
made for KSI 2021/2022
this was 3 separate files at first, but I had free time so I made this thing

SOLUTIONS:
==========

#1 brute-force:
password: pog
./zipuu.py brute.zip -b -s a -l 3 -o extracted/

#2 dictionary attack:
password: Snickers1
./zipuu.py rockme.zip -w rockyou.txt -o extracted/

#3 targeted:
(I also submitted copy of my targeted.txt file)
password: Maggie1956
./zipuu.py homer_simpson.zip -w targeted.txt -c 2 -o extracted/
'''

import argparse
from typing import Generator, Iterable, Tuple, Union
import string

import pyzipper

from itertools import product


def combinator(items: Iterable[str], pw_len: Union[int, Tuple[int, int]]):
    '''
    Function for making combination generators

    args:
    items: Iterable[str] -> items to make combinations from
    pw_len: int | Tuple[int, int] -> how many repetitions are to be used,
                                     can also be range
    '''

    if type(pw_len) == int:
        for password in product(items, repeat=pw_len):
            yield "".join(password)
    else:
        for i in range(pw_len[0], pw_len[1] + 1):
            for password in product(items, repeat=i):
                yield "".join(password)


def wordlist(filename: str) -> Generator[str, None, None]:
    '''Function that returns passwords from wordlist'''

    with open(filename, "r") as f:
        for line in f:
            yield line.rstrip()


def main(args: argparse.Namespace):
    # prepare password generator
    if args.brute:
        chars = ""
        if "a" in args.charsets:
            chars += string.ascii_lowercase
        if "A" in args.charsets:
            chars += string.ascii_uppercase
        if "0" in args.charsets:
            chars += "0123456789"
        pw_generator = combinator(chars, args.pw_length)
    elif args.combinations != 1:
        # this might have issues with giant files, that is why standard
        # wordlist attack avoids loading the whole wordlist file at once
        with open(args.wordlist_file, "r") as f:
            lines = f.read().split("\n")
        f.close()
        pw_generator = combinator(lines, args.combinations)
    elif args.wordlist_file is not None:
        pw_generator = wordlist(args.wordlist_file)

    # actual cracking
    with pyzipper.AESZipFile(args.zip_file) as enc_zip:
        for gen_password in pw_generator:
            if args.verbose:
                print(gen_password)
            password = bytes(gen_password, encoding="utf-8")
            try:
                enc_zip.extractall(path=args.output_dir, pwd=password)
            except RuntimeError:
                # most likely wrong password
                continue
            except Exception as e:
                # sometimes wrong passwords raise other exceptions
                print(f"Unknown error with password '{gen_password}':")
                print(e)
                continue

            print("============================")
            print("successfully found password:")
            print(gen_password)
            print("============================")
            exit(0)
        print("didn't find password!!")
        exit(1)


def number_range(arg: str) -> Union[int, Tuple[int, int]]:
    '''make sure argument is a number / range'''
    if "-" not in arg:
        try:
            result = int(arg)
        except ValueError:
            raise argparse.ArgumentTypeError("argument must be int")
        return result
    else:
        try:
            range_start, range_stop = map(int, arg.split("-"))
        except Exception as e:
            print(e)
            raise argparse.ArgumentTypeError("not valid range")
        return (range_start, range_stop)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ZIP password guesser (made for KSI)")
    parser.add_argument("zip_file", help="ZIP archive to crack", type=str)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.required = True
    mode_group.add_argument('-w', '--wordlist',
                            help='use wordlist file for cracking',
                            dest='wordlist_file',
                            default=None,
                            type=str)
    mode_group.add_argument('-b', '--brute',
                            action='store_true',
                            help='use brute force with character combinations')
    parser.add_argument('-c', '--combinations',
                        default=1,
                        help='use brute force with word combinations',
                        type=int)
    parser.add_argument('-l', '--length',
                        help='password length (chars or words), can also be range',
                        dest='pw_length',
                        type=number_range,
                        default=(1, 4))
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='show verbose information')
    parser.add_argument('-s', '--charsets',
                        default="aA0",
                        help='which charsets are to be used in -b (--brute) mode;\
                              available are "a" (lowercase), "A" (uppercase), "0" (numbers)')
    parser.add_argument('-o', '--output_dir',
                        help='where to extract files from ZIP',
                        default='.',
                        type=str)
    args = parser.parse_args()

    main(args)
