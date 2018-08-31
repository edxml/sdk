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

import sys

from edxml.EDXMLParser import EDXMLPullParser


class EDXMLEventPrinter(EDXMLPullParser):

    def __init__(self, which='story', print_colorized=False):

        super(EDXMLEventPrinter, self).__init__()
        self.__which = which
        self.__colorize = print_colorized

    def _parsed_event(self, event):

        print(self.get_ontology().get_event_type(event.get_type_name()).evaluate_template(
            event, which=self.__which, colorize=self.__colorize
        ))


def print_help():

    print("""

   This utility outputs evaluated event story or summary templates for every event in a given
   EDXML file or input stream. The strings are printed to standard output.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. If this option is not specified,
                       input will be read from standard input.

     --summary         By default, the event story will be printed. When
                       this switch is added, the summary will be printed in stead.

     -c                Adding this switch will cause the object values in the
                       printed stories and summaries to be highlighted.

   Example:

     cat input.edxml | edxml-to-strings.py -c

""")

# Program starts here.


argument_count = len(sys.argv)
current_argument = 1
event_input = sys.stdin
which = 'story'
colorize = False

# Parse commandline arguments

while current_argument < argument_count:

    if sys.argv[current_argument] in ('-h', '--help'):
        print_help()
        sys.exit(0)

    elif sys.argv[current_argument] == '-f':
        current_argument += 1
        event_input = open(sys.argv[current_argument])

    elif sys.argv[current_argument] == '--summary':
        which = 'summary'

    elif sys.argv[current_argument] == '-c':
        colorize = True

    else:
        sys.stderr.write("Unknown commandline argument: %s\n" %
                         sys.argv[current_argument])
        sys.exit()

    current_argument += 1

if event_input == sys.stdin:
    sys.stderr.write(
        'Waiting for EDXML data on standard input... (use --help option to get help)\n')

try:
    EDXMLEventPrinter(which=which, print_colorized=colorize).parse(event_input)
except KeyboardInterrupt:
    pass
