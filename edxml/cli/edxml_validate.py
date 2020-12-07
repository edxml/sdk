#!/usr/bin/env python3

# ========================================================================================
#                                                                                        =
#              Copyright (c) 2010 D.H.J. Takken (d.h.j.takken@xs4all.nl)                 =
#                      Copyright (c) 2020 the EDXML Foundation                           =
#                                                                                        =
#                                   http://edxml.org                                     =
#                                                                                        =
#             This file is part of the EDXML Software Development Kit (SDK)              =
#                       and is released under the MIT License:                           =
#                         https://opensource.org/licenses/MIT                            =
#                                                                                        =
# ========================================================================================

#  This script checks EDXML data against the specification requirements. Its exit
#  status will be zero if the provided data is valid EDXML. The utility accepts both
#  regular files and EDXML data streams on standard input.

import argparse
import sys

from edxml.cli import configure_logger
from edxml.parser import EDXMLPullParser
from edxml.error import EDXMLValidationError


def main():

    parser = argparse.ArgumentParser(
        description="This utility checks EDXML data against the specification requirements. Its exit "
                    "status will be zero if the provided data is valid EDXML."
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        action='append',
        help='By default, input is read from standard input. This option can be used to read from a '
             'file in stead.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    args = parser.parse_args()

    configure_logger(args)

    if args.file is None:

        # Feed the parser from standard input.
        args.file = [sys.stdin.buffer]

    try:
        with EDXMLPullParser() as parser:
            for file in args.file:
                parser.parse(file).close()
    except KeyboardInterrupt:
        return
    except EDXMLValidationError as e:
        # The string representations of exceptions do not
        # interpret newlines. As validation exceptions
        # may contain pretty printed XML snippets, this
        # does not yield readable exception messages.
        # So, we only print the message passed to the
        # constructor of the exception.
        print(e.args[0])
        exit(1)

    print("Input data is valid.\n")


if __name__ == "__main__":
    main()
