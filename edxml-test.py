#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import sys

from edxml.EDXMLParser import EDXMLPullParser


def PrintHelp():

    print """

   This utility checks EDXML data against the specification requirements. Its exit
   status will be zero if the provided data is valid EDXML. The utility accepts both
   regular files and EDXML data streams on standard input.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. If this option is not specified,
                       input will be read from standard input.

   Example:

     cat input.edxml | edxml-test.py

"""

# Program starts here.


ArgumentCount = len(sys.argv)
CurrentArgument = 1
Input = sys.stdin

# Parse commandline arguments

while CurrentArgument < ArgumentCount:

    if sys.argv[CurrentArgument] in ('-h', '--help'):
        PrintHelp()
        sys.exit(0)

    elif sys.argv[CurrentArgument] == '-f':
        CurrentArgument += 1
        Input = open(sys.argv[CurrentArgument])

    else:
        sys.stderr.write("Unknown commandline argument: %s\n" %
                         sys.argv[CurrentArgument])
        sys.exit()

    CurrentArgument += 1

if Input == sys.stdin:
    sys.stderr.write(
        'Waiting for EDXML data on standard input... (use --help option to get help)\n')

try:
    EDXMLPullParser().parse(Input)
except KeyboardInterrupt:
    sys.exit()

sys.stdout.write("Input data is valid.\n")
