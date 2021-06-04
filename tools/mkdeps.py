#!/usr/bin/env python3

import subprocess
import glob
import os
import sys
import re
import traceback
from argparse import ArgumentParser

__version__ = "0.1"


def main():

    FIX_RE = r"([^:]+:)"

    parser = ArgumentParser(description="mkdeps for SDCC",
                            epilog="Copyright (C) 2021 Juan J Martinez <jjm@usebox.net>",
                            )

    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__)

    parser.add_argument("-b", "--build-dir", dest="build", default=None, type=str,
                        help="Directory to build")
    parser.add_argument("-I", "--include", dest="include", default=None, type=str,
                        help="Include directory (for multiple directories, use : as separator)")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="Enable verbose output")

    parser.add_argument("dir", help="Directory to scan")
    parser.add_argument(
        "deps", help="Dependencies file (to include in Makefile)")

    args = parser.parse_args()

    fix_path = args.dir if args.build is None else args.build
    fix_path = r"%s\1" % (fix_path.strip("/") + "/").replace("\\", "\\\\")
    inc = ["-I%s" % d for d in args.include.split(":")]
    cmd = ["sdcc", "-MM"] + inc
    result = []
    for d in sorted(glob.glob(os.path.join(args.dir, "*.c"))):
        if args.verbose:
            print("running %r" % ' '.join(cmd + [d]))
        out = subprocess.run(cmd + [d], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        if out.returncode:
            sys.exit("Error: %s" % out.stderr)

        out = out.stdout.decode('utf-8').strip("\n\r")
        result.append(re.sub(FIX_RE, fix_path, out))

    try:
        old = open(args.deps, "rt").read()
    except Exception:
        if args.verbose:
            print("%r not found, will generate" % args.deps)
        old = None

    new = '\n'.join(result)

    if new != old:
        remove_list.append(args.deps)
        with open(args.deps, "wt") as fd:
            fd.write(new)
    else:
        if args.verbose:
            print("%r didn't change, skipping" % args.deps)


if __name__ == "__main__":
    remove_list = []

    try:
        main()
    except Exception as e:
        print("FATAL: %s\n***" % e, file=sys.stderr)
        traceback.print_exc()

        for filename in remove_list:
            if os.path.exists(filename):
                os.unlink(filename)

        sys.exit(1) 
