# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                        EDXMLDefinitions Python class
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



"""EDXMLDefinitions

This module contains the EDXMLDefinitions class, which manages
information from EDXML <definitions> sections.

"""

import hashlib
import sre_constants
from xml.sax.xmlreader import AttributesImpl
import datetime
import dateutil.relativedelta
import pytz
from iso3166 import countries
from termcolor import colored
from lxml import etree
from EDXMLBase import *

try:
  # SimpleXMLWriter is not a very common module. If available,
  # it can be used for generating EDXML definitions in stead
  # of SAX XMLGenerator.
  from elementtree.SimpleXMLWriter import XMLWriter
except ImportError:
  pass

class EDXMLDefinitions(EDXMLBase):
  """Class for managing information from EDXML <definitions> sections.

  This class is used for managing definitions of event types, object
  types and sources from EDXML files. It is used for storing parsed
  definitions, querying definitions, and merging definitions from
  various EDXML files. It can be used to store <definitions> sections
  from multiple EDXML streams in succession, which results in the
  definitions from all streams being merged together. During the merge,
  the definitions are automatically checked for compatibility with
  previously stored definitions. The :class:`edxml.EDXMLBase.EDXMLError`
  exception is raised when problems are detected.

  The class also offers methods to generate EDXML <definitions> sections
  from the stored definitions, or generate (partial) XSD and RelaxNG
  schemas which can be used for validation of EDXML files.

  """

  def __init__(self):

    self.SourceIDs = {}
    self.SourceURLs = {}
    self.EventTypes = {}
    self.Properties = {}
    self.ObjectTypes = {}
    self.ObjectTypeEventTypes = {}
    self.EventTypeClasses = {}
    self.RelationPredicates = set()
    self.RequiredObjectTypes = set()
    self.EntityProperties = {}
    self.CompiledObjectTypePatterns = {}

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

    self.KnownFormatters = ['TIMESPAN', 'DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR', 'DURATION',
                            'LATITUDE', 'LONGITUDE', 'BYTECOUNT', 'CURRENCY', 'COUNTRYCODE', 'FILESERVER', 
                            'BOOLEAN_STRINGCHOICE', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT', 'EMPTY']

    self.ReporterPlaceholderPattern = re.compile('\\[\\[([^\\]]*)\\]\\]')

    # Some validation patterns

    self.SimpleNamePattern    = re.compile("^[a-z0-9-]*$")
    self.DisplayNamePattern   = re.compile("^[ a-zA-Z0-9]*/[ a-zA-Z0-9]*$")
    self.TrueFalsePattern     = re.compile("^(true)|(false)$")
    self.DecimalPattern       = re.compile("^[0-9.]+$")
    self.SourceDatePattern    = re.compile("^[0-9]{8}$")
    self.SourceUrlPattern     = re.compile("^(/[a-z0-9-]+)*/$")
    self.PropertyMapPattern   = re.compile("[a-z0-9-]{1,64}:[a-z0-9-]{1,64}(,[a-z0-9-]{1,64}:[a-z0-9-]{1,64})*")
    self.MergeOptions         = re.compile("^(drop)|(add)|(replace)|(min)|(max)|(increment)|(sum)|(multiply)|(match)$")
    self.RelationTypePattern  = re.compile("^(intra|inter|parent|child|other):.+")
    self.FuzzyMatchingPattern = re.compile("^(none)|(phonetic)|(substring:.*)|(\[[0-9]{1,2}:\])|(\[:[0-9]{1,2}\])$")
    self.DataTypePattern      = re.compile("^(boolean)|(timestamp)|(ip)|(hashlink)|(" + \
                                             "(number:(" + \
                                                 "((((tiny)|(small)|(medium)|(big))?int)|(float)|(double))(:signed)?" + \
                                               "))|(number:decimal:[0-9]+:[0-9]+(:signed)?)|(number:hex:[0-9]+(:[0-9]+:.)?)|(enum:.*)|(" + \
                                             "geo:(" + \
                                                 "(point)" + \
                                               "))|(string:(" + \
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
        'name':           {'mandatory': True,  'length': 40,   'pattern': self.SimpleNamePattern},
        'display-name':   {'mandatory': False, 'length': 64,   'pattern': self.DisplayNamePattern, 'default': '/'},
        'description':    {'mandatory': True,  'length': 128,  'pattern': None},
        'classlist':      {'mandatory': True,  'length': None, 'pattern': None},
        'reporter-short': {'mandatory': True,  'length': None, 'pattern': None},
        'reporter-long':  {'mandatory': True,  'length': None, 'pattern': None}
      },
      'parent': {
        'eventtype':            {'mandatory': True,  'length': 40,   'pattern': self.SimpleNamePattern},
        'propertymap':          {'mandatory': True,  'length': None, 'pattern': self.PropertyMapPattern},
        'parent-description':   {'mandatory': True,  'length': 128, 'pattern': None},
        'siblings-description': {'mandatory': True,  'length': 128, 'pattern': None}
      },
      'property': {
        'name':              {'mandatory': True,  'length': 64,   'pattern': self.SimpleNamePattern},
        'description':       {'mandatory': True,  'length': 128,  'pattern': None},
        'similar':           {'mandatory': False, 'length': 64,   'pattern': None, 'default': ''},
        'object-type':       {'mandatory': True,  'length': 40,   'pattern': self.SimpleNamePattern},
        'unique':            {'mandatory': False, 'length': None, 'pattern': self.TrueFalsePattern, 'default': 'false'},
        'merge':             {'mandatory': False, 'length': None, 'pattern': self.MergeOptions,     'default': 'drop'},
        'defines-entity':    {'mandatory': False, 'length': None, 'pattern': self.TrueFalsePattern, 'default': 'false'},
        'entity-confidence': {'mandatory': False, 'length': None, 'pattern': self.DecimalPattern,   'default': '0'}
      },
      'relation': {
        'property1':   {'mandatory': True,  'length': 64,   'pattern': self.SimpleNamePattern},
        'property2':   {'mandatory': True,  'length': 64,   'pattern': self.SimpleNamePattern},
        'directed':    {'mandatory': False, 'length': None, 'pattern': self.TrueFalsePattern, 'default': 'true'},
        'description': {'mandatory': True,  'length': 255,  'pattern': None},
        'type':        {'mandatory': True,  'length': 32,   'pattern': self.RelationTypePattern},
        'confidence':  {'mandatory': True,  'length': None, 'pattern': self.DecimalPattern}
      },
      'objecttype': {
        'name':              {'mandatory': True,  'length': 40,   'pattern': self.SimpleNamePattern},
        'display-name':      {'mandatory': False, 'length': 64,   'pattern': self.DisplayNamePattern, 'default': '/'},
        'description':       {'mandatory': True,  'length': 128,  'pattern': None},
        'fuzzy-matching':    {'mandatory': False, 'length': None, 'pattern': self.FuzzyMatchingPattern, 'default': 'none'},
        'compress':          {'mandatory': False, 'length': None, 'pattern': self.TrueFalsePattern, 'default': 'false'},
        'enp':               {'mandatory': False, 'length': None, 'pattern': None, 'default': '0'},
        'regexp':            {'mandatory': False, 'length': 128,  'pattern': None, 'default': '[\s\S]*'},
        'data-type':         {'mandatory': True,  'length': None, 'pattern': self.DataTypePattern}
      },
      'source': {
        'source-id':        {'mandatory': True,  'length': None,  'pattern': None},
        'url':              {'mandatory': True,  'length': None,  'pattern': self.SourceUrlPattern},
        'date-acquired':    {'mandatory': True,  'length': None,  'pattern': self.SourceDatePattern},
        'description':      {'mandatory': True,  'length': 128,   'pattern': None},
      },
    }

    EDXMLBase.__init__(self)

  def SourceIdDefined(self, SourceId):
    """Returns boolean indicating if given Source ID exists.

    Args:
      SourceId (str): EDXML Source Identifier

    Returns:
      bool. Source ID exists (True) or not (False)
    """
    return SourceId in self.SourceIDs.keys()

  def EventTypeDefined(self, EventTypeName):
    """Returns boolean indicating if given event type is defined.

    Args:
      EventTypeName (str): Name of event type

    Returns:
      bool. Event type exists (True) or not (False)

    """
    return EventTypeName in self.EventTypes

  def PropertyDefined(self, EventTypeName, PropertyName):
    """Returns boolean indicating if given property is defined.

    Args:
      EventTypeName (str): Event type name

      PropertyName (str):  Property Name

    Returns:
      bool. Property exists (True) or not (False)
    """
    return PropertyName in self.EventTypes[EventTypeName]['properties']

  def ObjectTypeDefined(self, ObjectTypeName):
    """Returns boolean indicating if given object type is defined.

    Args:
      ObjectTypeName (str): Object type name

    Returns:
      bool. Object type exists (True) or not (False)
    """
    return ObjectTypeName in self.ObjectTypes

  def RelationDefined(self, EventTypeName, Property1Name, Property2Name):
    """Returns boolean indicating if given property relation is defined.

    Args:
      EventTypeName (str): Event type name

      Property1Name (str): Name of event type property

      Property2Name (str): Name of event type property

    Returns:
      bool. Relation exists (True) or not (False)
    """
    RelationId = Property1Name + ' -> ' + Property2Name
    return RelationId in self.EventTypes[EventTypeName]['relations']

  def GetRelationPredicates(self):
    """Returns list of known relation predicates.

    Returns:
      list. List of predicates
    """
    return list(self.RelationPredicates)

  def EventTypeIsUnique(self, EventTypeName):
    """Returns a boolean indicating if given eventtype is unique or not.

    Args:
      EventTypeName (str): Name of event type

    Returns:
      bool. Event type is unique (True) or not (False)
    """
    return self.EventTypes[EventTypeName]['unique']

  def PropertyIsUnique(self, EventTypeName, PropertyName):
    """Returns a boolean indicating if given property is unique or not.

    Args:
      EventTypeName (str): Name of event type

      PropertyName (str): Name of event property

    Returns:
      bool. Property is unique (True) or not (False)
    """
    return PropertyName in self.EventTypes[EventTypeName]['unique-properties']

  def GetUniqueProperties(self, EventTypeName):
    """Returns a list of names of unique properties

    Args:
      EventTypeName (str): Name of an event type

    Returns:
      list. List of unique properties
    """
    return self.EventTypes[EventTypeName]['unique-properties']

  def GetMandatoryObjectProperties(self, EventTypeName):
    """Returns a list of names of properties which must have an object

    Args:
      EventTypeName (str): Name of an event type

    Returns:
      list. List of mandatory properties
    """
    return self.EventTypes[EventTypeName]['mandatory-properties']

  def GetSingletonObjectProperties(self, EventTypeName):
    """Returns a list of names of properties which cannot have multiple objects

    Args:
      EventTypeName (str): Name of an event type

    Returns:
      list. List of singleton properties
    """
    return self.EventTypes[EventTypeName]['singleton-properties']

  def PropertyDefinesEntity(self, EventTypeName, PropertyName):
    """Returns boolean indicating if property of given event type is an entity identifier.

    Args:
      EventTypeName (str): Name of event type

      PropertyName (str): Name of event property

    Returns:
      bool. Is entity identifier (True) or not (False)

    """
    return PropertyName in self.EntityProperties[EventTypeName]

  def PropertyInRelation(self, EventTypeName, PropertyName):
    """Returns a boolean indicating if given
    property of specified event type is involved
    in any defined property relation.

    Args:
      EventTypeName (str): Name of event type

      PropertyName (str): Name of event property

    Returns:
      bool. Is part of relation definition (True) or not (False)
    """
    return PropertyName in self.EventTypes[EventTypeName]['related-properties']

  def GetSourceURLs(self):
    """Returns an ordered list of all parsed
    source URLs. The order as they
    appeared in the EDXML stream is preserved.

    Returns:
      list. List of EDXML source URLs

    """
    return self.SourceURLs.keys()

  def GetSourceIDs(self):
    """Returns a list of all known source ID

    Returns:
      list. List of EDXML source IDs
    """
    return self.Sources

  def GetSourceId(self, Url):
    """Returns the ID of event source having specified URL

    Args:
      Url (str): EDXML source URL

    Returns:
      str. EDXML source ID
    """
    return self.SourceURLs[Url]['source-id']

  def GetEventTypeNames(self):
    """Returns a list of all known
    event type names. The order as they
    appeared in the EDXML stream is preserved.

    Returns:
      list. List of event type names
    """
    return self.EventTypeNames

  def GetEventTypeAttributes(self, EventTypeName):
    """Returns a dictionary containing all
    attributes of requested event type.

    Args:
      EventTypeName (str): Name of an event type

    Returns:
      dict. EDXML attributes
    """
    return self.EventTypes[EventTypeName]['attributes']

  def GetEventTypeParent(self, EventTypeName):
    """Returns a dictionary containing all
    attributes of the parent of requested eventtype.
    Returns empty dictionary when event type has no
    defined parent.

    Args:
      EventTypeName (str): Name of an event type

    Returns:
      dict. EDXML attributes of parent
    """
    if 'parent' in self.EventTypes[EventTypeName]:
      return self.EventTypes[EventTypeName]['parent']
    else:
      return {}

  def GetEventTypeParentMapping(self, EventTypeName):
    """Returns a dictionary containing all property
    names of the event type that map to a parent property.
    The value of each key corresponds to the name of the
    parent property that the child property maps to.
    Returns empty dictionary when event type has no
    defined parent.

    Args:
      EventTypeName (str): Name of an event type

    Returns:
      dict. Child / Parent Property mapping
    """
    if 'parent' in self.EventTypes[EventTypeName]:
      return self.EventTypes[EventTypeName]['parentmapping']
    else:
      return {}

  def GetEventTypesHavingObjectType(self, ObjectTypeName):
    """Returns a list of event type names having specified object type.

    Args:
      ObjectTypeName (str): Name of an object type

    Returns:
      list. List of event type names
    """
    if not ObjectTypeName in self.ObjectTypeEventTypes:
      return []
    else:
      return list(self.ObjectTypeEventTypes[ObjectTypeName])

  def GetEventTypeNamesInClass(self, ClassName):
    """Returns a list of event type names that belong to specified class.

    Args:
      ClassName (str): Name of an EDXML event type class

    Returns:
      list. List of event type names
    """
    return list(self.EventTypeClasses[ClassName])

  def GetEventTypeNamesInClasses(self, ClassNames):
    """Returns a list of event type names that belong to specified list of classes.

    Args:
      ClassNames (iterable): Iterable yielding names of EDXML event type classes

    Returns:
      list. List of event type names
    """
    EventTypeNames = set()
    for ClassName in ClassNames:
      for EventTypeName in self.EventTypeClasses[ClassName]:
        EventTypeNames.add(EventTypeName)
    return list(EventTypeNames)

  def GetObjectTypeAttributes(self, ObjectTypeName):
    """Returns a dictionary containing all attributes of specified object type.

    Args:
      ObjectTypeName (str): Name of an object type

    Returns:
      dict. Dictionary of EDXML object type attributes
    """
    return self.ObjectTypes[ObjectTypeName]

  def GetEventTypeProperties(self, EventTypeName):
    """Returns a list of all property names
    of given event type. The order as they
    appeared in the EDXML stream is preserved.

    Args:
      EventTypeName (str): Name of an event type

    Returns:
      list. List of event type property names
    """
    return self.PropertyNames[EventTypeName]

  def GetEventTypePropertyRelations(self, EventTypeName):
    """Returns a list of all IDs of property relations
    in given event type. The order as they
    appeared in the EDXML stream is preserved.

    Args:
      EventTypeName (str): Name of an event type

    Returns:
      list. List of property relation identifiers
    """
    return self.PropertyRelations[EventTypeName]

  def GetPropertyRelationAttributes(self, EventTypeName, RelationId):
    """Returns a dictionary containing all attributes of requested relation.

    The returned attributes are the attributes of the EDXML <relation> tag
    that corresponds to the specified relation identifier.

    Args:
      EventTypeName (str): Name of an event type

      RelationId (str): Identifier of a property relation

    Returns:
      dict. Dictionary containing EDXML attributes of relation tag
    """
    return self.EventTypes[EventTypeName]['relations'][RelationId]

  def GetObjectTypeNames(self):
    """Returns a list of all known object type names.
    The order as they appeared in the EDXML stream is preserved.

    Returns:
      list. List of object type names
    """
    return self.ObjectTypeNames

  def GetSourceURLProperties(self, Url):
    """Returns dictionary containing attributes of the source specified by given URL.

    The returned dictionary contains the attributes of the EDXML <source> tag

    Args:
      Url (str): EDXML source URL

    Returns:
      dict. Dictionary containing the attributes of the source tag.
    """
    return self.SourceURLs[Url]

  def GetSourceIdProperties(self, SourceId):
    """Returns dictionary containing attributes of the source specified by given Source ID.

    Args:
      SourceId (str): Source identifier

    Returns:
      dict. Dictionary containing the attributes of the source tag.
    """
    return self.SourceURLs[self.SourceIDs[SourceId]]

  def ObjectTypeRequiresUnicode(self, ObjectTypeName):
    """Returns True when given string object type requires
    unicode characters, return False otherwise.

    Args:
      ObjectTypeName (str): Name of an object type

    Returns:
      bool. Objects require unicode encoding (True) or not (False)
    """
    ObjectDataType = self.ObjectTypes[ObjectTypeName]['data-type'].split(':')
    if len(ObjectDataType) < 4 or 'u' not in ObjectDataType[3]:
      return False
    else:
      return True

  def GetPropertyObjectType(self, EventTypeName, PropertyName):
    """Return the name of the object type of specified event property.

    Args:
      EventTypeName (str): Name of event type

      PropertyName (str): Name of event property

    Returns:
      str. Object type name
    """
    if EventTypeName in self.EventTypes:
      if PropertyName in self.EventTypes[EventTypeName]['properties']:
        ObjectType = self.EventTypes[EventTypeName]['properties'][PropertyName]['object-type']
        return ObjectType
      else:
        self.Error('Event type %s has no property named "%s"' % (( str(EventTypeName), str(PropertyName) )) )
    else:
      self.Error('Unknown event type %s' % str(EventTypeName) )

  def GetPropertyAttributes(self, EventTypeName, PropertyName):
    """Return dictionary of attributes of specified event property.

    Args:
      EventTypeName (str): Name of event type

      PropertyName (str): Name of event property

    Returns:
      dict. Dictionary containing the EDXML attributes of the <property> tag
    """
    return self.EventTypes[EventTypeName]['properties'][PropertyName]

  def GetObjectTypeDataType(self, ObjectTypeName):
    """Return the data type of given object type.

    Args:
      ObjectTypeName (str): Name of an object type

    Returns:
      str. EDXML data type
    """
    return self.ObjectTypes[ObjectTypeName]['data-type']

  def AddEventType(self, EventTypeName, Attributes):
    """Add an event type to the collection of event type
    definitions. If an event type definition with the same
    name exists, it will be checked for consistency with
    the existing definition.

    Args:
      EventTypeName (str): Name of event type

      Attributes (dict): Dictionary holding the attributes of the <eventtype> tag

    """
    if EventTypeName in self.EventTypes:
      # Event type definition was encountered before.
      self.CheckEdxmlEntityConsistency('eventtype', EventTypeName, self.EventTypes[EventTypeName]['attributes'], Attributes)
    else:
      # New event type
      self.AddNewEventType(EventTypeName, Attributes)

  def SetEventTypeParent(self, EventTypeName, Attributes):
    """Configure a parent of specified event type.

    Args:
      EventTypeName (str): Name of event type

      Attributes (dict): Dictionary holding the attributes of the <parent> tag.

    """

    if 'parent' in self.EventTypes[EventTypeName]:
      # Parent definition was encountered before.
      self.CheckEdxmlEntityConsistency('parent', Attributes['eventtype'], self.EventTypes[EventTypeName]['parent'], Attributes)
    else:
      # New parent definition
      self.SetNewEventTypeParent(EventTypeName, Attributes)

  def AddProperty(self, EventTypeName, PropertyName, Attributes):
    """Add a property to the collection of property
    definitions. If a property definition with the same
    name exists, it will be checked for consistency with
    the existing definition.

    Args:
      EventTypeName (str): Name of an event type

      PropertyName (str): Name of a property

      Attributes (dict): Dictionary holding the attributes of the <property> tag.

    """
    if PropertyName in self.EventTypes[EventTypeName]['properties']:
      # Property definition was encountered before.
      self.CheckEdxmlEntityConsistency('property', PropertyName, self.EventTypes[EventTypeName]['properties'][PropertyName], Attributes)
    elif PropertyName in self.Properties:
      # Property definition was encountered before. Here,
      # we enforce that properties having the same name must have
      # the same definition, even if they are used in different
      # event types.
      # TODO: Remove this limitation in EDXML 3
      self.CheckEdxmlEntityConsistency('property', PropertyName, self.Properties[PropertyName], Attributes)
      self.AddNewProperty(EventTypeName, PropertyName, Attributes)
    else:
      # New property
      self.AddNewProperty(EventTypeName, PropertyName, Attributes)

  def AddRelation(self, EventTypeName, Property1Name, Property2Name, Attributes):
    """Add a relation to the collection of relation
    definitions. If a relation definition with the same
    properties exists, it will be checked for consistency with
    the existing definition.

    Args:
      EventTypeName (str): Name of the event type

      Property1Name (str): Name of property 1

      Property2Name (str): Name of property 2

      Attributes (dict): Dictionary holding the attributes of the <relation> tag.

    """
    RelationId = Property1Name + ' -> ' + Property2Name
    if RelationId in self.EventTypes[EventTypeName]['relations']:
      # Relation definition was encountered before.
      self.CheckEdxmlEntityConsistency('relation', RelationId, self.EventTypes[EventTypeName]['relations'][RelationId], Attributes)
    else:
      self.AddNewRelation(EventTypeName, RelationId, Property1Name, Property2Name, Attributes)

  def AddObjectType(self, ObjectTypeName, Attributes, WarnNotUsed = True):
    """Add an object type to the collection of object type
    definitions. If an object type definition with the same
    name exists, it will be checked for consistency with
    the existing definition.

    Args:
      ObjectTypeName (str): Name of event type

      Attributes (str): Dictionary holding the attributes of the <objecttype> tag.

      WarnNotUsed (str, optional): Generate a warning if no property uses the object type

    """
    if WarnNotUsed:
      if not ObjectTypeName in self.RequiredObjectTypes:
        self.Warning("Object type %s was defined, but it is not used." % ObjectTypeName )
    if ObjectTypeName in self.ObjectTypes:
      # Object type was defined before
      self.CheckEdxmlEntityConsistency('objecttype', ObjectTypeName, self.ObjectTypes[ObjectTypeName], Attributes)
    else:
      # New object type
      self.AddNewObjectType(ObjectTypeName, Attributes)

  def AddSource(self, SourceUrl, Attributes):
    """Add a source to the collection of event source
    definitions. If a source definition with the same
    URL exists, it will be checked for consistency with
    the existing definition.

    Args:
      SourceUrl (str): URL of event source

      Attributes (str): Dictionary holding the attributes of the <source> tag.

    """
    SourceId = Attributes['source-id']
    self.SourceIDs[SourceId] = SourceUrl
    if SourceUrl in self.SourceURLs.keys():
      self.CheckEdxmlEntityConsistency('source', SourceUrl, self.SourceURLs[SourceUrl], Attributes)
    else:
      self.Sources.append(SourceId)
      self.AddNewSource(SourceUrl, Attributes)

  # Internal use only.
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
      'mandatory-properties': set(),
      'singleton-properties': set(),
      'parentmapping': {},
      'relations': {},
      'related-properties': set(),
      'unique': False
      }

    for Class in Attributes['classlist'].split(','):
      if not Class in self.EventTypeClasses:
        self.EventTypeClasses[Class] = set()
      self.EventTypeClasses[Class].add(EventTypeName)

  # Internal use only.
  def SetNewEventTypeParent(self, EventTypeName, Attributes):
    self.EventTypes[EventTypeName]['parent'] = Attributes

    self.ValidateEdxmlEntityAttributes('parent', Attributes)

    try:

      for PropertyMapping in Attributes['propertymap'].split(','):
        ChildProperty, ParentProperty = PropertyMapping.split(':')
        self.EventTypes[EventTypeName]['parentmapping'][ChildProperty] = ParentProperty

    except (KeyError, ValueError):

      self.Error("Event type %s contains a parent definition which has an invalid or missing property map." % EventTypeName)

  # Internal use only.
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

    if 'merge' in Attributes:
      if Attributes['merge'] in ['match', 'min', 'max', 'increment', 'sum', 'multiply']:
        self.EventTypes[EventTypeName]['mandatory-properties'].add(PropertyName)
      if Attributes['merge'] in ['match', 'replace', 'min', 'max', 'increment', 'sum', 'multiply']:
        self.EventTypes[EventTypeName]['singleton-properties'].add(PropertyName)
      if PropertyName in self.EventTypes[EventTypeName]['parentmapping']:
        self.EventTypes[EventTypeName]['singleton-properties'].add(PropertyName)

    if 'defines-entity' in Attributes and Attributes['defines-entity'].lower() == 'true':
      self.EntityProperties[EventTypeName].add(PropertyName)

    self.EventTypes[EventTypeName]['properties'][PropertyName] = {'unique': 'false', 'defines-entity': 'false'}
    self.EventTypes[EventTypeName]['properties'][PropertyName].update(Attributes)

    self.Properties[PropertyName] = {'unique': 'false', 'defines-entity': 'false'}
    self.Properties[PropertyName].update(Attributes)

  # Internal use only.
  def AddNewObjectType(self, ObjectTypeName, Attributes):

    self.ValidateEdxmlEntityAttributes('objecttype', Attributes)
    self.ValidateDataType(ObjectTypeName, Attributes['data-type'])

    if 'regexp' in Attributes and Attributes['regexp'] != '[\s\S]*':
      try:
        # Note that XML schema regular expressions match the entire object
        # value. We wrap the expression in anchors to mimic this behavior
        self.CompiledObjectTypePatterns[ObjectTypeName] = re.compile('^%s$' % Attributes['regexp'])
      except sre_constants.error:
        self.Error('Definition of object type %s has an invalid regular expression in its regexp attribute: "%s"' % (( ObjectTypeName, Attributes['regexp'] )) )

    if 'fuzzy-matching' in Attributes and Attributes['fuzzy-matching'][:10] == 'substring:':
      try:
        re.compile('%s' % Attributes['fuzzy-matching'][10:])
      except sre_constants.error:
        self.Error('Definition of object type %s has an invalid regular expression in its fuzzy-matching attribute: "%s"' % (( ObjectTypeName, Attributes['fuzzy-matching'] )) )

    self.ObjectTypes[ObjectTypeName] = Attributes
    self.ObjectTypeNames.append(ObjectTypeName)

  # Internal use only.
  def AddNewRelation(self, EventTypeName, RelationId, Property1Name, Property2Name, Attributes):
    self.EventTypes[EventTypeName]['related-properties'].add(Property1Name)
    self.EventTypes[EventTypeName]['related-properties'].add(Property2Name)
    self.PropertyRelations[EventTypeName].append(RelationId)

    self.ValidateEdxmlEntityAttributes('relation', Attributes)

    SplitEventType = Attributes['type'].split(':')
    if len(SplitEventType) == 2:
      self.RelationPredicates.add(SplitEventType[1])

    self.EventTypes[EventTypeName]['relations'][RelationId] = Attributes

  # Internal use only.
  def AddNewSource(self, SourceUrl, Attributes):
    self.ValidateEdxmlEntityAttributes('source', Attributes)
    self.SourceURLs[SourceUrl] = Attributes

  def RemoveSource(self, SourceId):
    """Remove a source from the collection of event source
    definitions.

    Args:
      SourceId (str): EDXML source ID

    """
    SourceURL = self.SourceIDs[SourceId]
    del self.SourceIDs[SourceId]
    del self.SourceURLs[SourceURL]

  def CheckPropertyObjectTypes(self):
    """Checks if all object types that properties
    refer to are defined. Calls self.Error when
    a problem is detected."""
    for ObjectTypeName in self.RequiredObjectTypes:
      if not self.ObjectTypeDefined(ObjectTypeName):
        self.Error("Objecttype %s was used in a property definition, but it was not defined." % ObjectTypeName )

  def CheckEventTypePropertyConsistency(self, EventTypeName, PropertyNames):
    """Check if specified list of property names
    is correct for the specified event type.
    Calls self.Error when a problem is detected.

    Args:
      EventTypeName (str): Name of an event type

      PropertyName (str): Name of an event property
    """
    for PropertyName in PropertyNames:
      if not self.PropertyDefined(EventTypeName, PropertyName):
        self.Error("Property %s was previously defined as part of eventtype %s, but this definition does not define it." % (( PropertyName, EventTypeName )) )

  def CheckEventTypeRelations(self, EventTypeName):
    """Check if the relation definitions for
    specified eventtype are correct.
    Calls self.Error when a problem is detected."""

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

  def CheckEventTypeParents(self, EventTypeName):
    """Checks if parent definition of given event type
    is valid, if there is any parent definition.

    Args:
      EventTypeName (str): Name of an event type

    """

    if not 'parent' in self.EventTypes[EventTypeName]: return

    ParentAttribs = self.EventTypes[EventTypeName]['parent']

    if not ParentAttribs['eventtype'] in self.EventTypes:
      self.Error("Event type %s contains a parent definition which refers to event type %s which is not defined." % (( EventTypeName, ParentAttribs['eventtype'] )))

    for UniqueParentProperty in self.EventTypes[ParentAttribs['eventtype']]['unique-properties']:
      if not UniqueParentProperty in self.EventTypes[EventTypeName]['parentmapping'].values():
        self.Error("Event type %s contains a parent definition which lacks a mapping for unique parent property '%s'." % (( EventTypeName, UniqueParentProperty )) )

    for ChildProperty, ParentProperty in self.EventTypes[EventTypeName]['parentmapping'].items():
      ChildMergeStrategy = self.EventTypes[EventTypeName]['properties'][ChildProperty]['merge']

      if not ChildProperty in self.EventTypes[EventTypeName]['properties']:
        self.Error("Event type %s contains a parent definition which refers to unknown child property '%s'." % (( EventTypeName, ChildProperty )) )

      if ChildMergeStrategy != 'match' and ChildMergeStrategy != 'drop':
        self.Error("Event type %s contains a parent definition which refers to child property '%s'. This property has merge strategy %s, which is not allowed for properties that are used in parent definitions." % (( EventTypeName, ChildProperty, ChildMergeStrategy )) )

      if not ParentProperty in self.EventTypes[ParentAttribs['eventtype']]['unique-properties']:
        self.Error("Event type %s contains a parent definition which refers to parent property '%s' of event type %s, but this property is not unique, or it does not exist.\n%s" % ( EventTypeName, ParentProperty, ParentAttribs['eventtype'], repr(self.EventTypes[ParentAttribs['eventtype']]) ) )


  def EvaluateReporterString(self, EventTypeName, EventProperties, Short = False, Capitalize = True, Colorize = False):
    """

    Evaluates the short or long reporter string of an event type using
    specified property values, returning the result. The EventProperties
    argument is an associative array containing property names as keys
    and lists of object value strings as values.

    By default, the long reporter string is evaluated, unless Short is
    set to True.

    By default, we will try to capitalize the first letter of the resulting
    string, unless Capitalize is set to False.

    Optionally, the output can be colorized. At his time this means that,
    when printed on the terminal, the objects in the evaluated string will
    be displayed using bold white characters.

    Args:
      EventTypeName (str): Name of the event type
      EventProperties (dict): Property values
      Short (bool): use short or long reporter string
      Capitalize (bool): Capitalize output or not
      Colorize (bool): Colorize output or not

    Returns:
      str:
    """

    # Recursively split a placeholder string at '{' and '}'
    def SplitPlaceholderString(String, Offset = 0):

      Elements = []
      Length = len(String)

      while Offset < Length:
        Pos1 = String.find('{', Offset)
        Pos2 = String.find('}', Offset)
        if Pos1 == -1:
          # There are no more sub-strings, Find closing bracket.
          if Pos2 == -1:
            # No closing bracket either, which means that the
            # remaining part of the string is one element.
            # lacks brackets.
            Substring = String[Offset:Length]
            Offset = Length
            Elements.append(Substring)
          else:
            # Found closing bracket. Add substring and return
            # to caller.
            Substring = String[Offset:Pos2]
            Offset = Pos2 + 1
            Elements.append(Substring)
            break
        else:
          # We found an opening bracket.

          if Pos2 == -1:
            # No closing bracket
            # Give up.
            Offset = Length
          else:
            # We also found a closing bracket.

            if Pos1 < Pos2:
              # Opening bracket comes first, which means we should
              # iterate.
              Substring = String[Offset:Pos1]
              Offset = Pos1 + 1

              Elements.append(Substring)
              Offset, Parsed = SplitPlaceholderString(String, Offset)
              Elements.append(Parsed)
            else:
              # closing bracket comes first, which means we found
              # an innermost substring. Add substring and return
              # to caller.
              Substring = String[Offset:Pos2]
              Offset = Pos2 + 1
              Elements.append(Substring)
              break

      return Offset, Elements

    def FormatTimeDuration(Min, Max):
      DateTimeA = datetime.datetime.fromtimestamp(Min)
      DateTimeB = datetime.datetime.fromtimestamp(Max)
      Delta = dateutil.relativedelta.relativedelta (DateTimeB, DateTimeA)

      if Delta.minutes > 0:
        if Delta.hours > 0:
          if Delta.days > 0:
            if Delta.months > 0:
              if Delta.years > 0:
                return "%d years, %d months, %d days, %d hours, %d minutes and %d seconds" % (Delta.years, Delta.months, Delta.days, Delta.hours, Delta.minutes, Delta.seconds)
              else:
                return "%d months, %d days, %d hours, %d minutes and %d seconds" % (Delta.months, Delta.days, Delta.hours, Delta.minutes, Delta.seconds)
            else:
              return "%d days, %d hours, %d minutes and %d seconds" % (Delta.days, Delta.hours, Delta.minutes, Delta.seconds)
          else:
            return "%d hours, %d minutes and %d seconds" % (Delta.hours, Delta.minutes, Delta.seconds)
        else:
          return "%d minutes and %d seconds" % (Delta.minutes, Delta.seconds)
      else:
        return "%d.%d seconds" % (Delta.seconds, Delta.microseconds)

    def FormatByteCount(ByteCount):
      Suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
      if ByteCount == 0: return '0 B'
      i = 0
      while ByteCount >= 1024 and i < len(Suffixes) - 1:
        ByteCount /= 1024.
        i += 1
      f = ('%.2f' % ByteCount).rstrip('0').rstrip('.')
      return '%s %s' % (f, Suffixes[i])

    def ProcessSimplePlaceholderString(String, EventObjectValues, Capitalize):

      Replacements = {}

      if Capitalize and String != '':
        if String[0] == '{':
          if String[1:2] != '[[':
            # Sting does not start with a placeholder,
            # so we can safely capitalize.
            String = String[0] + String[1].upper() + String[2:]
        else:
          if String[0:1] != '[[':
            # Sting does not start with a placeholder,
            # so we can safely capitalize.
            String = String[0].upper() + String[1:]

      # Match on placeholders like "[[FULLDATETIME:timestamp]]", creating
      # groups of the strings in between the placeholders and the
      # placeholders themselves, with and without brackets included.
      Placeholders = re.findall(r'(\[\[([^]]*)\]\])', String)

      for Placeholder in Placeholders:

        ObjectStrings = []
        Exploded = Placeholder[1].split(':')

        if len(Exploded) >= 2:
          Formatter = Exploded.pop(0)
          PropertyList = Exploded.pop(0)
        else:
          Formatter = ''
          PropertyList = Exploded[0]

        if len(PropertyList) > 0:
          Properties = PropertyList.split(',')

          for PropertyName in Properties:
            if not PropertyName in EventObjectValues or len(EventObjectValues[PropertyName]) == 0:
              if Formatter == 'EMPTY':
                # Use the first formatter argument
                # in stead of the object value itself.
                ObjectStrings.append(Exploded[0])
              else:
                # One of the place holders has no associated
                # value, so we return an empty string.
                return ''

          Properties = [PropertyName for PropertyName in Properties if PropertyName in EventObjectValues]

          if Formatter == 'TIMESPAN':

            Timestamps = []
            for PropertyName in Properties:
              for ObjectValue in EventObjectValues[PropertyName]:
                Timestamps.append(float(ObjectValue))

            if len(Timestamps) > 0:
              DateTimeA = datetime.datetime.fromtimestamp(min(Timestamps))
              DateTimeB = datetime.datetime.fromtimestamp(max(Timestamps))
              ObjectStrings.append("between %s and %s" % (DateTimeA.isoformat(' '), DateTimeB.isoformat(' ')))

          elif Formatter == 'DURATION':

            Timestamps = []
            for PropertyName in Properties:
              for ObjectValue in EventObjectValues[PropertyName]:
                Timestamps.append(float(ObjectValue))

            if len(Timestamps) > 0:
              ObjectStrings.append(FormatTimeDuration(min(Timestamps), max(Timestamps)))

          elif Formatter in ['YEAR', 'MONTH', 'WEEK', 'DATE', 'DATETIME', 'FULLDATETIME']:

            for PropertyName in Properties:
              for ObjectValue in EventObjectValues[PropertyName]:
                Timestamp = float(ObjectValue)
                TimeZone = pytz.timezone("UTC")

                try:
                  if Formatter == 'FULLDATETIME':
                    ObjectStrings.append(datetime.datetime.fromtimestamp(Timestamp, TimeZone).strftime('%A, %B %d %Y at %H:%M:%Sh UTC'))
                  elif Formatter == 'DATETIME':
                    ObjectStrings.append(datetime.datetime.fromtimestamp(Timestamp, TimeZone).strftime('B %d %Y at %H:%M:%Sh UTC'))
                  elif Formatter == 'DATE':
                    ObjectStrings.append(datetime.datetime.fromtimestamp(Timestamp, TimeZone).strftime('%a, %B %d %Y'))
                  elif Formatter == 'YEAR':
                    ObjectStrings.append(datetime.datetime.fromtimestamp(Timestamp, TimeZone).strftime('%Y'))
                  elif Formatter == 'MONTH':
                    ObjectStrings.append(datetime.datetime.fromtimestamp(Timestamp, TimeZone).strftime('%B %Y'))
                  elif Formatter == 'WEEK':
                    ObjectStrings.append(datetime.datetime.fromtimestamp(Timestamp, TimeZone).strftime('week %W of %Y'))
                except ValueError:
                  # This may happen for some time stamps before year 1900, which
                  # is not supported by strftime.
                  ObjectStrings.append('some date, a long, long time ago')

          elif Formatter == 'BYTECOUNT':

            for PropertyName in Properties:
              for ObjectValue in EventObjectValues[PropertyName]:
                ObjectStrings.append(FormatByteCount(int(ObjectValue)))

          elif Formatter == 'LATITUDE':
            Degrees = int(ObjectValue)
            Minutes = int((ObjectValue - Degrees) * 60.0)
            Seconds = int((ObjectValue - Degrees - (Minutes / 60.0)) * 3600.0)

            ObjectStrings.append('%d°%d′%d %s″' % (Degrees, Minutes, Seconds, 'N' if Degrees > 0 else 'S'))

          elif Formatter == 'LONGITUDE':
            Degrees = int(ObjectValue)
            Minutes = int((ObjectValue - Degrees) * 60.0)
            Seconds = int((ObjectValue - Degrees - (Minutes / 60.0)) * 3600.0)

            ObjectStrings.append('%d°%d′%d %s″' % (Degrees, Minutes, Seconds, 'E' if Degrees > 0 else 'W'))

          elif Formatter == 'CURRENCY':

            for PropertyName in Properties:
              for ObjectValue in EventObjectValues[PropertyName]:
                ObjectStrings.append('%.2f%s' % (int(ObjectValue), Exploded[0]))

          elif Formatter == 'COUNTRYCODE':

            for PropertyName in Properties:
              for ObjectValue in EventObjectValues[PropertyName]:
                Country = countries.get(ObjectValue)
                if Country:
                  # We found the name of the country, print it.
                  ObjectStrings.append(Country.name)
                else:
                  ObjectStrings.append(ObjectValue + ' (unknown country code)')

          elif Formatter == 'BOOLEAN_STRINGCHOICE':
            for PropertyName in Properties:
              for ObjectValue in EventObjectValues[PropertyName]:
                if ObjectValue == 'true':
                  # Print first string
                  ObjectStrings.append(Exploded[0])
                else:
                  # Print second string
                  ObjectStrings.append(Exploded[1])

          elif Formatter == 'BOOLEAN_ON_OFF':
            for PropertyName in Properties:
              for ObjectValue in EventObjectValues[PropertyName]:
                if ObjectValue == 'true':
                  # Print 'on'
                  ObjectStrings.append('on')
                else:
                  # Print 'off'
                  ObjectStrings.append('off')

          elif Formatter == 'BOOLEAN_IS_ISNOT':
            for PropertyName in Properties:
              for ObjectValue in EventObjectValues[PropertyName]:
                if ObjectValue == 'true':
                  # Print 'is'
                  ObjectStrings.append('is')
                else:
                  # Print 'is not'
                  ObjectStrings.append('is not')

          elif Formatter == 'EMPTY':
            pass

          else:
            for PropertyName in Properties:
              for ObjectValue in EventObjectValues[PropertyName]:
                ObjectStrings.append(ObjectValue)

        if len(ObjectStrings) > 0:
          if len(ObjectStrings) > 1:
            # If one property has multiple objects,
            # list them all.
            LastObjectValue = ObjectStrings.pop()
            if Colorize:
              ObjectString = ', '.join(colored(ObjectString, 'white', attrs=['bold']) for ObjectString in ObjectStrings) + ' and ' + LastObjectValue
            else:
              ObjectString = ', '.join(ObjectStrings) + ' and ' + LastObjectValue
          else:
            if Colorize:
              ObjectString = colored(ObjectStrings[0], 'white', attrs=['bold'])
            else:
              ObjectString = ObjectStrings[0]
        else:
          ObjectString = ''

        Replacements[Placeholder[0]] = ObjectString

      # Return ReporterString where all placeholders are replaced
      # by the actual (formatted) object values

      for Placeholder, Replacement in Replacements.items():
        String = String.replace(Placeholder, Replacement)

      return String

    def ProcessSplitPlaceholderString(Elements, Event, Capitalize, IterationLevel = 0):
      Result = ''
      ContainsSubStrings = False
      NonEmptySubstringCounter = 0

      for Element in Elements:
        if type(Element) == list:
          Processed = ProcessSplitPlaceholderString(Element, Event, Capitalize, IterationLevel + 1)
          ContainsSubStrings = True
          Capitalize = False
          if len(Processed) > 0: NonEmptySubstringCounter += 1
        else:
          if Element != '':
            Processed = ProcessSimplePlaceholderString(Element, Event, Capitalize)
            if Processed == '':
              # A non-empty component of the string evaluated into
              # an empty string, which means that it must have contained
              # a placeholder that resulted in an empty string, which
              # implies that we should return an empty string as well.
              return ''
            Capitalize = False
          else:
            Processed = ''
        Result += Processed

      if ContainsSubStrings:
        # Return empty string when all substrings are empty,
        # unless IterationLevel is zero. This has the effect that
        # the 'root' level processing never results in an empty string.
        if NonEmptySubstringCounter == 0 and IterationLevel > 0:
          return ''
        else:
          return Result
      else:
        return Result

    if Short:
      ReporterString = self.GetEventTypeAttributes(EventTypeName)['reporter-short']
    else:
      ReporterString = self.GetEventTypeAttributes(EventTypeName)['reporter-long']

    return ProcessSplitPlaceholderString(SplitPlaceholderString(ReporterString)[1], EventProperties, Capitalize)

  def CheckReporterString(self, EventTypeName, String, PropertyNames, CheckCompleteness = False):
    """Checks if given event type reporter string makes sense. Optionally,
    it can also check if all given properties are present in the string.

    Args:
      EventTypeName (str): Name of an event type

      String (str): The reporter string

      PropertyNames (list): List of property names belonging to the event type

      CheckCompleteness (bool, optional): Check if all properties are present in string

    """

    # Test if reporter string grammar is correct, by
    # checking that curly brackets are balanced.
    CurlyNestings = {'{': 1, '}': -1}
    Nesting = 0
    for Curly in [Char for Char in String if Char in ['{', '}']]:
      Nesting += CurlyNestings[Curly]
      if Nesting < 0:
        self.Error('The following reporter string contains unbalanced curly brackets:\n%s\n' % String)
        Nesting = 0
        break
    if Nesting != 0:
      self.Error('The following reporter string contains unbalanced curly brackets:\n%s\n' % String)

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
        if StringComponents[0] in ['DURATION', 'TIMESPAN']:
          DurationProperties = StringComponents[1].split(',')
          if len(DurationProperties) != 2:
            self.Error("Event type %s contains a reporter string containing a string formatter (%s) which requires two properties, but %d properties were specified." % (( EventTypeName, StringComponents[0], len(DurationProperties) )) )
          if DurationProperties[0] in PropertyNames and DurationProperties[1] in PropertyNames:
            ReferredProperties.append(DurationProperties[0])
            ReferredProperties.append(DurationProperties[1])

            # Check that both properties are timestamps
            if DurationProperties[0] == '':
              self.Error('Invalid property name in %s formatter: "%s"' % (DurationProperties[0], StringComponents[0]))
            if DurationProperties[1] == '':
              self.Error('Invalid property name in %s formatter: "%s"' % (DurationProperties[1], StringComponents[0]))

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
            if StringComponents[1] == '':
              self.Error('Invalid property name in %s formatter: "%s"' % (StringComponents[1], StringComponents[0]))
            if self.GetObjectTypeDataType(self.GetPropertyObjectType(EventTypeName, StringComponents[1])) != 'timestamp':
              self.Error("Event type %s contains a reporter string which uses the %s formatter. The used property (%s) is not a timestamp, though." % (( EventTypeName, StringComponents[0], StringComponents[1] )) )

          elif StringComponents[0] in ['LATITUDE', 'LONGITUDE', 'BYTECOUNT', 'COUNTRYCODE', 'FILESERVER', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT']:
            # Check that no additional options are present
            if len(StringComponents) > 2:
              self.Error("Event type %s contains a reporter string which uses the %s formatter. This formatter accepts no options, but they were specified: %s" % (( EventTypeName, StringComponents[0], String )) )
            # Check that only one property is specified after the formatter
            if len(StringComponents[1].split(',')) > 1:
              self.Error("Event type %s contains a reporter string which uses the %s formatter. This formatter accepts just one property. Multiple properties were given though: %s" % (( EventTypeName, StringComponents[0], StringComponents[1] )) )
            if StringComponents[0] in ['BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT']:
              # Check that property is a boolean
              if StringComponents[1] == '':
                self.Error('Invalid property name in %s formatter: "%s"' % (StringComponents[1], StringComponents[0]))
              if self.GetObjectTypeDataType(self.GetPropertyObjectType(EventTypeName, StringComponents[1])) != 'boolean':
                self.Error("Event type %s contains a reporter string which uses the %s formatter. The used property (%s) is not a boolean, though." % (( EventTypeName, StringComponents[0], StringComponents[1] )) )

          elif StringComponents[0] == 'CURRENCY':
            if len(StringComponents) != 3:
              self.Error("Event type %s contains a reporter string which uses a malformed %s formatter: %s" % (( EventTypeName, StringComponents[0], String )) )

          elif StringComponents[0] == 'EMPTY':
            if len(StringComponents) != 3:
              self.Error("Event type %s contains a reporter string which uses a malformed %s formatter: %s" % (( EventTypeName, StringComponents[0], String )) )

          elif StringComponents[0] == 'BOOLEAN_STRINGCHOICE':
            if len(StringComponents) != 4:
              self.Error("Event type %s contains a reporter string which uses a malformed %s formatter: %s" % (( EventTypeName, StringComponents[0], String )) )
            # Check that property is a boolean
            if StringComponents[1] == '':
              self.Error('Invalid property name in %s formatter: "%s"' % (StringComponents[1], StringComponents[0]))
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
  #
  # Internal use only.
  def CheckEdxmlEntityConsistency(self, Entity, EntityDescription, CurrentAttributes, UpdatedAttributes):

    Current = set(CurrentAttributes.keys())
    Update  = set(UpdatedAttributes.keys())

    AttribsAdded    = Update - Current
    AttribsRetained = Update & Current
    AttribsRemoved  = Current - Update

    # First we check if the attributes that are retained in the
    # update are consistent with the exiting attribute values.

    for Attribute in AttribsRetained:
      if CurrentAttributes[Attribute] != UpdatedAttributes[Attribute]:
        self.Error("Attribute %s of %s '%s' does not match previous definition:\nNew:      %s\nExisting: %s\n" % (( Attribute, Entity, EntityDescription, UpdatedAttributes[Attribute], CurrentAttributes[Attribute] )))

    # At the moment, we do not accept new attributes to appear or 
    # existing attributes to disappear, unless they are optional
    # and have a default value. These optional attributes with
    # or without defaults cause some exceptions to the above rule.
    # We will get rid of most of these exceptions as soon as EDXML
    # version 3 hits the road.

    for Attrib in AttribsAdded:
      if self.EDXMLEntityAttributes[Entity][Attrib]['mandatory']:
        self.Error("Definition of %s '%s' contains mandatory attribute that was not previously defined: %s" % (( Entity, EntityDescription, Attrib)) )
      else:
        if 'default' in self.EDXMLEntityAttributes[Entity][Attrib]:
          if UpdatedAttributes[Attrib] != self.EDXMLEntityAttributes[Entity][Attrib]['default']:
            self.Error("Definition of %s '%s' contains attribute with non-default value (%s) that was not previously defined: %s" % (( Entity, EntityDescription, UpdatedAttributes[Attrib], Attrib)) )
        else:
          self.Error("Definition of %s '%s' contains attribute that was not previously defined and has no default value: %s" % (( Entity, EntityDescription, Attrib)) )

    for Attrib in AttribsRemoved:
      if self.EDXMLEntityAttributes[Entity][Attrib]['mandatory']:
        self.Error("Definition of %s '%s' lacks mandatory attribute: %s" % (( Entity, EntityDescription, Attrib)) )
      else:
        if 'default' in self.EDXMLEntityAttributes[Entity][Attrib]:
          if CurrentAttributes[Attrib] != self.EDXMLEntityAttributes[Entity][Attrib]['default']:
            self.Error("Previous definition of %s '%s' contains optional attribute %s with non-default value (%s) while new definition does not define it." % (( Entity, EntityDescription, Attrib, CurrentAttributes[Attrib] )) )
        else:
          self.Error("Definition of %s '%s' lacks optional attribute that was previously defined and has no default value: %s" % (( Entity, EntityDescription, Attrib)) )

  # Checks the attributes of a specific EDXML entity (eventtype, 
  # objecttype, relation, ...) against the constaints as specified in
  # self.EDXMLEntityAttributes.
  #
  # Automatically sets default values for missing attributes.
  # 
  # Internal use only.
  def ValidateEdxmlEntityAttributes(self, EntityName, Attributes):

    for Attribute in self.EDXMLEntityAttributes[EntityName]:

      if not Attribute in Attributes:
        if self.EDXMLEntityAttributes[EntityName][Attribute]['mandatory']:
          self.Error("Definition of %s lacks mandatory attribute '%s'." % (( EntityName, Attribute )) )
        else:
          Attributes[Attribute] = self.EDXMLEntityAttributes[EntityName][Attribute]['default']

      if self.EDXMLEntityAttributes[EntityName][Attribute]['length']:
        if len(Attributes[Attribute]) > self.EDXMLEntityAttributes[EntityName][Attribute]['length']:
          self.Error("Value of %s attribute %s is too long: %s " % (( EntityName, Attribute, Attributes[Attribute] )))
      if self.EDXMLEntityAttributes[EntityName][Attribute]['pattern']:
        if not re.match(self.EDXMLEntityAttributes[EntityName][Attribute]['pattern'], Attributes[Attribute]):
          self.Error("Value of %s attribute %s is invalid: %s " % (( EntityName, Attribute, Attributes[Attribute] )))

    UnknownAttributes = list(set(Attributes.keys()) - set(self.EDXMLEntityAttributes[EntityName].keys()))

    if len(UnknownAttributes) > 0:
      self.Error("Definition of %s contains unknown attributes: %s" % (( EntityName, ','.join(UnknownAttributes) )) )

  def UniqueSourceIDs(self):
    """Source IDs are required to be unique only
    within a single EDXML file. When multiple 
    EDXML files are parsed using the same EDXMLParser
    instance, it may happen that different sources have
    the same ID. This method changes the Source IDs
    of all known sources to be unique.

    It returns a mapping that maps old Source ID into
    new Source ID.

    Returns:
      dict. Source identifier mapping
    """

    Counter = 1
    Mapping = {}
    for SourceUrl in self.SourceURLs:
      Mapping[SourceUrl] = str(Counter)
      self.SourceURLs[SourceUrl]['source-id'] = str(Counter)
      self.SourceIDs[str(Counter)] = SourceUrl
      Counter += 1
    return Mapping

  def MergeEvents(self, EventTypeName, EventObjectsA, EventObjectsB):
    """Merges the objects of an event 'B' with the objects
    of another event 'A'. The arguments EventObjectsA
    and EventObjectsB should be dictionaries where the keys are
    property names and the values lists of object values.

    The objects in EventObjectsA are updated using the
    objects from EventObjectsB. It returns True when EventObjectsA
    was modified, False otherwise.

    Note that this method does NOT merge parent hashes, only the property objects.

    Args:
      EventTypeName (str): Name of event type of the events

      EventObjectsA (dict): Objects of event A

      EventObjectsB (dict): Objects of event B

    """

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

        if MergeStrategy in ['min', 'max', 'increment', 'sum', 'multiply']:
          SplitDataType = self.GetObjectTypeDataType(self.GetPropertyObjectType(EventTypeName, PropertyName)).split(':')
          if SplitDataType[0] in ['number', 'timestamp']:

            if MergeStrategy in ['min', 'max']:
              Values = set()

              if SplitDataType[0] == 'timestamp':
                for Value in Source[PropertyName]: Values.add(Decimal(Value))
                for Value in Target[PropertyName]: Values.add(Decimal(Value))
              else:
                if SplitDataType[1] in ['float', 'double']:
                  for Value in Source[PropertyName]: Values.add(float(Value))
                  for Value in Target[PropertyName]: Values.add(float(Value))
                elif SplitDataType[1] == 'decimal':
                  for Value in Source[PropertyName]: Values.add(Decimal(Value))
                  for Value in Target[PropertyName]: Values.add(Decimal(Value))
                elif SplitDataType[1] != 'hex':
                  for Value in Source[PropertyName]: Values.add(int(Value))
                  for Value in Target[PropertyName]: Values.add(int(Value))

              if MergeStrategy == 'min':
                Target[PropertyName] = set([str(min(Values))])
              else:
                Target[PropertyName] = set([str(max(Values))])

            elif MergeStrategy == 'increment':
              if SplitDataType[0] == 'timestamp':
                Target[PropertyName] = set(['%.6f' % (Decimal(list(Target[PropertyName])[0]) + Decimal(1))])
              else:
                if SplitDataType[1] in ['float', 'double']:
                  Target[PropertyName] = set([str(float(list(Target[PropertyName])[0]) + 1)])
                elif SplitDataType[1] == 'decimal':
                  Target[PropertyName] = set([str(Decimal(list(Target[PropertyName])[0]) + Decimal(1))])
                elif SplitDataType[1] != 'hex':
                  Target[PropertyName] = set([str(int(list(Target[PropertyName])[0]) + 1)])

            elif MergeStrategy == 'sum':
              if SplitDataType[0] == 'timestamp':
                Target[PropertyName] = set(['%.6f' % (Decimal(list(Source[PropertyName])[0]) + Decimal(list(Target[PropertyName])[0]))])
              else:
                if SplitDataType[1] in ['float', 'double']:
                  Target[PropertyName] = set([str(float(list(Source[PropertyName])[0]) + float(list(Target[PropertyName])[0]))])
                elif SplitDataType[1] == 'decimal':
                  Target[PropertyName] = set([str(Decimal(list(Source[PropertyName])[0]) + Decimal(list(Target[PropertyName])[0]))])
                elif SplitDataType[1] != 'hex':
                  Target[PropertyName] = set([str(int(list(Source[PropertyName])[0]) + int(list(Target[PropertyName])[0]))])

            elif MergeStrategy == 'multiply':
              if SplitDataType[0] == 'timestamp':
                Target[PropertyName] = set(['%.6f' % (Decimal(list(Source[PropertyName])[0]) * Decimal(list(Target[PropertyName])[0]))])
              else:
                if SplitDataType[1] in ['float', 'double']:
                  Target[PropertyName] = set([str(float(list(Source[PropertyName])[0]) * float(list(Target[PropertyName])[0]))])
                elif SplitDataType[1] == 'decimal':
                  Target[PropertyName] = set([str((Decimal(list(Source[PropertyName])[0]) * Decimal(list(Target[PropertyName])[0])).quantize(Decimal(list(Source[PropertyName])[0])))])
                elif SplitDataType[1] != 'hex':
                  Target[PropertyName] = set([str(int(list(Source[PropertyName])[0]) * int(list(Target[PropertyName])[0]))])

        elif MergeStrategy == 'add':
          Target[PropertyName] = Source[PropertyName] | Target[PropertyName]

        elif MergeStrategy == 'replace':
          Target[PropertyName] = Source[PropertyName]

    # Remove any objects due to replace strategy
    for PropertyName in [Property for Property in self.GetEventTypeProperties(EventTypeName) if (Property not in Source or len(Source[Property]) == 0) and Property in Target and len(Target[Property]) > 0]:
      if self.EventTypes[EventTypeName]['properties'][PropertyName]['merge'] == 'replace':
        Target[PropertyName] = set()

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
      for PropertyName in Target:
        EventObjectsA[PropertyName] = Target[PropertyName]
      return True
    else:
      return False

  def ComputeStickyHash(self, EventTypeName, EventObjects, EventContent):
    """Computes a sticky hash from given event. The EventObjects argument
    should be a list containing dictionaries representing the objects. The
    dictionaries should contain the property name stored under the 'property'
    key and the value stored under the 'value' key.

    Args:
      EventTypeName (str): The name of the event type

      EventObjects (list): List of event objects

      EventContent (str): The content of the event

    Note:
      The supplied object values must be normalized using
      :func:`edxml.EDXMLBase.EDXMLBase.NormalizeObject`.

    Returns:
      str. A hexadecimal string representation of the hash.

    """

    ObjectStrings = set()

    for EventObject in EventObjects:
      Property = unicode(EventObject['property'])
      Value    = EventObject['value']
      if self.EventTypeIsUnique(EventTypeName) and self.PropertyIsUnique(EventTypeName, Property) == False:
        # We use only unique properties for
        # hash computation. Skip this one.
        continue
      ObjectType = self.GetPropertyObjectType(EventTypeName, Property)
      DataType = self.GetObjectTypeDataType(ObjectType).split(':')

      if DataType[0] == 'number' and DataType[1] in ['float', 'double']:
        # Floating point objects are ignored.
        continue

      # Normalize the object value to a unicode string
      try:
        NormalizedValue = self.NormalizeObject(Value, DataType)
      except EDXMLError as Except:
        self.Error("Invalid value in property %s of event type %s: '%s': %s" % (( Property, EventTypeName, Value, Except )))

      ObjectStrings.add(Property + u':' + NormalizedValue)

    # Now we compute the SHA1 hash value of the unicode
    # string representation of the event, and output in hex

    if self.EventTypeIsUnique(EventTypeName):
      return hashlib.sha1((EventTypeName + '\n' + '\n'.join(sorted(ObjectStrings))).encode('utf-8')).hexdigest()
    else:
      return hashlib.sha1((EventTypeName + '\n' + '\n'.join(sorted(ObjectStrings)) + '\n' + EventContent).encode('utf-8')).hexdigest()

  def ComputeStickyHashV3(self, EventTypeName, SourceUrl, EventObjects, EventContent):
    """Computes a sticky hash from given event, using the hashing algorithm
    from EDXML specification version 3.x. The EventObjects argument
    should be a list containing dictionaries representing the objects. The
    dictionaries should contain the property name stored under the 'property'
    key and the value stored under the 'value' key.

    Args:
      EventTypeName (str): The name of the event type

      EventObjects (list): List of event objects

      EventContent (str): The content of the event

    Note:
      The supplied object values must be normalized using
      :func:`edxml.EDXMLBase.EDXMLBase.NormalizeObject`.

    Returns:
      str. A hexadecimal string representation of the hash.

    """

    ObjectStrings = set()

    for EventObject in EventObjects:
      Property = unicode(EventObject['property'])
      Value    = EventObject['value']
      if self.EventTypeIsUnique(EventTypeName) and self.PropertyIsUnique(EventTypeName, Property) == False:
        # We use only unique properties for
        # hash computation. Skip this one.
        continue
      ObjectType = self.GetPropertyObjectType(EventTypeName, Property)
      DataType = self.GetObjectTypeDataType(ObjectType).split(':')

      if DataType[0] == 'number' and DataType[1] in ['float', 'double']:
        # Floating point objects are ignored.
        continue

      # Normalize the object value to a unicode string
      try:
        NormalizedValue = self.NormalizeObject(Value, DataType)
      except EDXMLError as Except:
        self.Error("Invalid value in property %s of event type %s: '%s': %s" % (( Property, EventTypeName, Value, Except )))

      ObjectStrings.add(Property + u':' + NormalizedValue)

    # Now we compute the SHA1 hash value of the unicode
    # string representation of the event, and output in hex

    if self.EventTypeIsUnique(EventTypeName):
      return hashlib.sha1((SourceUrl + '\n' + EventTypeName + '\n' + '\n'.join(sorted(ObjectStrings))).encode('utf-8')).hexdigest()
    else:
      return hashlib.sha1((SourceUrl + '\n' + EventTypeName + '\n' + '\n'.join(sorted(ObjectStrings)) + '\n' + EventContent).encode('utf-8')).hexdigest()

  def GenerateEventTypeXML(self, EventTypeName, XMLGenerator):
    """Generates an EDXML fragment which defines specified
    eventtype. Can be useful for constructing new EDXML
    files based on existing event type definitions.

    The XMLGenerator argument may be either a SAX XMLGenerator
    instance or a ElementTree SimpleXMLWriter instance.

    Args:
      EventTypeName (str): Name of the event type

      XMLGenerator (XMLGenerator,XMLWriter): XMLGenerator / XMLWriter instance

    """

    if not 'start' in dir(XMLGenerator):

      # Using SAX XML Generator:

      XMLGenerator.startElement('eventtype', AttributesImpl(self.GetEventTypeAttributes(EventTypeName)))
      XMLGenerator.startElement('properties', AttributesImpl({}))

      for PropertyName in self.GetEventTypeProperties(EventTypeName):

        XMLGenerator.startElement('property', AttributesImpl(self.GetPropertyAttributes(EventTypeName, PropertyName)))
        XMLGenerator.endElement('property')

      XMLGenerator.endElement('properties')

      XMLGenerator.startElement('relations', AttributesImpl({}))

      for RelationId in self.GetEventTypePropertyRelations(EventTypeName):

        XMLGenerator.startElement('relation', AttributesImpl(self.GetPropertyRelationAttributes(EventTypeName, RelationId)))
        XMLGenerator.endElement('relation')

      XMLGenerator.endElement('relations')

      XMLGenerator.endElement('eventtype')

    else:

      # Using ElementTree SimpleXMLWriter:

      XMLGenerator.start('eventtype', self.GetEventTypeAttributes(EventTypeName))
      XMLGenerator.start('properties')

      for PropertyName in self.GetEventTypeProperties(EventTypeName):
        XMLGenerator.element('property', '', self.GetPropertyAttributes(EventTypeName, PropertyName))

      XMLGenerator.end('properties')

      XMLGenerator.start('relations')

      for RelationId in self.GetEventTypePropertyRelations(EventTypeName):
        XMLGenerator.element('relation', '', self.GetPropertyRelationAttributes(EventTypeName, RelationId))

      XMLGenerator.end('relations')
      XMLGenerator.end('eventtype')

  def GenerateEventPropertyXML(self, EventTypeName, PropertyName, XMLGenerator):
    """Generates an EDXML fragment which defines specified
    eventtype property. Can be useful for constructing new EDXML
    files based on existing event type definitions.

    The XMLGenerator argument may be either a SAX XMLGenerator
    instance or a ElementTree SimpleXMLWriter instance.

    Args:
      EventTypeName (str): Name of the event type
      PropertyName (str): Name of the property

      XMLGenerator (XMLGenerator,XMLWriter): XMLGenerator / XMLWriter instance

    """

    if not 'start' in dir(XMLGenerator):

      # Using SAX XML Generator:

      XMLGenerator.startElement('property', AttributesImpl(self.GetPropertyAttributes(EventTypeName, PropertyName)))
      XMLGenerator.endElement('property')

    else:

      # Using ElementTree SimpleXMLWriter:

      for PropertyName in self.GetEventTypeProperties(EventTypeName):
        XMLGenerator.element('property', '', self.GetPropertyAttributes(EventTypeName, PropertyName))

  def GeneratePropertyRelationsXML(self, EventTypeName, XMLGenerator):
    """Generates an EDXML fragment which defines all property
    relation of specified eventtype. Can be useful for constructing new EDXML
    files based on existing event type definitions.

    The XMLGenerator argument may be either a SAX XMLGenerator
    instance or a ElementTree SimpleXMLWriter instance.

    Args:
      EventTypeName (str): Name of the event type

      XMLGenerator (XMLGenerator,XMLWriter): XMLGenerator / XMLWriter instance

    """

    if not 'start' in dir(XMLGenerator):

      # Using SAX XML Generator:

      XMLGenerator.startElement('relations', AttributesImpl({}))

      for RelationId in self.GetEventTypePropertyRelations(EventTypeName):

        XMLGenerator.startElement('relation', AttributesImpl(self.GetPropertyRelationAttributes(EventTypeName, RelationId)))
        XMLGenerator.endElement('relation')

      XMLGenerator.endElement('relations')

    else:

      # Using ElementTree SimpleXMLWriter:

      XMLGenerator.start('relations')

      for RelationId in self.GetEventTypePropertyRelations(EventTypeName):
        XMLGenerator.element('relation', '', self.GetPropertyRelationAttributes(EventTypeName, RelationId))

      XMLGenerator.end('relations')

  def GeneratePropertyRelationXML(self, EventTypeName, RelationId, XMLGenerator):
    """Generates an EDXML fragment which defines specified property
    relation of specified eventtype. Can be useful for constructing new EDXML
    files based on existing event type definitions.

    The XMLGenerator argument may be either a SAX XMLGenerator
    instance or a ElementTree SimpleXMLWriter instance.

    Args:
      EventTypeName (str): Name of the event type
      RelationId (str): Identifier of a property relation

      XMLGenerator (XMLGenerator,XMLWriter): XMLGenerator / XMLWriter instance

    """

    if not 'start' in dir(XMLGenerator):

      # Using SAX XML Generator:

      XMLGenerator.startElement('relation', AttributesImpl(self.GetPropertyRelationAttributes(EventTypeName, RelationId)))
      XMLGenerator.endElement('relation')

    else:

      # Using ElementTree SimpleXMLWriter:

      XMLGenerator.element('relation', '', self.GetPropertyRelationAttributes(EventTypeName, RelationId))

  def GenerateObjectTypeXML(self, ObjectTypeName, XMLGenerator):
    """Generates an EDXML fragment which defines specified
    object type. Can be useful for constructing new EDXML
    files based on existing object type definitions.

    The XMLGenerator argument may be either a SAX XMLGenerator
    instance or a ElementTree SimpleXMLWriter instance.

    Args:
      EventTypeName (str): Name of the event type

      XMLGenerator (XMLGenerator,XMLWriter): XMLGenerator / XMLWriter instance

    """

    if not 'start' in dir(XMLGenerator):

      # Using SAX XML Generator:

      XMLGenerator.startElement('objecttype', AttributesImpl(self.GetObjectTypeAttributes(ObjectTypeName)))
      XMLGenerator.endElement('objecttype')

    else:

      # Using ElementTree SimpleXMLWriter:

      XMLGenerator.element('objecttype', '', self.GetObjectTypeAttributes(ObjectTypeName))

  def GenerateEventSourceXML(self, SourceUrl, XMLGenerator):
    """Generates an EDXML fragment which defines specified
    event source. Can be useful for constructing new EDXML
    files based on existing event source definitions.

    The XMLGenerator argument may be either a SAX XMLGenerator
    instance or a ElementTree SimpleXMLWriter instance.

    Args:
      SourceUrl (str): EDXML source URL

      XMLGenerator (XMLGenerator,XMLWriter): XMLGenerator / XMLWriter instance

    """

    if not 'start' in dir(XMLGenerator):

      # Using SAX XML Generator:

      XMLGenerator.startElement('source', AttributesImpl(self.GetSourceURLProperties(SourceUrl)))
      XMLGenerator.endElement('source')

    else:

      # Using ElementTree SimpleXMLWriter:

      XMLGenerator.element('source', '', self.GetSourceURLProperties(SourceUrl))

  def GenerateXMLDefinitions(self, XMLGenerator, IncludeSources = True):
    """Generates a full EDXML <definitions> section, containing
    all known event types, event types and optionally sources.

    The XMLGenerator argument may be either a SAX XMLGenerator
    instance or a ElementTree SimpleXMLWriter instance.

    Args:
      XMLGenerator (XMLGenerator,XMLWriter):  XMLGenerator / XMLWriter instance

      IncludeSources (bool, optional): Boolean, include source definitions yes or no

    """

    if not 'start' in dir(XMLGenerator):

      # Using SAX XML Generator:

      XMLGenerator.startElement('definitions', AttributesImpl({}))
      XMLGenerator.startElement('eventtypes', AttributesImpl({}))

      for EventTypeName in self.GetEventTypeNames():
        self.GenerateEventTypeXML(EventTypeName, XMLGenerator)

      XMLGenerator.endElement('eventtypes')

      XMLGenerator.startElement('objecttypes', AttributesImpl({}))

      for ObjectTypeName in self.GetObjectTypeNames():
        self.GenerateObjectTypeXML(ObjectTypeName, XMLGenerator)

      XMLGenerator.endElement('objecttypes')

      XMLGenerator.startElement('sources', AttributesImpl({}))

      if IncludeSources:
        for SourceUrl in self.GetSourceURLs():
          self.GenerateEventSourceXML(SourceUrl, XMLGenerator)

      XMLGenerator.endElement('sources')
      XMLGenerator.endElement('definitions')

    else:

      # Using ElementTree SimpleXMLWriter:

      XMLGenerator.start('definitions')
      XMLGenerator.start('eventtypes')

      for EventTypeName in self.GetEventTypeNames():
        self.GenerateEventTypeXML(EventTypeName, XMLGenerator)

      XMLGenerator.end('eventtypes')
      XMLGenerator.start('objecttypes')

      for ObjectTypeName in self.GetObjectTypeNames():
        self.GenerateObjectTypeXML(ObjectTypeName, XMLGenerator)

      XMLGenerator.end('objecttypes')
      XMLGenerator.start('sources')

      if IncludeSources:
        for SourceUrl in self.GetSourceURLs():
          self.GenerateEventSourceXML(SourceUrl, XMLGenerator)

      XMLGenerator.end('sources')
      XMLGenerator.end('definitions')

  def OpenXSD(self):
    """Start generating an XSD schema from stored
    definitions. Always call this before constructing
    a (partial) XSD schema."""
    self.SchemaXSD = etree.Element('{%s}schema' % self.XSD['xs'], nsmap=self.XSD)
    self.CurrentElementXSD = self.SchemaXSD

  def CloseXSD(self):
    """Finalize generated XSD and return it as a string."""
    return etree.tostring(self.SchemaXSD, pretty_print = True, encoding='utf-8')

  # Internal convenience method
  def OpenElementXSD(self, ElementName):
    self.CurrentElementXSD = etree.SubElement(self.CurrentElementXSD, "{%s}%s" % (( self.XSD['xs'], ElementName )) )
    return self.CurrentElementXSD

  # Internal convenience method
  def CloseElementXSD(self):
    self.CurrentElementXSD = self.CurrentElementXSD.getparent()

  def GenerateEventTypeXSD(self, EventTypeName):
    """Generates an XSD fragment related to the event type
    definition of specified event type. Can be useful for
    generating modular XSD schemas or constructing full
    EDXML validation schemas.

    Make sure to call :func:`OpenXSD` first.

    Args:
      EventTypeName (str): Name of an event type

    """

    self.OpenElementXSD('element').set('name', 'eventtype')
    self.OpenElementXSD('complexType')
    self.OpenElementXSD('sequence')

    if self.GetEventTypeParent(EventTypeName) != {}:
      self.OpenElementXSD('element').set('name', 'parent')
      self.OpenElementXSD('complexType')
      for Attribute, Value in self.GetEventTypeParent(EventTypeName).items():
        self.OpenElementXSD('attribute').set('name', 'name')
        self.CurrentElementXSD.set('name', Attribute)
        self.CurrentElementXSD.set('type', 'xs:string')
        self.CurrentElementXSD.set('fixed', Value)
        if self.EDXMLEntityAttributes['parent'][Attribute]['mandatory'] or Value != self.EDXMLEntityAttributes['parent'][Attribute]['default']:
          self.CurrentElementXSD.set('use', 'required')
        self.CloseElementXSD()
      self.CloseElementXSD()
      self.CloseElementXSD()

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
        if self.EDXMLEntityAttributes['property'][Attribute]['mandatory'] or Value != self.EDXMLEntityAttributes['property'][Attribute]['default']:
          self.CurrentElementXSD.set('use', 'required')
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
        if self.EDXMLEntityAttributes['relation'][Attribute]['mandatory'] or Value != self.EDXMLEntityAttributes['relation'][Attribute]['default']:
          self.CurrentElementXSD.set('use', 'required')
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
      if self.EDXMLEntityAttributes['eventtype'][Attribute]['mandatory'] or Value != self.EDXMLEntityAttributes['eventtype'][Attribute]['default']:
        self.CurrentElementXSD.set('use', 'required')
      self.CloseElementXSD()

    self.CloseElementXSD()
    self.CloseElementXSD()

  def GenerateObjectTypeXSD(self, ObjectTypeName):
    """Generates an XSD fragment related to the object type
    definition of specified object type. Can be useful for
    generating modular XSD schemas or constructing full
    EDXML validation schemas.

    Make sure to call :func:`OpenXSD` first.

    Args:
      ObjectTypeName (str): Name of an object type
    """

    self.OpenElementXSD('element').set('name', 'objecttype')
    self.OpenElementXSD('complexType')
    for Attribute, Value in self.GetObjectTypeAttributes(ObjectTypeName).items():
      self.OpenElementXSD('attribute').set('name', 'name')
      self.CurrentElementXSD.set('name', Attribute)
      self.CurrentElementXSD.set('type', 'xs:string')
      self.CurrentElementXSD.set('fixed', Value)
      if self.EDXMLEntityAttributes['objecttype'][Attribute]['mandatory'] or Value != self.EDXMLEntityAttributes['objecttype'][Attribute]['default']:
        self.CurrentElementXSD.set('use', 'required')
      self.CloseElementXSD()
    self.CloseElementXSD()
    self.CloseElementXSD()

  def GenerateFullXSD(self):
    """Generates an full XSD schema for EDXML files that
    contain all known definitions of event types, object
    types and sources.

    Make sure to call :func:`OpenXSD` first.

    """

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
        self.CurrentElementXSD.set('use', 'required')
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
    self.CurrentElementXSD.set('use', 'required')
    self.CloseElementXSD()
    self.OpenElementXSD('attribute')
    self.CurrentElementXSD.set('name', 'event-type')
    self.CurrentElementXSD.set('type', 'xs:string')
    self.CurrentElementXSD.set('use', 'required')
    self.CloseElementXSD()
    self.CloseElementXSD()
    self.CloseElementXSD()

    self.CloseElementXSD()
    self.CloseElementXSD()
    self.CloseElementXSD()

    self.CloseElementXSD()
    self.CloseElementXSD()

  def OpenRelaxNG(self):
    """Start generating a RelaxNG schema from stored
    definitions. Always call this before constructing
    a (partial) RelaxNG schema."""
    self.SchemaRelaxNG = None

  def CloseRelaxNG(self):
    """Finalize RelaxNG schema and return it as a string.

    Returns:
      str. The RelaxNG schema
    """
    Schema = etree.tostring(self.SchemaRelaxNG, pretty_print = True, encoding='utf-8')
    self.SchemaRelaxNG = None
    return Schema

  # Internal convenience method
  def OpenElementRelaxNG(self, ElementName):
    self.CurrentElementRelaxNG = etree.SubElement(self.CurrentElementRelaxNG, ElementName )
    return self.CurrentElementRelaxNG

  # Internal convenience method
  def CloseElementRelaxNG(self):
    self.CurrentElementRelaxNG = self.CurrentElementRelaxNG.getparent()

  def GenerateEventTypeRelaxNG(self, EventTypeName):
    """Generates a RelaxNG fragment related to the event type
    definition of specified event type. Can be useful for
    generating modular RelaxNG schemas or constructing full
    EDXML validation schemas.

    Args:
      EventTypeName (str): Name of an event type

    Make sure to call :func:`OpenRelaxNG` first.

    """

    if self.SchemaRelaxNG is None:
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
      OptionalAttribute = False
      if self.EDXMLEntityAttributes['eventtype'][Attribute]['mandatory'] == False and Value == self.EDXMLEntityAttributes['eventtype'][Attribute]['default']:
        OptionalAttribute = True
        self.OpenElementRelaxNG('optional')
      self.OpenElementRelaxNG('attribute').set('name', Attribute)
      self.OpenElementRelaxNG('value').set('type', 'string')
      self.CurrentElementRelaxNG.text = Value
      self.CloseElementRelaxNG()
      self.CloseElementRelaxNG()
      if OptionalAttribute:
        self.CloseElementRelaxNG()

    if self.GetEventTypeParent(EventTypeName) != {}:
      self.OpenElementRelaxNG('element').set('name', 'parent')
      for Attribute, Value in self.GetEventTypeParent(EventTypeName).items():
        OptionalAttribute = False
        if self.EDXMLEntityAttributes['parent'][Attribute]['mandatory'] == False and Value == self.EDXMLEntityAttributes['parent'][Attribute]['default']:
          OptionalAttribute = True
          self.OpenElementRelaxNG('optional')

        self.OpenElementRelaxNG('attribute').set('name', Attribute)
        self.OpenElementRelaxNG('value').set('type', 'string')
        self.CurrentElementRelaxNG.text = Value
        self.CloseElementRelaxNG()
        self.CloseElementRelaxNG()
        if OptionalAttribute:
          self.CloseElementRelaxNG()
      self.CloseElementRelaxNG()

    self.OpenElementRelaxNG('element').set('name', 'properties')
    self.OpenElementRelaxNG('oneOrMore')
    self.OpenElementRelaxNG('choice')
    for EventPropertyName in self.GetEventTypeProperties(EventTypeName):
      self.OpenElementRelaxNG('element').set('name', 'property')
      for Attribute, Value in self.GetPropertyAttributes(EventTypeName, EventPropertyName).items():
        OptionalAttribute = False
        if self.EDXMLEntityAttributes['property'][Attribute]['mandatory'] == False and Value == self.EDXMLEntityAttributes['property'][Attribute]['default']:
          OptionalAttribute = True
          self.OpenElementRelaxNG('optional')
        self.OpenElementRelaxNG('attribute').set('name', Attribute)
        self.OpenElementRelaxNG('value').set('type', 'string')
        self.CurrentElementRelaxNG.text = Value
        self.CloseElementRelaxNG()
        self.CloseElementRelaxNG()
        if OptionalAttribute:
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
          OptionalAttribute = False
          if self.EDXMLEntityAttributes['relation'][Attribute]['mandatory'] == False and Value == self.EDXMLEntityAttributes['relation'][Attribute]['default']:
            OptionalAttribute = True
            self.OpenElementRelaxNG('optional')
          self.OpenElementRelaxNG('attribute').set('name', Attribute)
          self.OpenElementRelaxNG('value').set('type', 'string')
          self.CurrentElementRelaxNG.text = Value
          self.CloseElementRelaxNG()
          self.CloseElementRelaxNG()
          if OptionalAttribute:
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


  def GenerateObjectTypeRelaxNG(self, ObjectTypeName):
    """Generates a RelaxNG fragment related to the object type
    definition of specified object type. Can be useful for
    generating modular RelaxNG schemas or constructing full
    EDXML validation schemas.

    Make sure to call :func:`OpenRelaxNG` first.

    Args:
      ObjectTypeName (str): Name of an object type
    """

    if self.SchemaRelaxNG is None:
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
      OptionalAttribute = False
      if self.EDXMLEntityAttributes['objecttype'][Attribute]['mandatory'] == False and Value == self.EDXMLEntityAttributes['objecttype'][Attribute]['default']:
        OptionalAttribute = True
        self.OpenElementRelaxNG('optional')
      self.OpenElementRelaxNG('attribute').set('name', Attribute)
      self.OpenElementRelaxNG('value').set('type', 'string')
      self.CurrentElementRelaxNG.text = Value
      self.CloseElementRelaxNG()
      self.CloseElementRelaxNG()
      if OptionalAttribute:
        self.CloseElementRelaxNG()

    self.CloseElementRelaxNG()
    self.CloseElementRelaxNG()

    if self.SchemaRelaxNG is not None:
      self.CloseElementRelaxNG()

  def GenerateEventRelaxNG(self, EventTypeName):
    """Generates a RelaxNG fragment related to the object type
    definition of specified object type. Can be useful for
    generating modular RelaxNG schemas or constructing full
    EDXML validation schemas.

    Make sure to call :func:`OpenRelaxNG` first.

    Args:
      EventTypeName (str): Name of an event type
    """

    if self.SchemaRelaxNG is None:
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
    """Generates a RelaxNG fragment representing an event source. Can be useful for
    generating modular RelaxNG schemas or constructing full
    EDXML validation schemas.

    Make sure to call :func:`OpenRelaxNG` first.

    """

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

  def GenerateFullRelaxNG(self, EventRefs = None, EventTypeRefs = None, ObjectTypeRefs = None):
    """Generates a full RelaxNG schema, containing all known definitions
    of event types, object types and sources. You can optionally
    provide dictionaries which map event type names or object type names
    to URIs. In this case, the resulting schema will refer to these URIs
    in stead of generating the schema patterns in place. This might be
    useful if you have a central storage for event type definitions or
    object type definitions.

    Make sure to call :func:`OpenRelaxNG` first.

    Args:
      EventRefs (dict, optional): Dictionary containing URI of event schema for every event type name

      EventTypeRefs (dict, optional): Dictionary containing URI of event type schema for every event type name

      ObjectTypeRefs (dict, optional): Dictionary containing URI of object type schema for every object type name

    """

    self.SchemaRelaxNG = etree.Element('element')
    self.SchemaRelaxNG.set('name', 'events')
    self.SchemaRelaxNG.set('xmlns', 'http://relaxng.org/ns/structure/1.0')
    self.SchemaRelaxNG.set('datatypeLibrary', 'http://www.w3.org/2001/XMLSchema-datatypes')
    self.CurrentElementRelaxNG = self.SchemaRelaxNG

    self.OpenElementRelaxNG('element').set('name', 'definitions')

    self.OpenElementRelaxNG('element').set('name', 'eventtypes')
    self.OpenElementRelaxNG('oneOrMore')
    self.OpenElementRelaxNG('choice')

    if EventTypeRefs is None:
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

    if ObjectTypeRefs is None:
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

    if EventRefs is None:
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
