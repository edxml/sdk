#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                           EDXML to XSD Converter
#
#                  Copyright (c) 2010 - 2012 by D.H.J. Takken
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
#  section of the input EDXML file *exactly*. You can use it to check if
#  two EDXML files are identical, definitions-wise. The XSD does not do any
#  validation on the event data in the EDXML.

import sys
from xml.sax import make_parser
from edxml.EDXMLBase import EDXMLError, EDXMLProcessingInterrupted
from edxml.EDXMLParser import EDXMLParser

# Create a SAX parser, and provide it with
# an EDXMLParser instance as content handler.
# This places the EDXMLParser instance in the
# XML processing chain, just after SaxParser.

SaxParser   = make_parser()
EDXMLParser = EDXMLParser(SaxParser, True)

SaxParser.setContentHandler(EDXMLParser)

# Now we just push EDXML data into the Sax parser,
# either from a file or from standard input.

if len(sys.argv) < 2:
  sys.stderr.write("\nNo filename was given, waiting for EDXML data on STDIN...")
  sys.stdout.flush()
  try:
    SaxParser.parse(sys.stdin)
  except EDXMLProcessingInterrupted:
    pass
else:
  sys.stderr.write("\nProcessing file %s:" % sys.argv[1] );
  try:
    SaxParser.parse(open(sys.argv[1]))
  except EDXMLProcessingInterrupted:
    pass

# Finally, we use the XSD functions of the
# EDXMLDefinitions instance of EDXMLParser
# to generate an XSD schema.

EDXMLParser.Definitions.OpenXSD()
EDXMLParser.Definitions.GenerateFullXSD()

print EDXMLParser.Definitions.CloseXSD()
