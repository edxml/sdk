# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                     Python class for parsing EDXML data
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
#  These classes parse and store information about eventtype, objecttype
#  and source definitions in EDXML files. They can optionally skip reading
#  the event data if you are only interested in the definitions. In that
#  case, they will abort XML processing by raising the SAXNotSupportedException
#  exception, which you can catch and handle.
#
#  The classes contain a Definitions property which is in instance of the
#  EDXMLDefinitions class. All parsed information from the EDXML header is stored
#  there, and you can use it to query information about event types, object types,
#  and so on.
#
#  The EDXMLParser class features several functions that can be overridden to 
#  implement custom EDXML processing scripts. An example of this can be found in
#  the EDXMLValidatingParser class, which is also found in this source file. This
#  class extends the functionality of EDXMLParser with thorough checking of the
#  EDXML data. You can use the EDXMLValidatingParser class to parse EDXML data that
#  you don't trust. The class will raise the EDXMLError exception when it finds
#  problems in the data.


import sys
import re
from decimal import *
from xml.sax import make_parser, SAXNotSupportedException
from xml.sax.saxutils import XMLFilterBase
from EDXMLBase import *
from EDXMLDefinitions import EDXMLDefinitions

class EDXMLParser(EDXMLBase, XMLFilterBase):

  def __init__ (self, upstream, SkipEvents = False):
  
    self.EventCounters = {}
    self.TotalEventCount = 0
    self.SkipEvents = SkipEvents
    self.NewEventType = True
    self.AccumulatingEventContent = False
    self.CurrentEventContent = ''
    
    self.Definitions = EDXMLDefinitions()
    
    XMLFilterBase.__init__(self, upstream)
    EDXMLBase.__init__(self)

  def Error(self, Message):
    raise EDXMLError(Message)
  
  # This function can be overridden to finish
  # processing the event stream
  def EndOfStream(self):
    return

  # This function can be overridden to process events.
  def ProcessEvent(self, EventTypeName, SourceId, EventObjects, EventContent):
    return

  # This function can be overridden to perform some
  # action as soon as the definitions are read and parsed.
  def DefinitionsLoaded(self):
    return
    
  # Returns the number of events parsed. When an
  # event type is passed, only the number of events
  # of this type is returned.
  def GetEventCount(self, EventTypeName = None):
    if EventTypeName:
      if EventTypeName in self.EventCounters:
        return self.EventCounters[EventTypeName]
      else:
        return 0
    else:
      return self.TotalEventCount

  def GetWarningCount(self):
    return self.WarningCount + self.Definitions.GetWarningCount()
    
  def GetErrorCount(self):
    return self.ErrorCount + self.Definitions.GetErrorCount()
  
  def startElement(self, name, attrs):

    #if name == 'events':
      #self.SourceIDs = {}
  
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

    if name == 'definitions':
      
      self.DefinitionsLoaded()
      
      if self.SkipEvents:
  
        # We hit the end of the definitions block,
        # and we were instructed to skip parsing the
        # event data, so we should abort parsing now.
        raise SAXNotSupportedException('')

    if name == 'eventtype':
      if not self.NewEventType:
        try:
          self.Definitions.CheckEventTypePropertyConsistency(self.CurrentEventTypeName, self.CurrentEventTypeProperties)
        except EDXMLError as Error:
          self.Error(Error)
        
    if name == 'objecttypes':
      # Check if all objecttypes that properties
      # refer to are actually defined.
      try:
        self.Definitions.CheckPropertyObjectTypes()
      except EDXMLError as Error:
        self.Error(Error)

    elif name == 'event':
      self.TotalEventCount += 1
      self.EventCounters[self.CurrentEventTypeName] += 1
      self.ProcessEvent(self.CurrentEventTypeName, self.CurrentSourceId, self.EventObjects, self.CurrentEventContent)

    elif name == 'events':
      self.EndOfStream()

    elif name == 'content':
      self.AccumulatingEventContent = False
      
  def characters(self, text):

    if self.AccumulatingEventContent:
      self.CurrentEventContent += text

# TODO:
#
# * Check for every event if the event reporter evaluates into an empty string, due
#   to missing objects. Maybe look at objects in outermost substring.

class EDXMLValidatingParser(EDXMLParser):
  
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

  # Overridden from EDXMLParser
  def ProcessObject(self, EventTypeName, ObjectProperty, ObjectValue):
    # Validate the object value against its data type
    ObjectTypeName = self.Definitions.GetPropertyObjectType(EventTypeName, ObjectProperty)
    ObjectTypeAttributes = self.Definitions.GetObjectTypeAttributes(ObjectTypeName)
    self.ValidateObject(ObjectValue, ObjectTypeName, ObjectTypeAttributes['data-type'])
    
  # Overridden from EDXMLParser
  def ProcessEvent(self, EventTypeName, SourceId, EventObjects, EventContent):

    UniquePropertyObjects = []
    
    for Object in EventObjects:

      # Check if the property is actually
      # supposed to be in this event.
      if not Object['property'] in self.Definitions.GetEventTypeProperties(EventTypeName):
        self.Error("An event of type %s contains an object of property %s, but this property does not belong to the event type." % (( EventTypeName, Object['property'] )) )

      ObjectTypeName = self.Definitions.GetPropertyObjectType(EventTypeName, Object['property'])
      ObjectTypeAttributes = self.Definitions.GetObjectTypeAttributes(ObjectTypeName)
      PropertyAttributes = self.Definitions.GetPropertyAttributes(EventTypeName, Object['property'])
      
      if 'unique' in PropertyAttributes:
        if PropertyAttributes['unique'].lower() == "true":
          # We have a unique property here.
          if not Object['property'] in UniquePropertyObjects:
            UniquePropertyObjects.append(Object['property'])
          else:
            self.Error("An event of type %s was found to have multiple objects of unique property %s." % (( EventTypeName, Object['property'] )) )
      

    if self.Definitions.EventTypeIsUnique(EventTypeName):
      # Verify that every unique properties has one object.
      for PropertyName in self.Definitions.GetUniqueProperties(EventTypeName):
        if not PropertyName in UniquePropertyObjects:
          EventObjectStrings = []
          for Object in EventObjects:
            EventObjectStrings.append("%s = %s" % (( Object['property'], Object['value'] )) )
          self.Error("An event of type %s is missing an object for unique property %s:\n%s" % (( EventTypeName, PropertyName, '\n'.join(EventObjectStrings) )) )

