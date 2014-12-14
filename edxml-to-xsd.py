#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                           EDXML to XSD Converter
#
#                            EXAMPLE APPLICATION
#
#                  Copyright (c) 2010 - 2014 by D.H.J. Takken
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
#  This utility reads EDXML from a file or from standard input, and prints
#  an XSD schema to STDOUT. The XSD is constructed to match the definitions
#  section of the input EDXML file *exactly*. Due to the limitations of XSD
#  schemas, even the order of eventtype definitions must match. You can use
#  it to check if two EDXML files have identical ontologies. Note that XSD
#  schemas cannot be used to check if two EDXML files have different ontolo-
#  gies.

import sys
from xml.sax import make_parser
from edxml.EDXMLBase import EDXMLError, EDXMLProcessingInterrupted
from edxml.EDXMLParser import EDXMLParser

def PrintHelp():

  print """

   This utility reads EDXML from a file or from standard input, and prints
   an XSD schema to STDOUT. The XSD is constructed to match the definitions
   section of the input EDXML file *exactly*. Due to the limitations of XSD
   schemas, even the order of eventtype definitions must match. You can use
   it to check if two EDXML files have identical ontologies. Note that XSD
   schemas cannot be used to check if two EDXML files have different ontolo-
   gies.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. If this option is not specified,
                       input will be read from standard input.

   Example:

     cat input.edxml | edxml-to-xsd.py > schema.xsd

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
# an EDXMLParser instance as content handler.
# This places the EDXMLParser instance in the
# XML processing chain, just after SaxParser.

SaxParser   = make_parser()
EDXMLParser = EDXMLParser(SaxParser, True)

SaxParser.setContentHandler(EDXMLParser)

# Now we just push EDXML data into the Sax parser,
# either from a file or from standard input.

if Input == sys.stdin:
  sys.stderr.write('Waiting for EDXML data on standard input... (use --help option to get help)\n')

try:
  SaxParser.parse(Input)
except EDXMLProcessingInterrupted:
  pass

# Finally, we use the XSD functions of the
# EDXMLDefinitions instance of EDXMLParser
# to generate an XSD schema.

EDXMLParser.Definitions.OpenXSD()
EDXMLParser.Definitions.GenerateFullXSD()

print EDXMLParser.Definitions.CloseXSD()
