# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                          EDXML Consistency Checker
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
# 
#  Python script that checks if the <definitions> sections
#  in all specified EDXML files are mutually consistent.

import sys
from xml.sax import make_parser, SAXNotSupportedException
from edxml.EDXMLParser import EDXMLParser, EDXMLError

SaxParser = make_parser()

Parser = EDXMLParser(SaxParser, True)

SaxParser.setContentHandler(Parser)

if len(sys.argv) <= 1:
  sys.stderr.write("Please specify one or more filenames to check.");
  sys.exit(0)
  
for arg in sys.argv[1:]:
  print("Checking %s" % arg)
  
  try:
    SaxParser.parse(open(arg))
  except SAXNotSupportedException:
    pass
  except EDXMLError as Error:
    print("EDXML file %s is inconsistent with previous files:\n%s" % (( arg, str(Error) )) )
  except:
    raise

print("\n\nTotal Warnings: %d\nTotal Errors:   %d\n\n" % (( Parser.GetWarningCount(), Parser.GetErrorCount() )) )    

if Parser.GetErrorCount() == 0:
  sys.exit(0)
else:
  sys.exit(255)