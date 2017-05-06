# -*- coding: utf-8 -*-
import datetime
from StringIO import StringIO

import pytz
import re
from collections import MutableMapping

from dateutil.parser import parse
from typing import Dict
from typing import List
from dateutil import relativedelta
from iso3166 import countries
from lxml import etree
from lxml.builder import ElementMaker
from termcolor import colored

import edxml
from edxml.EDXMLBase import EDXMLValidationError


class EventType(MutableMapping):
  """
  Class representing an EDXML event type. The class provides
  access to event properties by means of a dictionary interface.
  For each of the properties there is a key matching the name of
  the event property, the value is the property itself.
  """

  NAME_PATTERN = re.compile("^[a-z0-9.]*$")
  DISPLAY_NAME_PATTERN = re.compile("^[ a-zA-Z0-9]*/[ a-zA-Z0-9]*$")
  CLASS_LIST_PATTERN = re.compile("^[a-z0-9, ]*$")
  REPORTER_PLACEHOLDER_PATTERN = re.compile('\\[\\[([^\\]]*)\\]\\]')
  KNOWN_FORMATTERS = (
    'TIMESPAN', 'DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR', 'DURATION',
    'LATITUDE', 'LONGITUDE', 'BYTECOUNT', 'CURRENCY', 'COUNTRYCODE', 'FILESERVER',
    'BOOLEAN_STRINGCHOICE', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT', 'EMPTY', 'NEWPAR', 'URL', 'UPPERCASE'
  )

  def __init__(self, Ontology, Name, DisplayName = None, Description = None, ClassList ='',
               ReporterShort ='no description available', ReporterLong ='no description available', Parent = None):

    self._attr = {
      'name': Name,
      'display-name'   : DisplayName or ' '.join(('%s/%s' % (Name, Name)).split('.')),
      'description'    : Description or Name,
      'classlist'      : ClassList,
      'reporter-short' : ReporterShort,
      'reporter-long'  : ReporterLong.replace('\n', '[[NEWPAR:]]')
    }

    self._properties = {}      # type: Dict[str, edxml.ontology.EventProperty]
    self._relations = []       # type: List[edxml.ontology.PropertyRelation]
    self._parent = Parent      # type: edxml.ontology.EventTypeParent
    self._relaxNG = None       # type: etree.RelaxNG
    self._ontology = Ontology  # type: edxml.ontology.Ontology

    self._parentDescription = None  # type: str

    self.__cachedUniqueProperties = None  # type: Dict[str, edxml.ontology.EventProperty]
    self.__cachedHashProperties = None    # type: Dict[str, edxml.ontology.EventProperty]

  def __delitem__(self, propertyName):
    self._properties.pop(propertyName, None)

  def __setitem__(self, propertyName, propertyInstance):
    if isinstance(propertyInstance, edxml.ontology.EventProperty):
      self._properties[propertyName] = propertyInstance
    else:
      raise TypeError('Not an event property: %s' % repr(propertyInstance))

  def __len__(self):
    return len(self._properties)

  def __getitem__(self, propertyName):
    """

    Args:
      propertyName (str): Name of an event property

    Returns:
      edxml.ontology.EventProperty:
    """
    try:
      return self._properties[propertyName]
    except KeyError:
      raise Exception('Event type %s has no property named %s.' % (self._attr['name'], propertyName))

  def __contains__(self, propertyName):
    try:
      self._properties[propertyName]
    except (KeyError, IndexError):
      return False
    else:
      return True

  def __iter__(self):
    """

    Yields:
      Dict[str, edxml.ontology.EventProperty]
    """
    for propertyName, prop in self._properties.iteritems():
      yield propertyName

  def _childModifiedCallback(self):
    """Callback for change tracking"""
    self.__cachedUniqueProperties = None
    self.__cachedHashProperties = None
    self._ontology._childModifiedCallback()
    return self

  def GetName(self):
    """

    Returns the event type name

    Returns:
      str:
    """
    return self._attr['name']

  def GetDescription(self):
    """

    Returns the event type description

    Returns:
      str:
    """
    return self._attr['description']

  def GetDisplayNameSingular(self):
    """

    Returns the event type display name, in singular form.

    Returns:
      str:
    """
    return self._attr['display-name'].split('/')[0]

  def GetDisplayNamePlural(self):
    """

    Returns the event type display name, in plural form.

    Returns:
      str:
    """
    return self._attr['display-name'].split('/')[1]

  def GetClasses(self):
    """

    Returns the list of classes that this event type
    belongs to.

    Returns:
      List[str]:
    """
    return self._attr['classlist'].split(',')

  def GetProperties(self):
    """

    Returns a dictionary containing all properties
    of the event type. The keys in the dictionary
    are the property names, the values are the
    EDXMLProperty instances.

    Returns:
       Dict[str,edxml.ontology.EventProperty]: Properties
    """
    return self._properties

  def GetUniqueProperties(self):
    """

    Returns a dictionary containing all unique properties
    of the event type. The keys in the dictionary
    are the property names, the values are the
    EDXMLProperty instances.

    Returns:
       Dict[str, edxml.ontology.EventProperty]: Properties
    """
    return {n: p for n, p in self._properties.items() if p.IsUnique()}

  def GetHashProperties(self):
    """

    Returns a dictionary containing all properties
    of the event type that must be included when
    computing its sticky hash. The keys in the dictionary
    are the property names, the values are the
    EDXMLProperty instances.

    Returns:
       Dict[str, edxml.ontology.EventProperty]: Properties
    """

    if self.__cachedHashProperties is None:
      props = {}

      for n, p in self._properties.items():
        dataType = p.GetDataType().GetSplit()

        if not self.IsUnique() or p.IsUnique():
          if dataType[0] != 'number' or dataType[1] not in ('float', 'double'):
            # Floating point objects are ignored.
            props[n] = p

      self.__cachedHashProperties = props

    return self.__cachedHashProperties

  def GetPropertyRelations(self):
    """

    Returns the list of property relations that
    are defined in the event type.

    Returns:
      List[edxml.ontology.PropertyRelation]:
    """
    return self._relations

  def HasClass(self, ClassName):
    """

    Returns True if specified class is in the list of
    classes that this event type belongs to, return False
    otherwise.

    Args:
      ClassName (str): The class name

    Returns:
      bool:
    """
    return ClassName in self._attr['classlist'].split(',')

  def IsUnique(self):
    """

    Returns True if the event type is a unique
    event type, returns False otherwise.

    Returns:
      bool:
    """
    if self.__cachedUniqueProperties is None:
      self.__cachedUniqueProperties = {}
      for propertyName, eventProperty in self._properties.iteritems():
        if eventProperty.IsUnique():
          self.__cachedUniqueProperties[propertyName] = eventProperty

    return len(self.__cachedUniqueProperties) > 0

  def GetReporterShort(self):
    """

    Returns the short reporter string.

    Returns:
      str:
    """
    return self._attr['reporter-short']

  def GetReporterLong(self):
    """

    Returns the long reporter string.

    Returns:
      str:
    """
    return self._attr['reporter-long']

  def GetParent(self):
    """

    Returns the parent event type, or None
    if no parent has been defined.

    Returns:
      EventTypeParent: The parent event type
    """
    return self._parent

  def CreateProperty(self, Name, ObjectTypeName, Description = None):
    """

    Create a new event property.

    Note:
       The description should be really short, indicating
       which role the object has in the event type.

    Args:
      Name (str): Property name
      ObjectTypeName (str): Name of the object type
      Description (str): Property description

    Returns:
      edxml.ontology.EventProperty: The EventProperty instance
    """
    if Name not in self._properties:
      objectType = self._ontology.GetObjectType(ObjectTypeName)
      if not objectType:
        # Object type is not defined, try to load it from
        # any registered ontology bricks
        self._ontology._importObjectTypeFromBrick(ObjectTypeName)
        objectType = self._ontology.GetObjectType(ObjectTypeName)
      if objectType:
        self._properties[Name] = edxml.ontology.EventProperty(self, Name, objectType, Description).Validate()
      else:
        raise Exception(
          'Attempt to create property "%s" of event type "%s" referring to undefined object type "%s".' %
          (Name, self.GetName(), ObjectTypeName)
        )
    else:
      raise Exception(
        'Attempt to create existing property "%s" of event type "%s".' %
        (Name, self.GetName())
      )

    self._childModifiedCallback()
    return self._properties[Name]

  def AddProperty(self, Property):
    """

    Add specified property

    Args:
      Property (edxml.ontology.EventProperty): EventProperty instance

    Returns:
      edxml.ontology.EventType: The EventType instance
    """
    self._properties[Property.GetName()] = Property.Validate()

    self._childModifiedCallback()
    return self

  def CreateRelation(self, Source, Target, Description, TypeClass, TypePredicate, Confidence = 1.0, Directed = True):
    """

    Create a new property relation

    Args:
      Source (str): Name of source property
      Target (str): Name of target property
      Description (str): Relation description, with property placeholders
      TypeClass (str): Relation type class ('inter', 'intra' or 'other')
      TypePredicate (str): free form predicate
      Confidence (float): Relation confidence [0.0,1.0]
      Directed (bool): Directed relation True / False

    Returns:
      edxml.ontology.PropertyRelation: The PropertyRelation instance
    """

    if Source not in self:
      raise KeyError('Cannot find property %s in event type %s.' % (Source, self._attr['name']))

    if Target not in self:
      raise KeyError('Cannot find property %s in event type %s.' % (Target, self._attr['name']))

    relation = edxml.ontology.PropertyRelation(self, self[Source], self[Target], Description, TypeClass, TypePredicate, Confidence, Directed)
    self._relations.append(relation.Validate())

    self._childModifiedCallback()
    return relation

  def AddRelation(self, Relation):
    """

    Add specified property relation. It is recommended to use the methods
    from the EventProperty class in stead, to create property relations using
    a syntax that yields more readable code.

    Args:
      Relation (edxml.ontology.PropertyRelation): Property relation

    Returns:
      edxml.ontology.EventType: The EventType instance
    """
    self._relations.append(Relation.Validate())

    self._childModifiedCallback()
    return self

  def MakeChildren(self, SiblingsDescription, Parent):
    """

    Marks this event type as child of the specified parent event type. In
    case all unique properties of the parent also exist in the child, a
    default property mapping will be generated, mapping properties based
    on identical property names.

    Notes:
      You must call IsParent() on the parent before calling MakeChildren()

    Args:
      SiblingsDescription (str): EDXML siblings-description attribute
      Parent (edxml.ontology.EventType): Parent event type

    Returns:
      edxml.ontology.EventTypeParent: The event type parent definition
    """

    if self._parentDescription:
      self._parent = edxml.ontology.EventTypeParent(Parent.GetName(), '', self._parentDescription, SiblingsDescription)
    else:
      raise Exception('You must call IsParent() on the parent before calling MakeChildren().')

    # If all unique properties of the parent event type
    # also exist in the child event type, we can create
    # a default property map.
    propertyMap = {}
    for propertyName, eventProperty in Parent.GetUniqueProperties().items():
      if propertyName in self:
        propertyMap[propertyName] = propertyName
      else:
        propertyMap = {}
        break

    for childProperty, parentProperty in propertyMap.items():
      self._parent.Map(childProperty, parentProperty)

    self._childModifiedCallback()
    return self._parent

  def IsParent(self, ParentDescription, Child):
    """

    Marks this event type as parent of the specified child event type.

    Notes:
      To be used in conjunction with the MakeChildren() method.

    Args:
      ParentDescription (str): EDXML parent-description attribute
      Child (edxml.ontology.EventType): Child event type

    Returns:
      edxml.ontology.EventType: The EventType instance

    """

    Child._parentDescription = ParentDescription
    Child._childModifiedCallback()
    return self

  def SetDescription(self, Description):
    """

    Sets the event type description

    Args:
      Description (str): Description

    Returns:
      edxml.ontology.EventType: The EventType instance
    """

    self._attr['description'] = str(Description)

    self._childModifiedCallback()
    return self

  def SetParent(self, Parent):
    """

    Set the parent event type

    Notes:
      It is recommended to use the MakeChildren() and
      IsParent() methods in stead whenever possible,
      which results in more readable code.

    Args:
      Parent (edxml.ontology.EventTypeParent): Parent event type

    Returns:
      edxml.ontology.EventType: The EventType instance
    """
    self._parent = Parent

    self._childModifiedCallback()
    return self

  def AddClass(self, ClassName):
    """

    Adds the specified event type class

    Args:
      ClassName (str):

    Returns:
      edxml.ontology.EventType: The EventType instance
    """
    if ClassName:
      if self._attr['classlist'] == '':
        self._attr['classlist'] = ClassName
      else:
        self._attr['classlist'] = ','.join(list(set(self._attr['classlist'].split(',') + [ClassName])))

    self._childModifiedCallback()
    return self

  def SetClasses(self, ClassNames):
    """

    Replaces the list of classes that the event type
    belongs to with the specified list. Any duplicates
    are automatically removed from the list.

    Args:
      ClassNames (Iterable[str]):

    Returns:
      edxml.ontology.EventType: The EventType instance
    """
    self._attr['classlist'] = ','.join(list(set(ClassNames)))

    self._childModifiedCallback()
    return self

  def SetName(self, EventTypeName):
    """

    Sets the name of the event type.

    Args:
     EventTypeName (str): Event type name

    Returns:
      edxml.ontology.EventType: The EventType instance
    """
    self._attr['name'] = EventTypeName

    self._childModifiedCallback()
    return self

  def SetDisplayName(self, Singular, Plural = None):
    """

    Configure the display name. If the plural form
    is omitted, it will be auto-generated by
    appending an 's' to the singular form.

    Args:
      Singular (str): Singular display name
      Plural (str): Plural display name

    Returns:
      edxml.ontology.EventType: The EventType instance
    """

    if Plural is None:
      Plural = '%ss' % Singular
    self._attr['display-name'] = '%s/%s' % (Singular, Plural)

    self._childModifiedCallback()
    return self

  def SetReporterShort(self, Reporter):
    """

    Set the short reporter string

    Args:
      Reporter (str): The short reporter string

    Returns:
      edxml.ontology.EventType: The EventType instance
    """

    if Reporter:
      self._attr['reporter-short'] = Reporter

    self._childModifiedCallback()
    return self

  def SetReporterLong(self, Reporter):
    """

    Set the long reporter string. Newline characters are automatically
    replaced with [[NEWPAR:]] place holders.

    Args:
      Reporter (str): The long reporter string

    Returns:
      edxml.ontology.EventType: The EventType instance
    """

    if Reporter:
      self._attr['reporter-long'] = Reporter.replace('\n', '[[NEWPAR:]]')

    self._childModifiedCallback()
    return self

  def EvaluateReporterString(self, edxmlEvent, short=False, capitalize=True, colorize=False):
    """

    Evaluates the short or long reporter string of an event type using
    specified event, returning the result.

    By default, the long reporter string is evaluated, unless short is
    set to True.

    By default, we will try to capitalize the first letter of the resulting
    string, unless capitalize is set to False.

    Optionally, the output can be colorized. At his time this means that,
    when printed on the terminal, the objects in the evaluated string will
    be displayed using bold white characters.

    Args:
      edxmlEvent (edxml.EDXMLEvent): the EDXML event to use
      short (bool): use short or long reporter string
      capitalize (bool): Capitalize output or not
      colorize (bool): Colorize output or not

    Returns:
      unicode:
    """

    # Recursively split a placeholder string at '{' and '}'
    def __splitPlaceholderString(String, offset=0):

      elements = []
      length = len(String)

      while offset < length:
        pos1 = String.find('{', offset)
        pos2 = String.find('}', offset)
        if pos1 == -1:
          # There are no more sub-strings, Find closing bracket.
          if pos2 == -1:
            # No closing bracket either, which means that the
            # remaining part of the string is one element.
            # lacks brackets.
            substring = String[offset:length]
            offset = length
            elements.append(substring)
          else:
            # Found closing bracket. Add substring and return
            # to caller.
            substring = String[offset:pos2]
            offset = pos2 + 1
            elements.append(substring)
            break
        else:
          # We found an opening bracket.

          if pos2 == -1:
            # No closing bracket
            # Give up.
            offset = length
          else:
            # We also found a closing bracket.

            if pos1 < pos2:
              # Opening bracket comes first, which means we should
              # iterate.
              substring = String[offset:pos1]
              offset = pos1 + 1

              elements.append(substring)
              offset, Parsed = __splitPlaceholderString(String, offset)
              elements.append(Parsed)
            else:
              # closing bracket comes first, which means we found
              # an innermost substring. Add substring and return
              # to caller.
              substring = String[offset:pos2]
              offset = pos2 + 1
              elements.append(substring)
              break

      return offset, elements

    def __formatTimeDuration(Min, Max):
      dateTimeA = parse(Min)
      dateTimeB = parse(Max)
      delta = relativedelta.relativedelta(dateTimeB, dateTimeA)

      if delta.minutes > 0:
        if delta.hours > 0:
          if delta.days > 0:
            if delta.months > 0:
              if delta.years > 0:
                return u'%d years, %d months, %d days, %d hours, %d minutes and %d seconds' % \
                       (delta.years, delta.months, delta.days, delta.hours, delta.minutes, delta.seconds)
              else:
                return u'%d months, %d days, %d hours, %d minutes and %d seconds' % \
                       (delta.months, delta.days, delta.hours, delta.minutes, delta.seconds)
            else:
              return u'%d days, %d hours, %d minutes and %d seconds' % \
                     (delta.days, delta.hours, delta.minutes, delta.seconds)
          else:
            return u'%d hours, %d minutes and %d seconds' % \
                   (delta.hours, delta.minutes, delta.seconds)
        else:
          return u'%d minutes and %d seconds' % \
                 (delta.minutes, delta.seconds)
      else:
        return u'%d.%d seconds' % \
               (delta.seconds, delta.microseconds)

    def __formatByteCount(byteCount):
      suffixes = [u'B', u'KB', u'MB', u'GB', u'TB', u'PB']
      if byteCount == 0:
        return u'0 B'
      i = 0
      while byteCount >= 1024 and i < len(suffixes) - 1:
        byteCount /= 1024.
        i += 1
      f = (u'%.2f' % byteCount).rstrip('0').rstrip('.')
      return u'%s %s' % (f, suffixes[i])

    def __processSimplePlaceholderString(string, eventObjectValues, capitalizeString):

      replacements = {}

      if capitalizeString and string != '':
        if string[0] == '{':
          if string[1:2] != '[[':
            # Sting does not start with a placeholder,
            # so we can safely capitalize.
            string = string[0] + string[1].upper() + string[2:]
        else:
          if string[0:1] != '[[':
            # Sting does not start with a placeholder,
            # so we can safely capitalize.
            string = string[0].upper() + string[1:]

      # Match on placeholders like "[[FULLDATETIME:datetime]]", creating
      # groups of the strings in between the placeholders and the
      # placeholders themselves, with and without brackets included.
      placeholders = re.findall(r'(\[\[([^]]*)\]\])', string)

      for placeholder in placeholders:

        objectStrings = []
        try:
          formatter, argumentString = placeholder[1].split(':', 1)
          arguments = argumentString.split(',')
        except ValueError:
          # No formatter present.
          formatter = None
          arguments = placeholder[1].split(',')

        if not formatter:
          try:
            objectStrings.extend(eventObjectValues[arguments[0]])
          except KeyError:
            # Property has no object, which implies that
            # we must produce an empty result.
            return u''

        elif formatter == 'TIMESPAN':

          dateTimeStrings = []
          for propertyName in arguments:
            try:
              for objectValue in eventObjectValues[propertyName]:
                dateTimeStrings.append(objectValue)
            except KeyError:
              pass

          if len(dateTimeStrings) > 0:
            # Note that we use lexicographic sorting here.
            dateTimeA = parse(min(dateTimeStrings))
            dateTimeB = parse(max(dateTimeStrings))
            objectStrings.append(u'between %s and %s' % (dateTimeA.isoformat(' '), dateTimeB.isoformat(' ')))
          else:
            # No valid replacement string could be generated, which implies
            # that we must return an empty string.
            return u''

        elif formatter == 'DURATION':

          dateTimeStrings = []
          for propertyName in arguments:
            try:
              for objectValue in eventObjectValues[propertyName]:
                dateTimeStrings.append(objectValue)
            except KeyError:
              pass

          if len(dateTimeStrings) > 0:
            objectStrings.append(__formatTimeDuration(min(dateTimeStrings), max(dateTimeStrings)))
          else:
            # No valid replacement string could be generated, which implies
            # that we must return an empty string.
            return u''

        elif formatter in ['YEAR', 'MONTH', 'WEEK', 'DATE', 'DATETIME', 'FULLDATETIME']:

          try:
            values = eventObjectValues[arguments[0]]
          except KeyError:
            # Property has no object, which implies that
            # we must produce an empty result.
            return u''

          for objectValue in values:
            dateTime = parse(objectValue)

            try:
              if formatter == 'FULLDATETIME':
                objectStrings.append(dateTime.strftime(u'%A, %B %d %Y at %H:%M:%Sh UTC'))
              elif formatter == 'DATETIME':
                objectStrings.append(dateTime.strftime(u'%B %d %Y at %H:%M:%Sh UTC'))
              elif formatter == 'DATE':
                objectStrings.append(dateTime.strftime(u'%a, %B %d %Y'))
              elif formatter == 'YEAR':
                objectStrings.append(dateTime.strftime(u'%Y'))
              elif formatter == 'MONTH':
                objectStrings.append(dateTime.strftime(u'%B %Y'))
              elif formatter == 'WEEK':
                objectStrings.append(dateTime.strftime(u'week %W of %Y'))
            except ValueError:
              # This may happen for some time stamps before year 1900, which
              # is not supported by strftime.
              objectStrings.append(u'some date, a long, long time ago')

        elif formatter == 'BYTECOUNT':

          try:
            values = eventObjectValues[arguments[0]]
          except KeyError:
            # Property has no object, which implies that
            # we must produce an empty result.
            return u''

          for objectValue in values:
            objectStrings.append(__formatByteCount(int(objectValue)))

        elif formatter == 'LATITUDE':

          try:
            values = eventObjectValues[arguments[0]]
          except KeyError:
            # Property has no object, which implies that
            # we must produce an empty result.
            return u''

          for objectValue in values:
            degrees = int(objectValue)
            minutes = int((objectValue - degrees) * 60.0)
            seconds = int((objectValue - degrees - (minutes / 60.0)) * 3600.0)

            objectStrings.append(u'%d°%d′%d %s″' % (degrees, minutes, seconds, 'N' if degrees > 0 else 'S'))

        elif formatter == 'LONGITUDE':

          try:
            values = eventObjectValues[arguments[0]]
          except KeyError:
            # Property has no object, which implies that
            # we must produce an empty result.
            return u''

          for objectValue in values:
            degrees = int(objectValue)
            minutes = int((objectValue - degrees) * 60.0)
            seconds = int((objectValue - degrees - (minutes / 60.0)) * 3600.0)

            objectStrings.append(u'%d°%d′%d %s″' % (degrees, minutes, seconds, 'E' if degrees > 0 else 'W'))

        elif formatter == 'UPPERCASE':

          try:
            values = eventObjectValues[arguments[0]]
          except KeyError:
            # Property has no object, which implies that
            # we must produce an empty result.
            return u''

          for objectValue in values:
            objectStrings.append(objectValue.upper())

        elif formatter == 'CURRENCY':

          try:
            values = eventObjectValues[arguments[0]]
          except KeyError:
            # Property has no object, which implies that
            # we must produce an empty result.
            return u''

          propertyName, currencySymbol = arguments
          for objectValue in values:
            objectStrings.append(u'%.2f%s' % (int(objectValue), currencySymbol))

        elif formatter == 'URL':

          try:
            values = eventObjectValues[arguments[0]]
          except KeyError:
            # Property has no object, which implies that
            # we must produce an empty result.
            return u''

          propertyName, targetName = arguments
          for objectValue in values:
            objectStrings.append(u'%s (%s)' % (targetName, objectValue))

        elif formatter == 'COUNTRYCODE':

          try:
            values = eventObjectValues[arguments[0]]
          except KeyError:
            # Property has no object, which implies that
            # we must produce an empty result.
            return u''

          for objectValue in values:
            try:
              objectStrings.append(countries.get(objectValue).name)
            except KeyError:
              objectStrings.append(objectValue + u' (unknown country code)')

        elif formatter == 'BOOLEAN_STRINGCHOICE':

          try:
            values = eventObjectValues[arguments[0]]
          except KeyError:
            # Property has no object, which implies that
            # we must produce an empty result.
            return u''

          propertyName, true, false = arguments
          for objectValue in values:
            if objectValue == u'true':
              objectStrings.append(true)
            else:
              objectStrings.append(false)

        elif formatter == 'BOOLEAN_ON_OFF':

          try:
            values = eventObjectValues[arguments[0]]
          except KeyError:
            # Property has no object, which implies that
            # we must produce an empty result.
            return u''

          for objectValue in values:
            if objectValue == u'true':
              # Print 'on'
              objectStrings.append(u'on')
            else:
              # Print 'off'
              objectStrings.append(u'off')

        elif formatter == 'BOOLEAN_IS_ISNOT':

          try:
            values = eventObjectValues[arguments[0]]
          except KeyError:
            # Property has no object, which implies that
            # we must produce an empty result.
            return u''

          for objectValue in values:
            if objectValue == u'true':
              # Print 'is'
              objectStrings.append(u'is')
            else:
              # Print 'is not'
              objectStrings.append(u'is not')

        elif formatter == 'EMPTY':

          propertyName = arguments[0]
          if propertyName not in eventObjectValues or len(eventObjectValues[propertyName]) == 0:
            # Property has no object, use the second formatter argument
            # in stead of the object value itself.
            objectStrings.append(arguments[0])
          else:
            # Property has an object, so the formatter will
            # yield an empty string. This in turn implies that
            # we must produce an empty result.
            return u''

        elif formatter == 'NEWPAR':

          objectStrings.append('\n')

        if len(objectStrings) > 0:
          if len(objectStrings) > 1:
            # If one property has multiple objects,
            # list them all.
            if u''.join(objectStrings) != u'':
              LastObjectValue = objectStrings.pop()
              if colorize:
                ObjectString = u', '.join(colored(ObjectString, 'white', attrs=['bold']) for ObjectString in objectStrings)\
                               + u' and ' + LastObjectValue
              else:
                ObjectString = u', '.join(objectStrings)\
                               + u' and ' + LastObjectValue
            else:
              ObjectString = u''
          else:
            if colorize and objectStrings[0] != u'':
              ObjectString = colored(objectStrings[0], 'white', attrs=['bold'])
            else:
              ObjectString = objectStrings[0]
        else:
          ObjectString = u''

        replacements[placeholder[0]] = ObjectString

      # Return ReporterString where all placeholders are replaced
      # by the actual (formatted) object values

      for placeholder, replacement in replacements.items():
        if replacement == u'':
          # Placeholder produces empty string, which
          # implies that we must produce an empty result.
          return u''
        string = string.replace(placeholder, replacement)

      return string

    def __processSplitPlaceholderString(Elements, Event, Capitalize, IterationLevel=0):
      Result = ''
      ContainsSubStrings = False
      NonEmptySubstringCounter = 0

      for Element in Elements:
        if type(Element) == list:
          Processed = __processSplitPlaceholderString(Element, Event, Capitalize, IterationLevel + 1)
          ContainsSubStrings = True
          Capitalize = False
          if len(Processed) > 0:
            NonEmptySubstringCounter += 1
        else:
          if Element != '':
            Processed = __processSimplePlaceholderString(Element, Event, Capitalize)
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

    if short:
      ReporterString = unicode(self._attr['reporter-short'])
    else:
      ReporterString = unicode(self._attr['reporter-long'])

    return __processSplitPlaceholderString(
      __splitPlaceholderString(ReporterString)[1], edxmlEvent.GetProperties(), capitalize
    )

  def ValidateReporterString(self, string, ontology):
    """Checks if given reporter string makes sense.

    Args:
      string (unicode): The reporter string
      ontology (edxml.ontology.Ontology): The corresponding ontology

    Raises:
      EDXMLValidationError

    Returns:
      edxml.ontology.EventType: The EventType instance

    """

    ZeroArgumentFormatters = [
      'LATITUDE', 'LONGITUDE', 'BYTECOUNT', 'COUNTRYCODE', 'FILESERVER', 'BOOLEAN_ON_OFF',
      'BOOLEAN_IS_ISNOT', 'UPPERCASE'
    ]

    # Test if reporter string grammar is correct, by
    # checking that curly brackets are balanced.
    curlyNestings = {u'{': 1, u'}': -1}
    nesting = 0
    for curly in [c for c in string if c in [u'{', u'}']]:
      nesting += curlyNestings[curly]
      if nesting < 0:
        raise EDXMLValidationError('The following reporter string contains unbalanced curly brackets:\n%s\n' % string)
    if nesting != 0:
      raise EDXMLValidationError('The following reporter string contains unbalanced curly brackets:\n%s\n' % string)

    placeholderStrings = re.findall(self.REPORTER_PLACEHOLDER_PATTERN, string)

    for string in placeholderStrings:
      try:
        formatter, argumentString = str(string).split(':', 1)
        arguments = argumentString.split(',')
      except ValueError:
        # Placeholder does not contain a formatter.
        if str(string) in self._properties.keys():
          continue
        else:
          raise EDXMLValidationError(
            'Event type %s contains a reporter string which refers to one or more nonexistent properties: %s' %
            (self._attr['name'], string)
          )

      # Some kind of string formatter was used.
      # Figure out which one, and check if it
      # is used correctly.
      if formatter in ['DURATION', 'TIMESPAN']:

        if len(arguments) != 2:
          raise EDXMLValidationError(
            ('Event type %s contains a reporter string containing a string formatter (%s) '
             'which requires two properties, but %d properties were specified.') %
            (self._attr['name'], formatter, len(arguments))
          )

        if arguments[0] in self._properties.keys() and \
           arguments[1] in self._properties.keys():

          # Check that both properties are datetime values
          for propertyName in arguments:
            if propertyName == '':
              raise EDXMLValidationError('Invalid property name in %s formatter: "%s"' % (propertyName, formatter))
            if str(self._properties[propertyName].GetDataType()) != 'datetime':
              raise EDXMLValidationError(
                ('Event type %s contains a reporter string which uses a time related formatter, '
                 'but the used property (%s) is not a datetime value.') % (self._attr['name'], propertyName)
              )

          continue
      else:
        if formatter not in self.KNOWN_FORMATTERS:
          raise EDXMLValidationError(
            'Event type %s contains a reporter string which refers to an unknown formatter: %s' %
            (self._attr['name'], formatter)
          )

        if formatter in ['DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR']:
          # Check that only one property is specified after the formatter
          if len(arguments) > 1:
            raise EDXMLValidationError(
              ('Event type %s contains a reporter string which uses the %s formatter, which accepts just one property. '
               'Multiple properties were specified: %s') % (self._attr['name'], formatter, argumentString)
            )
          # Check that property is a datetime value
          if argumentString == '':
            raise EDXMLValidationError(
              'Invalid property name in %s formatter: "%s"' % (argumentString, formatter)
            )
          if str(self._properties[argumentString].GetDataType()) != 'datetime':
            raise EDXMLValidationError(
              ('Event type %s contains a reporter string which uses the %s formatter. '
               'The used property (%s) is not a datetime value, though.') % (self._attr['name'], formatter, argumentString)
            )

        elif formatter in ZeroArgumentFormatters:
          # Check that no additional arguments are present
          if len(arguments) > 1:
            raise EDXMLValidationError(
              ('Event type %s contains a reporter string which uses the %s formatter. '
               'This formatter accepts no arguments, but they were specified: %s') %
              (self._attr['name'], formatter, string)
            )
          # Check that only one property is specified after the formatter
          if len(arguments) > 1:
            raise EDXMLValidationError(
              ('Event type %s contains a reporter string which uses the %s formatter. '
               'This formatter accepts just one property. Multiple properties were given though: %s')
              % (self._attr['name'], formatter, argumentString)
            )
          if formatter in ['BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT']:
            # Check that property is a boolean
            if argumentString == '':
              raise EDXMLValidationError(
                'Invalid property name in %s formatter: "%s"' % (argumentString, formatter)
              )
            if str(self._properties[argumentString].GetDataType()) != 'boolean':
              raise EDXMLValidationError(
                ('Event type %s contains a reporter string which uses the %s formatter. '
                 'The used property (%s) is not a boolean, though.') %
                (self._attr['name'], formatter, argumentString)
              )

        elif formatter == 'CURRENCY':
          if len(arguments) != 2:
            raise EDXMLValidationError(
              'Event type %s contains a reporter string which uses a malformed %s formatter: %s' %
              (self._attr['name'], formatter, string)
            )

        elif formatter == 'URL':
          if len(arguments) != 2:
            raise EDXMLValidationError(
              'Event type %s contains a reporter string which uses a malformed %s formatter: %s' %
              (self._attr['name'], formatter, string)
            )

        elif formatter == 'EMPTY':
          if len(arguments) != 2:
            raise EDXMLValidationError(
              'Event type %s contains a reporter string which uses a malformed %s formatter: %s' %
              (self._attr['name'], formatter, string)
            )

        elif formatter == 'NEWPAR':
          if len(arguments) != 1 or arguments[0] != '':
            raise EDXMLValidationError(
              'Event type %s contains a reporter string which uses a malformed %s formatter: %s' %
              (self._attr['name'], formatter, string)
            )

        elif formatter == 'BOOLEAN_STRINGCHOICE':
          if len(arguments) != 3:
            raise EDXMLValidationError(
              'Event type %s contains a reporter string which uses a malformed %s formatter: %s' %
              (self._attr['name'], formatter, string)
            )
          # Check that property is a boolean
          if argumentString == '':
            raise EDXMLValidationError(
              'Invalid property name in %s formatter: "%s"' % (argumentString, formatter)
            )
          if str(self._properties[arguments[0]].GetDataType()) != 'boolean':
            raise EDXMLValidationError(
              ('Event type %s contains a reporter string which uses the %s formatter. '
               'The used property (%s) is not a boolean, though.') %
              (self._attr['name'], formatter, argumentString)
            )

        else:
          raise EDXMLValidationError(
            'Event type %s contains a reporter string which uses an unknown formatter: %s' %
            (self._attr['name'], formatter)
          )

    return self

  def Validate(self):
    """

    Checks if the event type definition is valid. Since it does
    not have access to the full ontology, the context of
    the event type is not considered. For example, it does not
    check if the event type definition refers to a parent event
    type that actually exists. Also, reporter strings are not
    validated.

    Raises:
      EDXMLValidationError
    Returns:
      EventType: The EventType instance

    """
    if not len(self._attr['name']) <= 64:
      raise EDXMLValidationError('The name of event type "%s" is too long.' % self._attr['name'])
    if not re.match(self.NAME_PATTERN, self._attr['name']):
      raise EDXMLValidationError('Event type "%s" has an invalid name.' % self._attr['name'])

    if not len(self._attr['display-name']) <= 64:
      raise EDXMLValidationError(
        'The display name of object type "%s" is too long: "%s"' % (self._attr['name'], self._attr['display-name'])
      )
    if not re.match(self.DISPLAY_NAME_PATTERN, self._attr['display-name']):
      raise EDXMLValidationError(
        'Object type "%s" has an invalid display-name attribute: "%s"' % (self._attr['name'], self._attr['display-name'])
      )

    if not len(self._attr['description']) <= 128:
      raise EDXMLValidationError(
        'The description of object type "%s" is too long: "%s"' % (self._attr['name'], self._attr['description'])
      )

    if not re.match(self.CLASS_LIST_PATTERN, self._attr['classlist']):
      raise EDXMLValidationError(
        'Event type "%s" has an invalid class list: "%s"' %
        (self._attr['name'], self._attr['classlist'])
      )

    for propertyName, eventProperty in self.GetProperties().items():
      eventProperty.Validate()

    for relation in self._relations:
      relation.Validate()

    return self

  @classmethod
  def Read(cls, typeElement, ontology):
    eventType = cls(ontology, typeElement.attrib['name'], typeElement.attrib['display-name'],
                    typeElement.attrib['description'], typeElement.attrib['classlist'],
                    typeElement.attrib['reporter-short'], typeElement.attrib['reporter-long'])

    for element in typeElement:
      if element.tag == 'parent':
        eventType.SetParent(edxml.ontology.EventTypeParent.Read(element))
      elif element.tag == 'properties':
        for propertyElement in element:
          eventType.AddProperty(edxml.ontology.EventProperty.Read(propertyElement, eventType))

      elif element.tag == 'relations':
        for relationElement in element:
          eventType.AddRelation(edxml.ontology.PropertyRelation.Read(relationElement, eventType))

    return eventType

  def Update(self, eventType):
    """

    Updates the event type to match the EventType
    instance passed to this method, returning the
    updated instance.

    Args:
      eventType (edxml.ontology.EventType): The new EventType instance

    Returns:
      edxml.ontology.EventType: The updated EventType instance

    """
    if self._attr['name'] != eventType.GetName():
      raise Exception('Attempt to update event type "%s" with event type "%s".' %
                      (self._attr['name'], eventType.GetName()))

    if self._attr['description'] != eventType.GetDescription():
      raise Exception('Attempt to update event type "%s", but descriptions do not match.' % self._attr['name'],
                      (self._attr['description'], eventType.GetName()))

    if self.GetParent() is not None:
      if eventType.GetParent() is not None:
        self.GetParent().Update(eventType.GetParent())
      else:
        raise Exception('Attempt to update event type "%s", but update does not define a parent.' % self._attr['name'])
    else:
      if eventType.GetParent() is not None:
        raise Exception('Attempt to update event type "%s", but update defines a parent.' % self._attr['name'])

    updatePropertyNames = set(eventType.GetProperties().keys())
    existingPropertyNames = set(self.GetProperties().keys())

    propertiesAdded = updatePropertyNames - existingPropertyNames
    propertiesRemoved = existingPropertyNames - updatePropertyNames

    if len(propertiesAdded) > 0:
      raise Exception('Event type update added properties.')
    if len(propertiesRemoved) > 0:
      raise Exception('Event type update removed properties.')

    for propertyName, eventProperty in self.GetProperties().items():
      eventProperty.Update(eventType[propertyName])

    self._childModifiedCallback()
    self.Validate()

    return self

  def GenerateXml(self):
    """

    Generates an lxml etree Element representing
    the EDXML <eventtype> tag for this event type.

    Returns:
      etree.Element: The element

    """

    element = etree.Element('eventtype', self._attr)
    if self._parent:
      element.append(self._parent.GenerateXml())
    properties = etree.Element('properties')
    for Property in self._properties.values():
      properties.append(Property.GenerateXml())
    relations = etree.Element('relations')
    for Relation in self._relations:
      relations.append(Relation.GenerateXml())

    element.append(properties)
    element.append(relations)

    return element

  def GetSingularPropertyNames(self):
    """

    Returns a list of properties that cannot have multiple values.

    Returns:
       list(str): List of property names
    """
    Singular = {}
    for PropertyName, Property in self._properties.items():
      if Property.GetMergeStrategy() in ('match', 'min', 'max', 'increment', 'sum', 'multiply', 'replace'):
        Singular[PropertyName] = True

    if self._parent:
      Singular.update(self._parent.GetPropertyMap())
    return Singular.keys()

  def GetMandatoryPropertyNames(self):
    """

    Returns a list of properties that must have a value

    Returns:
       list(str): List of property names
    """
    Singular = {}
    for PropertyName, Property in self._properties.items():
      if Property.GetMergeStrategy() in ('match', 'min', 'max', 'increment', 'sum', 'multiply'):
        Singular[PropertyName] = True

    return Singular.keys()

  def validateEventStructure(self, edxmlEvent):
    """

    Validates the structure of the event by comparing its
    properties and their object count to the requirements
    of the event type. Generates exceptions that are much
    more readable than standard XML validation exceptions.

    Args:
      edxmlEvent (edxml.EDXMLEvent):

    Raises:
      EDXMLValidationError

    Returns:
      edxml.ontology.EventType: The EventType instance
    """

    if self.GetParent() is not None:
      ParentPropertyMapping = self.GetParent().GetPropertyMap()
    else:
      ParentPropertyMapping = {}

    for propertyName, objects in edxmlEvent.items():

      if propertyName in ParentPropertyMapping and len(objects) > 1:
          raise EDXMLValidationError(
            ('An event of type %s contains multiple objects of property %s, '
             'but this property can only have one object due to it being used '
             'in an implicit parent definition.') % (self._attr['name'], propertyName)
          )

      # Check if the property is actually
      # supposed to be in this event.
      if propertyName not in self.GetProperties():
        raise EDXMLValidationError(
          ('An event of type %s contains an object of property %s, '
           'but this property does not belong to the event type.') %
          (self._attr['name'], propertyName)
        )

    # Verify that match, min and max properties have an object.
    for PropertyName in self.GetMandatoryPropertyNames():
      if PropertyName not in edxmlEvent:
        raise EDXMLValidationError(
          ('An event of type %s is missing an object for property %s, '
           'while it must have an object due to its configured merge strategy.')
          % (self._attr['name'], PropertyName)
        )

    # Verify that properties that cannot have multiple
    # objects actually have at most one object
    for PropertyName in self.GetSingularPropertyNames():
      if PropertyName in edxmlEvent:
        if len(edxmlEvent[PropertyName]) > 1:
          raise EDXMLValidationError(
            ('An event of type %s has multiple objects of property %s, '
             'while it cannot have more than one due to its configured merge strategy '
             'or due to a implicit parent definition.') %
            (self._attr['name'], PropertyName)
          )

    return self

  def validateEventObjects(self, edxmlEvent):
    """

    Validates the object values in the event by comparing
    the values with their data types. Generates exceptions
    that are much more readable than standard XML validation
    exceptions.

    Args:
      edxmlEvent (edxml.EDXMLEvent):

    Raises:
      EDXMLValidationError

    Returns:
      edxml.ontology.EventType: The EventType instance
    """

    for propertyName, objects in edxmlEvent.items():

      propertyObjectType = self._properties[propertyName].GetObjectType()

      for objectValue in objects:
        try:
          propertyObjectType.ValidateObjectValue(objectValue)
        except EDXMLValidationError as e:
          raise EDXMLValidationError(
            'Invalid value for property %s of event type %s: %s' % (propertyName, self._attr['name'], e)
          )

    return self

  def generateRelaxNG(self, Ontology):
    """

    Returns an ElementTree containing a RelaxNG schema for validating
    events of this event type. It requires an Ontology instance for
    obtaining the definitions of objects types referred to by the
    properties of the event type.

    Args:
      Ontology (edxml.ontology.Ontology): Ontology containing the event type

    Returns:
      ElementTree: The schema
    """
    e = ElementMaker()

    properties = []

    for PropertyName, Property in self._properties.items():
      objectType = Ontology.GetObjectType(Property.GetObjectTypeName())
      if PropertyName in self.GetMandatoryPropertyNames():
        # Exactly one object must be present, no need
        # to wrap it into an element to indicate this.
        properties.append(e.element(objectType.GenerateRelaxNG(), name=PropertyName))
      else:
        if PropertyName in self.GetSingularPropertyNames():
          # Property is not mandatory, but if present there
          # cannot be multiple values.
          properties.append(e.optional(e.element(objectType.GenerateRelaxNG(), name=PropertyName)))
        else:
          # Property is not mandatory and can have any
          # number of objects.
          properties.append(e.zeroOrMore(e.element(objectType.GenerateRelaxNG(), name=PropertyName)))

    schema = e.element(
      e.optional(
        e.attribute(
          e.data(
            e.param('([0-9a-f]{40})(,[0-9a-f]{40})*', name='pattern'),
            type='normalizedString'),
          name='parents'
        )
      ),
      e.element(
        e.interleave(*properties),
        name='properties'
      ),
      e.optional(e.element(e.text(), name='content')),
      name='event',
      xmlns='http://relaxng.org/ns/structure/1.0',
      datatypeLibrary='http://www.w3.org/2001/XMLSchema-datatypes'
    )

    # Note that, for some reason, using a programmatically built ElementTree
    # to instantiate a RelaxNG object fails with 'schema is empty'. If we
    # convert the schema to a string and parse it back gain, all is good.
    return etree.parse(StringIO(etree.tostring(etree.ElementTree(schema))))
