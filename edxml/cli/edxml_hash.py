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

#  This script outputs sticky hashes for every event in a given
#  EDXML file or input stream. The hashes are printed to standard output.

import argparse
import hashlib
import sys

from edxml.cli import configure_logger
from edxml.parser import EDXMLPullParser


class EDXMLEventHasher(EDXMLPullParser):

    def __init__(self, hash_function):
        super().__init__()
        self.hash_function = hash_function

    def _parsed_event(self, event):
        event_type = self.get_ontology().get_event_type(event.get_type_name())
        print(event.compute_sticky_hash(event_type, hash_function=self.hash_function))


def main():
    parser = argparse.ArgumentParser(
        description='This utility outputs sticky hashes for every event in a given '
                    'EDXML file or input stream. The hashes are printed to standard output.'
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='By default, input is read from standard input. This option can be used to read from a '
             'file in stead.'
    )

    parser.add_argument(
        '--sha256', action='store_true', help='Output SHA256 hashes in stead of SHA1.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    args = parser.parse_args()

    configure_logger(args)

    event_input = args.file or sys.stdin.buffer

    try:
        EDXMLEventHasher(hash_function=hashlib.sha256 if args.sha256 else hashlib.sha1).parse(event_input)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()
