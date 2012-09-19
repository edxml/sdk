# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                          EDXML Statistics Utility
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
#  Python script that outputs various statistics for a set of EDXML files.
#  It prints event counts, lists defined event types, object types, source
#  URLs, and so on.

import sys
import string
from xml.sax import make_parser, SAXNotSupportedException
from edxml.EDXMLParser import EDXMLParser, EDXMLError

SaxParser = make_parser()

Parser = EDXMLParser(SaxParser, False)

SaxParser.setContentHandler(Parser)

if len(sys.argv) <= 1:
  sys.stderr.write("\nNo filename was given, waiting for EDXML data on STDIN...")
  sys.stdout.flush()
  SaxParser.parse(sys.stdin)

else:
  
  for arg in sys.argv[1:]:
    sys.stderr.write("Processing %s..." % arg)
  
    try:
      SaxParser.parse(open(arg))
    except SAXNotSupportedException:
      pass
    except EDXMLError as Error:
      print("\n\nEDXML file %s is inconsistent with previous files:\n\n%s" % (( arg, str(Error) )) )
      sys.exit(1)
    except:
      raise

print "\n"
print "Total event count: %s\n" % Parser.GetEventCount()
print "Event counts per type:\n"

for EventTypeName in sorted(Parser.Definitions.GetEventTypeNames()):
  print "%s: %s" % (( string.ljust(EventTypeName, 40), Parser.GetEventCount(EventTypeName) ))

print "\nObject Types:\n"

for ObjectTypeName in sorted(Parser.Definitions.GetObjectTypeNames()):
  DataType = Parser.Definitions.GetObjectTypeDataType(ObjectTypeName)
  print "%s: %s" % (( string.ljust(ObjectTypeName, 40), DataType ))

print "\nProperty relation predicates:\n"
for Predicate in sorted(Parser.Definitions.GetRelationPredicates()):
  print Predicate

print "\nSource URLs:\n"
for URL in sorted(Parser.Definitions.GetSourceURLs()):
  print URL
