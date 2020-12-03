#!/usr/bin/env python3
#
#
#  ===========================================================================
#
#                              EDXML Validator
#
#                            EXAMPLE APPLICATION
#
#                  Copyright (c) 2010 - 2016 by D.H.J. Takken
#                          (d.h.j.takken@xs4all.nl)
#
#          This file is part of the EDXML Software Development Kit (SDK).
#
#
#  The EDXML SDK is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  The EDXML SDK is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with the EDXML SDK.  If not, see <http://www.gnu.org/licenses/>.
#
#
#  ===========================================================================
#
#  This script checks EDXML data against the specification requirements. Its exit
#  status will be zero if the provided data is valid EDXML. The utility accepts both
#  regular files and EDXML data streams on standard input.
import argparse
import logging
import sys

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

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())

    args = parser.parse_args()

    if args.quiet:
        logger.setLevel(logging.ERROR)
    elif args.verbose:
        if args.verbose > 0:
            logger.setLevel(logging.INFO)
        if args.verbose > 1:
            logger.setLevel(logging.DEBUG)

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
