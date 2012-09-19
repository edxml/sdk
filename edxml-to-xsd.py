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
from xml.sax.saxutils import escape
from lxml import etree
from edxml.EDXMLParser import *

class EDXMLSchemaGenerator(EDXMLParser):
  
  def __init__ (self, upstream, SkipEvents = False):

    
    EDXMLParser.__init__(self, upstream, SkipEvents)
  
  
    
  
  def DefinitionsLoaded(self):
        
    self.OpenElement('element').set('name', 'events')
    self.OpenElement('complexType')
    self.OpenElement('sequence')
    self.OpenElement('element').set('name', 'definitions')
    self.OpenElement('complexType')
    self.OpenElement('sequence')
    self.OpenElement('element').set('name', 'eventtypes')
    self.OpenElement('complexType')
    self.OpenElement('sequence')

    for EventTypeName in self.Definitions.GetEventTypeNames():
      self.GenerateEventTypeSchema(EventTypeName)
     
    self.CloseElement()
    self.CloseElement()
    self.CloseElement()
    
    self.OpenElement('element').set('name', 'objecttypes')
    self.OpenElement('complexType')
    self.OpenElement('sequence')

    for ObjectTypeName in self.Definitions.GetObjectTypeNames():
      self.OpenElement('element').set('name', 'objecttype')
      self.OpenElement('complexType')
      for Attribute, Value in self.Definitions.GetObjectTypeAttributes(ObjectTypeName).items():
        self.OpenElement('attribute').set('name', 'name')
        self.CurrentElement.set('name', Attribute)
        self.CurrentElement.set('type', 'xs:string')
        self.CurrentElement.set('fixed', Value)
        self.CloseElement()
      self.CloseElement()
      self.CloseElement()
    
    self.CloseElement()
    self.CloseElement()
    self.CloseElement()
    
    self.OpenElement('element').set('name', 'sources')
    self.OpenElement('complexType')
    self.OpenElement('sequence')

    for SourceId in self.Definitions.GetSourceIDs():
      self.OpenElement('element').set('name', 'source')
      self.OpenElement('complexType')
      for Attribute, Value in self.Definitions.GetSourceIdProperties(SourceId).items():
        self.OpenElement('attribute').set('name', 'name')
        self.CurrentElement.set('name', Attribute)
        self.CurrentElement.set('type', 'xs:string')
        self.CurrentElement.set('fixed', Value)
        self.CloseElement()
      self.CloseElement()
      self.CloseElement()
    
    self.CloseElement()
    self.CloseElement()
    self.CloseElement()
    
    self.CloseElement()
    self.CloseElement()
    self.CloseElement()

    self.OpenElement('element').set('name', 'eventgroups')
    self.OpenElement('complexType')
    self.OpenElement('sequence').set('minOccurs', '0')
    self.CurrentElement.set('maxOccurs', 'unbounded')

    self.OpenElement('element').set('name', 'eventgroup')
    self.OpenElement('complexType')
    
    self.OpenElement('sequence').set('minOccurs', '0')
    self.CurrentElement.set('maxOccurs', 'unbounded')
    self.OpenElement('element').set('name', 'event')
    
    self.CloseElement()
    self.CloseElement()
    
    self.OpenElement('attribute')
    self.CurrentElement.set('name', 'source-id')
    self.CurrentElement.set('type', 'xs:string')
    self.CloseElement()
    self.OpenElement('attribute')
    self.CurrentElement.set('name', 'event-type')
    self.CurrentElement.set('type', 'xs:string')
    self.CloseElement()
    self.CloseElement()
    self.CloseElement()
    
    self.CloseElement()
    self.CloseElement()
    self.CloseElement()
    
    self.CloseElement()
    self.CloseElement()
     
    print etree.tostring(self.Schema, pretty_print = True, encoding='utf-8')
    
SaxParser = make_parser()
SaxParser.setContentHandler(EDXMLSchemaGenerator(SaxParser, True))

if len(sys.argv) < 2:
  sys.stderr.write("\nNo filename was given, waiting for EDXML data on STDIN...")
  sys.stdout.flush()
  try:
    SaxParser.parse(sys.stdin)
  except SAXNotSupportedException:
    pass
else:
  sys.stderr.write("\nProcessing file %s:" % sys.argv[1] );
  
  try:
    SaxParser.parse(open(sys.argv[1]))
  except SAXNotSupportedException:
    pass
