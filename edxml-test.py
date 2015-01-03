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
#                  Copyright (c) 2010 - 2015 by D.H.J. Takken
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
from xml.sax import make_parser
from edxml.EDXMLParser import EDXMLValidatingParser

# This class is based on EDXMLValidatingParser. All it
# does is overriding the Error and Warning calls, to
# count them and allow processing to continue when 
# EDXMLValidatingParser generates an error.

class EDXMLChecker(EDXMLValidatingParser):

  def __init__ (self, upstream, SkipEvents = False):

    EDXMLValidatingParser.__init__(self, upstream, SkipEvents)

    self.ErrorCount = 0
    self.WarningCount = 0

  # Override of EDXMLParser implementation
  def Error(self, Message):
    if self.ErrorCount == 0:
      print ""

    print(unicode("ERROR: %s" % Message).encode('utf-8'))
    self.ErrorCount += 1

  # Override of EDXMLParser implementation
  def Warning(self, Message):
    if self.WarningCount == 0:
      print ""

    print(unicode("WARNING: " + Message).encode('utf-8'))
    self.WarningCount += 1

  def GetErrorCount(self):
    return self.ErrorCount

  def GetWarningCount(self):
    return self.WarningCount

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
    sys.stderr.write("Unknown commandline argument: %s\n" % sys.argv[CurrentArgument])
    sys.exit()

  CurrentArgument += 1

# Create a SAX parser, and provide it with
# an MyChecker instance as content handler.
# This places the EDXMLParser instance in the
# XML processing chain, just after SaxParser.

SaxParser = make_parser()
MyChecker = EDXMLChecker(SaxParser)
SaxParser.setContentHandler(MyChecker)

if Input == sys.stdin:
  sys.stderr.write('Waiting for EDXML data on standard input... (use --help option to get help)\n')

# Feed the EDXML data to the Sax parser.
SaxParser.parse(Input)

# Fetch the error and warning counts
ErrorCount   = MyChecker.GetErrorCount()
WarningCount = MyChecker.GetWarningCount()

# Print results.

if ErrorCount == 0:
  sys.stdout.write("Input data is valid.\n")
  sys.exit(0)
else:
  sys.stdout.write("\nInput data is invalid: %d errors were found ( and %d warnings ).\n" % (( ErrorCount, WarningCount )) )
  sys.exit(255)

