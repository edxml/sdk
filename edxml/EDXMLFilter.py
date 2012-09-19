# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                   Python classes for filtering EDXML data
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
#  ===========================================================================
#
# 
#  These classes can be used to base EDXML filtering scripts on. There is
#  a generic EDXML stream filter class and a object editing class. Both of
#  these classes are in turn based on EDXMLParser, so all parsed definitions 
#  are available through the functionality offered by EDXMLParser.

import sys
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl
from EDXMLParser import *

# This class inherits from EDXMLParser and causes the
# EDXML data to be passed through to STDOUT. It is used
# as a base class for implementing EDXML filters.

class EDXMLStreamFilter(EDXMLParser):
  
  def __init__ (self, upstream, SkipEvents = False):

    self.OutputEnabled = True
    self.Passthrough = XMLGenerator(sys.stdout, 'utf-8')
    EDXMLParser.__init__(self, upstream, SkipEvents)
  
  # This function implements a global switch
  # to turn XML passthrough on or off. You can
  # use it to allow certain parts of EDXML files
  # to pass through to STDOUT while other parts
  # are filtered out.
  def SetOutputEnabled(self, YesOrNo):
    self.OutputEnabled = YesOrNo
  
  def startElement(self, name, attrs):
  
    EDXMLParser.startElement(self, name, attrs)
    if self.OutputEnabled:
      self.Passthrough.startElement(name, attrs)
  
  def startElementNS(self, name, qname, attrs):
  
    if self.OutputEnabled:
      self.Passthrough.startElementNS(name, qname, attrs)
  
  def endElement(self, name):
  
    EDXMLParser.endElement(self, name)
    if self.OutputEnabled:
      self.Passthrough.endElement(name)
  
  def endElementNS(self, name, qname):
  
    if self.OutputEnabled:
      self.Passthrough.endElementNS(name, qname)
  
  def processingInstruction(self, target, body):

    if self.OutputEnabled:
      self.Passthrough.processingInstruction(target, body)
  
  def comment(self, body):
  
    if self.OutputEnabled:
      self.Passthrough.comment(body)

  def characters(self, text):

    if self.OutputEnabled:
      self.Passthrough.characters(text)

  def ignorableWhitespace(self, ws):

    if self.OutputEnabled:
      self.Passthrough.ignorableWhitespace(ws)

    
# This class implements an EDXML filter which can
# edit objects in an EDXML stream. It offers the
# ProcessObject() function which can be overridden
# to implement your own object editing EDXML processor.
#
# HINT: Use the AttributesImpl class from the xml.sax.xmlreader
#       module to replace the attributes of an object.

class EDXMLObjectEditor(EDXMLStreamFilter):
  def __init__ (self, upstream):

    EDXMLStreamFilter.__init__(self, upstream, False)
  
  def InsertObject(self, PropertyName, Value):
    self.InsertedObjects.append({'property': PropertyName, 'value': Value})
  
  def startElement(self, name, attrs):
    if name == 'object':
      Property = attrs.get('property')
      Value = attrs.get('value')
      ObjectTypeName = self.Definitions.GetPropertyObjectType(self.CurrentEventTypeName, Property)
      self.InsertedObjects = []
      attrs = self.EditObject(self.CurrentSourceId, self.CurrentEventTypeName, ObjectTypeName, attrs)
      
      for Item in self.InsertedObjects:
        EDXMLStreamFilter.startElement(self, 'object', AttributesImpl({'property': Item['property'], 'value': Item['value']}))
        EDXMLStreamFilter.endElement(self, 'object')
      
    EDXMLStreamFilter.startElement(self, name, attrs)

  # This function can be overridden to process single
  # objects. It should return the modified object attributes.
  def EditObject(self, SourceId, EventTypeName, ObjectTypeName, attrs):
    return attrs
    
    
# This class implements an EDXML filter which can
# edit events in an EDXML stream. It offers the
# ProcessEvent() function which can be overridden
# to implement your own event editing EDXML processor.

class EDXMLEventEditor(EDXMLStreamFilter):
  def __init__ (self, upstream):

    self.ReadingEvent = False
    self.CurrentEvent = []
    self.CurrentEventAttributes = AttributesImpl({})
    self.ReceivingEventContent = False
    
    EDXMLStreamFilter.__init__(self, upstream, False)
  
  def startElement(self, name, attrs):
    
    if name == 'event':
      self.CurrentEventAttributes = attrs
      self.SetOutputEnabled(False)
      self.CurrentEventDeleted = False
      self.CurrentEvent = []

    elif name == 'object':
      PropertyName = attrs.get('property')
      Value = attrs.get('value')
      self.CurrentEvent.append({'property': PropertyName, 'value': Value})
      
    elif name == 'content':
      self.ReceivingEventContent = True

    EDXMLStreamFilter.startElement(self, name, attrs)
      
  def endElement(self, name):
    if name == 'event':
      
      self.SetOutputEnabled(True)
      
      # Allow event to be edited
      self.CurrentEvent, self.CurrentEventContent, self.CurrentEventAttributes = self.EditEvent(self.CurrentSourceId, self.CurrentEventTypeName, self.CurrentEvent, self.CurrentEventContent, self.CurrentEventAttributes)
      
      # Output buffered event
      if self.CurrentEventDeleted == False and len(self.CurrentEvent) > 0:
        EDXMLStreamFilter.startElement(self, 'event', AttributesImpl({}))
        EDXMLStreamFilter.ignorableWhitespace(self, '\n      ')
        for Object in self.CurrentEvent:
          EDXMLStreamFilter.ignorableWhitespace(self, '  ')
          EDXMLStreamFilter.startElement(self, 'object', AttributesImpl({'property': Object['property'], 'value': Object['value']}))
          EDXMLStreamFilter.endElement(self, 'object')
          EDXMLStreamFilter.ignorableWhitespace(self, '\n      ')
        if len(self.CurrentEventContent) > 0:
          EDXMLStreamFilter.startElement(self, 'content', AttributesImpl({}))
          EDXMLStreamFilter.characters(self.CurrentEventContent)
          EDXMLStreamFilter.endElement(self, 'content')
          EDXMLStreamFilter.ignorableWhitespace(self, '\n      ')
        
        EDXMLStreamFilter.endElement(self, 'event')
  
      return
  
    EDXMLStreamFilter.endElement(self, name)

  def characters(self, text):
    
    if self.ReceivingEventContent:
      self.CurrentEventContent += text
    EDXMLStreamFilter.characters(self, text)
    
  # Call this function from EditEvent() to delete
  # an event in stead of just editing it.
  def DeleteEvent(self):
    self.CurrentEventDeleted = True
    
  # This function can be overridden to process single
  # events. It should return the modified event attributes, objects and content.
  def EditEvent(self, SourceId, EventTypeName, EventObjects, EventContent, EventAttributes):
    return EventObjects, EventContent, EventAttributes
