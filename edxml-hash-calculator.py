#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                        EDXML Sticky Hash Calculator
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
#  This script outputs sticky hashes for every event in a given
#  EDXML file or input stream. The hashes are printed to standard output.

import sys
from edxml.EDXMLParser import EDXMLPullParser


class EDXMLEventHasher(EDXMLPullParser):

    def __init__(self):

        super(EDXMLEventHasher, self).__init__(sys.stdout)

    def _parsed_event(self, event):

        ontology = self.get_ontology()
        print(event.compute_sticky_hash(ontology))


def print_help():

    print("""

   This utility outputs sticky hashes for every event in a given
   EDXML file or input stream. The hashes are printed to standard output.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. If this option is not specified,
                       input will be read from standard input.

   Example:

     cat input.edxml | edxml-hash-calculator.py > hashes.txt

""")

# Program starts here.


argument_count = len(sys.argv)
current_argument = 1
event_input = sys.stdin

# Parse commandline arguments

while current_argument < argument_count:

    if sys.argv[current_argument] in ('-h', '--help'):
        print_help()
        sys.exit(0)

    elif sys.argv[current_argument] == '-f':
        current_argument += 1
        event_input = open(sys.argv[current_argument])

    else:
        sys.stderr.write("Unknown commandline argument: %s\n" %
                         sys.argv[current_argument])
        sys.exit()

    current_argument += 1

if event_input == sys.stdin:
    sys.stderr.write(
        'Waiting for EDXML data on standard input... (use --help option to get help)\n')

try:
    EDXMLEventHasher().parse(event_input)
except KeyboardInterrupt:
    sys.exit()
