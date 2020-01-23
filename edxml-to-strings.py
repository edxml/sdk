#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                           EDXML String Printer
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
#
#  This script prints an evaluated event story or summary for each event in a given
#  EDXML file or input stream. The strings are printed to standard output.
import argparse
import sys

from edxml.EDXMLParser import EDXMLPullParser


class EDXMLEventPrinter(EDXMLPullParser):

    def __init__(self, print_summaries=False, print_colorized=False):

        super(EDXMLEventPrinter, self).__init__()
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
        help='By default, input is read from standard input. This option can be used to read from a'
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

    args = parser.parse_args()

    if args.file is None:
        sys.stderr.write(
            'Waiting for EDXML data on standard input... (use --help option to get help)\n'
        )

    input = open(args.file) if args.file else sys.stdin.buffer

    try:
        EDXMLEventPrinter(print_summaries=args.short, print_colorized=args.colored).parse(input)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
