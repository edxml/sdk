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

#  This script prints an evaluated event story or summary for each event in a given
#  EDXML file or input stream. The strings are printed to standard output.

import argparse
import sys

from edxml.cli import configure_logger
from edxml.parser import EDXMLPullParser


class EDXMLEventPrinter(EDXMLPullParser):

    def __init__(self, print_summaries=False, print_colorized=False):
        super().__init__()
        self.__print_summaries = print_summaries
        self.__colorize = print_colorized

    def _parsed_event(self, event):

        print(self.get_ontology().get_event_type(event.get_type_name()).evaluate_template(
            event, which='summary' if self.__print_summaries else 'story', colorize=self.__colorize
        ))


def main():
    parser = argparse.ArgumentParser(
        description="This utility outputs evaluated event story or summary templates for every event "
                    "in a given EDXML file or input stream. The strings are printed to standard output."
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='By default, input is read from standard input. This option can be used to read from a '
             'file in stead.'
    )

    parser.add_argument(
        '-c',
        '--colored',
        action='store_true',
        help='Produce colored output, highlighting object values.'
    )

    parser.add_argument(
        '-s',
        '--short',
        action='store_true',
        help='By default, the event story is rendered. This option switches to shorter summary rendering.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    args = parser.parse_args()

    configure_logger(args)

    input = open(args.file, 'rb') if args.file else sys.stdin.buffer

    try:
        EDXMLEventPrinter(print_summaries=args.short, print_colorized=args.colored).parse(input)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
