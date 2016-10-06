# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                 Python class for EDXML data stream generation
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
#
#  ===========================================================================
#
#

"""EDXMLWriter

This module contains the EDXMLWriter class, which is used
to generate EDXML streams.

"""
import sre_constants
import sys
from xml.sax import make_parser

try:
  # lxml is not a very common module.
  from lxml import etree
except ImportError:
  sys.stderr.write('Failed to import the lxml Python package. Please install it.\n')
  sys.exit(1)

from EDXMLBase import *
from EDXMLParser import EDXMLValidatingParser

class EDXMLWriter(EDXMLBase):
  """Class for generating EDXML streams

  The Output parameter is a file-like object
  that will be used to send the XML data to.
  This file-like object can be pretty much 
  anything, as long as it has a write() method.

  The optional Validate parameter controls if
  the generated EDXML stream should be autovalidated
  or not. Automatic validation is
  enabled by default. This parameter applies
  to all aspects of EDXML validation, except
  for object value validation, which is covered
  by the ValidateObjects parameter.

  Enabling object value validation always results
  in full EDXML validation, regardless of the value
  of the Validate parameter.

  Args:
    Output (file): File-like output object

    Validate (bool, optional): Enable output validation (True) or not (False)

    ValidateObjects (bool, optional): Enable object validation (True) or not (False)
  """
  def __init__(self, Output, Validate = True, ValidateObjects = True):

    EDXMLBase.__init__(self)

    self.InvalidEvents = 0
    self.Validate = Validate
    self.Output = Output
    self.ElementStack = []

    # The lxml package does not filter out illegal XML
    # characters. So, below we compile a regular expression
    # matching all ranges of illegal characters. We will
    # use that to do our own filtering.

    IllegalRanges = [
      (0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F),
      (0x7F, 0x84), (0x86, 0x9F),
      (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF)
    ]

    if sys.maxunicode >= 0x10000:  # not narrow build
      IllegalRanges.extend([
        (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
        (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
        (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
        (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
        (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
        (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
        (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
        (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF)
      ])

    RegExpRanges = ["%s-%s" % (unichr(Low), unichr(High)) for (Low, High) in IllegalRanges]

    self.XMLReplaceRegexp = re.compile(u'[%s]' % u''.join(RegExpRanges))

    if self.Validate:

      # Construct validating EDXML parser
      self.SaxParser = make_parser()
      self.EDXMLParser = EDXMLValidatingParser(self.SaxParser, ValidateObjects = ValidateObjects)
      self.SaxParser.setContentHandler(self.EDXMLParser)

      # Construct a bridge that will be used to connect the
      # output of the XML Generator to the parser / validator.
      # We use the Bridge to output the XML to, so we have built
      # a chain that automatically validates the EDXML stream while
      # it is being generated. The full chain looks like this:
      #
      # lxml.etree generator => EDXMLValidatingParser => Output

      self.Bridge = EDXMLWriter.XMLParserBridge(self.SaxParser, Output)

    else:

      # Validation is disabled. 
      self.Bridge = Output
      self.EDXMLParser = None
      self.SaxParser = None

    # Initialize lxml.etree based XML generators. This
    # will write the XML declaration and open the
    # <events> tag.
    # Note that we use two XML generators. Due to the way
    # coroutines work, we can only flush the output buffer
    # after generating sub-elements of the <events> element
    # which contains the entire EDXML stream. That means we
    # need to build <eventgroup> tags in memory, which is
    # not acceptable. We solve that issue by writing the event
    # groups into a secondary XML generator, allowing us to
    # flush after each event.
    self.XMLWriter = self.__OuterXMLSerialiserCoRoutine()
    self.XMLWriter.next()

    self.CurrentElementType = ""
    self.EventTypes = {}
    self.ObjectTypes = {}

  # SaxParser instances can only be fed using the
  # feed() method. On the other hand, etree.xmlfile
  # instances can only write to file like objects.
  # This helper class acts like a file object, passing
  # through to a SaxParser instance.

  class XMLParserBridge():

    def __init__(self, Parser, Passthrough = None):
      self.BufferOutput = False
      self.Parse = True
      self.ParseError = None
      self.Buffer = ''
      self.Parser = Parser
      self.Passthrough = Passthrough

    def ReplaceParser(self, Parser):
      self.Parser = Parser

    def DisableParser(self):
      self.Parse = False

    def EnableParser(self):
      self.Parse = True

    def EnableBuffering(self):
      self.BufferOutput = True

    def ClearBuffer(self):
      self.Buffer = ''

    def DisableBuffering(self):
      self.BufferOutput = False
      if self.Passthrough:
        self.Passthrough.write(self.Buffer)
        self.Passthrough.flush()
        self.Buffer = ''

    def write(self, String):
      if self.Parse:
        try:
          self.Parser.feed(String)
        except Exception as Except:
          # We catch parsing exceptions here, because lxml does
          # not handle them correctly: When the file-like object
          # that it writes into raises an exception, it will initially
          # ignore it. On the next write attempt, a generic IO error
          # is raised, which means that the information about the
          # original exception is lost. So, we store the original
          # exception here to allow EDXMLWriter to check for it and
          # raise a proper, informative exception.
          Message = '%s: %s' % (Except.__class__.__name__, str(Except))
          if isinstance(Except, EDXMLError):
            Message = '%s\n\nStack trace:\n\n%s\n\n' % (Message, Except.GetStackTrace())

          if self.ParseError:
            # Another exception occurred, combine into
            # a new exception.
            self.ParseError = Exception('%s\n\nwhich was followed by:\n\n%s' % (self.ParseError, Message))
          else:
            self.ParseError = Exception('%s: %s' % (Except.__class__.__name__, Message))
      if self.Passthrough:
        if self.BufferOutput:
          # Add to buffer
          self.Buffer += String
        else:
          # Write directly to output
          self.Passthrough.write(String)
          self.Passthrough.flush()

  def __OuterXMLSerialiserCoRoutine(self):
    """Coroutine which performs the actual XML serialisation"""
    with etree.xmlfile(self.Bridge, encoding='utf-8') as Writer:
      if not 'flush' in dir(Writer):
        raise Exception('The installed version of lxml is too old. Please install version >= 3.4.')
      Writer.write_declaration()
      with Writer.element('events'):
        Writer.flush()
        try:
          while True:
            Element = (yield)
            if Element is None:
              # Sending None signals the end of the generation of
              # the definitions element, and the beginning of the
              # eventgroups element.
              with Writer.element('eventgroups'):
                Writer.flush()
                while True:
                  Element = (yield)
                  Writer.write(Element, pretty_print=True)
                  Writer.flush()
            Writer.write(Element, pretty_print=True)
            Writer.flush()
        except GeneratorExit:
          pass

  def __InnerXMLSerialiserCoRoutine(self, EventTypeName, EventSourceId):
    """Coroutine which performs the actual XML serialisation of eventgroups"""
    with etree.xmlfile(self.Bridge, encoding='utf-8') as Writer:
      with Writer.element('eventgroup', **{'event-type': EventTypeName, 'source-id': EventSourceId}):
        Writer.flush()
        try:
          while True:
            Element = (yield)
            Writer.write(Element, pretty_print=True)
            Writer.flush()
        except GeneratorExit:
          pass

  def AddXmlDefinitionsElement(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this method to insert a full <definitions> element.

    Args:
      XmlString (str): String containing the <definitions> element

    """
    self.Bridge.write(XmlString)

    # Adding a definitions element triggers validation,
    # which may raise exceptions.
    if self.Validate:
      if self.Bridge.ParseError is not None:
        raise self.Bridge.ParseError

  def AddXmlEventTypeElement(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this method to insert a full <eventtype> element.

    Args:
      XmlString (str): String containing the <eventtype> element

    """
    self.Bridge.write(XmlString)

    # Adding an event type triggers validation,
    # which may raise exceptions.
    if self.Validate:
      if self.Bridge.ParseError is not None:
        raise self.Bridge.ParseError

  def AddXmlObjectTypeTag(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this method to insert an <objecttype> tag.

    Args:
      XmlString (str): String containing the <objecttype> tag

    """
    self.Bridge.write(XmlString)

    # Adding an object type triggers validation,
    # which may raise exceptions.
    if self.Validate:
      if self.Bridge.ParseError is not None:
        raise self.Bridge.ParseError

  def AddXmlPropertyTag(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this method to insert a <property> tag.

    Args:
      XmlString (str): String containing the <property> tag

    """
    self.Bridge.write(XmlString)

    # Adding a property triggers validation,
    # which may raise exceptions.
    if self.Validate:
      if self.Bridge.ParseError is not None:
        raise self.Bridge.ParseError

  def AddXmlRelationTag(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this method to insert a <relation> tag.

    Args:
      XmlString (str): String containing the <relation> tag

    """
    self.Bridge.write(XmlString)

    # Adding a relation triggers validation,
    # which may raise exceptions.
    if self.Validate:
      if self.Bridge.ParseError is not None:
        raise self.Bridge.ParseError

  def AddXmlSourceTag(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this method to insert a <source> tag.

    Args:
      XmlString (str): String containing the <source> tag

    """
    self.Bridge.write(XmlString)

    # Adding a source tag triggers validation,
    # which may raise exceptions.
    if self.Validate:
      if self.Bridge.ParseError is not None:
        raise self.Bridge.ParseError

  def AddXmlEventTag(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this method to insert a full <event> element.

    Args:
      XmlString (str): String containing the <event> element

    """
    self.Bridge.write(XmlString)

    # Adding an event triggers validation,
    # which may raise exceptions.
    if self.Validate:
      if self.Bridge.ParseError is not None:
        raise self.Bridge.ParseError

  def OpenDefinitions(self):
    """Opens the <definitions> element"""
    self.ElementStack.append(etree.Element('definitions'))

  def OpenEventDefinitions(self):
    """Opens the <eventtypes> element"""
    if self.ElementStack[-1].tag != 'definitions': self.Error('A <eventtypes> tag must be child of an <definitions> tag. Did you forget to call OpenDefinitions()?')
    self.ElementStack.append(etree.SubElement(self.ElementStack[-1], 'eventtypes'))

  def OpenEventDefinition(self, Name, Description, ClassList, ReporterShort, ReporterLong, DisplayName = '/'):
    """Opens an event type definition.

    Args:
      Name (str): Name of the eventtype

      Description (str): Description of the eventtype

      ClassList (str): String containing a comma seperated list of class names

      ReporterShort (str): Short reporter string. Please refer to the specification for details.

      LongReporter (str): Long reporter string. Please refer to the specification for details.

      DisplayName (str,optional): EDXML display-name attribute

    """

    if self.ElementStack[-1].tag != 'eventtypes': self.Error('A <eventtype> tag must be child of an <eventtypes> tag. Did you forget to call OpenEventDefinitions()?')

    Attributes = {
      'name': Name,
      'display-name': DisplayName,
      'description': Description,
      'classlist': ClassList,
      'reporter-short': ReporterShort,
      'reporter-long': ReporterLong
      }

    self.ElementStack.append(etree.SubElement(self.ElementStack[-1], 'eventtype', **Attributes))

  def AddEventTypeParent(self, EventTypeName, PropertyMapping, ParentDescription, SiblingsDescription):
    """Adds a parent to an event definition.

    Args:
      EventTypeName (str): Name of the parent eventtype
      PropertyMapping (str): Value of the EDXML propertymap attribute
      ParentDescription (str): Value of the EDXML parent-description attribute
      SiblingsDescription (str): Value of the EDXML siblings-description attribute

    """
    if self.ElementStack[-1].tag != 'eventtype': self.Error('A <parent> tag must be child of an <eventtype> tag. Did you forget to call OpenEventDefinition()?')

    Attributes = {
      'eventtype': EventTypeName,
      'propertymap': PropertyMapping,
      'parent-description': ParentDescription,
      'siblings-description': SiblingsDescription
    }

    etree.SubElement(self.ElementStack[-1], 'parent', **Attributes)

  def OpenEventDefinitionProperties(self):
    """Opens a <properties> element for defining eventtype properties."""
    if self.ElementStack[-1].tag != 'eventtype': self.Error('A <properties> tag must be child of an <eventtype> tag. Did you forget to call OpenEventDefinition()?')
    self.ElementStack.append(etree.SubElement(self.ElementStack[-1], 'properties'))

  def AddEventProperty(self, Name, ObjectTypeName, Description, DefinesEntity = False, EntityConfidence = 0, Unique = False, Merge = 'drop', Similar = None):
    """Adds a property to an event definition.

    Args:
      Name (str): Name of the property

      ObjectTypeName (str): Name of the object type

      Description (str): Description of the property

      DefinesEntity (bool,optional): Property is entity identifier or not

      EntityConfidence (float,optional): Floating point confidence

      Unique (bool,optional): Property is unique or not

      Merge (str,optional): Merge strategy (only for unique properties)

      Similar (str,optional): EDXML similar attribute value

    """

    if self.ElementStack[-1].tag != 'properties': self.Error('A <property> tag must be child of an <properties> tag. Did you forget to call OpenEventDefinitionProperties()?')

    Attributes = {
      'name': Name,
      'object-type': ObjectTypeName,
      'description': Description,
      'unique': 'false',
      'merge': Merge,
      'defines-entity': 'false',
      'entity-confidence': '0'
      }

    if Unique:
      Attributes['unique'] = 'true'

    if DefinesEntity:
      Attributes['defines-entity'] = 'true'
      Attributes['entity-confidence'] = "%1.2f" % float(EntityConfidence)

    if Similar:
      Attributes['similar'] = Similar

    etree.SubElement(self.ElementStack[-1], 'property', **Attributes)

  def CloseEventDefinitionProperties(self):
    """Closes a previously opened <properties> section"""
    if self.ElementStack[-1].tag != 'properties': self.Error('Unbalanced <properties> tag. Did you forget to call OpenEventDefinitionProperties()?')
    self.ElementStack.pop()

  def OpenEventDefinitionRelations(self):
    """Opens a <relations> section for defining property relations."""
    if self.ElementStack[-1].tag != 'eventtype': self.Error('A <relations> tag must be child of an <eventtype> tag. Did you forget to call OpenEventDefinition()?')
    self.ElementStack.append(etree.SubElement(self.ElementStack[-1], 'relations'))

  def AddRelation(self, PropertyName1, PropertyName2, Type, Description, Confidence, Directed = True):
    """Adds a property relation to an event definition.

    Args:
      PropertyName1 (str): Name of first property

      PropertyName2 (str): Name of second property

      Type (str): EDXML Relation type attribute

      Description (str): Relation description

      Confidence (float): Floating point confidence value

      Directed (bool,optional): Boolean indicating if relation is directed (True) or not (False)

    """

    if self.ElementStack[-1].tag != 'relations': self.Error('A <relation> tag must be child of an <relations> tag. Did you forget to call OpenEventDefinitionRelations()?')

    Attributes = {
      'property1': PropertyName1,
      'property2': PropertyName2,
      'description': Description,
      'confidence': "%1.2f" % float(Confidence),
      'type': Type,
      'directed': ['false', 'true'][int(Directed)]
      }

    etree.SubElement(self.ElementStack[-1], 'relation', **Attributes)

  def CloseEventDefinitionRelations(self):
    """Closes a previously opened <relations> section"""
    if self.ElementStack[-1].tag != 'relations': self.Error('Unbalanced <relations> tag. Did you forget to call OpenEventDefinitionRelations()?')
    self.ElementStack.pop()

  def CloseEventDefinition(self):
    """Closes a previously opened event definition"""
    if self.ElementStack[-1].tag != 'eventtype': self.Error('Unbalanced <eventtype> tag. Did you forget to call CloseEventDefinitionRelations()?')
    self.ElementStack.pop()

  def CloseEventDefinitions(self):
    """Closes a previously opened <eventtypes> section"""
    if self.ElementStack[-1].tag != 'eventtypes': self.Error('Unbalanced <eventtypes> tag. Did you forget to call CloseEventDefinition()?')
    self.ElementStack.pop()

  def OpenObjectTypes(self):
    """Opens a <objecttypes> section for defining object types."""
    if self.ElementStack[-1].tag != 'definitions': self.Error('A <objecttypes> tag must be child of an <definitions> tag. Did you forget to call OpenDefinitions()?')
    self.ElementStack.append(etree.SubElement(self.ElementStack[-1], 'objecttypes'))

  def AddObjectType(self, Name, Description, ObjectDataType, FuzzyMatching = 'none', DisplayName = '/', Compress = False, ENP = 0, Regexp = '[\s\S]*'):
    """Adds a object type definition.

    Args:
      Name (str): Name of object type

      Description (str): Description of object type

      ObjectDataType (str): EDXML Data type

      FuzzyMatching (str,optional): EDXML fuzzy-matching attribute

      DisplayName (str): Display name

      Compress (bool,optional): Use data compression (True) or not (False)

      ENP (int,optional): EDXML enp attribute

      Regexp (str,optional): EDXML regexp attribute

    """

    if self.ElementStack[-1].tag != 'objecttypes': self.Error('A <objecttype> tag must be child of an <objecttypes> tag. Did you forget to call OpenObjectTypes()?')

    Attributes = {
      'name':           Name,
      'description':    Description,
      'data-type':      ObjectDataType,
      'fuzzy-matching': FuzzyMatching,
      'compress':       ['false', 'true'][int(Compress)],
      'enp':            str(ENP),
      'regexp':         Regexp,
      'display-name':   DisplayName
      }

    if 'regexp' != '[\s\S]*':
      try:
        # Note that XML schema regular expressions match the entire object
        # value. We wrap the expression in anchors to mimic this behavior
        re.compile('^%s$' % Attributes['regexp'])
      except sre_constants.error as Except:
        self.Error('Definition of object type %s has an invalid regular expression in its regexp attribute: "%s"' % (( Name, Attributes['regexp'] )) )

    if Attributes['fuzzy-matching'][:10] == 'substring:':
      try:
        re.compile('%s' % Attributes['fuzzy-matching'][10:])
      except sre_constants.error as Except:
        self.Error('Definition of object type %s has an invalid regular expresion in its fuzzy-matching attribute: "%s"' % (( Name, Attributes['fuzzy-matching'] )) )

    etree.SubElement(self.ElementStack[-1], 'objecttype', **Attributes)

  def CloseObjectTypes(self):
    """Closes a previously opened <objecttypes> section"""
    if self.ElementStack[-1].tag != 'objecttypes': self.Error('Unbalanced <objecttypes> tag. Did you forget to call OpenObjectTypes()?')
    self.ElementStack.pop()

  def OpenSourceDefinitions(self):
    """Opens a <sources> section for defining event sources."""
    if self.ElementStack[-1].tag != 'definitions': self.Error('A <sources> tag must be child of an <definitions> tag. Did you forget to call OpenObjectTypes()?')
    self.ElementStack.append(etree.SubElement(self.ElementStack[-1], 'sources'))

  def AddSource(self, SourceId, URL, DateAcquired, Description):
    """Adds a source definition.

    Args:
      SourceId (str): EDXML source ID

      URL (str): Source URL

      DateAcquired (str): Acquisition date (yyyymmdd)

      Description (str): Description of the source

    """

    if self.ElementStack[-1].tag != 'sources': self.Error('A <source> tag must be child of an <sources> tag. Did you forget to call OpenSourceDefinitions()?')

    Attributes = {
      'source-id':     str(SourceId),
      'url':           URL.lower(),
      'date-acquired': DateAcquired,
      'description':   Description
      }

    etree.SubElement(self.ElementStack[-1], 'source', **Attributes)

  def CloseSourceDefinitions(self):
    """Closes a previously opened <sources> section"""
    if self.ElementStack[-1].tag != 'sources': self.Error('Unbalanced <sources> tag. Did you forget to call OpenSourceDefinitions()?')
    self.ElementStack.pop()

  def CloseDefinitions(self):
    """Closes the <definitions> section"""

    if self.ElementStack[-1].tag != 'definitions': self.Error('Unbalanced <definitions> tag. Did you forget to call OpenDefinitions()?')

    # The definitions element is complete. Send it
    # to the coroutine, which will write it into
    # the Output or into the Bridge. If an EDXMLParser
    # has been created, any problems in the definitions
    # element will possibly raise an exception here or
    # populate the ParseError property of the bridge.
    Error = None
    try:
      self.XMLWriter.send(self.ElementStack.pop())
    except Exception as Except:
      Error = Except

    if isinstance(self.Bridge, EDXMLWriter.XMLParserBridge) and self.Bridge.ParseError:
      raise EDXMLError, str(self.Bridge.ParseError), sys.exc_info()[2]
    else:
      if Error:
        raise EDXMLError, str(Error), sys.exc_info()[2]

  def OpenEventGroups(self):
    """Opens the <eventgroups> section, containing all eventgroups"""
    if len(self.ElementStack) > 0: self.Error('An <eventgroups> tag must be child of the <events> tag. Did you forget to call CloseDefinitions()?')

    # We send None to the outer XML generator, to
    # hint it that the definitions element has been
    # completed and we want it to generate the
    # eventgroups opening tag.
    self.XMLWriter.send(None)

    self.ElementStack.append('eventgroups')

  def OpenEventGroup(self, EventTypeName, SourceId):
    """Opens an event group.

    Args:
      EventTypeName (str): Name of the eventtype

      SourceId (str): Source Id

    """

    if self.ElementStack[-1] != 'eventgroups': self.Error('An <eventgroup> tag must be child of an <eventgroups> tag. Did you forget to call CloseEventGroup()?')
    self.ElementStack.append('eventgroup')

    self.CurrentElementTypeName = EventTypeName
    self.CurrentElementSourceId = SourceId

    Attributes = {
      'event-type': EventTypeName,
      'source-id' : str(SourceId)
      }

    self.EventGroupXMLWriter = self.__InnerXMLSerialiserCoRoutine(self.CurrentElementTypeName, str(self.CurrentElementSourceId))
    self.EventGroupXMLWriter.next()

    # Opening an event group triggers validation,
    # which may raise exceptions.
    if self.Validate:
      if self.Bridge.ParseError is not None:
        raise self.Bridge.ParseError


  def CloseEventGroup(self):
    """Closes a previously opened event group"""
    if self.ElementStack[-1] != 'eventgroup': self.Error('Unbalanced <eventgroup> tag. Did you forget to call CloseEvent()?')
    self.ElementStack.pop()

    # This closes the generator, writing the closing eventgroup tag.
    self.EventGroupXMLWriter.close()

  def AddEvent(self, PropertyObjects, Content = '', ParentHashes = [], IgnoreInvalidObjects = False):
    """Alternative method for adding an event

    This method expects a dictionary containing a list of
    object values for every property.

    The optional ParentHashes parameter may contain
    a list of sticky hashes of explicit parent events,
    in hexadecimal string representation.

    if IgnoreInvalidObjects is set to True, any errors thrown
    by the validator as a result of invalid object values will
    be ignored, and the object will not be included in the event.

    Args:
      PropertyObjects (dict): Object dictionary

      Content (str,optional): Event content

      ParentHashes (list,optional): List of explicit parent events

      IgnoreInvalidObjects (bool,optional): Option to ignore invalid object values

    """

    if self.ElementStack[-1] != 'eventgroup': self.Error('A <event> tag must be child of an <eventgroup> tag. Did you forget to call OpenEventGroup()?')

    EventAttributes = {}

    if ParentHashes:
      EventAttributes['parents'] = ','.join(ParentHashes)

    Event = etree.Element('event', **EventAttributes)

    for PropertyName, Objects in PropertyObjects.items():
      for ObjectValue in Objects:
        if self.EDXMLParser:
          try:
            ObjectTypeName = self.EDXMLParser.Definitions.GetPropertyObjectType(self.CurrentElementTypeName, PropertyName)
            ObjectTypeAttributes = self.EDXMLParser.Definitions.GetObjectTypeAttributes(ObjectTypeName)
            self.ValidateObject(ObjectValue, ObjectTypeName, ObjectTypeAttributes['data-type'])
          except EDXMLError as Error:
            if IgnoreInvalidObjects:
              self.Warning("EDXMLWriter::AddObject: Object '%s' of property %s is invalid. Object will be ignored.\n" % (( ObjectValue, PropertyName )) )
              continue
            else:
              raise EDXMLError, 'Error adding property %s: %s' % (PropertyName, str(Error)), sys.exc_info()[2]

        try:
          etree.SubElement(Event, 'object', property = PropertyName, value = unicode(ObjectValue))
        except ValueError:
          # Object string contains weird characters that are illegal
          # in XML, like control characters and null bytes. Strip them.
          etree.SubElement(Event, 'object', property=PropertyName, value=unicode(re.sub(self.XMLReplaceRegexp, '', ObjectValue)))

    if Content:
      try:
        etree.SubElement(Event, 'content').text = Content
      except ValueError:
        # Content string contains weird characters that are illegal
        # in XML, like control characters and null bytes. Strip them.
        Event[-1].text = re.sub(self.XMLReplaceRegexp, '', Content)

    if self.Validate:

      # We enable buffering at this point, until we know
      # for certain that the event is valid. If the event
      # turns out to be invalid, the applcation can continue
      # generating the EDXML stream, skipping the invalid event.
      self.Bridge.ParseError = None
      self.Bridge.EnableBuffering()

    # Send element to coroutine, which will use lxml.etree
    # to write the event.
    self.EventGroupXMLWriter.send(Event)

    if self.Validate and self.Bridge.ParseError is not None:

      self.RecoverInvalidEvent()
      self.InvalidEvents += 1

      # Now we can throw an exception, which the
      # application can catch and recover from.
      InvalidEventException = self.Bridge.ParseError
      self.Bridge.ParseError = None
      self.Error('An invalid event was produced. The EDXML validator said: %s.\nNote that this exception is not fatal. You can recover by catching it and begin writing a new event.' % InvalidEventException)

    if self.Validate:
      # At this point, the event has been validated. We disable
      # buffering, which pushes it to the output.
      self.Bridge.DisableBuffering()

  def OpenEvent(self, ParentHashes = []):
    """Opens an event.

    The optional ParentHashes parameter may contain
    a list of sticky hashes of explicit parent events,
    in hexadecimal string representation.

    Args:
      ParentHashes (list,optional): List of explicit parent events

    """

    if self.ElementStack[-1] != 'eventgroup': self.Error('An <event> tag must be child of an <eventgroup> tag. Did you forget to call OpenEventGroup()?')


    if self.Validate:

      # We enable buffering at this point, until we know
      # for certain that the event is valid. If the event
      # turns out to be invalid, the applcation can continue
      # generating the EDXML stream, skipping the invalid event.
      self.Bridge.ParseError = None
      self.Bridge.EnableBuffering()

    Attributes = {}

    if ParentHashes:
      Attributes['parents'] = ','.join(ParentHashes)

    self.ElementStack.append(etree.Element('event', **Attributes))

  def AddObject(self, PropertyName, Value, IgnoreInvalid = False):
    """Adds an object to previously opened event.

    if IgnoreInvalidObjects is set to True, any errors thrown
    by the validator as a result of invalid object values will
    be ignored, and the object will not be included in the event.

    Args:
      PropertyName (str): Name of object property

      Value: Object value, can be any object that can be converted to unicode.

      IgnoreInvalid (bool,optional): Generate a warning in stead of an error for invalid values

    """

    if self.ElementStack[-1].tag != 'event': self.Error('An <object> tag must be child of an <event> tag. Did you forget to call OpenEvent()?')

    if ( isinstance(Value, str) or isinstance(Value, unicode) ) and len(Value) == 0:
      self.Warning("EDXMLWriter::AddObject: Object of property %s is empty. Object will be ignored.\n" % PropertyName)
      return

    try:

      if self.EDXMLParser:

        # We disabled the automatic object validation in the
        # EDXMLValidatingParser instance, because we want to
        # validate the object values before writing them into
        # the Bridge. So, we manually invoke object validation
        # here and handle any exceptions if they occur, optionally
        # skipping any invalid objects. This allows users of
        # the EDXMLWriter class to be sloppy about generating
        # object values.

        ObjectTypeName = self.EDXMLParser.Definitions.GetPropertyObjectType(self.CurrentElementTypeName, PropertyName)
        ObjectTypeAttributes = self.EDXMLParser.Definitions.GetObjectTypeAttributes(ObjectTypeName)
        self.ValidateObject(Value, ObjectTypeName, ObjectTypeAttributes['data-type'])

    except EDXMLError:

      if IgnoreInvalid:
        self.Warning("EDXMLWriter::AddObject: Object '%s' of property %s is invalid. Object will be ignored.\n" % (( Value, PropertyName )) )
      else:
        raise

    else:
      # We survived object validation, which means that we
      # can safely add the object to the 
      # This statement will generate the actual XML and
      # trigger EDXMLValidatingParser.
      etree.SubElement(self.ElementStack[-1], 'object', property = PropertyName, value = unicode(Value))

  def AddContent(self, ContentString):
    """Adds plain text content to previously opened event.

    Args:
      ContentString (str): Event content

    """
    if self.ElementStack[-1].tag != 'event': self.Error('A <content> tag must be child of an <event> tag. Did you forget to call OpenEvent()?')

    if len(ContentString) > 0:
      etree.SubElement(self.ElementStack[-1], 'content').text = ContentString

  def AddTranslation(self, Language, Interpreter, TranslationString):
    """Adds translated content to previously opened event.

    Args:
      Language (str): ISO 639-1 language code

      Interpreter (str): Name of interpreter

      TranslationString (str): The translation

    """

    if self.ElementStack[-1].tag != 'event': self.Error('A <translation> tag must be child of an <event> tag. Did you forget to call OpenEvent()?')

    if len(TranslationString) > 0:
      etree.SubElement(self.ElementStack[-1], 'translation', language = Language, interpreter = Interpreter).text = TranslationString
    else:
      self.Warning("EDXMLWriter::AddTranslation: Empty content encountered. Content will be ignored!\n")

  def CloseEvent(self):
    """Closes a previously opened event"""

    if self.ElementStack[-1].tag != 'event': self.Error('Attempt to close an <event> tag without a corresponding opening tag.')

    # This triggers event structure validation.
    self.EventGroupXMLWriter.send(self.ElementStack.pop())

    if self.Validate:
      if self.Bridge.ParseError is not None:

        self.RecoverInvalidEvent()
        self.InvalidEvents += 1

        # Now we can throw an exception, which the
        # application can catch and recover from.
        InvalidEventException = self.Bridge.ParseError
        self.Bridge.ParseError = None
        self.Error('An invalid event was produced. The EDXML validator said: %s.\nNote that this exception is not fatal. You can recover by catching it and begin writing a new event.' % InvalidEventException)

      # At this point, the event has been validated. We disable
      # buffering, which pushes it to the output.
      self.Bridge.DisableBuffering()

  def RecoverInvalidEvent(self):
    # Ok, the EDXMLParser instance that handles the content
    # from the SAX parser has borked on an invalid event.
    # This means that the SAX parser cannot continue. We
    # have no other choice than rebuild the data processing
    # chain from scratch and restore the state of both the
    # EDXMLParser instance and XML Generator to the point
    # where it can output events again.

    DefinitionsBackup = self.EDXMLParser.GetDefinitionsElementAsString()

    # Create new SAX parser and validating EDXML parser
    self.SaxParser = make_parser()
    self.EDXMLParser = EDXMLValidatingParser(self.SaxParser, ValidateObjects = False)

    # Install the new EDXMLParser as content handler.
    self.SaxParser.setContentHandler(self.EDXMLParser)

    # Replace the parser in the bridge
    self.Bridge.ReplaceParser(self.SaxParser)

    # We need to push some XML into the XMLGenerator and into
    # the bridge, but we do not want that to end up in the
    # output. So, we enable buffering and clear the buffer later.
    self.Bridge.EnableBuffering()

    # Push the EDXML definitions header into the bridge, which
    # will restore the state of the EDXMLParser instance.
    self.Bridge.write('<events>\n%s\n  <eventgroups>\n' % DefinitionsBackup)

    # Close the XML generator that is generating the
    # current event group. We do not want the resulting
    # closing eventgroup tag to reach the parser.
    self.Bridge.DisableParser()
    self.EventGroupXMLWriter.close()
    self.Bridge.EnableParser()

    # Create a new XML generator.
    self.EventGroupXMLWriter = self.__InnerXMLSerialiserCoRoutine(self.CurrentElementTypeName, str(self.CurrentElementSourceId))
    self.EventGroupXMLWriter.next()

    # Discard all buffered output and stop buffering. Now,
    # our processing chain is in the state that it was when
    # we started producing events.
    self.Bridge.ClearBuffer()
    self.Bridge.DisableBuffering()

  def CloseEventGroups(self):
    """Closes a previously opened <eventgroups> section"""
    if self.ElementStack[-1] != 'eventgroups': self.Error('Unbalanced <eventgroups> tag. Did you forget to call CloseEventGroup()?')
    self.ElementStack.pop()

    self.XMLWriter.close()

    if self.SaxParser:
      # This triggers well-formedness validation
      # if validation is enabled.
      self.SaxParser.close()

