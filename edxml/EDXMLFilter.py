# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                   Python classes for filtering EDXML data
#
#                  Copyright (c) 2010 - 2016 by D.H.J. Takken
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
EDXML streams. All filtering classes are based on :class:`edxml.EDXMLParser`,
so you can conveniently use Definitions attribute of EDXMLParser to query
details about all defined event types, object types, sources, and so on.

"""

from xml.sax.xmlreader import AttributesImpl
from EDXMLParser import *

class EDXMLStreamFilter(EDXMLParser):
  """Base class for implementing EDXML filters

  This class inherits from EDXMLParser and causes the
  EDXML data to be passed through to STDOUT.

  You can pass any file-like object using the Output parameter, which
  will be used to send the filtered data stream to. It defaults to
  sys.stdout (standard output).

  Args:
    upstream: XML source (SaxParser instance in most cases)

    SkipEvents (bool, optional): Set to True to parse only the definitions section

    Output (bool, optional): An optional file-like object, defaults to sys.stdout

  """

  def __init__ (self, upstream, SkipEvents = False, Output = sys.stdout):

    self.OutputEnabled = True
    self.Passthrough = XMLGenerator(Output, 'utf-8')
    EDXMLParser.__init__(self, upstream, SkipEvents)

  def SetOutputEnabled(self, YesOrNo):
    """This method implements a global switch
    to turn XML pass through on or off. You can
    use it to allow certain parts of EDXML files
    to pass through to STDOUT while other parts
    are filtered out.

    Args:
      YesOrNo (bool): Output enabled (True) or disabled (False)

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

  You can pass any file-like object using the Output parameter, which
  will be used to send the filtered data stream to. It defaults to
  sys.stdout (standard output).

  Parameters:
    upstream: XML source (SaxParser instance in most cases)

    SkipEvents (bool, optional): Set to True to parse only the definitions section

    Output (bool, optional): An optional file-like object, defaults to sys.stdout

  """

  def __init__ (self, upstream, SkipEvents = False, Output = sys.stdout):

    self.OutputEnabled = True
    self.Passthrough = XMLGenerator(Output, 'utf-8')
    EDXMLValidatingParser.__init__(self, upstream, SkipEvents)

  def SetOutputEnabled(self, YesOrNo):
    """This method implements a global switch
    to turn XML pass through on or off. You can
    use it to allow certain parts of EDXML files
    to pass through to STDOUT while other parts
    are filtered out.

    Note that the output of the filter is validated,
    so be careful not to break the EDXML data while
    filtering it.

    Args:
      YesOrNo (bool): Output enabled (True) or disabled (False)

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
  ProcessObject() method which can be overridden
  to implement your own object editing EDXML processor.

  You can pass any file-like object using the Output parameter, which
  will be used to send the filtered data stream to. It defaults to
  sys.stdout (standard output).

  Parameters:
    upstream: XML source (SaxParser instance in most cases)

    Output (optional): A file-like object, defaults to sys.stdout
  """

  def __init__ (self, upstream, Output = sys.stdout):

    self.InsertedObjects = []
    EDXMLValidatingStreamFilter.__init__(self, upstream, False, Output)

  def InsertObject(self, PropertyName, Value):
    """Insert a new object into the EDXML stream

    This method can be called from implementations of
    :func:`EditObject` to add objects to the current event.

    Args:
      PropertyName (str): Property of the new object

      Value (str): Value of the new object
    """
    self.InsertedObjects.append({'property': PropertyName, 'value': Value})

  def startElement(self, name, attrs):
    if name == 'object':
      Property = attrs.get('property')
      ObjectTypeName = self.Definitions.GetPropertyObjectType(self.CurrentEventTypeName, Property)
      self.InsertedObjects = []
      attrs = self.EditObject(self.CurrentSourceId, self.CurrentEventTypeName, ObjectTypeName, attrs)

      for Item in self.InsertedObjects:
        EDXMLValidatingStreamFilter.startElement(self, 'object', AttributesImpl({'property': Item['property'], 'value': Item['value']}))
        EDXMLValidatingStreamFilter.endElement(self, 'object')

    EDXMLValidatingStreamFilter.startElement(self, name, attrs)

  def EditObject(self, SourceId, EventTypeName, ObjectTypeName, attrs):
    """This method can be overridden to process single objects.

    Implementations should return the new object attributes by means
    of an :class:`xml.sax.xmlreader.AttributesImpl` object.

    Args:
      SourceId (str): EDXML Source Identifier

      EventTypeName (str): Name of the event type of current event

      ObjectTypeName (str): Object type of the object

      attrs (AttributesImpl): XML attributes of the <object> tag

    Returns:
      AttributesImpl. Updated XML attributes of the <object> tag
    """
    return attrs

class EDXMLEventEditor(EDXMLValidatingStreamFilter):
  """This class implements an EDXML filter which can
  use to edit events in an EDXML stream. It offers the
  ProcessEvent() method which can be overridden
  to implement your own event editing EDXML processor.

  You can pass any file-like object using the Output parameter, which
  will be used to send the filtered data stream to. It defaults to
  sys.stdout (standard output).

  Args:
    upstream: XML source (SaxParser instance in most cases)

    Output (optional): A file-like object, defaults to sys.stdout
  """

  def __init__ (self, upstream, Output = sys.stdout):

    self.ReadingEvent = False
    self.CurrentEventDeleted = False
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
      CurrentEvent, CurrentEventContent, CurrentEventAttributes = self.EditEvent(self.CurrentSourceId, self.CurrentEventTypeName, self.CurrentEvent, self.CurrentEventContent, self.CurrentEventAttributes)

      # Output buffered event
      if self.CurrentEventDeleted == False and len(CurrentEvent) > 0:
        EDXMLValidatingStreamFilter.startElement(self, 'event', AttributesImpl(CurrentEventAttributes))
        EDXMLValidatingStreamFilter.ignorableWhitespace(self, '\n      ')
        for Object in CurrentEvent:
          EDXMLValidatingStreamFilter.ignorableWhitespace(self, '  ')
          EDXMLValidatingStreamFilter.startElement(self, 'object', AttributesImpl({'property': Object['property'], 'value': Object['value']}))
          EDXMLValidatingStreamFilter.endElement(self, 'object')
          EDXMLValidatingStreamFilter.ignorableWhitespace(self, '\n      ')
        if len(CurrentEventContent) > 0:
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

    Call this method from :func:`EditEvent` to delete
    the event in stead of just editing it.
    """
    self.CurrentEventDeleted = True

  def EditEvent(self, SourceId, EventTypeName, EventObjects, EventContent, EventAttributes):
    """Modifies an event

    This method can be overridden to process single
    events.

    The EventObjects parameter is a list of dictionaries. Each
    dictionary represents one object, containing a 'property'
    key and a 'value' key.

    Args:
      SourceId (str): EDXML source identifier

      EventTypeName (str): Name of the event type

      EventObjects (list): List of event objects

      EventContent (str): Event content string

      EventAttributes (AttributesImpl): Sax AttributesImpl object containing <event> tag attributes

    Returns:
      tuple. Modified copies of the EventObjects, EventContent and EventAttributes parameters, in that order.
    """
    return EventObjects, EventContent, EventAttributes
