#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                          Relative EDXML Validator
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
# 
#  Python script that checks if the ontologies in de <definitions>
#  sections in all specified EDXML files are compatible.

import sys
from xml.sax import make_parser
from edxml.EDXMLParser import EDXMLParser
from edxml.EDXMLBase import EDXMLError, EDXMLProcessingInterrupted

# Create a SAX parser, and provide it with
# an EDXMLParser instance as content handler.
# This places the EDXMLParser instance in the
# XML processing chain, just after SaxParser.

SaxParser = make_parser()
Parser    = EDXMLParser(SaxParser, True)

SaxParser.setContentHandler(Parser)

# Check commandline parameters

if len(sys.argv) <= 1:
  sys.stderr.write("Please specify one or more filenames to check.");
  sys.exit(0)

# Now we feed each of the input files
# to the Sax parser. This will effectively
# cause the EDXMLParser instance to try and
# merge the <definitions> sections of all
# input files, raising EDXMLError when it
# detects a problem.

for arg in sys.argv[1:]:
  print("Checking %s" % arg)
  
  try:
    SaxParser.parse(open(arg))
  except EDXMLProcessingInterrupted:
    pass
  except EDXMLError as Error:
    print("EDXML file %s is inconsistent with previous files:\n%s" % (( arg, str(Error) )) )
  except:
    raise

# Print results.

print("\n\nTotal Warnings: %d\nTotal Errors:   %d\n\n" % (( Parser.GetWarningCount(), Parser.GetErrorCount() )) )    

if Parser.GetErrorCount() == 0:
  sys.exit(0)
else:
  sys.exit(255)