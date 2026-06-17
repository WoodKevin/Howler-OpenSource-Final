#!/usr/bin/env python3
"""Howler"""

import argparse
import os
import sys


# --------------------------------------------------
def get_args():
    """get command-line arguments"""

    parser = argparse.ArgumentParser(
        description='Howler (upper-cases input)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('text', metavar='text', type=str, help='Input string or file')

    parser.add_argument('-o', '--outfile', help='Output filename', metavar='str', type=str, default='') #pylint: disable=line-too-long

    args = parser.parse_args()

    if os.path.isfile(args.text):
        with open(args.text, "rt", encoding="utf-8") as in_fh:
            args.text = in_fh.read().rstrip()
    return args


# --------------------------------------------------
def main():
    """Where the Howling happens"""

    args = get_args()
    if args.outfile:
        with open(args.outfile, "wt", encoding="utf-8") as out_fh:
            out_fh.write(args.text.upper() + "\n")
    else:
        sys.stdout.write(args.text.upper() + "\n")


# --------------------------------------------------
if __name__ == '__main__':
    main()
