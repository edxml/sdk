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

    def __init__(self, Which='story', PrintColorized=False):

        super(EDXMLEventPrinter, self).__init__()
        self.Which = Which
        self.Colorize = PrintColorized

    def _parsedEvent(self, edxmlEvent):

        print self.getOntology().GetEventType(edxmlEvent.GetTypeName()).EvaluateTemplate(
            edxmlEvent, which=self.Which == 'summary', colorize=self.Colorize
        )


def PrintHelp():

    print """

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

"""

# Program starts here.


ArgumentCount = len(sys.argv)
CurrentArgument = 1
Input = sys.stdin
Which = 'story'
Colorize = False

# Parse commandline arguments

while CurrentArgument < ArgumentCount:

    if sys.argv[CurrentArgument] in ('-h', '--help'):
        PrintHelp()
        sys.exit(0)

    elif sys.argv[CurrentArgument] == '-f':
        CurrentArgument += 1
        Input = open(sys.argv[CurrentArgument])

    elif sys.argv[CurrentArgument] == '--summary':
        Which = 'summary'

    elif sys.argv[CurrentArgument] == '-c':
        Colorize = True

    else:
        sys.stderr.write("Unknown commandline argument: %s\n" %
                         sys.argv[CurrentArgument])
        sys.exit()

    CurrentArgument += 1

if Input == sys.stdin:
    sys.stderr.write(
        'Waiting for EDXML data on standard input... (use --help option to get help)\n')

try:
    EDXMLEventPrinter(Which=Which, PrintColorized=Colorize).parse(Input)
except KeyboardInterrupt:
    pass
