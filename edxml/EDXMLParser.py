# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                     Python class for parsing EDXML data
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

"""EDXMLParser

This module is used for parsing out information about eventtype, objecttype
and source definitions from EDXML streams.

The classes contain a Definitions property which is in instance of the
EDXMLDefinitions class. All parsed information from the EDXML header is stored
there, and you can use it to query information about event types, object types,
and so on.

Classes in this module:
  
EDXMLParser
EDXMLValidatingParser
  
"""

import sys
import re
from cStringIO import StringIO
from lxml import etree
from xml.sax import make_parser
from xml.sax.saxutils import XMLFilterBase, XMLGenerator
from xml.sax.xmlreader import AttributesImpl
from EDXMLBase import *
from EDXMLDefinitions import EDXMLDefinitions


class EDXMLParser(EDXMLBase, XMLFilterBase):
  """The EDXMLParser class can be used as a content
  handler for Sax, and has several functions that
  can be overridden to implement custom EDXML processing
  scripts. It can optionally skip reading the event data
  itself if you are only interested in obtaining the 
  definitions. In that case, it will abort XML processing
  by raising the EDXMLProcessingInterrupted exception, which
  you can catch and handle."""
  
  def __init__ (self, upstream, SkipEvents = False):
    """Constructor.
    
    Parameters:
    upstream   -- XML source (SaxParser instance in most cases)
    SkipEvents -- Set to True to parse only the definitions section (default False)
    
    """
  
    self.EventCounters = {}
    self.TotalEventCount = 0
    self.SkipEvents = SkipEvents
    self.NewEventType = True
    self.AccumulatingEventContent = False
    self.CurrentEventContent = ''
    self.StreamCopyEnabled = True

    # This buffer will be used to compile a copy of the incoming EDXML
    # stream that has all event data filtered out. We use this stripped
    # copy to do RelaxNG validation, as Python has no incremental XML
    # validator like for instance PHP does.
    self.DefinitionsXMLStringIO = StringIO()

    # And this is the XMLGenerator instance that we will use
    # to fill the buffer.
    self.DefinitionsXMLGenerator = XMLGenerator(self.DefinitionsXMLStringIO, 'utf-8')

    """EDXMLDefinitions instance"""
    self.Definitions = EDXMLDefinitions()
    self.Definitions.Error = self.Error
    
    XMLFilterBase.__init__(self, upstream)
    EDXMLBase.__init__(self)

  def Error(self, Message):
    raise EDXMLError(Message)
  
  def EndOfStream(self):
    """This function can be overridden to finish
    processing the event stream."""
    return

  def ProcessEvent(self, EventTypeName, SourceId, EventObjects, EventContent, Parents):
    """This function can be overridden to process events. The
    EventObjects parameter contains a list of dictionaries, one
    for each object. Each dictionary has two keys. The 'property'
    key contains the name of the property. The 'value' key contains
    the value.
    
    Parameters:
    EventTypeName -- The name of the event type
    SourceId      -- Id of event source
    EventObjects  -- List of objects
    EventContent  -- String containing event content
    Parents       -- List of hashes of explicit parent events
    
    """
    return

  def ProcessObject(self, EventTypeName, ObjectProperty, ObjectValue):
    """This function can be overridden to process objects.
    
    Parameters:
    EventTypeName  -- The name of the event type
    ObjectProperty -- The name of the object property
    ObjectValue    -- String containing object value
    
    """
    return

  def DefinitionsLoaded(self):
    """This function can be overridden to perform some
    action as soon as the definitions are read and parsed."""
    return
    
  def GetEventCount(self, EventTypeName = None):
    """Returns the number of events parsed. When an
    event type is passed, only the number of events
    of this type is returned."""
    if EventTypeName:
      if EventTypeName in self.EventCounters:
        return self.EventCounters[EventTypeName]
      else:
        return 0
    else:
      return self.TotalEventCount

  def GetWarningCount(self):
    """Returns the number of warnings issued"""
    return self.WarningCount + self.Definitions.GetWarningCount()
    
  def GetErrorCount(self):
    """Returns the number of errors issued"""
    return self.ErrorCount + self.Definitions.GetErrorCount()
  
  def startElement(self, name, attrs):

    if self.StreamCopyEnabled:
      self.DefinitionsXMLGenerator.startElement(name, attrs)

    if name == 'eventgroup':
      SourceId = attrs.get('source-id')
      EventType = attrs.get('event-type')
      self.CurrentSourceId = SourceId
      self.CurrentEventTypeName = EventType
      if not EventType in self.EventCounters:
        self.EventCounters[EventType] = 0
      self.CurrentEventGroup = {'source-id': SourceId, 'event-type': EventType}
      if not self.Definitions.SourceIdDefined(SourceId):
        self.Error("An eventgroup refers to Source ID %s, which is not defined." % SourceId )
      if not self.Definitions.EventTypeDefined(EventType):
        self.Error("An eventgroup refers to eventtype %s, which is not defined." % EventType )

      self.StreamCopyEnabled = False

    elif name == 'source':
      Url = attrs.get('url')
      try:
        self.Definitions.AddSource(Url, dict(attrs.items()))
      except EDXMLError as Error:
        self.Error(Error)
        

    elif name == 'eventtype':
      self.CurrentEventTypeProperties = []
      self.CurrentEventTypeName = attrs.get('name')
      if self.Definitions.EventTypeDefined(self.CurrentEventTypeName):
        self.NewEventType = False
      else:
        self.NewEventType = True
      try:
        self.Definitions.AddEventType(self.CurrentEventTypeName, dict(attrs.items()))
      except EDXMLError as Error:
        self.Error(Error)
      
    elif name == 'property':
      PropertyName = attrs.get('name')
      self.CurrentEventTypeProperties.append(PropertyName)
      if not self.NewEventType:
        if not self.Definitions.PropertyDefined(self.CurrentEventTypeName, PropertyName):
          # Eventtype has been defined before, but this
          # property is not known in the existing eventtype
          # definition.
          self.Error("Property %s of eventtype %s did not exist in previous definition of this eventtype." % (( PropertyName, self.CurrentEventTypeName )) )
      try:
        self.Definitions.AddProperty(self.CurrentEventTypeName, PropertyName, dict(attrs.items()))
      except EDXMLError as Error:
        self.Error(Error)
      
    elif name == 'parent':
      try:
        self.Definitions.SetEventTypeParent(self.CurrentEventTypeName, dict(attrs.items()))
      except EDXMLError as Error:
        self.Error(Error)
          
    elif name == 'relation':
      Property1Name = attrs.get('property1')
      Property2Name = attrs.get('property2')
      if not self.NewEventType:
        if not self.Definitions.RelationDefined(self.CurrentEventTypeName, Property1Name, Property2Name):
          # Apparently, the relation was not defined in
          # the previous eventtype definition.
          self.Error("Relation between %s and %s in eventtype %s did not exist in previous definition of this eventtype." % (( Property1Name, Property2Name, self.CurrentEventTypeName )) )
      
      try:
        self.Definitions.AddRelation(self.CurrentEventTypeName, Property1Name, Property2Name, dict(attrs.items()))
      except EDXMLError as Error:
        self.Error(Error)
          
    elif name == 'event':
      self.ExplicitEventParents = []
      if attrs.has_key('parents'): self.ExplicitEventParents = attrs.get('parents').split(',')
      self.EventObjects = []
      self.CurrentEventContent = ''

    elif name == 'content':
      self.AccumulatingEventContent = True
      
    elif name == 'object':
      ObjectProperty  = attrs.get('property')
      ObjectValue = attrs.get('value')
      self.EventObjects.append({'property': ObjectProperty, 'value': ObjectValue})
      self.ProcessObject(self.CurrentEventTypeName, ObjectProperty, ObjectValue)
      
    elif name == 'objecttype':
      ObjectTypeName = attrs.get('name')
      try:
        self.Definitions.AddObjectType(ObjectTypeName, dict(attrs.items()))
      except EDXMLError as Error:
        self.Error(Error)
  
  def endElement(self, name):

    if name == 'event':
      self.TotalEventCount += 1
      self.EventCounters[self.CurrentEventTypeName] += 1
      self.ProcessEvent(self.CurrentEventTypeName, self.CurrentSourceId, self.EventObjects, self.CurrentEventContent, self.ExplicitEventParents)

    elif name == 'content':
      self.AccumulatingEventContent = False

    elif name == 'definitions':

      # Definitions section is complete, which means we can
      # finish the stream copy by adding the <eventgroups> tag
      # and closing the <events> tag. It is then ready for
      # RelaxNG validation.

      self.StreamCopyEnabled = True
      self.DefinitionsXMLGenerator.endElement(name)
      self.DefinitionsXMLGenerator.startElement('eventgroups', AttributesImpl({}))
      self.DefinitionsXMLGenerator.endElement('eventgroups')
      self.DefinitionsXMLGenerator.endElement('events')

      # Invoke callback
      self.DefinitionsLoaded()

      if self.SkipEvents:

        # We hit the end of the definitions block,
        # and we were instructed to skip parsing the
        # event data, so we should abort parsing now.
        raise EDXMLProcessingInterrupted('')

    elif name == 'eventtype':
      if not self.NewEventType:
        try:
          self.Definitions.CheckEventTypePropertyConsistency(self.CurrentEventTypeName, self.CurrentEventTypeProperties)
        except EDXMLError as Error:
          self.Error(Error)

    elif name == 'objecttypes':
      # Check if all objecttypes that properties
      # refer to are actually defined.
      try:
        self.Definitions.CheckPropertyObjectTypes()
      except EDXMLError as Error:
        self.Error(Error)

    elif name == 'events':
      self.EndOfStream()

    if self.StreamCopyEnabled:
      self.DefinitionsXMLGenerator.endElement(name)
      self.DefinitionsXMLGenerator.ignorableWhitespace("\n")

  def characters(self, text):

    if self.AccumulatingEventContent:
      self.CurrentEventContent += text

class EDXMLValidatingParser(EDXMLParser):
  """This class extends the functionality of EDXMLParser with thorough
  checking of the EDXML data. You can use the EDXMLValidatingParser 
  class to parse EDXML data that you don't trust. The class will raise
  the EDXMLError exception when it finds problems in the data. Validation
  is implemented by overriding the DefinitionsLoaded, ProcessObject and
  ProcessEvent calls."""  
  
  def __init__ (self, upstream, SkipEvents = False):

    EDXMLParser.__init__(self, upstream, SkipEvents)
    
  # Overridden from EDXMLParser
  def DefinitionsLoaded(self):

    ObjectTypeNames = self.Definitions.GetObjectTypeNames()
    for EventTypeName in self.Definitions.GetEventTypeNames():
      Attributes = self.Definitions.GetEventTypeAttributes(EventTypeName)
      PropertyNames = self.Definitions.GetEventTypeProperties(EventTypeName)
      # Check reporter strings
      self.Definitions.CheckReporterString(EventTypeName, Attributes['reporter-short'], PropertyNames, False)
      self.Definitions.CheckReporterString(EventTypeName, Attributes['reporter-long'], PropertyNames, True)
      # Check relations
      self.Definitions.CheckEventTypeRelations(EventTypeName)
      # Check parent definitions
      self.Definitions.CheckEventTypeParents(EventTypeName)
      # Check if properties refer to existing object types
      for PropertyName in PropertyNames:
        PropertyAttributes = self.Definitions.GetPropertyAttributes(EventTypeName, PropertyName)
        PropertyObjectType = self.Definitions.GetPropertyObjectType(EventTypeName, PropertyName)
        if self.Definitions.EventTypeIsUnique(EventTypeName):
          if not 'merge' in PropertyAttributes:
            self.Error("Property %s in unique event type %s does not have its 'merge' attribute set." % (( PropertyName, EventTypeName,  )) )
          if self.Definitions.PropertyIsUnique(EventTypeName, PropertyName):
            # All unique properties in a unique event type
            # must have the 'match' merge attribute.
            if PropertyAttributes['merge'] != 'match':
              self.Error("Unique property %s of event type %s has its 'match' attribute set to '%s'. Expected 'match' in stead." % (( PropertyName, EventTypeName, PropertyAttributes['merge'] )))
          else:
            if PropertyAttributes['merge'] == 'match':
              self.Error("Property %s of event type %s is not unique, but it has its 'match' attribute set to 'match'." % (( PropertyName, EventTypeName )))
        if not PropertyObjectType in ObjectTypeNames:
          self.Error("Event type %s contains a property (%s) which refers to unknown object type %s" % (( EventTypeName, PropertyName, PropertyObjectType )) )

    # We perform RelaxNG validation *after* running the above checks, because
    # XML validators generate rather cryptic errors. If the above code catches
    # a problem, the generated error message will be far more helpful. The RelaxNG
    # validation is really a double check that complements the above code.
    SchemaString = etree.parse(os.path.dirname(os.path.realpath(__file__)) + '/edxml-schema.xml')
    Schema = etree.RelaxNG(SchemaString)
    try:
      Schema.assertValid(etree.fromstring(self.DefinitionsXMLStringIO.getvalue()))
    except etree.DocumentInvalid as ValidationError:
      self.Error("Invalid EDXML detected in the generated <definitions> section: %s\nThe RelaxNG validator generated the following error: %s" % (( self.DefinitionsXMLStringIO.getvalue(), ValidationError )) )

  # Overridden from EDXMLParser
  def ProcessObject(self, EventTypeName, ObjectProperty, ObjectValue):
    # Validate the object value against its data type
    ObjectTypeName = self.Definitions.GetPropertyObjectType(EventTypeName, ObjectProperty)
    ObjectTypeAttributes = self.Definitions.GetObjectTypeAttributes(ObjectTypeName)
    self.ValidateObject(ObjectValue, ObjectTypeName, ObjectTypeAttributes['data-type'])
    
  # Overridden from EDXMLParser
  def ProcessEvent(self, EventTypeName, SourceId, EventObjects, EventContent, Parents):

    ParentPropertyMapping = self.Definitions.GetEventTypeParentMapping(EventTypeName)
    PropertyObjects = {}

    for Object in EventObjects:

      if Object['property'] in PropertyObjects:
        if Object['property'] in ParentPropertyMapping:
          self.Error("An event of type %s contains multiple objects of property %s, but this property can only have one object due to it being used in an implicit parent definition." % (( EventTypeName, Object['property'] )) )
        PropertyObjects[Object['property']].append(Object['value'])
      else:
        PropertyObjects[Object['property']] = [Object['value']]

      # Check if the property is actually
      # supposed to be in this event.
      if not Object['property'] in self.Definitions.GetEventTypeProperties(EventTypeName):
        self.Error("An event of type %s contains an object of property %s, but this property does not belong to the event type." % (( EventTypeName, Object['property'] )) )

      ObjectTypeName = self.Definitions.GetPropertyObjectType(EventTypeName, Object['property'])
      ObjectTypeAttributes = self.Definitions.GetObjectTypeAttributes(ObjectTypeName)
      PropertyAttributes = self.Definitions.GetPropertyAttributes(EventTypeName, Object['property'])

    if self.Definitions.EventTypeIsUnique(EventTypeName):
      # Verify that match, min and max properties have an object.
      for PropertyName in self.Definitions.GetMandatoryObjectProperties(EventTypeName):
        if not PropertyName in PropertyObjects:
          EventObjectStrings = []
          for Object in EventObjects:
            EventObjectStrings.append("%s = %s" % (( Object['property'], Object['value'] )) )
          self.Error("An event of type %s is missing an object for property %s, while it must have an object due to its configured merge strategy:\n%s" % (( EventTypeName, PropertyName, '\n'.join(EventObjectStrings) )) )
      for PropertyName in self.Definitions.GetSingletonObjectProperties(EventTypeName):
        if PropertyName in PropertyObjects:
          if len(PropertyObjects[PropertyName]) > 1:
            EventObjectStrings = []
            for Object in EventObjects:
              EventObjectStrings.append("%s = %s" % (( Object['property'], Object['value'] )) )
            self.Error("An event of type %s has multiple objects of property %s, while it cannot have more than one due to its configured merge strategy or due to a implicit parent definition:\n%s" % (( EventTypeName, PropertyName, '\n'.join(EventObjectStrings))))

