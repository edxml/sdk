#!/usr/bin/env python
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
#  This utility reads multiple compatible EDXML files and merges them into
#  one new EDXML file, which is then printed on standard output. It works in
#  two passes. First, it compiles and integrates all <definitions> sections
#  from all EDXML files into a EDXMLParser instance. Then, in a second pass,
#  it outputs the unified <definitions> section and outputs the eventgroups
#  in each of the EDXML files.
#
#  The script demonstrates the use of EDXMLStreamFilter and merging of 
#  <definitions> sections from multiple EDXML sources.

import sys
from xml.sax import make_parser
from xml.sax.xmlreader import AttributesImpl
from xml.sax.saxutils import XMLGenerator
from edxml.EDXMLBase import EDXMLError, EDXMLProcessingInterrupted
from edxml.EDXMLParser import EDXMLParser
from edxml.EDXMLFilter import EDXMLStreamFilter

# This class is based on the EDXMLStreamFilter class,
# and filters out <eventgroup> sections, omitting
# all other content. It needs a dictionary which 
# translates Source URLs to a new set of unique
# Source Identifiers. This mapping is used to translate
# the source-id attributes in the <eventgroup> tags,
# assuring the uniqueness of Source ID.

class EDXMLEventGroupFilter(EDXMLStreamFilter):
  def __init__ (self, upstream, SourceUrlIdMapping):

    # Call parent constructor
    EDXMLStreamFilter.__init__(self, upstream, False)
    
    # Initialize source id / url mappings
    self.SourceUrlIdMapping = SourceUrlIdMapping
    self.SourceIdUrlMapping = {}
    
    # Disable output of EDXMLStreamFilter.
    self.SetOutputEnabled(False)
  
  def startElement(self, name, attrs):
    AttributeItems = {}
    # Populate the AttributeItems dictionary.
    for AttributeName, AttributeValue in attrs.items():
      AttributeItems[AttributeName] = AttributeValue
      
    if name == 'source':
      # Store the relations between source URL and ID
      self.SourceIdUrlMapping[AttributeItems['source-id']] = AttributeItems['url']
      # Translate the source ID of this source definition
      NewSourceId = self.SourceUrlIdMapping[AttributeItems['url']]
      AttributeItems['source-id'] = NewSourceId
      
    if name == 'eventgroup':
      # Turn filter output back on.
      self.SetOutputEnabled(True)
      # Edit the AttributeItems dictionary to ensure that the
      # source IDs in the output stream are unique.
      GroupSourceUrl = self.SourceIdUrlMapping[AttributeItems['source-id']]
      AttributeItems['source-id'] = self.SourceUrlIdMapping[GroupSourceUrl]

    # Call parent startElement to generate the output XML element.
    EDXMLStreamFilter.startElement(self, name, AttributesImpl(AttributeItems))

  def endElement(self, name):
    # Call parent implementation
    EDXMLStreamFilter.endElement(self, name)

    if name == 'eventgroup':
      # Turn filter output off
      self.SetOutputEnabled(False)
      

# Program starts here. Check commandline arguments.

if len(sys.argv) < 2:
  sys.stderr.write("\nPlease specify at least two EDXML files for merging.")
  sys.exit()

# Create a SAX parser, and provide it with
# an EDXMLParser instance as content handler.
# This places the EDXMLParser instance in the
# XML processing chain, just after SaxParser.

SaxParser   = make_parser()
EDXMLParser = EDXMLParser(SaxParser, True)

SaxParser.setContentHandler(EDXMLParser)

# First, we parse all specified EDXML files
# using the EDXMLParser, which will compile
# and merge all event type, object type
# and source definitions in the EDXML files.
  
for FileName in sys.argv[1:]:
  sys.stderr.write("\nParsing file %s:" % FileName );
  
  try:
    SaxParser.parse(open(FileName))
  except EDXMLProcessingInterrupted:
    pass
  except EDXMLError as Error:
    sys.stderr.write("\n\nEDXML file %s is inconsistent with previous files:\n\n%s" % (( arg, str(Error) )) )
    sys.exit(1)
  except:
    raise

# Instantiate a Sax XML generator, and open
# the <events> tag. This will be our new
# output EDXML stream.

XMLGenerator = XMLGenerator(sys.stdout, 'utf-8')
XMLGenerator.startElement('events', AttributesImpl({}))
XMLGenerator.ignorableWhitespace("\n  ")

# Use the EDXMLDefinitions instance of EDXMLParser to
# generate a set of new, unique source IDs. The resulting
# dictionary maps Source URLs to source IDs.

SourceIdMapping = EDXMLParser.Definitions.UniqueSourceIDs()

# Now we can use the EDXMLParser to generate a new
# <definitions> section, containing all previously
# compiled event types, object types and sources.
# The definitions section is output to STDOUT

EDXMLParser.Definitions.GenerateXMLDefinitions(XMLGenerator)

# Next, we will output the eventgroups from all input files.
# Open the <eventgroups> tag.

XMLGenerator.startElement('eventgroups', AttributesImpl({}))
XMLGenerator.ignorableWhitespace("\n    ")

# Now we process each of the specified EDXML files
# a second time. We will feed each file into the
# EventGroupFilter, which will only output the <eventgroup>
# sections from the EDXML files to STDOUT, and translate
# event source IDs.

SaxParser        = make_parser()
EventGroupFilter = EDXMLEventGroupFilter(SaxParser, SourceIdMapping)

SaxParser.setContentHandler(EventGroupFilter)

for FileName in sys.argv[1:]:
  sys.stderr.write("\nMerging file %s:" % FileName );
  
  try:
    SaxParser.parse(open(FileName))
  except EDXMLProcessingInterrupted:
    pass
  except EDXMLError as Error:
    sys.stderr.write("\n\nEDXML file %s is inconsistent with previous files:\n\n%s" % (( FileName, str(Error) )) )
    sys.exit(1)
  except:
    raise

# Finish the EDXML stream.

XMLGenerator.ignorableWhitespace("\n")    
XMLGenerator.endElement('eventgroups')
XMLGenerator.ignorableWhitespace("\n")
XMLGenerator.endElement('events')
XMLGenerator.ignorableWhitespace("\n")
