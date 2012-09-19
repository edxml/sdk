# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                          EDXML Merging Utility
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
#  This utility reads multiple EDXML files and merges them into one new 
#  EDXML file, which is then printed on standard output.

import sys
from xml.sax import make_parser, SAXNotSupportedException
from xml.sax.xmlreader import AttributesImpl
from xml.sax.saxutils import XMLGenerator
from edxml.EDXMLParser import EDXMLParser, EDXMLError
from edxml.EDXMLFilter import EDXMLStreamFilter

class EDXMLEventGroupFilter(EDXMLStreamFilter):
  def __init__ (self, upstream, SourceIdMapping):

    EDXMLStreamFilter.__init__(self, upstream, False)
    self.SourceIdMapping = SourceIdMapping
    self.SetOutputEnabled(False)
  
  def startElement(self, name, attrs):
    AttributeItems = {} 
    for AttributeName, AttributeValue in attrs.items():
      AttributeItems[AttributeName] = AttributeValue
    if name == 'eventgroup':
      self.SetOutputEnabled(True)
      AttributeItems['source-id'] = self.SourceIdMapping[AttributeItems['source-id']]
    if name == 'source':
      AttributeItems['source-id'] = self.SourceIdMapping[AttributeItems['source-id']]
    EDXMLStreamFilter.startElement(self, name, AttributesImpl(AttributeItems))

  def endElement(self, name):
    if name == 'eventgroup':
      EDXMLStreamFilter.endElement(self, name)
      self.SetOutputEnabled(False)
    else:
      EDXMLStreamFilter.endElement(self, name)
      
  # This function does nothing, but it can be overridden to process
  # single objects. It should return the modified object attributes.
  def ProcessObject(self, SourceId, EventTypeName, ObjectTypeName, attrs):
    return attrs

if len(sys.argv) < 2:
  sys.stderr.write("\nPlease specify at least two EDXML files for merging.")
  sys.stdout.flush()
  sys.exit()

# First, we parse all specified EDXML files
# using the EDXMLParser, which will compile
# collection of all event types, object types
# and sources defined in the EDXML files.
  
SaxParser = make_parser()

EDXMLParser = EDXMLParser(SaxParser, True)

SaxParser.setContentHandler(EDXMLParser)

for FileName in sys.argv[1:]:
  sys.stderr.write("\nParsing file %s:" % FileName );
  
  try:
    SaxParser.parse(open(FileName))
  except SAXNotSupportedException:
    pass
  except EDXMLError as Error:
    sys.stderr.write("\n\nEDXML file %s is inconsistent with previous files:\n\n%s" % (( arg, str(Error) )) )
    sys.exit(1)
  except:
    raise

XMLGenerator = XMLGenerator(sys.stdout, 'utf-8')
XMLGenerator.startElement('events', AttributesImpl({}))
XMLGenerator.ignorableWhitespace("\n  ")


# Now we can use the EDXMLParser to generate a new
# <definitions> section, containing all previously
# compiled event types, object types and sources.
# The definitions section is output to STDOUT

SourceIdMapping = EDXMLParser.Definitions.UniqueSourceIDs()
EDXMLParser.Definitions.GenerateXMLDefinitions(XMLGenerator)

XMLGenerator.startElement('eventgroups', AttributesImpl({}))
XMLGenerator.ignorableWhitespace("\n    ")

# Now we process each of the specified EDXML files
# a second time. We will feed each file into the
# EventGroupFilter, which will only print the <eventgroups>
# sections from the EDXML files to STDOUT.

SaxParser = make_parser()

EventGroupFilter = EDXMLEventGroupFilter(SaxParser, SourceIdMapping)

SaxParser.setContentHandler(EventGroupFilter)

for FileName in sys.argv[1:]:
  sys.stderr.write("\nMerging file %s:" % FileName );
  
  try:
    SaxParser.parse(open(FileName))
  except SAXNotSupportedException:
    pass
  except EDXMLError as Error:
    sys.stderr.write("\n\nEDXML file %s is inconsistent with previous files:\n\n%s" % (( FileName, str(Error) )) )
    sys.exit(1)
  except:
    raise

XMLGenerator.ignorableWhitespace("\n")    
XMLGenerator.endElement('eventgroups')
XMLGenerator.ignorableWhitespace("\n")
XMLGenerator.endElement('events')
XMLGenerator.ignorableWhitespace("\n")
