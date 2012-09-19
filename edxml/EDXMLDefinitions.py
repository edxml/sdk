# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                        EDXMLDefinitions Python class
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
#  This class is used for managing definitions of event types, object
#  types and sources from EDXML files. It is used for storing parsed
#  definitions, querying definitions, and combining definitions from
#  various EDXML files. When new definitions are stored, they are auto-
#  matically checked for consistency with existing definitions.
# 
#  The class also offers methods to generate EDXML <definitions> sections
#  from the stored definitions, or generate (partial) XSD and RelaxNG
#  schemas which can be used for validation of EDXML files.
#
#  ===========================================================================
#
#
# 

import hashlib
from decimal import *
from EDXMLBase import *
from lxml import etree
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl

class EDXMLDefinitions(EDXMLBase):
  
  def __init__(self):
    
    self.SourceIDs = {}
    self.SourceURLs = {}
    self.EventTypes = {}
    self.ObjectTypes = {}
    self.ObjectTypeEventTypes = {}
    self.EventTypeClasses = {}
    self.RelationPredicates = set()
    self.RequiredObjectTypes = set()
    self.EntityProperties = {}
    
    # These arrays hold names of event types,
    # properties and sources, in the exact
    # order they were encountered
    # in the EDXML stream.
    self.EventTypeNames = []
    self.PropertyNames = {}
    self.PropertyRelations = {}
    self.ObjectTypeNames = []
    self.Sources = []

    # Used for XSD generation
    self.XSD = {'xs': 'http://www.w3.org/2001/XMLSchema'}
    
    self.SchemaRelaxNG = None
    self.SchemaXSD = None

    self.KnownFormatters = ['DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR', 'DURATION',
                            'LATITUDE', 'LONGITUDE', 'BYTECOUNT', 'CURRENCY', 'FILESERVER', 
                            'BOOLEAN_STRINGCHOICE', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT']
                            
    self.ReporterPlaceholderPattern = re.compile('\\[\\[([^\\]]*)\\]\\]')
  
    # Some validation patterns
  
    self.SimpleNamePattern    = re.compile("^[a-z0-9-]*$")
    self.TrueFalsePattern     = re.compile("^(true)|(false)$")
    self.DecimalPattern       = re.compile("^[0-9.]+$")
    self.SourceDatePattern    = re.compile("^[0-9]{8}$")
    self.MergeOptions         = re.compile("^(drop)|(add)|(replace)|(min)|(max)|(match)$")
    self.RelationTypePattern  = re.compile("^(intra|inter|parent|child|other):.+")
    self.FuzzyMatchingPattern = re.compile("^(phonetic)|(\[[0-9]{1,2}:\])|(\[:[0-9]{1,2}\])$")
    self.DataTypePattern      = re.compile("^(boolean)|(timestamp)|(ip)|(hashlink)|(" + \
                                             "(number:(" + \
                                                 "((((tiny)|(small)|(medium)|(big))?int)|(float)|(double))(:signed)?" + \
                                               "))|(number:decimal:[0-9]+:[0-9]+(:signed)?)|(enum:.*)|(string:(" + \
                                                 "[0-9]+:((cs)|(ci))(:[ru]+)?" + \
                                               "))|(binstring:(" + \
                                                 "[0-9]+(:r)?" + \
                                               "))" + \
                                           ")$")
  
    # This dictionary contains constraints of attribute values of EDXML
    # entities, like eventtype, objecttype, property, etc. The restrictions
    # are extracted from the RelaxNG schema.
    
    self.EDXMLEntityAttributes = {
      'eventtype': {
        'name':           {'mandatory': True, 'length': 40,   'pattern': self.SimpleNamePattern},
        'description':    {'mandatory': True, 'length': 128,  'pattern': None},
        'classlist':      {'mandatory': True, 'length': None, 'pattern': None},
        'reporter-short': {'mandatory': True, 'length': None, 'pattern': None},
        'reporter-long':  {'mandatory': True, 'length': None, 'pattern': None}
      },
      'property': {
        'name':              {'mandatory': True,  'length': 64,   'pattern': self.SimpleNamePattern},
        'description':       {'mandatory': True,  'length': 128,  'pattern': None},
        'object-type':       {'mandatory': True,  'length': 40,   'pattern': self.SimpleNamePattern},
        'unique':            {'mandatory': False, 'length': None, 'pattern': self.TrueFalsePattern},
        'merge':             {'mandatory': False, 'length': None, 'pattern': self.MergeOptions},
        'defines-entity':    {'mandatory': False, 'length': None, 'pattern': self.TrueFalsePattern},
        'entity-confidence': {'mandatory': False, 'length': None, 'pattern': self.DecimalPattern}
      },
      'relation': {
        'property1':   {'mandatory': True,  'length': 64,   'pattern': self.SimpleNamePattern},
        'property2':   {'mandatory': True,  'length': 64,   'pattern': self.SimpleNamePattern},
        'description': {'mandatory': True,  'length': 255,  'pattern': None},
        'type':        {'mandatory': True,  'length': 32,   'pattern': self.RelationTypePattern},
        'confidence':  {'mandatory': True, 'length': None, 'pattern': self.DecimalPattern}
      },
      'objecttype': {
        'name':              {'mandatory': True,  'length': 40,   'pattern': self.SimpleNamePattern},
        'description':       {'mandatory': True,  'length': 128,  'pattern': None},
        'fuzzy-matching':    {'mandatory': False, 'length': None,  'pattern': self.FuzzyMatchingPattern},
        'data-type':         {'mandatory': True,  'length': None,  'pattern': self.DataTypePattern}
      },
      'source': {
        'source-id':        {'mandatory': True,  'length': None,   'pattern': None},
        'url':              {'mandatory': True,  'length': None,   'pattern': None},
        'date-acquired':    {'mandatory': True,  'length': None,   'pattern': self.SourceDatePattern},
        'description':      {'mandatory': True,  'length': 128,  'pattern': None},
      },
    }
  
    EDXMLBase.__init__(self)
  
  def SourceIdDefined(self, SourceId):
    return SourceId in self.SourceIDs.keys()
  
  def EventTypeDefined(self, EventTypeName):
    return EventTypeName in self.EventTypes
  
  def PropertyDefined(self, EventTypeName, PropertyName):
    return PropertyName in self.EventTypes[EventTypeName]['properties']
      
  def ObjectTypeDefined(self, ObjectTypeName):
    return ObjectTypeName in self.ObjectTypes
  
  def RelationDefined(self, EventTypeName, Property1Name, Property2Name):
    RelationId = Property1Name + ' -> ' + Property2Name
    return RelationId in self.EventTypes[EventTypeName]['relations']
  
  def GetRelationPredicates(self):
    return list(self.RelationPredicates)
  
  # Returns a boolean indicating if given
  # eventtype is unique or not.
  def EventTypeIsUnique(self, EventTypeName):
    return self.EventTypes[EventTypeName]['unique']

  # Returns a boolean indicating if given
  # property is unique or not.
  def PropertyIsUnique(self, EventTypeName, PropertyName):
    return PropertyName in self.EventTypes[EventTypeName]['unique-properties']

  def GetUniqueProperties(self, EventTypeName):
    return self.EventTypes[EventTypeName]['unique-properties']
  
  def PropertyDefinesEntity(self, EventTypeName, PropertyName):
    return PropertyName in self.EntityProperties[EventTypeName]
  
  # Returns a boolean indicating if given
  # property of specified event type is involved
  # in any defined property relation
  def PropertyInRelation(self, EventTypeName, PropertyName):
    return PropertyName in self.EventTypes[EventTypeName]['related-properties']
  
  # Returns an ordered list of all parsed
  # source URLs. The order as they
  # appeared in the XML is preserved.
  def GetSourceURLs(self):
    return self.SourceURLs.keys()

  def GetSourceIDs(self):
    return self.Sources
    
  def GetSourceId(self, Url):
    return self.SourceURLs[Url]['source-id']

  # Returns a list of all parsed
  # event type names. The order as they
  # appeared in the XML is preserved.
  def GetEventTypeNames(self):
    return self.EventTypeNames
    
  # Returns a dictionary containing all
  # attributes of requested event type
  def GetEventTypeAttributes(self, EventTypeName):
    return self.EventTypes[EventTypeName]['attributes']

  def GetEventTypesHavingObjectType(self, ObjectTypeName):
    if not ObjectTypeName in self.ObjectTypeEventTypes:
      return []
    else:
      return list(self.ObjectTypeEventTypes[ObjectTypeName])
    
  # Returns a list of event type names that
  # belong to specified class.
  def GetEventTypeNamesInClass(self, ClassName):
    return list(self.EventTypeClasses[ClassName])
    
  # Returns a list of event type names that
  # belong to specified list of classes.
  def GetEventTypeNamesInClasses(self, ClassNames):
    EventTypeNames = set()
    for ClassName in ClassNames:
      for EventTypeName in self.EventTypeClasses[ClassName]:
        EventTypeNames.add(EventTypeName)
    return list(EventTypeNames)
    
  # Returns a dictionary containing all
  # attributes of requested object type
  def GetObjectTypeAttributes(self, ObjectTypeName):
    return self.ObjectTypes[ObjectTypeName]
    
  # Returns a list of all property names
  # of given event type. The order as they
  # appeared in the XML is preserved.
  def GetEventTypeProperties(self, EventTypeName):
    return self.PropertyNames[EventTypeName]
    
  # Returns a list of all IDs of property relations
  # of given event type. The order as they
  # appeared in the XML is preserved.
  def GetEventTypePropertyRelations(self, EventTypeName):
    return self.PropertyRelations[EventTypeName]
  
  # Returns a dictionary containing all
  # attributes of requested object type
  def GetPropertyRelationAttributes(self, EventTypeName, RelationId):
    return self.EventTypes[EventTypeName]['relations'][RelationId]
  
  # Returns a list of all defined object type names
  # The order as they appeared in the XML is preserved.
  def GetObjectTypeNames(self):
    return self.ObjectTypeNames

  # Returns source properties of source
  # specified by given URL
  def GetSourceURLProperties(self, Url):
    return self.SourceURLs[Url]

  # Returns source properties of source
  # specified by given Source ID
  def GetSourceIdProperties(self, SourceId):
    return self.SourceURLs[self.SourceIDs[SourceId]]
  
  # Returns True when given object type requires
  # unicode characters, return False otherwise.
  def ObjectTypeRequiresUnicode(self, ObjectTypeName):
    ObjectDataType = self.ObjectTypes[ObjectTypeName]['data-type'].split(':')
    if len(ObjectDataType) < 4 or 'u' not in ObjectDataType[3]:
      return False
    else:
      return True
    
  # Return the name of the objecttype of specified event property
  def GetPropertyObjectType(self, EventTypeName, PropertyName):
    if EventTypeName in self.EventTypes:
      if PropertyName in self.EventTypes[EventTypeName]['properties']:
        ObjectType = self.EventTypes[EventTypeName]['properties'][PropertyName]['object-type']
        return ObjectType
      else:
        self.Error('Event type %s has no property named "%s"' % (( str(EventTypeName), str(PropertyName) )) )
    else:
      self.Error('Unknown event type %s' % str(EventTypeName) )

  # Return dictionary of attributes of specified event property
  def GetPropertyAttributes(self, EventTypeName, PropertyName):
    return self.EventTypes[EventTypeName]['properties'][PropertyName]

  # Return the datatype of given object type
  def GetObjectTypeDataType(self, ObjectTypeName):
    return self.ObjectTypes[ObjectTypeName]['data-type']

  # Add an eventtype to the collection of eventtype
  # definitions. If an eventtype definition with the same
  # name exists, it will be checked for consistency with
  # the existing definition.
  # => Attributes should be a dictionary holding the
  #    attributes of the 'eventtype' XML tag.
  def AddEventType(self, EventTypeName, Attributes):
    self.RequiredObjectTypes = set()
    if EventTypeName in self.EventTypes:
      # Event type definition was encountered before.
      self.CheckEdxmlEntityConsistency('eventtype', EventTypeName, self.EventTypes[EventTypeName]['attributes'], Attributes)
    else:
      # New event type
      self.AddNewEventType(EventTypeName, Attributes)
    
  # Add a property to the collection of event property
  # definitions. If a property definition with the same
  # name exists, it will be checked for consistency with
  # the existing definition.
  # => Attributes should be a dictionary holding the
  #    attributes of the 'property' XML tag.
  def AddProperty(self, EventTypeName, PropertyName, Attributes):
    if PropertyName in self.EventTypes[EventTypeName]['properties']:
      # Property definition was encountered before.
      self.CheckEdxmlEntityConsistency('property', PropertyName, self.EventTypes[EventTypeName]['properties'][PropertyName], Attributes)
    else:
      # New property
      self.AddNewProperty(EventTypeName, PropertyName, Attributes)
        
  # Add a relation to the collection of property relation
  # definitions. If a property relation with the same
  # combination of property names exists, it will be 
  # checked for consistency with the existing definition.
  # => Attributes should be a dictionary holding the
  #    attributes of the 'relation' XML tag.
  def AddRelation(self, EventTypeName, Property1Name, Property2Name, Attributes):
    RelationId = Property1Name + ' -> ' + Property2Name
    if RelationId in self.EventTypes[EventTypeName]['relations']:
      # Relation definition was encountered before.
      self.CheckEdxmlEntityConsistency('relation', RelationId, self.EventTypes[EventTypeName]['relations'][RelationId], Attributes)
    else:
      self.AddNewRelation(EventTypeName, RelationId, Property1Name, Property2Name, Attributes)
      
  # Add a object type to the collection of object type
  # definitions. If a object type definition with the same
  # name exists, it will be checked for consistency with
  # the existing definition.
  # => Attributes should be a dictionary holding the
  #    attributes of the 'objecttype' XML tag.
  def AddObjectType(self, ObjectTypeName, Attributes, WarnNotUsed = True):
    if WarnNotUsed:
      if not ObjectTypeName in self.RequiredObjectTypes:
        self.Warning("Object type %s was defined, but it is not used." % ObjectTypeName )
    if ObjectTypeName in self.ObjectTypes:
      # Object type was defined before
      self.CheckEdxmlEntityConsistency('objecttype', ObjectTypeName, self.ObjectTypes[ObjectTypeName], Attributes)
    else:
      # New object type
      self.AddNewObjectType(ObjectTypeName, Attributes)
      
  # Add a source to the collection of data source
  # definitions. If a source definition with the same
  # URL exists, it will be checked for consistency with
  # the existing definition.
  # => Attributes should be a dictionary holding the
  #    attributes of the 'source' XML tag.
  def AddSource(self, SourceUrl, Attributes):
    SourceId = Attributes['source-id']
    self.SourceIDs[SourceId] = SourceUrl
    if SourceUrl in self.SourceURLs.keys():
      self.CheckEdxmlEntityConsistency('source', SourceUrl, self.SourceURLs[SourceUrl], Attributes)
    else:
      self.Sources.append(SourceId)
      self.AddNewSource(SourceUrl, Attributes)
  
  def AddNewEventType(self, EventTypeName, Attributes):
    
    self.EventTypeNames.append(EventTypeName)
    self.PropertyNames[EventTypeName] = []
    self.EntityProperties[EventTypeName] = set()
    self.PropertyRelations[EventTypeName] = []
    
    self.ValidateEdxmlEntityAttributes('eventtype', Attributes)

    self.EventTypes[EventTypeName] = {
      'attributes': Attributes, 
      'properties': {}, 
      'unique-properties': set(), 
      'relations': {}, 
      'related-properties': set(), 
      'unique': False
      }

    for Class in Attributes['classlist'].split(','):
      if not Class in self.EventTypeClasses:
        self.EventTypeClasses[Class] = set()
      self.EventTypeClasses[Class].add(EventTypeName)
      
  def AddNewProperty(self, EventTypeName, PropertyName, Attributes):
    self.PropertyNames[EventTypeName].append(PropertyName)

    self.ValidateEdxmlEntityAttributes('property', Attributes)
    
    ObjectType = Attributes['object-type']
    self.RequiredObjectTypes.add(ObjectType)
    if not ObjectType in self.ObjectTypeEventTypes:
      self.ObjectTypeEventTypes[ObjectType] = set()
    self.ObjectTypeEventTypes[ObjectType].add(EventTypeName)
    
    if 'unique' in Attributes and Attributes['unique'].lower() == 'true':
      self.EventTypes[EventTypeName]['unique'] = True
      self.EventTypes[EventTypeName]['unique-properties'].add(PropertyName)

    if 'defines-entity' in Attributes and Attributes['defines-entity'].lower() == 'true':
      self.EntityProperties[EventTypeName].add(PropertyName)
      
    self.EventTypes[EventTypeName]['properties'][PropertyName] = {'unique': 'false', 'defines-entity': 'false'}
    self.EventTypes[EventTypeName]['properties'][PropertyName].update(Attributes)

  def AddNewObjectType(self, ObjectTypeName, Attributes):
    
    self.ValidateEdxmlEntityAttributes('objecttype', Attributes)
    self.ValidateDataType(ObjectTypeName, Attributes['data-type'])

    self.ObjectTypes[ObjectTypeName] = Attributes
    self.ObjectTypeNames.append(ObjectTypeName)

  def AddNewRelation(self, EventTypeName, RelationId, Property1Name, Property2Name, Attributes):
    self.EventTypes[EventTypeName]['related-properties'].add(Property1Name)
    self.EventTypes[EventTypeName]['related-properties'].add(Property2Name)
    self.PropertyRelations[EventTypeName].append(RelationId)

    self.ValidateEdxmlEntityAttributes('relation', Attributes)

    SplitEventType = Attributes['type'].split(':')
    if len(SplitEventType) == 2:
      self.RelationPredicates.add(SplitEventType[1])
    
    self.EventTypes[EventTypeName]['relations'][RelationId] = Attributes

  def AddNewSource(self, SourceUrl, Attributes):
    self.ValidateEdxmlEntityAttributes('source', Attributes)
    self.SourceURLs[SourceUrl] = Attributes

  # Checks if all object types that properties
  # refer to are defined. Throws an error when
  # a problem is detected.
  def CheckPropertyObjectTypes(self):
      for ObjectTypeName in self.RequiredObjectTypes:
        if not self.ObjectTypeDefined(ObjectTypeName):
          self.Error("Objecttype %s was used in a property definition, but it was not defined." % ObjectTypeName )

  # Check if specified list of property names
  # is correct for the specified event type.
  def CheckEventTypePropertyConsistency(self, EventTypeName, PropertyNames):
    for PropertyName in PropertyNames:
      if not self.PropertyDefined(EventTypeName, PropertyName):
        self.Error("Property %s was previously defined as part of eventtype %s, but this definition does not define it." % (( PropertyName, EventTypeName )) )

  # Check if the relation definitions for
  # specified eventtype are correct.
  def CheckEventTypeRelations(self, EventTypeName):
    
    for RelationId in self.EventTypes[EventTypeName]['relations']:
      PropertyA   = None
      PropertyB   = None
      Description = None
      
      for Attribute in self.EventTypes[EventTypeName]['relations'][RelationId]:
        if Attribute == 'property1':
          PropertyA = self.EventTypes[EventTypeName]['relations'][RelationId][Attribute]
        elif Attribute == 'property2':
          PropertyB = self.EventTypes[EventTypeName]['relations'][RelationId][Attribute]
        elif Attribute == 'description':
          Description = self.EventTypes[EventTypeName]['relations'][RelationId][Attribute]
      
      Placeholders = re.findall(self.PlaceHolderPattern, Description)
      
      if not PropertyA in Placeholders:
        self.Error("Event type %s defines relation %s which does not have one of its properties (%s) in the description." % (( EventTypeName, RelationId, PropertyA )) )
    
      if not PropertyB in Placeholders:
        self.Error("Event type %s defines relation %s which does not have one of its properties (%s) in the description." % (( EventTypeName, RelationId, PropertyB )) )
        
      if not self.PropertyDefined(EventTypeName, PropertyA):
        self.Error("Event type %s defines relation %s which refers to property %s, which does not exist in this event type." % (( EventTypeName, RelationId, PropertyA )))
        
      if not self.PropertyDefined(EventTypeName, PropertyB):
        self.Error("Event type %s defines relation %s which refers to property %s, which does not exist in this event type." % (( EventTypeName, RelationId, PropertyB )))

  # Checks if given eventtype reporter string makes sense. Optionally,
  # it can also check if all given properties are present in the string.
  def CheckReporterString(self, EventTypeName, String, PropertyNames, CheckCompleteness = False):
    PlaceholderStrings = re.findall(self.ReporterPlaceholderPattern, String)
    ReferredProperties = []
    
    for String in PlaceholderStrings:
      StringComponents = String.split(':')
      if len(StringComponents) == 1:
        # Placeholder does not contain a formatter.
        if StringComponents[0] in PropertyNames:
          ReferredProperties.append(StringComponents[0])
          continue
      else:
        # Some kind of string formatter was used.
        # Figure out which one, and check if it
        # is used correctly.
        if StringComponents[0] == 'DURATION':
          DurationProperties = StringComponents[1].split(',')
          if DurationProperties[0] in PropertyNames and DurationProperties[1] in PropertyNames:
            ReferredProperties.append(DurationProperties[0])
            ReferredProperties.append(DurationProperties[1])

            # Check that both properties are timestamps
            if self.GetObjectTypeDataType(self.GetPropertyObjectType(EventTypeName, DurationProperties[0])) != 'timestamp':
              self.Error("Event type %s contains a reporter string which uses a time related formatter, but the used property (%s) is not a timestamp." % (( EventTypeName, DurationProperties[0] )) )
            if self.GetObjectTypeDataType(self.GetPropertyObjectType(EventTypeName, DurationProperties[1])) != 'timestamp':
              self.Error("Event type %s contains a reporter string which uses a time related formatter, but the used property (%s) is not a timestamp." % (( EventTypeName, DurationProperties[1] )) )

            continue
        else:
          if not StringComponents[0] in self.KnownFormatters:
            self.Error("Event type %s contains a reporter string which refers to an unknown formatter: %s" % (( EventTypeName, StringComponents[0] )) )
            
          if StringComponents[0] in ['DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR']:
            # Check that only one property is specified after the formatter
            if len(StringComponents[1].split(',')) > 1:
              self.Error("Event type %s contains a reporter string which uses the %s formatter, which accepts just one property. Multiple properties were specified: %s" % (( EventTypeName, StringComponents[0], StringComponents[1] )) )
            # Check that property is a timestamp
            if self.GetObjectTypeDataType(self.GetPropertyObjectType(EventTypeName, StringComponents[1])) != 'timestamp':
              self.Error("Event type %s contains a reporter string which uses the %s formatter. The used property (%s) is not a timestamp, though." % (( EventTypeName, StringComponents[0], StringComponents[1] )) )

          elif StringComponents[0] in ['LATITUDE', 'LONGITUDE', 'BYTECOUNT', 'FILESERVER', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT']:
            # Check that no additional options are present
            if len(StringComponents) > 2:
              self.Error("Event type %s contains a reporter string which uses the %s formatter. This formatter accepts no options, but they were specified: %s" % (( EventTypeName, StringComponents[0], String )) )
            # Check that only one property is specified after the formatter
            if len(StringComponents[1].split(',')) > 1:
              self.Error("Event type %s contains a reporter string which uses the %s formatter. This formatter accepts just one property. Multiple properties were given though: %s" % (( EventTypeName, StringComponents[0], StringComponents[1] )) )
            if StringComponents[0] in ['BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT']:
              # Check that property is a boolean
              if self.GetObjectTypeDataType(self.GetPropertyObjectType(EventTypeName, StringComponents[1])) != 'boolean':
                self.Error("Event type %s contains a reporter string which uses the %s formatter. The used property (%s) is not a boolean, though." % (( EventTypeName, StringComponents[0], StringComponents[1] )) )

          elif StringComponents[0] == 'CURRENCY':
            if len(StringComponents) != 3:
              self.Error("Event type %s contains a reporter string which uses a malformed %s formatter: %s" % (( EventTypeName, StringComponents[0], String )) )
              
          elif StringComponents[0] == 'BOOLEAN_STRINGCHOICE':
            if len(StringComponents) != 4:
              self.Error("Event type %s contains a reporter string which uses a malformed %s formatter: %s" % (( EventTypeName, StringComponents[0], String )) )
            # Check that property is a boolean
            if self.GetObjectTypeDataType(self.GetPropertyObjectType(EventTypeName, StringComponents[1])) != 'boolean':
              self.Error("Event type %s contains a reporter string which uses the %s formatter. The used property (%s) is not a boolean, though." % (( EventTypeName, StringComponents[0], StringComponents[1] )) )

          else:
              self.Error("Event type %s contains a reporter string which uses an unknown formatter: %s" % (( EventTypeName, StringComponents[0] )) )
            
              
          if StringComponents[1] in PropertyNames:
            ReferredProperties.append(StringComponents[1])
            continue
          
      self.Error("Event type %s contains a reporter string which refers to one or more nonexisting properties: %s" % (( EventTypeName, String )) )
  
    if CheckCompleteness:
      for PropertyName in PropertyNames:
          if not PropertyName in ReferredProperties:
            self.Warning("Event type %s contains an incomplete long reporter string. The property '%s' is missing." % (( EventTypeName, PropertyName )))
  
  # Checks if two sets of attributes of EDXML entities (eventtype, property, relation, ...)
  # are mutually consistent. The parameters CurrentAttributes and UpdatedAttributes
  # should contain dictionaries with attributes of the entity.
  
  def CheckEdxmlEntityConsistency(self, Entity, EntityDescription, CurrentAttributes, UpdatedAttributes):
    
    Current = set(CurrentAttributes.keys())
    Update  = set(UpdatedAttributes.keys())
    
    AttribsAdded    = Update - Current
    AttribsRetained = Update & Current
    AttribsRemoved  = Current - Update
    
    # First we check if the attributes that are retained in the
    # update are consistent with the exiting atribute values.
    
    for Attribute in AttribsRetained:
      if CurrentAttributes[Attribute] != UpdatedAttributes[Attribute]:
        self.Error("Attribute %s of %s '%s' does not match previous definition:\nNew:      %s\nExisting: %s\n" % (( Attribute, Entity, EntityDescription, UpdatedAttributes[Attribute], CurrentAttributes[Attribute] )))
        
    # At the moment, we do not accept new attributes to appear or 
    # existing attributes to disappear, even if they are optional.
    # there are some exceptions, which we will get rid of as soon 
    # as eventtype versioning is implemented.
    
    if len(AttribsAdded) > 0:
      
      if Entity == 'property':
        for Attrib in AttribsAdded:
          if Attrib in ['unique', 'defines-entity']:
            if UpdatedAttributes[Attrib] == 'false':
              continue
          self.Error("Definition of %s '%s' contains attribute that were not previously defined: %s" % (( Entity, EntityDescription, Attrib)) )
      else:
        self.Error("Definition of %s '%s' contains attributes that were not previously defined: %s" % (( Entity, EntityDescription, ','.join(list(AttribsAdded)) )))
    
    if len(AttribsRemoved) > 0:

      if Entity == 'property':
        for Attrib in AttribsAdded:
          if Attrib in ['unique', 'defines-entity']:
            if CurrentAttributes[Attrib] == 'false':
              continue
          self.Error("Definition of %s '%s' lacks attribute that was previously defined: %s" % (( Entity, EntityDescription, Attrib)) )
      else:
        self.Error("Definition of %s '%s' lacks attributes that were present in previous definition: %s" % (( Entity, EntityDescription, ','.join(list(AttribsRemoved)) )))
  
  # Checks the attributes of a specific EDXML entity (eventtype, 
  # objecttype, relation, ...) against the constaints as specified in
  # self.EDXMLEntityAttributes.
  
  def ValidateEdxmlEntityAttributes(self, EntityName, Attributes):

    for Attribute in self.EDXMLEntityAttributes[EntityName]:
      
      if Attribute in Attributes:
        Value = Attributes[Attribute]
      else:
        if self.EDXMLEntityAttributes[EntityName][Attribute]['mandatory']:
          self.Error("Definition of %s lacks mandatory attribute '%s'." % (( EntityName, Attribute )) )
        else:
          Value = None
    
      if Value:
    
        if self.EDXMLEntityAttributes[EntityName][Attribute]['length']:
          if len(Value) > self.EDXMLEntityAttributes[EntityName][Attribute]['length']:
            self.Error("Value of %s attribute %s is too long: %s " % (( EntityName, Attribute, Value )))
        if self.EDXMLEntityAttributes[EntityName][Attribute]['pattern']:
          if re.match(self.EDXMLEntityAttributes[EntityName][Attribute]['pattern'], Value) == None:
            self.Error("Value of %s attribute %s is invalid: %s " % (( EntityName, Attribute, Value )))
    
    UnknownAttributes = list(set(Attributes.keys()) - set(self.EDXMLEntityAttributes[EntityName].keys()))

    if len(UnknownAttributes) > 0:
      self.Error("Definition of %s contains unknown attributes: %s" % (( EntityName, ','.join(UnknownAttributes) )) )
    
  # Source IDs are required to be unique only
  # within a single EDXML file. When multiple 
  # EDXML files are parsed using the same EDXMLParser
  # instance, it may happen that different sources have
  # the same ID. This function changes the Source IDs
  # of all known sources to be unique.
  #
  # It returns a mapping that maps old Source ID into
  # new Source ID.
  
  def UniqueSourceIDs(self):
    Counter = 1
    Mapping = {}
    for SourceUrl in self.SourceURLs:
      Mapping[self.SourceURLs[SourceUrl]['source-id']] = str(Counter)
      self.SourceURLs[SourceUrl]['source-id'] = str(Counter)
      self.SourceIDs[str(Counter)] = SourceUrl
      Counter += 1
    return Mapping

  # Merges the objects of an event 'B' with the objects
  # of another event 'A'. The arguments EventObjectsA
  # and EventObjectsB should be lists of dictionaries,
  # where each dictionary has two keys:
  #
  # - 'property'
  # - 'value'
  #
  # It updates the object values in EventObjectsA, using the
  # values from EventObjectsB. It returns True when EventObjectsA
  # was modified, False otherwise.
  
  def MergeEvents(self, EventTypeName, EventObjectsA, EventObjectsB):
    
    if self.EventTypes[EventTypeName]['unique'] == False:
      self.Error("MergeEvent was called for event type %s, which is not a unique event type." % EventTypeName)
    
    Original = {}
    Source = {}
    Target = {}
    
    for PropertyName in self.GetEventTypeProperties(EventTypeName):
      if PropertyName in EventObjectsA: 
        Original[PropertyName] = set(EventObjectsA[PropertyName])
        Target[PropertyName] = set(EventObjectsA[PropertyName])
      else:
        Original[PropertyName] = set()
        Target[PropertyName] = set()
      if PropertyName in EventObjectsB: Source[PropertyName] = set(EventObjectsB[PropertyName])
      else: Source[PropertyName] = set()
    
    # Now we update the objects in Target
    # using the values in Source
    for PropertyName in Source:

      if not PropertyName in self.EventTypes[EventTypeName]['unique-properties']:
        # Not a unique property, needs to be merged.
        MergeStrategy = self.EventTypes[EventTypeName]['properties'][PropertyName]['merge']
        
        if MergeStrategy in ['min', 'max']:
          SplitDataType = self.GetObjectTypeDataType(self.GetPropertyObjectType(EventTypeName, PropertyName)).split(':')
          if SplitDataType[0] in ['number', 'timestamp']:
            
            Values = set()
            
            if SplitDataType[0] == 'timestamp':
              
              Values = Source[PropertyName] | Target[PropertyName]

            else:  
              
              if SplitDataType[1] in ['float', 'double']:
                for Value in Source[PropertyName]: Values.add(float(Value))
                for Value in Target[PropertyName]: Values.add(float(Value))
              elif SplitDataType[1] == 'decimal':
                for Value in Source[PropertyName]: Values.add(Decimal(Value))
                for Value in Target[PropertyName]: Values.add(Decimal(Value))
              else:
                for Value in Source[PropertyName]: Values.add(int(Value))
                for Value in Target[PropertyName]: Values.add(int(Value))
              
            if MergeStrategy == 'min':
              Target[PropertyName] = set([str(min(Values))])
            else:
              Target[PropertyName] = set([str(max(Values))])
          
        elif MergeStrategy == 'add':
          Target[PropertyName] = Source[PropertyName] | Target[PropertyName]

        elif MergeStrategy == 'replace':
          Target[PropertyName] = Source[PropertyName]
          
    # Determine if anything changed
    
    EventUpdated = False
    for PropertyName in self.GetEventTypeProperties(EventTypeName):
      if not PropertyName in Original and len(Target[PropertyName]) > 0:
        EventUpdated = True
        break
      if Target[PropertyName] != Original[PropertyName]:
        EventUpdated = True
        break
    
    # Modify EventObjectsA if needed
    
    if EventUpdated:
      EventObjectsA.clear()
      for PropertyName in Target:
        EventObjectsA[PropertyName] = []
        for Value in Target[PropertyName]:
          EventObjectsA[PropertyName].append(Value)
      return True
    else:
      return False

  # Computes a sticky hash from given event. The EventObjects argument
  # should be an array containing dictionaries representing objects. The
  # dictionaries shoud contain the property name stored under the 'property'
  # key and the value stored under the 'value' key.
  #
  # Returns a hexadecimal string representation of the hash.
  
  def ComputeStickyHash(self, EventTypeName, EventObjects, EventContent):

    ObjectStrings = []
  
    for EventObject in EventObjects:
      Property = EventObject['property']
      Value    = EventObject['value']
      if self.EventTypeIsUnique(EventTypeName) and self.PropertyIsUnique(EventTypeName, Property) == False:
        # We use only unique properties for
        # hash computation. Skip this one.
        continue
      ObjectType = self.GetPropertyObjectType(EventTypeName, Property)
      DataType = self.GetObjectTypeDataType(ObjectType).split(':')
      if DataType[0] == 'timestamp':
        ObjectStrings.append(u'%s:%.6f' % (( Property, Decimal(Value) )) )
      elif DataType[0] == 'number':
        if DataType[1] == 'decimal':
          DecimalPrecision = DataType[3]
          ObjectStrings.append(unicode('%s:%.' + DecimalPrecision + 'f') % (( Property, Decimal(Value) )) )
        elif DataType[1] in [ 'tinyint', 'smallint', 'mediumint', 'int', 'bigint']:
          ObjectStrings.append(u'%s:%d' % (( Property, int(Value) )) )
        else:
          # Anything else is floating point, which we ignore.
          continue
          
      elif DataType[0] == 'ip':
        try:
          Octets = Value.split('.')
          ObjectStrings.append(unicode('%s:%d.%d.%d.%d' % (( Property, int(Octets[0]), int(Octets[1]), int(Octets[2]), int(Octets[3]) ))  ))
        except Exception as Except:
          self.Error("Invalid IP in property %s of event type %s: '%s': %s" % (( Property, EventTypeName, Value, Except )))
      elif DataType[0] == 'string':
        
        if not isinstance(Value, unicode):
          if not isinstance(Value, str):
            sys.stderr.write("ComputeStickyHash: WARNING: Expected a string, but passed value is no string: '%s'" % str(Value) )
            Value = unicode(Value)
          try:
            Value = Value.decode('utf-8')
          except UnicodeDecodeError:
            # String is not proper UTF8. Lets try to decode it as Latin1
            try:
              Value = Value.decode('latin-1').encode('utf-8').decode('utf-8')
            except:
              self.Error("ComputeStickyHash: Failed to convert string object to unicode: '%s'." % repr(Value) )
              
        if DataType[2] == 'ci':
          Value = Value.lower()
        if self.ObjectTypeRequiresUnicode(ObjectType):
          ObjectStrings.append(unicode('%s:%s' % (( Property, Value )) ))
        else:
          ObjectStrings.append(unicode('%s:%s' % (( Property, Value )) ))
      elif DataType[0] == 'boolean':
        ObjectStrings.append(unicode('%s:%s' % (( Property, Value.lower() )) ))
      else:
        ObjectStrings.append(unicode('%s:%s' % (( Property, Value )) ))

    # Now we compute the SHA1 hash value of the unicode
    # string representation of the event, and output in hex
    
    if self.EventTypeIsUnique(EventTypeName):
      return hashlib.sha1((EventTypeName + '\n' + '\n'.join(sorted(ObjectStrings))).encode('utf-8')).hexdigest()
    else:    
      return hashlib.sha1((EventTypeName + '\n' + '\n'.join(sorted(ObjectStrings)) + '\n' + EventContent).encode('utf-8')).hexdigest()

      
  # Generates an EDXML fragment which defines specified
  # eventtype. Can be useful for constructing new EDXML
  # files based on existing event type definitions.
  
  def GenerateEventTypeXML(self, EventTypeName, XMLGenerator, Indent = 0):
    
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.startElement('eventtype', AttributesImpl(self.GetEventTypeAttributes(EventTypeName)))
    Indent += 2
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.startElement('properties', AttributesImpl({}))
    Indent += 2
    
    for PropertyName in self.GetEventTypeProperties(EventTypeName):
    
      XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
      XMLGenerator.startElement('property', AttributesImpl(self.GetPropertyAttributes(EventTypeName, PropertyName)))
      XMLGenerator.endElement('property')
  
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.endElement('properties')
    Indent -= 2
    
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.startElement('relations', AttributesImpl({}))
    Indent += 2

    for RelationId in self.GetEventTypePropertyRelations(EventTypeName):
      
      XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
      XMLGenerator.startElement('relation', AttributesImpl(self.GetPropertyRelationAttributes(EventTypeName, RelationId)))
      XMLGenerator.endElement('relation')
    
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.endElement('relations')
    Indent -= 2
    
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.endElement('eventtype')
    Indent -= 2

  # Generates an EDXML fragment which defines specified
  # object type. Can be useful for constructing new EDXML
  # files based on existing object type definitions.
  
  def GenerateObjectTypeXML(self, ObjectTypeName, XMLGenerator, Indent = 0):
    
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.startElement('objecttype', AttributesImpl(self.GetObjectTypeAttributes(ObjectTypeName)))
    XMLGenerator.endElement('objecttype')
    
  # Generates an EDXML fragment which defines specified
  # event source. Can be useful for constructing new EDXML
  # files based on existing event source definitions.
  
  def GenerateEventSourceXML(self, SourceUrl, XMLGenerator, Indent = 0):
    
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.startElement('source', AttributesImpl(self.GetSourceURLProperties(SourceUrl)))
    XMLGenerator.endElement('source')
      
  # Generates a full EDXML <definitions> section, containing
  # all known event types, event types and sources.
  
  def GenerateXMLDefinitions(self, XMLGenerator):
    
    Indent = 2
    
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.startElement('definitions', AttributesImpl({}))
    Indent += 2
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.startElement('eventtypes', AttributesImpl({}))
    Indent += 2
    
    for EventTypeName in self.GetEventTypeNames():
      self.GenerateEventTypeXML(EventTypeName, XMLGenerator, Indent)
    
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.endElement('eventtypes')
    Indent -= 2
    
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.startElement('objecttypes', AttributesImpl({}))
    Indent += 2
    
    for ObjectTypeName in self.GetObjectTypeNames():
      self.GenerateObjectTypeXML(ObjectTypeName, XMLGenerator, Indent)
    
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.endElement('objecttypes')
    Indent -= 2
    
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.startElement('sources', AttributesImpl({}))
    Indent += 2
    
    for SourceUrl in self.GetSourceURLs():
      self.GenerateEventSourceXML(SourceUrl, XMLGenerator, Indent)
    
    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.endElement('sources')
    Indent -= 2

    XMLGenerator.ignorableWhitespace('\n'.ljust(Indent))
    XMLGenerator.endElement('definitions')
    Indent -= 2

  # Always call this before constructing
  # a (partial) XSD schema.
  def OpenXSD(self):
    self.SchemaXSD = etree.Element('{%s}schema' % self.XSD['xs'], nsmap=self.XSD)
    self.CurrentElementXSD = self.SchemaXSD

  # Returns the generated XSD schema
  def CloseXSD(self):
    return etree.tostring(self.SchemaXSD, pretty_print = True, encoding='utf-8')
    
  # Internal convenience function
  def OpenElementXSD(self, ElementName):
    self.CurrentElementXSD = etree.SubElement(self.CurrentElementXSD, "{%s}%s" % (( self.XSD['xs'], ElementName )) )
    return self.CurrentElementXSD
  
  # Internal convenience function
  def CloseElementXSD(self):
    self.CurrentElementXSD = self.CurrentElementXSD.getparent()
    
  # Generates an XSD fragment related to the event type
  # definition of specified event type. Can be useful for
  # generating modular XSD schemas or constructing full
  # EDXML validation schemas.
  
  def GenerateEventTypeXSD(self, EventTypeName):
    
    self.OpenElementXSD('element').set('name', 'eventtype')
    self.OpenElementXSD('complexType')
    
    self.OpenElementXSD('sequence')
    self.OpenElementXSD('element').set('name', 'properties')
    self.OpenElementXSD('complexType')
    self.OpenElementXSD('sequence')
    for EventPropertyName in self.GetEventTypeProperties(EventTypeName):
      self.OpenElementXSD('element').set('name', 'property')
      self.OpenElementXSD('complexType')
      for Attribute, Value in self.GetPropertyAttributes(EventTypeName, EventPropertyName).items():
        self.OpenElementXSD('attribute').set('name', 'name')
        self.CurrentElementXSD.set('name', Attribute)
        self.CurrentElementXSD.set('type', 'xs:string')
        self.CurrentElementXSD.set('fixed', Value)
        self.CloseElementXSD()
      self.CloseElementXSD()
      self.CloseElementXSD()
    self.CloseElementXSD()
      
    self.CloseElementXSD()
    self.CloseElementXSD()

    self.OpenElementXSD('element').set('name', 'relations')
    self.OpenElementXSD('complexType')
    self.OpenElementXSD('sequence')

    for RelationId in self.GetEventTypePropertyRelations(EventTypeName):
      self.OpenElementXSD('element').set('name', 'relation')
      self.OpenElementXSD('complexType')
      for Attribute, Value in self.GetPropertyRelationAttributes(EventTypeName, RelationId).items():
        self.OpenElementXSD('attribute').set('name', 'name')
        self.CurrentElementXSD.set('name', Attribute)
        self.CurrentElementXSD.set('type', 'xs:string')
        self.CurrentElementXSD.set('fixed', Value)
        self.CloseElementXSD()
      self.CloseElementXSD()
      self.CloseElementXSD()
    
    self.CloseElementXSD()
    self.CloseElementXSD()
    self.CloseElementXSD()
    self.CloseElementXSD()
    
    for Attribute, Value in self.GetEventTypeAttributes(EventTypeName).items():
      self.OpenElementXSD('attribute').set('name', 'name')
      self.CurrentElementXSD.set('name', Attribute)
      self.CurrentElementXSD.set('type', 'xs:string')
      self.CurrentElementXSD.set('fixed', Value)
      self.CloseElementXSD()
    
    self.CloseElementXSD()
    self.CloseElementXSD()

  # Generates an XSD fragment related to the object type
  # definition of specified object type. Can be useful for
  # generating modular XSD schemas or constructing full
  # EDXML validation schemas.
  
  def GenerateObjectTypeXSD(self, ObjectTypeName):    
    
      self.OpenElementXSD('element').set('name', 'objecttype')
      self.OpenElementXSD('complexType')
      for Attribute, Value in self.GetObjectTypeAttributes(ObjectTypeName).items():
        self.OpenElementXSD('attribute').set('name', 'name')
        self.CurrentElementXSD.set('name', Attribute)
        self.CurrentElementXSD.set('type', 'xs:string')
        self.CurrentElementXSD.set('fixed', Value)
        self.CloseElementXSD()
      self.CloseElementXSD()
      self.CloseElementXSD()

  # Generates an full XSD schema for EDXML files that
  # contain all known definitions of event types, object
  # types and sources.
  
  def GenerateFullXSD(self):
    
    self.OpenElementXSD('element').set('name', 'events')
    self.OpenElementXSD('complexType')
    self.OpenElementXSD('sequence')
    self.OpenElementXSD('element').set('name', 'definitions')
    self.OpenElementXSD('complexType')
    self.OpenElementXSD('sequence')
    self.OpenElementXSD('element').set('name', 'eventtypes')
    self.OpenElementXSD('complexType')
    self.OpenElementXSD('sequence')

    for EventTypeName in self.GetEventTypeNames():
      self.GenerateEventTypeXSD(EventTypeName)
     
    self.CloseElementXSD()
    self.CloseElementXSD()
    self.CloseElementXSD()
    
    self.OpenElementXSD('element').set('name', 'objecttypes')
    self.OpenElementXSD('complexType')
    self.OpenElementXSD('sequence')

    for ObjectTypeName in self.GetObjectTypeNames():
      self.GenerateObjectTypeXSD(ObjectTypeName)
    
    self.CloseElementXSD()
    self.CloseElementXSD()
    self.CloseElementXSD()
    
    self.OpenElementXSD('element').set('name', 'sources')
    self.OpenElementXSD('complexType')
    self.OpenElementXSD('sequence')

    for SourceId in self.GetSourceIDs():
      self.OpenElementXSD('element').set('name', 'source')
      self.OpenElementXSD('complexType')
      for Attribute, Value in self.GetSourceIdProperties(SourceId).items():
        self.OpenElementXSD('attribute').set('name', 'name')
        self.CurrentElementXSD.set('name', Attribute)
        self.CurrentElementXSD.set('type', 'xs:string')
        self.CurrentElementXSD.set('fixed', Value)
        self.CloseElementXSD()
      self.CloseElementXSD()
      self.CloseElementXSD()
    
    self.CloseElementXSD()
    self.CloseElementXSD()
    self.CloseElementXSD()
    
    self.CloseElementXSD()
    self.CloseElementXSD()
    self.CloseElementXSD()

    self.OpenElementXSD('element').set('name', 'eventgroups')
    self.OpenElementXSD('complexType')
    self.OpenElementXSD('sequence').set('minOccurs', '0')
    self.CurrentElementXSD.set('maxOccurs', 'unbounded')

    self.OpenElementXSD('element').set('name', 'eventgroup')
    self.OpenElementXSD('complexType')
    
    self.OpenElementXSD('sequence').set('minOccurs', '0')
    self.CurrentElementXSD.set('maxOccurs', 'unbounded')
    self.OpenElementXSD('element').set('name', 'event')
    
    self.CloseElementXSD()
    self.CloseElementXSD()
    
    self.OpenElementXSD('attribute')
    self.CurrentElementXSD.set('name', 'source-id')
    self.CurrentElementXSD.set('type', 'xs:string')
    self.CloseElementXSD()
    self.OpenElementXSD('attribute')
    self.CurrentElementXSD.set('name', 'event-type')
    self.CurrentElementXSD.set('type', 'xs:string')
    self.CloseElementXSD()
    self.CloseElementXSD()
    self.CloseElementXSD()
    
    self.CloseElementXSD()
    self.CloseElementXSD()
    self.CloseElementXSD()
    
    self.CloseElementXSD()
    self.CloseElementXSD()
  
  # Always call this before constructing
  # a (partial) RelaxNG schema.
  def OpenRelaxNG(self):
    self.SchemaRelaxNG = None

  # Returns the generated schema.
  def CloseRelaxNG(self):
    Schema = etree.tostring(self.SchemaRelaxNG, pretty_print = True, encoding='utf-8')
    self.SchemaRelaxNG = None
    return Schema
    
  # Internal convenience function
  def OpenElementRelaxNG(self, ElementName):
    self.CurrentElementRelaxNG = etree.SubElement(self.CurrentElementRelaxNG, ElementName )
    return self.CurrentElementRelaxNG
  
  # Internal convenience function
  def CloseElementRelaxNG(self):
    self.CurrentElementRelaxNG = self.CurrentElementRelaxNG.getparent()
    
  # Generates a RelaxNG fragment related to the event type
  # definition of specified event type. Can be useful for
  # generating modular RelaxNG schemas or constructing full
  # EDXML validation schemas.
  
  def GenerateEventTypeRelaxNG(self, EventTypeName):

    if self.SchemaRelaxNG == None:
      # Apparently, we are generating an eventtyoe
      # definition that is not part of a bigger schema.
      self.CurrentElementRelaxNG = etree.Element('grammar')
      self.CurrentElementRelaxNG.set('xmlns', 'http://relaxng.org/ns/structure/1.0')
      self.SchemaRelaxNG = self.CurrentElementRelaxNG
    else:
      self.OpenElementRelaxNG('grammar')
    
    self.OpenElementRelaxNG('start')
    self.OpenElementRelaxNG('ref').set('name', 'eventtypedef')
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    
    self.OpenElementRelaxNG('define').set('name', 'eventtypedef')
    
    self.OpenElementRelaxNG('element').set('name', 'eventtype')
    for Attribute, Value in self.GetEventTypeAttributes(EventTypeName).items():
      self.OpenElementRelaxNG('attribute').set('name', Attribute)
      self.OpenElementRelaxNG('value').set('type', 'string')
      self.CurrentElementRelaxNG.text = Value
      self.CloseElementRelaxNG()
      self.CloseElementRelaxNG()
      
    self.OpenElementRelaxNG('element').set('name', 'properties')
    self.OpenElementRelaxNG('oneOrMore')
    self.OpenElementRelaxNG('choice')
    for EventPropertyName in self.GetEventTypeProperties(EventTypeName):
      self.OpenElementRelaxNG('element').set('name', 'property')
      for Attribute, Value in self.GetPropertyAttributes(EventTypeName, EventPropertyName).items():
        self.OpenElementRelaxNG('attribute').set('name', Attribute)
        self.OpenElementRelaxNG('value').set('type', 'string')
        self.CurrentElementRelaxNG.text = Value
        self.CloseElementRelaxNG()
        self.CloseElementRelaxNG()
      self.CloseElementRelaxNG()
      
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()

    Relations = self.GetEventTypePropertyRelations(EventTypeName)
    
    self.OpenElementRelaxNG('element').set('name', 'relations')
    
    if len(Relations) > 0:
    
      for RelationId in self.GetEventTypePropertyRelations(EventTypeName):
        self.OpenElementRelaxNG('element').set('name', 'relation')
        for Attribute, Value in self.GetPropertyRelationAttributes(EventTypeName, RelationId).items():
          self.OpenElementRelaxNG('attribute').set('name', Attribute)
          self.OpenElementRelaxNG('value').set('type', 'string')
          self.CurrentElementRelaxNG.text = Value
          self.CloseElementRelaxNG()
          self.CloseElementRelaxNG()
        self.CloseElementRelaxNG()
      
    else:
      
      self.OpenElementRelaxNG('empty')
      self.CloseElementRelaxNG()
      
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()

    return    


  # Generates a RelaxNG fragment related to the object type
  # definition of specified object type. Can be useful for
  # generating modular RelaxNG schemas or constructing full
  # EDXML validation schemas.
  
  def GenerateObjectTypeRelaxNG(self, ObjectTypeName):    
    
    if self.SchemaRelaxNG == None:
      # Apparently, we are generating an objecttype
      # definition that is not part of a bigger schema.
      self.CurrentElementRelaxNG = etree.Element('grammar')
      self.CurrentElementRelaxNG.set('xmlns', 'http://relaxng.org/ns/structure/1.0')
      self.SchemaRelaxNG = self.CurrentElementRelaxNG
    else:
      self.OpenElementRelaxNG('grammar')

    self.OpenElementRelaxNG('start')
    self.OpenElementRelaxNG('ref').set('name', 'objecttypedef')
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    
    self.OpenElementRelaxNG('define').set('name', 'objecttypedef')
      
    self.OpenElementRelaxNG('element').set('name', 'objecttype')
    for Attribute, Value in self.GetObjectTypeAttributes(ObjectTypeName).items():
      self.OpenElementRelaxNG('attribute').set('name', Attribute)
      self.OpenElementRelaxNG('value').set('type', 'string')
      self.CurrentElementRelaxNG.text = Value
      self.CloseElementRelaxNG()
      self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    return
  

  # Generates a RelaxNG fragment related to the object type
  # definition of specified object type. Can be useful for
  # generating modular RelaxNG schemas or constructing full
  # EDXML validation schemas.
  
  def GenerateEventRelaxNG(self, EventTypeName):
    
    if self.SchemaRelaxNG == None:
      # Apparently, we are generating an objecttype
      # definition that is not part of a bigger schema.
      self.CurrentElementRelaxNG = etree.Element('grammar')
      self.CurrentElementRelaxNG.set('xmlns', 'http://relaxng.org/ns/structure/1.0')
      self.SchemaRelaxNG = self.CurrentElementRelaxNG
    else:
      self.OpenElementRelaxNG('grammar')

    self.OpenElementRelaxNG('start')
    self.OpenElementRelaxNG('ref').set('name', 'eventdef-' + EventTypeName)
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    
    self.OpenElementRelaxNG('define').set('name', 'eventdef-' + EventTypeName)
    
    # Ideally, one would like to use an <interleave> pattern
    # here to define the mix of mandatory and optional objects.
    # However, since all objects have the same element name, 
    # this cannot be done. Interleave patterns don't allow it.
    # For now, we just check if all objects have a property
    # name that is allowed for the relevant event type.
    
    self.OpenElementRelaxNG('element').set('name', 'event')
    self.OpenElementRelaxNG('oneOrMore')
      
    self.OpenElementRelaxNG('element').set('name', 'object')
    self.OpenElementRelaxNG('attribute').set('name', 'property')
    self.OpenElementRelaxNG('choice')
      
    for PropertyName in self.GetEventTypeProperties(EventTypeName):
      self.OpenElementRelaxNG('value').set('type', 'string')
      self.CurrentElementRelaxNG.text = PropertyName
      self.CloseElementRelaxNG()
      
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.OpenElementRelaxNG('attribute').set('name', 'value')
    self.OpenElementRelaxNG('data').set('type', 'string')
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()

    self.CloseElementRelaxNG()
    
    self.OpenElementRelaxNG('optional')
    self.OpenElementRelaxNG('element').set('name', 'content')
    self.OpenElementRelaxNG('text')
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    
    self.CloseElementRelaxNG()
    
    self.CloseElementRelaxNG()
    return
    
  def GenerateGenericSourcesRelaxNG(self):
    
    self.OpenElementRelaxNG('element').set('name', 'source')
    self.OpenElementRelaxNG('attribute').set('name', 'source-id')
    self.OpenElementRelaxNG('data').set('type', 'token')
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.OpenElementRelaxNG('attribute').set('name', 'url')
    self.OpenElementRelaxNG('data').set('type', 'token')
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.OpenElementRelaxNG('attribute').set('name', 'description')
    self.OpenElementRelaxNG('data').set('type', 'normalizedString')
    self.OpenElementRelaxNG('param').set('name', 'maxLength')
    self.CurrentElementRelaxNG.text = '128'
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.OpenElementRelaxNG('attribute').set('name', 'date-acquired')
    self.OpenElementRelaxNG('data').set('type', 'normalizedString')
    self.OpenElementRelaxNG('param').set('name', 'maxLength')
    self.CurrentElementRelaxNG.text = '8'
    self.CloseElementRelaxNG()
    self.OpenElementRelaxNG('param').set('name', 'pattern')
    self.CurrentElementRelaxNG.text = '[0-9]{8}'
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()

  # Generates a full RelaxNG schema, containing all known definitions
  # of event types, object types and sources. You can optionally
  # provide dictionaries which map event type names or object type names
  # to URIs. In this case, the resulting schema will refer to these URIs
  # in stead of generating the schema patterns in place. This might be
  # useful if you have a central storage for event type definitions or
  # object type definitions.
  
  def GenerateFullRelaxNG(self, EventRefs = None, EventTypeRefs = None, ObjectTypeRefs = None):
    
    self.SchemaRelaxNG = etree.Element('element')
    self.SchemaRelaxNG.set('name', 'events')
    self.SchemaRelaxNG.set('xmlns', 'http://relaxng.org/ns/structure/1.0')
    self.SchemaRelaxNG.set('datatypeLibrary', 'http://www.w3.org/2001/XMLSchema-datatypes')
    self.CurrentElementRelaxNG = self.SchemaRelaxNG
    
    self.OpenElementRelaxNG('element').set('name', 'definitions')
    
    self.OpenElementRelaxNG('element').set('name', 'eventtypes')
    self.OpenElementRelaxNG('oneOrMore')
    self.OpenElementRelaxNG('choice')

    if EventTypeRefs == None:
      for EventTypeName in self.GetEventTypeNames():
        self.GenerateEventTypeRelaxNG(EventTypeName)
    else:
      for EventTypeName in self.GetEventTypeNames():
        self.OpenElementRelaxNG('externalRef').set('href', EventTypeRefs[EventTypeName])
        self.CloseElementRelaxNG()
      
    
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    
    self.OpenElementRelaxNG('element').set('name', 'objecttypes')
    self.OpenElementRelaxNG('oneOrMore')
    self.OpenElementRelaxNG('choice')
    
    if ObjectTypeRefs == None:
      for ObjectTypeName in self.GetObjectTypeNames():
        self.GenerateObjectTypeRelaxNG(ObjectTypeName)
    else:
      for ObjectTypeName in self.GetObjectTypeNames():
        self.OpenElementRelaxNG('externalRef').set('href', ObjectTypeRefs[ObjectTypeName])
        self.CloseElementRelaxNG()
      
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    
    self.OpenElementRelaxNG('element').set('name', 'sources')
    self.OpenElementRelaxNG('oneOrMore')
    
    self.GenerateGenericSourcesRelaxNG()
      
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    
    self.CloseElementRelaxNG()

    self.OpenElementRelaxNG('element').set('name', 'eventgroups')
    self.OpenElementRelaxNG('zeroOrMore')
    self.OpenElementRelaxNG('element').set('name', 'eventgroup')
    self.OpenElementRelaxNG('attribute').set('name', 'event-type')
    self.OpenElementRelaxNG('data').set('type', 'token')
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.OpenElementRelaxNG('attribute').set('name', 'source-id')
    self.OpenElementRelaxNG('data').set('type', 'token')
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    
    self.OpenElementRelaxNG('zeroOrMore')
    self.OpenElementRelaxNG('choice')
    
    if EventRefs == None:
      for EventTypeName in self.GetEventTypeNames():
        self.GenerateEventRelaxNG(EventTypeName)
    else:
      for EventTypeName in self.GetEventTypeNames():
        self.OpenElementRelaxNG('externalRef').set('href', EventRefs[EventTypeName])
        self.CloseElementRelaxNG()
    
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    
    
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()
    