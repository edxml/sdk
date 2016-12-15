# -*- coding: utf-8 -*-
import datetime
from StringIO import StringIO

import pytz
import re
from collections import MutableMapping
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

  NAME_PATTERN = re.compile("^[a-z0-9-]*$")
  DISPLAY_NAME_PATTERN = re.compile("^[ a-zA-Z0-9]*/[ a-zA-Z0-9]*$")
  CLASS_LIST_PATTERN = re.compile("^[a-z0-9, ]*$")
  REPORTER_PLACEHOLDER_PATTERN = re.compile('\\[\\[([^\\]]*)\\]\\]')
  KNOWN_FORMATTERS = ('TIMESPAN', 'DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR', 'DURATION',
                      'LATITUDE', 'LONGITUDE', 'BYTECOUNT', 'CURRENCY', 'COUNTRYCODE', 'FILESERVER',
                      'BOOLEAN_STRINGCHOICE', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT', 'EMPTY')

  def __init__(self, Ontology, Name, DisplayName = None, Description = None, ClassList ='',
               ReporterShort ='no description available', ReporterLong ='no description available', Parent = None):

    self._attr = {
      'name': Name,
      'display-name'   : DisplayName or ' '.join(('%s/%s' % (Name, Name)).split('-')),
      'description'    : Description or Name,
      'classlist'      : ClassList,
      'reporter-short' : ReporterShort,
      'reporter-long'  : ReporterLong
    }

    self._properties = {}      # type: Dict[str, edxml.ontology.EventProperty]
    self._relations = []       # type: List[edxml.ontology.PropertyRelation]
    self._parent = Parent      # type: edxml.ontology.EventTypeParent
    self._relaxNG = None       # type: etree.RelaxNG
    self._ontology = Ontology  # type: edxml.ontology.Ontology


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
    return self._properties[propertyName]

  def __contains__(self, propertyName):
    try:
      self._properties[propertyName]
    except (KeyError, IndexError):
      return False
    else:
      return True

  def __iter__(self):
    for propertyName, prop in self._properties.iteritems():
      yield propertyName

  def _setOntology(self, ontology):
    self._ontology = ontology
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
      list[str]:
    """
    return self._attr['classlist'].split(',')

  def GetProperties(self):
    """

    Returns a dictionary containing all properties
    of the event type. The keys in the dictionary
    are the property names, the values are the
    EDXMLProperty instances.

    Returns:
       dict[str,EventProperty]: Properties
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
    for eventProperty in self._properties.values():
      if eventProperty.IsUnique():
        return True

    return False

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
      EventProperty: The EventProperty instance
    """
    if Name not in self._properties:
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

    return self._properties[Name]

  def AddProperty(self, Property):
    """

    Add specified property

    Args:
      Property (EventProperty): EventProperty instance

    Returns:
      EventType: The EventType instance
    """
    self._properties[Property.GetName()] = Property.Validate()

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
      PropertyRelation: The PropertyRelation instance
    """
    relation = edxml.ontology.PropertyRelation(self, self[Source], self[Target], Description, TypeClass, TypePredicate, Confidence, Directed)
    self._relations.append(relation.Validate())
    return relation

  def AddRelation(self, Relation):
    """

    Add specified property relation. It is recommended to use the methods
    from the EventProperty class in stead, to create property relations using
    a syntax that yields more readable code.

    Args:
      Relation (PropertyRelation): Property relation

    Returns:
      EventType: The EventType instance
    """
    self._relations.append(Relation.Validate())

    return self

  def SetDescription(self, Description):
    """

    Sets the event type description

    Args:
      Description (str): Description

    Returns:
      EventType: The EventType instance
    """

    self._attr['description'] = str(Description)
    return self

  def SetParent(self, Parent):
    """

    Set the parent event type

    Args:
      Parent (EventTypeParent): Parent event type

    Returns:
      EventType: The EventType instance
    """
    self._parent = Parent

    return self

  def AddClass(self, ClassName):
    """

    Adds the specified event type class

    Args:
      ClassName (str):

    Returns:
      EventType: The EventType instance
    """
    if ClassName:
      if self._attr['classlist'] == '':
        self._attr['classlist'] = ClassName
      else:
        self._attr['classlist'] = ','.join(list(set(self._attr['classlist'].split(',') + [ClassName])))

    return self

  def SetClasses(self, ClassNames):
    """

    Replaces the list of classes that the event type
    belongs to with the specified list. Any duplicates
    are automatically removed from the list.

    Args:
      ClassNames (Iterable[str]):

    Returns:
      EventType: The EventType instance
    """
    self._attr['classlist'] = ','.join(list(set(ClassNames)))

    return self

  def SetName(self, EventTypeName):
    """

    Sets the name of the event type.

    Args:
     EventTypeName (str): Event type name
    Returns:
      EventType: The EventType instance
    """
    self._attr['name'] = EventTypeName

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
      EventType: The EventType instance
    """

    if Plural is None:
      Plural = '%ss' % Singular
    self._attr['display-name'] = '%s/%s' % (Singular, Plural)

    return self

  def SetReporterShort(self, Reporter):
    """
    
    Set the short reporter string
    
    Args:
      Reporter (str): The short reporter string 

    Returns:
      EventType: The EventType instance
    """

    if Reporter:
      self._attr['reporter-short'] = Reporter
    return self

  def SetReporterLong(self, Reporter):
    """

    Set the long reporter string

    Args:
      Reporter (str): The long reporter string 

    Returns:
      EventType: The EventType instance
    """

    if Reporter:
      self._attr['reporter-long'] = Reporter
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
      dateTimeA = datetime.datetime.fromtimestamp(Min)
      dateTimeB = datetime.datetime.fromtimestamp(Max)
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

      # Match on placeholders like "[[FULLDATETIME:timestamp]]", creating
      # groups of the strings in between the placeholders and the
      # placeholders themselves, with and without brackets included.
      placeholders = re.findall(r'(\[\[([^]]*)\]\])', string)

      for placeholder in placeholders:

        objectStrings = []
        exploded = placeholder[1].split(':')

        if len(exploded) >= 2:
          formatter = exploded.pop(0)
          propertyList = exploded.pop(0)
        else:
          formatter = ''
          propertyList = exploded[0]

        if len(propertyList) > 0:
          properties = propertyList.split(',')

          for propertyName in properties:
            if propertyName not in eventObjectValues or len(eventObjectValues[propertyName]) == 0:
              if formatter == 'EMPTY':
                # Use the first formatter argument
                # in stead of the object value itself.
                objectStrings.append(exploded[0])
              else:
                # One of the place holders has no associated
                # value, so we return an empty string.
                return ''

          properties = [propertyName for propertyName in properties if propertyName in eventObjectValues]

          if formatter == 'TIMESPAN':

            timestamps = []
            for propertyName in properties:
              for objectValue in eventObjectValues[propertyName]:
                timestamps.append(float(objectValue))

            if len(timestamps) > 0:
              dateTimeA = datetime.datetime.fromtimestamp(min(timestamps))
              dateTimeB = datetime.datetime.fromtimestamp(max(timestamps))
              objectStrings.append(u'between %s and %s' % (dateTimeA.isoformat(' '), dateTimeB.isoformat(' ')))

          elif formatter == 'DURATION':

            timestamps = []
            for propertyName in properties:
              for objectValue in eventObjectValues[propertyName]:
                timestamps.append(float(objectValue))

            if len(timestamps) > 0:
              objectStrings.append(__formatTimeDuration(min(timestamps), max(timestamps)))

          elif formatter in ['YEAR', 'MONTH', 'WEEK', 'DATE', 'DATETIME', 'FULLDATETIME']:

            for propertyName in properties:
              for objectValue in eventObjectValues[propertyName]:
                timestamp = float(objectValue)
                timeZone = pytz.timezone("UTC")

                try:
                  if formatter == 'FULLDATETIME':
                    objectStrings.append(datetime.datetime.fromtimestamp(timestamp, timeZone)
                                         .strftime(u'%A, %B %d %Y at %H:%M:%Sh UTC'))
                  elif formatter == 'DATETIME':
                    objectStrings.append(datetime.datetime.fromtimestamp(timestamp, timeZone)
                                         .strftime(u'B %d %Y at %H:%M:%Sh UTC'))
                  elif formatter == 'DATE':
                    objectStrings.append(datetime.datetime.fromtimestamp(timestamp, timeZone)
                                         .strftime(u'%a, %B %d %Y'))
                  elif formatter == 'YEAR':
                    objectStrings.append(datetime.datetime.fromtimestamp(timestamp, timeZone)
                                         .strftime(u'%Y'))
                  elif formatter == 'MONTH':
                    objectStrings.append(datetime.datetime.fromtimestamp(timestamp, timeZone)
                                         .strftime(u'%B %Y'))
                  elif formatter == 'WEEK':
                    objectStrings.append(datetime.datetime.fromtimestamp(timestamp, timeZone)
                                         .strftime(u'week %W of %Y'))
                except ValueError:
                  # This may happen for some time stamps before year 1900, which
                  # is not supported by strftime.
                  objectStrings.append(u'some date, a long, long time ago')

          elif formatter == 'BYTECOUNT':

            for propertyName in properties:
              for objectValue in eventObjectValues[propertyName]:
                objectStrings.append(__formatByteCount(int(objectValue)))

          elif formatter == 'LATITUDE':
            degrees = int(objectValue)
            minutes = int((objectValue - degrees) * 60.0)
            seconds = int((objectValue - degrees - (minutes / 60.0)) * 3600.0)

            objectStrings.append(u'%d°%d′%d %s″' % (degrees, minutes, seconds, 'N' if degrees > 0 else 'S'))

          elif formatter == 'LONGITUDE':
            degrees = int(objectValue)
            minutes = int((objectValue - degrees) * 60.0)
            seconds = int((objectValue - degrees - (minutes / 60.0)) * 3600.0)

            objectStrings.append(u'%d°%d′%d %s″' % (degrees, minutes, seconds, 'E' if degrees > 0 else 'W'))

          elif formatter == 'CURRENCY':

            for propertyName in properties:
              for objectValue in eventObjectValues[propertyName]:
                objectStrings.append(u'%.2f%s' % (int(objectValue), exploded[0]))

          elif formatter == 'COUNTRYCODE':

            for propertyName in properties:
              for objectValue in eventObjectValues[propertyName]:
                try:
                  objectStrings.append(countries.get(objectValue).name)
                except KeyError:
                  objectStrings.append(objectValue + u' (unknown country code)')

          elif formatter == 'BOOLEAN_STRINGCHOICE':
            for propertyName in properties:
              for objectValue in eventObjectValues[propertyName]:
                if objectValue == 'true':
                  # Print first string
                  objectStrings.append(exploded[0])
                else:
                  # Print second string
                  objectStrings.append(exploded[1])

          elif formatter == 'BOOLEAN_ON_OFF':
            for propertyName in properties:
              for objectValue in eventObjectValues[propertyName]:
                if objectValue == 'true':
                  # Print 'on'
                  objectStrings.append(u'on')
                else:
                  # Print 'off'
                  objectStrings.append(u'off')

          elif formatter == 'BOOLEAN_IS_ISNOT':
            for propertyName in properties:
              for objectValue in eventObjectValues[propertyName]:
                if objectValue == 'true':
                  # Print 'is'
                  objectStrings.append(u'is')
                else:
                  # Print 'is not'
                  objectStrings.append(u'is not')

          elif formatter == 'EMPTY':
            pass

          else:
            for propertyName in properties:
              for objectValue in eventObjectValues[propertyName]:
                objectStrings.append(objectValue)

        if len(objectStrings) > 0:
          if len(objectStrings) > 1:
            # If one property has multiple objects,
            # list them all.
            LastObjectValue = objectStrings.pop()
            if colorize:
              ObjectString = ', '.join(colored(ObjectString, 'white', attrs=['bold']) for ObjectString in objectStrings)\
                             + u' and ' + LastObjectValue
            else:
              ObjectString = ', '.join(objectStrings)\
                             + u' and ' + LastObjectValue
          else:
            if colorize:
              ObjectString = colored(objectStrings[0], 'white', attrs=['bold'])
            else:
              ObjectString = objectStrings[0]
        else:
          ObjectString = ''

        replacements[placeholder[0]] = ObjectString

      # Return ReporterString where all placeholders are replaced
      # by the actual (formatted) object values

      for placeholder, replacement in replacements.items():
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
      EventType: The EventType instance

    """

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
      stringComponents = str(string).split(':')
      if len(stringComponents) == 1:
        # Placeholder does not contain a formatter.
        if stringComponents[0] in self._properties.keys():
          continue
      else:
        # Some kind of string formatter was used.
        # Figure out which one, and check if it
        # is used correctly.
        if stringComponents[0] in ['DURATION', 'TIMESPAN']:
          durationProperties = stringComponents[1].split(',')

          if len(durationProperties) != 2:
            raise EDXMLValidationError(
              ('Event type %s contains a reporter string containing a string formatter (%s) '
               'which requires two properties, but %d properties were specified.') %
              (self._attr['name'], stringComponents[0], len(durationProperties))
            )

          if durationProperties[0] in self._properties.keys() and \
             durationProperties[1] in self._properties.keys():

            # Check that both properties are timestamps
            for propertyName in durationProperties:
              if propertyName == '':
                raise EDXMLValidationError('Invalid property name in %s formatter: "%s"' % (propertyName, stringComponents[0]))
              if str(self._properties[propertyName].GetDataType()) != 'timestamp':
                raise EDXMLValidationError(
                  ('Event type %s contains a reporter string which uses a time related formatter, '
                   'but the used property (%s) is not a timestamp.') % (self._attr['name'], propertyName)
                )

            continue
        else:
          if not stringComponents[0] in self.KNOWN_FORMATTERS:
            raise EDXMLValidationError(
              'Event type %s contains a reporter string which refers to an unknown formatter: %s' %
              (self._attr['name'], stringComponents[0])
            )

          if stringComponents[0] in ['DATE', 'DATETIME', 'FULLDATETIME', 'WEEK', 'MONTH', 'YEAR']:
            # Check that only one property is specified after the formatter
            if len(stringComponents[1].split(',')) > 1:
              raise EDXMLValidationError(
                ('Event type %s contains a reporter string which uses the %s formatter, which accepts just one property. '
                 'Multiple properties were specified: %s') % (self._attr['name'], stringComponents[0], stringComponents[1])
              )
            # Check that property is a timestamp
            if stringComponents[1] == '':
              raise EDXMLValidationError(
                'Invalid property name in %s formatter: "%s"' % (stringComponents[1], stringComponents[0])
              )
            if str(self._properties[stringComponents[1]].GetDataType()) != 'timestamp':
              raise EDXMLValidationError(
                ('Event type %s contains a reporter string which uses the %s formatter. '
                 'The used property (%s) is not a timestamp, though.') % (self._attr['name'], stringComponents[0], stringComponents[1])
              )

          elif stringComponents[0] in ['LATITUDE', 'LONGITUDE', 'BYTECOUNT', 'COUNTRYCODE', 'FILESERVER', 'BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT']:
            # Check that no additional options are present
            if len(stringComponents) > 2:
              raise EDXMLValidationError(
                ('Event type %s contains a reporter string which uses the %s formatter. '
                 'This formatter accepts no options, but they were specified: %s') %
                (self._attr['name'], stringComponents[0], string)
              )
            # Check that only one property is specified after the formatter
            if len(stringComponents[1].split(',')) > 1:
              raise EDXMLValidationError(
                ('Event type %s contains a reporter string which uses the %s formatter. '
                 'This formatter accepts just one property. Multiple properties were given though: %s')
                % (self._attr['name'], stringComponents[0], stringComponents[1])
              )
            if stringComponents[0] in ['BOOLEAN_ON_OFF', 'BOOLEAN_IS_ISNOT']:
              # Check that property is a boolean
              if stringComponents[1] == '':
                raise EDXMLValidationError(
                  'Invalid property name in %s formatter: "%s"' % (stringComponents[1], stringComponents[0])
                )
              if str(self._properties[stringComponents[1]].GetDataType()) != 'boolean':
                raise EDXMLValidationError(
                  ('Event type %s contains a reporter string which uses the %s formatter. '
                   'The used property (%s) is not a boolean, though.') %
                  (self._attr['name'], stringComponents[0], stringComponents[1])
                )

          elif stringComponents[0] == 'CURRENCY':
            if len(stringComponents) != 3:
              raise EDXMLValidationError(
                'Event type %s contains a reporter string which uses a malformed %s formatter: %s' %
                (self._attr['name'], stringComponents[0], string)
              )

          elif stringComponents[0] == 'EMPTY':
            if len(stringComponents) != 3:
              raise EDXMLValidationError(
                'Event type %s contains a reporter string which uses a malformed %s formatter: %s' %
                (self._attr['name'], stringComponents[0], string)
              )

          elif stringComponents[0] == 'BOOLEAN_STRINGCHOICE':
            if len(stringComponents) != 4:
              raise EDXMLValidationError(
                'Event type %s contains a reporter string which uses a malformed %s formatter: %s' %
                (self._attr['name'], stringComponents[0], string)
              )
            # Check that property is a boolean
            if stringComponents[1] == '':
              raise EDXMLValidationError(
                'Invalid property name in %s formatter: "%s"' % (stringComponents[1], stringComponents[0])
              )
            if str(self._properties[stringComponents[1]].GetDataType()) != 'boolean':
              raise EDXMLValidationError(
                ('Event type %s contains a reporter string which uses the %s formatter. '
                 'The used property (%s) is not a boolean, though.') %
                (self._attr['name'], stringComponents[0], stringComponents[1])
              )

          else:
            raise EDXMLValidationError(
              'Event type %s contains a reporter string which uses an unknown formatter: %s' %
              (self._attr['name'], stringComponents[0])
            )

          if stringComponents[1] in self._properties.keys():
            continue

          raise EDXMLValidationError(
            'Event type %s contains a reporter string which refers to one or more nonexistent properties: %s' %
            (self._attr['name'], string)
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
    if not len(self._attr['name']) <= 40:
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
      eventType (EventType): The new EventType instance

    Returns:
      EventType: The updated EventType instance

    """
    if self._attr['name'] != eventType.GetName():
      raise Exception('Attempt to update event type "%s" with event type "%s".',
                      (self._attr['name'], eventType.GetName()))

    if self._attr['description'] != eventType.GetDescription():
      raise Exception('Attempt to update event type "%s", but descriptions do not match.',
                      (self._attr['name'], eventType.GetName()))

    if self.GetParent() is not None:
      if eventType.GetParent() is not None:
        self.GetParent().Update(eventType.GetParent())
      else:
        raise Exception('Attempt to update event type "%s", but update does not define a parent.', self._attr['name'])
    else:
      if eventType.GetParent() is not None:
        raise Exception('Attempt to update event type "%s", but update defines a parent.', self._attr['name'])

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
      EventType: The EventType instance
    """

    if self.GetParent() is not None:
      ParentPropertyMapping = self.GetParent().GetPropertyMap()
    else:
      ParentPropertyMapping = {}

    for propertyName, objects in edxmlEvent.items():

      if propertyName in ParentPropertyMapping and len(objects) > 0:
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

  def generateRelaxNG(self, Ontology):
    """

    Returns an ElementTree containing a RelaxNG schema for validating
    events of this event type. It requires an Ontology instance for
    obtaining the definitions of objects types referred to by the
    properties of the event type.

    Args:
      Ontology: Ontology containing the event type

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
