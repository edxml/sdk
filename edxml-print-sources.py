#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                         EDXML Source URL Extractor
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
#  Python script that outputs a list of source URLs that is found in
#  specified EDXML file.

import sys

from edxml.EDXMLParser import ProcessingInterrupted, EDXMLOntologyPullParser


class EdxmlSourceParser(EDXMLOntologyPullParser):

    def _parsed_ontology(self, ontology):
        self.__sources = ontology.get_event_sources().keys()

    def get_sources(self):
        return self.__sources


def print_help():

    print("""

   Python script that outputs a list of source URLs that is found in
   specified EDXML file.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. If this option is not specified,
                       input will be read from standard input.

   Example:

     cat input.edxml | edxml-print-sources.py > urls.txt

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
    with EdxmlSourceParser() as parser:
        parser.parse(event_input)
        for source in parser.get_sources():
            print(source)
except ProcessingInterrupted:
    pass
