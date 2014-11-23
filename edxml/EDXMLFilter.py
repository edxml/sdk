# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                   Python classes for filtering EDXML data
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
#  ===========================================================================
#

"""EDXMLFilter

This module can be used to write EDXML filtering scripts, which can edit
EDXML streams. All filtering classes are based on EDXMLParser, so you can
conveniently use the EDXMLDefinitions instance of EDXMLParser to query
details about all defined event types, object types, sources, and so on.

Classes in this module:

EDXMLStreamFilter:           A generic stream filter
EDXMLValidatingStreamFilter: A validating, generic stream filter
EDXMLObjectEditor:           Stream filter for editing individual objects in stream
EDXMLEventEditor:            Stream filter for editing events in stream

"""

import sys
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl
from EDXMLParser import *

class EDXMLStreamFilter(EDXMLParser):
  """Base class for implementing EDXML filters
  
  This class inherits from EDXMLParser and causes the
  EDXML data to be passed through to STDOUT.
  
  """
  
  def __init__ (self, upstream, SkipEvents = False, Output = sys.stdout):
    """Constructor.

    You can pass any file-like object using the Output parameter, which
    will be used to send the filtered data stream to. It defaults to
    sys.stdout (standard output).
    
    Parameters:
    upstream   -- XML source (SaxParser instance in most cases)
    SkipEvents -- Set to True to parse only the definitions section (default False)
    Output     -- An optional file-like object, defaults to sys.stdout
    
    """
    
    self.OutputEnabled = True
    self.Passthrough = XMLGenerator(Output, 'utf-8')
    EDXMLParser.__init__(self, upstream, SkipEvents)
  
  def SetOutputEnabled(self, YesOrNo):
    """This function implements a global switch
    to turn XML passthrough on or off. You can
    use it to allow certain parts of EDXML files
    to pass through to STDOUT while other parts
    are filtered out.

    Note that the output of the filter is validated,
    so be careful not to break the EDXML data while
    filtering it.

    """
    self.OutputEnabled = YesOrNo
  
  def startElement(self, name, attrs):
  
    if self.OutputEnabled:
      EDXMLParser.startElement(self, name, attrs)
      self.Passthrough.startElement(name, attrs)
  
  def endElement(self, name):
  
    if self.OutputEnabled:
      EDXMLParser.endElement(self, name)
      self.Passthrough.endElement(name)
  
  def characters(self, text):

    if self.OutputEnabled:
      self.Passthrough.characters(text)

  def ignorableWhitespace(self, ws):

    if self.OutputEnabled:
      self.Passthrough.ignorableWhitespace(ws)

class EDXMLValidatingStreamFilter(EDXMLValidatingParser):
  """Base class for implementing EDXML filters

  This class is identical to the EDXMLStreamFilter class, except that
  it fully validates each event that is output by the filter.

  """

  def __init__ (self, upstream, SkipEvents = False, Output = sys.stdout):
    """Constructor.

    You can pass any file-like object using the Output parameter, which
    will be used to send the filtered data stream to. It defaults to
    sys.stdout (standard output).

    Parameters:
    upstream   -- XML source (SaxParser instance in most cases)
    SkipEvents -- Set to True to parse only the definitions section (default False)
    Output     -- An optional file-like object, defaults to sys.stdout

    """

    self.OutputEnabled = True
    self.Passthrough = XMLGenerator(Output, 'utf-8')
    EDXMLValidatingParser.__init__(self, upstream, SkipEvents)

  def SetOutputEnabled(self, YesOrNo):
    """This function implements a global switch
    to turn XML passthrough on or off. You can
    use it to allow certain parts of EDXML files
    to pass through to STDOUT while other parts
    are filtered out.

    Note that the output of the filter is validated,
    so be careful not to break the EDXML data while
    filtering it.

    """
    self.OutputEnabled = YesOrNo

  def startElement(self, name, attrs):

    if self.OutputEnabled:
      EDXMLValidatingParser.startElement(self, name, attrs)
      self.Passthrough.startElement(name, attrs)

  def startElementNS(self, name, qname, attrs):

    if self.OutputEnabled:
      self.Passthrough.startElementNS(name, qname, attrs)

  def endElement(self, name):

    if self.OutputEnabled:
      EDXMLValidatingParser.endElement(self, name)
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

class EDXMLObjectEditor(EDXMLValidatingStreamFilter):
  """This class implements an EDXML filter which can
  be used to edit objects in an EDXML stream. It offers the
  ProcessObject() function which can be overridden
  to implement your own object editing EDXML processor.
  
   HINT: Use the AttributesImpl class from the xml.sax.xmlreader
         module to replace the attributes of an object.
  """
  
  def __init__ (self, upstream, Output = sys.stdout):
    """ Constructor.

    You can pass any file-like object using the Output parameter, which
    will be used to send the filtered data stream to. It defaults to
    sys.stdout (standard output).

    Parameters:
    upstream   -- XML source (SaxParser instance in most cases)
    Output     -- An optional file-like object, defaults to sys.stdout
    """

    EDXMLValidatingStreamFilter.__init__(self, upstream, False, Output)
  
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
        EDXMLValidatingStreamFilter.startElement(self, 'object', AttributesImpl({'property': Item['property'], 'value': Item['value']}))
        EDXMLValidatingStreamFilter.endElement(self, 'object')
      
    EDXMLValidatingStreamFilter.startElement(self, name, attrs)

  # This function can be overridden to process single
  # objects. It should return the modified object attributes.
  def EditObject(self, SourceId, EventTypeName, ObjectTypeName, attrs):
    return attrs
    
    
class EDXMLEventEditor(EDXMLValidatingStreamFilter):
  """This class implements an EDXML filter which can
  use to edit events in an EDXML stream. It offers the
  ProcessEvent() function which can be overridden
  to implement your own event editing EDXML processor.
  """
  
  def __init__ (self, upstream, Output = sys.stdout):
    """ Constructor.

    You can pass any file-like object using the Output parameter, which
    will be used to send the filtered data stream to. It defaults to
    sys.stdout (standard output).

    Parameters:
    upstream   -- XML source (SaxParser instance in most cases)
    Output     -- An optional file-like object, defaults to sys.stdout
    """

    self.ReadingEvent = False
    self.CurrentEvent = []
    self.CurrentEventAttributes = AttributesImpl({})
    self.ReceivingEventContent = False
    
    EDXMLValidatingStreamFilter.__init__(self, upstream, False, Output)
  
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

    EDXMLValidatingStreamFilter.startElement(self, name, attrs)
      
  def endElement(self, name):
    if name == 'event':
      
      self.SetOutputEnabled(True)
      
      # Allow event to be edited
      self.CurrentEvent, self.CurrentEventContent, self.CurrentEventAttributes = self.EditEvent(self.CurrentSourceId, self.CurrentEventTypeName, self.CurrentEvent, self.CurrentEventContent, self.CurrentEventAttributes)
      
      # Output buffered event
      if self.CurrentEventDeleted == False and len(self.CurrentEvent) > 0:
        EDXMLValidatingStreamFilter.startElement(self, 'event', AttributesImpl({}))
        EDXMLValidatingStreamFilter.ignorableWhitespace(self, '\n      ')
        for Object in self.CurrentEvent:
          EDXMLValidatingStreamFilter.ignorableWhitespace(self, '  ')
          EDXMLValidatingStreamFilter.startElement(self, 'object', AttributesImpl({'property': Object['property'], 'value': Object['value']}))
          EDXMLValidatingStreamFilter.endElement(self, 'object')
          EDXMLValidatingStreamFilter.ignorableWhitespace(self, '\n      ')
        if len(self.CurrentEventContent) > 0:
          EDXMLValidatingStreamFilter.startElement(self, 'content', AttributesImpl({}))
          EDXMLValidatingStreamFilter.characters(self.CurrentEventContent)
          EDXMLValidatingStreamFilter.endElement(self, 'content')
          EDXMLValidatingStreamFilter.ignorableWhitespace(self, '\n      ')
        
        EDXMLValidatingStreamFilter.endElement(self, 'event')
  
      return
  
    EDXMLValidatingStreamFilter.endElement(self, name)

  def characters(self, text):
    
    if self.ReceivingEventContent:
      self.CurrentEventContent += text
    EDXMLValidatingStreamFilter.characters(self, text)
    
  def DeleteEvent(self):
    """Delete an event while editing

    Call this function from EditEvent() to delete
    an event in stead of just editing it.
    """
    self.CurrentEventDeleted = True
    
  def EditEvent(self, SourceId, EventTypeName, EventObjects, EventContent, EventAttributes):
    """Modifies an event

    This function can be overridden to process single
    events. It should modified copies of the EventObjects,
    EventContent and EventAttributes parameters, in that order.

    The EventObjects parameter is a list of dictionaries. Each
    dictionary represents one object, containing a 'property'
    key and a 'value' key.

    Parameters:
    SourceId        -- EDXML source identifier
    EventTypeName   -- Name of the event type
    EventObjects    -- List of event objects
    EventContent    -- Event content string
    EventAttributes -- Sax AttributesImpl instance containing event tag attributes
    """
    return EventObjects, EventContent, EventAttributes
