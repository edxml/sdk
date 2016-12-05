# -*- coding: utf-8 -*-
import re
import sre_constants

from edxml.EDXMLBase import EDXMLValidationError
from edxml.ontology import DataType


class ObjectType(object):
  """
  Class representing an EDXML object type
  """

  NAME_PATTERN = re.compile('^[a-z0-9-]{1,40}$')
  DISPLAY_NAME_PATTERN = re.compile("^[ a-zA-Z0-9]*/[ a-zA-Z0-9]*$")
  FUZZY_MATCHING_PATTERN = re.compile("^(none)|(phonetic)|(substring:.*)|(\[[0-9]{1,2}:\])|(\[:[0-9]{1,2}\])$")

  def __init__(self, Name, DisplayName, Description = None, DataType ='string:0:cs:u', Enp = 0, Compress = False, FuzzyMatching ='none', Regexp ='[\s\S]*'):

    self._attr = {
      'name': Name,
      'display-name'   : DisplayName or ' '.join(('%s/%s' % (Name, Name)).split('-')),
      'description'    : Description or Name,
      'data-type'      : DataType,
      'enp'            : Enp,
      'compress'       : Compress,
      'fuzzy-matching' : FuzzyMatching,
      'regexp'         : Regexp
    }

  @classmethod
  def Create(cls, Name, DisplayNameSingular = None, DisplayNamePlural = None, Description = None, DataType ='string:0:cs:u'):
    """

    Creates and returns a new ObjectType instance. When no display
    names are specified, display names will be created from the
    object type name. If only a singular form is specified, the
    plural form will be auto-generated by appending an 's'.

    Args:
      Name (str): object type name
      DisplayNameSingular (str): display name (singular form)
      DisplayNamePlural (str): display name (plural form)
      Description (str): short description of the object type
      DataType (str): a valid EDXML data type

    Returns:
      ObjectType: The ObjectType instance
    """

    if DisplayNameSingular:
      DisplayName = '%s/%s' % (DisplayNameSingular, DisplayNamePlural if DisplayNamePlural else '%ss' % DisplayNameSingular)
    else:
      DisplayName = '/'
    return cls(Name, DisplayName, Description, DataType)

  def GetName(self):
    """

    Returns the name of the object type.

    Returns:
      str: The object type name
    """

    return self._attr['name']

  def GetDisplayName(self):
    """

    Returns the display-name attribute of the object type.

    Returns:
      str:
    """

    return self._attr['display-name']

  def GetDisplayNameSingular(self):
    """

    Returns the display name of the object type, in singular form.

    Returns:
      str:
    """

    return self._attr['display-name'].split('/')[0]

  def GetDisplayNamePlural(self):
    """

    Returns the display name of the object type, in plural form.

    Returns:
      str:
    """

    return self._attr['display-name'].split('/')[1]

  def GetDescription(self):
    """

    Returns the description of the object type.

    Returns:
      str:
    """

    return self._attr['description']

  def GetDataType(self):
    """

    Returns the data type of the object type.

    Returns:
      str:
    """

    return self._attr['data-type']

  def GetEntityNamingPriority(self):
    """

    Returns entity naming priority of the object type.

    Returns:
      int:
    """

    return self._attr['enp']

  def IsCompressible(self):
    """

    Returns True if compression is advised for the object type,
    returns False otherwise.

    Returns:
      bool:
    """

    return self._attr['compress']

  def GetFuzzyMatching(self):
    """

    Returns the EDXML fuzzy-matching attribute for the object type.

    Returns:
      str:
    """

    return self._attr['fuzzy-matching']

  def GetRegexp(self):
    """

    Returns the regular expression that object values must match.

    Returns:
      str:
    """

    return self._attr['regexp']

  def SetDescription(self, Description):
    """

    Sets the object type description

    Args:
      Description (str): Description

    Returns:
      EventSource: The ObjectType instance
    """

    self._attr['description'] = str(Description)
    return self

  def SetDataType(self, DataType):
    """

    Configure the data type.
    
    Args:
      DataType (DataType): DataType instance

    Returns:
      ObjectType: The ObjectType instance
    """
    self._attr['data-type'] = str(DataType)

    return self

  def SetDisplayName(self, Singular, Plural = None):
    """

    Configure the display name. If the plural form
    is omitted, it will be auto-generated by
    appending an 's' to the singular form.

    Args:
      Singular (str): display name (singular form)
      Plural (str): display name (plural form)

    Returns:
      ObjectType: The ObjectType instance
    """

    if Plural is None:
      Plural = '%ss' % Singular
    self._attr['display-name'] = '%s/%s' % (Singular, Plural)

    return self

  def SetEntityNamingPriority(self, Priority):
    """

    Configure the entity naming priority of
    the object type.

    Args:
      Priority (int): The EDXML priority attribute

    Returns:
      ObjectType: The ObjectType instance
    """
    self._attr['enp'] = int(Priority)

    return self

  def SetRegexp(self, Pattern):
    """

    Configure a regular expression that object
    values must match.

    Args:
      Pattern (str): Regular expression

    Returns:
      ObjectType: The ObjectType instance
    """
    self._attr['regexp'] = str(Pattern)

    return self


  def FuzzyMatchHead(self, Length):
    """

    Configure fuzzy matching on the head of the string
    (only for string data types).

    Args:
      Length (int): Number of characters to match

    Returns:
      ObjectType: The ObjectType instance
    """
    self._attr['fuzzy-matching'] = '[%d:]' % int(Length)

    return self

  def FuzzyMatchTail(self, Length):
    """

    Configure fuzzy matching on the tail of the string
    (only for string data types).

    Args:
      Length (int): Number of characters to match

    Returns:
      ObjectType: The ObjectType instance
    """
    self._attr['fuzzy-matching'] = '[:%d]' % int(Length)

    return self

  def FuzzyMatchSubstring(self, Pattern):
    """

    Configure fuzzy matching on a substring
    (only for string data types).

    Args:
      Pattern (str): Regular expression

    Returns:
      ObjectType: The ObjectType instance
    """
    self._attr['fuzzy-matching'] = 'substring:%s' % str(Pattern)

    return self

  def FuzzyMatchPhonetic(self):
    """

    Configure fuzzy matching on the sound
    of the string (phonetic fingerprinting).

    Returns:
      ObjectType: The ObjectType instance
    """
    self._attr['fuzzy-matching'] = 'phonetic'

    return self

  def Compress(self):
    """

    Enable compression for the object type.

    Returns:
      ObjectType: The ObjectType instance
    """
    self._attr['compress'] = True

    return self

  def Validate(self):
    """

    Checks if the object type is valid. It only looks
    at the attributes of the definition itself. Since it does
    not have access to the full ontology, the context of
    the event type is not considered. For example, it does not
    check if other, conflicting object type definitions exist.

    Raises:
      EDXMLValidationError
    Returns:
      ObjectType: The ObjectType instance

    """
    if not len(self._attr['name']) <= 40:
      raise EDXMLValidationError('The name of object type "%s" is too long.' % self._attr['name'])
    if not re.match(self.NAME_PATTERN, self._attr['name']):
      raise EDXMLValidationError('Object type "%s" has an invalid name.' % self._attr['name'])

    if not len(self._attr['display-name']) <= 64:
      raise EDXMLValidationError(
        'The display name of object type "%s" is too long: "%s".' % (self._attr['name'], self._attr['display-name'])
      )
    if not re.match(self.DISPLAY_NAME_PATTERN, self._attr['display-name']):
      raise EDXMLValidationError(
        'Object type "%s" has an invalid display name: "%s"' % (self._attr['name'], self._attr['display-name'])
      )

    if not len(self._attr['description']) <= 128:
      raise EDXMLValidationError(
        'The description of object type "%s" is too long: "%s"' % (self._attr['name'], self._attr['description'])
      )

    if not re.match(self.FUZZY_MATCHING_PATTERN, self._attr['fuzzy-matching']):
      raise EDXMLValidationError(
        'Object type "%s" has an invalid fuzzy-matching attribute: "%s"' % (self._attr['name'], self._attr['fuzzy-matching'])
      )
    if self._attr['fuzzy-matching'][:10] == 'substring:':
      try:
        re.compile('%s' % self._attr['fuzzy-matching'][10:])
      except sre_constants.error:
        raise EDXMLValidationError(
          'Definition of object type %s has an invalid regular expression in its fuzzy-matching attribute: "%s"' % (
            (self._attr['name'], self._attr['fuzzy-matching'])))

    if type(self._attr['compress']) != bool:
      raise EDXMLValidationError(
        'Object type "%s" has an invalid compress attribute: "%s"' % (self._attr['name'], repr(self._attr['compress']))
      )

    if not 0 <= int(self._attr['enp']) < 256:
      raise EDXMLValidationError(
        'Object type "%s" has an invalid entity naming priority: "%d"' % (self._attr['name'], self._attr['enp'])
      )

    try:
      re.compile(self._attr['regexp'])
    except sre_constants.error:
      raise EDXMLValidationError('Object type "%s" contains invalid regular expression: "%s"' %
                                 (self._attr['name'], self._attr['regexp']))

    DataType(self._attr['data-type']).Validate()

    return self

  @classmethod
  def Read(cls, typeElement):
    return cls(
      typeElement.attrib['name'],
      typeElement.get('display-name', '/'),
      typeElement.attrib['description'],
      typeElement.attrib['data-type'],
      int(typeElement.get('enp', 0)),
      typeElement.get('compress', 'false') == 'true',
      typeElement.get('fuzzy-matching', 'none'),
      typeElement.get('regexp', '[\s\S]*')
    )

  def Update(self, objectType):
    """

    Args:
      objectType (ObjectType): The new ObjectType instance

    Returns:
      ObjectType: The updated ObjectType instance

    """
    if self._attr['name'] != objectType.GetName():
      raise Exception('Attempt to update object type "%s" with object type "%s".',
                      (self._attr['name'], objectType.GetName()))

    if self._attr['display-name'] != objectType.GetDisplayName():
      raise Exception('Attempt to update object type "%s", but display names do not match.',
                      (self._attr['name'], objectType.GetName()))

    if self._attr['description'] != objectType.GetDescription():
      raise Exception('Attempt to update object type "%s", but descriptions do not match.',
                      (self._attr['name'], objectType.GetName()))

    if self._attr['data-type'] != objectType.GetDataType():
      raise Exception('Attempt to update object type "%s", but data types do not match.',
                      (self._attr['name'], objectType.GetName()))

    if int(self._attr['enp']) != objectType.GetEntityNamingPriority():
      raise Exception('Attempt to update object type "%s", but Entity Naming Priorities do not match.',
                      (self._attr['name'], objectType.GetName()))

    if self._attr['compress'] != objectType.IsCompressible():
      raise Exception('Attempt to update object type "%s", but compress flags do not match.',
                      (self._attr['name'], objectType.GetName()))

    if self._attr['fuzzy-matching'] != objectType.GetFuzzyMatching():
      raise Exception('Attempt to update object type "%s", but fuzzy matching attributes do not match.',
                      (self._attr['name'], objectType.GetName()))

    if self._attr['regexp'] != objectType.GetRegexp():
      raise Exception('Attempt to update object type "%s", but their regular expressions do not match.',
                      (self._attr['name'], objectType.GetName()))

    self.Validate()

    return self

  def Write(self, Writer):
    """

    Write the object type definition into the
    provided EDXMLWriter instance.

    Args:
      Writer (EDXMLWriter): An EDXMLWriter instance
    Returns:
      ObjectType: The ObjectType instance
    """

    Writer.AddObjectType(self._attr['name'], self._attr['description'],self._attr['data-type'],self._attr['fuzzy-matching'],self._attr['display-name'],self._attr['compress'],self._attr['enp'], self._attr['regexp'])

    return self
