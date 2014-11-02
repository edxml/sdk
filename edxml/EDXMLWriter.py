# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                 Python class for EDXML data stream generation
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
#

"""EDXMLWriter

This module contains the EDXMLWriter class, which is used
to generate EDXML streams.

"""

import string, sys
from cStringIO import StringIO
from xml.sax import make_parser
from xml.sax.saxutils import XMLGenerator
import traceback

try:
  # lxml is not a very common module.
  from lxml import etree
except ImportError:
  sys.stderr.write('Failed to import the lxml Python package. Please install it.\n')
  sys.exit(1)

from EDXMLBase import *
from EDXMLParser import EDXMLValidatingParser

class EDXMLWriter(EDXMLBase):
  """Class for generating EDXML streams"""

  def __init__(self, Output, Validate = True):
    """Constructor.
    The Output parameter is a file-like object
    that will be used to send the XML data to.
    This file-like object can be pretty much 
    anything, as long as it has a write() call.

    The optional Validate parameter controls if
    the generated EDXML stream should be auto-
    validated or not. Automatic validation is
    enabled by default.
    """

    EDXMLBase.__init__(self)

    self.InvalidEvents = 0
    self.Validate = Validate
    self.Output = Output
    self.ElementStack = []

    # Expression used for replacing invalid XML unicode characters
    self.XMLReplaceRegexp = re.compile(u'[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD\u10000-\u10FFFF]')

    if self.Validate:

      # Construct validating EDXML parser
      self.SaxParser = make_parser()
      self.EDXMLParser = EDXMLValidatingParser(self.SaxParser, ValidateObjects = False)
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

    # We still need a SAX XMLGenerator instance in order to
    # extract a backup copy of the definitions element.
    self.Definitions = StringIO()
    self.SaxGenerator = XMLGenerator(self.Definitions, 'utf-8')

    self.CurrentElementType = ""
    self.EventTypes = {}
    self.ObjectTypes = {}

  # SaxParser instances can only be fed using the
  # feed() function. On the other hand, etree.xmlfile
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
        except EDXMLError as Except:
          # We catch parsing exceptions here, because lxml does
          # not handle them correctly: It transforms any exception
          # in its output object into a general IO error, which means
          # that the information about the validation exception is lost.
          # So, we store the original exception here to allow EDXMLWriter
          # to check for it and raise a proper exception.
          self.ParseError = Except
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
            if Element == None:
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

    Use this function to insert a full <definitions> element.

    Parameters:

    XmlString: String containing the <definitions> element

    """
    self.Bridge.write(XmlString)

  def AddXmlEventTypeElement(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this function to insert a full <eventtype> element.

    Parameters:

    XmlString: String containing the <eventtype> element

    """
    self.Bridge.write(XmlString)

  def AddXmlObjectTypeTag(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this function to insert an <objecttype> tag.

    Parameters:

    XmlString: String containing the <objecttype> tag

    """
    self.Bridge.write(XmlString)

  def AddXmlPropertyTag(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this function to insert a <property> tag.

    Parameters:

    XmlString: String containing the <property> tag

    """
    self.Bridge.write(XmlString)

  def AddXmlRelationTag(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this function to insert a <relation> tag.

    Parameters:

    XmlString: String containing the <relation> tag

    """
    self.Bridge.write(XmlString)

  def AddXmlSourceTag(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this function to insert a <source> tag.

    Parameters:

    XmlString: String containing the <source> tag

    """
    self.Bridge.write(XmlString)

  def AddXmlEventTag(self, XmlString):
    """Apart from programmatically adding to an EDXML
    stream, it is also possible to insert plain XML into
    the stream. Both methods result in full automatic
    validation of the EDXML stream.

    Use this function to insert a full <event> element.

    Parameters:

    XmlString: String containing the <event> element

    """
    self.Bridge.write(XmlString)

  def OpenDefinitions(self):
    """Opens the <definitions> element"""
    self.ElementStack.append(etree.Element('definitions'))

  def OpenEventDefinitions(self):
    """Opens the <eventtypes> element"""
    if self.ElementStack[-1].tag != 'definitions': self.Error('A <eventtypes> tag must be child of an <definitions> tag. Did you forget to call OpenDefinitions()?')
    self.ElementStack.append(etree.SubElement(self.ElementStack[-1], 'eventtypes'))

  def OpenEventDefinition(self, Name, Description, ClassList, ReporterShort, ReporterLong, DisplayName = None):
    """Opens an event type definition.
    Parameters:

    Name          -- Name of the eventtype
    Description   -- Description of the eventtype
    ClassList     -- String containing a comma seperated list of class names
    ReporterShort -- Short reporter string. Please refer to the specification for details.
    LongReporter  -- Long reporter string. Please refer to the specification for details.
    DisplayName   -- EDXML display-name attribute (optional, defaults to none)

    """

    if self.ElementStack[-1].tag != 'eventtypes': self.Error('A <eventtype> tag must be child of an <eventtypes> tag. Did you forget to call OpenEventDefinitions()?')

    Attributes = {
      'name': Name,
      'description': Description,
      'classlist': ClassList,
      'reporter-short': ReporterShort,
      'reporter-long': ReporterLong
      }

    if DisplayName:
      Attributes['display-name'] = DisplayName

    self.ElementStack.append(etree.SubElement(self.ElementStack[-1], 'eventtype', **Attributes))

  def AddEventTypeParent(self, EventTypeName, PropertyMapping):
    """Adds a parent to an event definition.
    Parameters:

    EventTypeName     -- Name of the parent eventtype
    PropertyMapping   -- Value of the EDXML propertymap attribute

    """
    if self.ElementStack[-1].tag != 'eventtype': self.Error('A <parent> tag must be child of an <eventtype> tag. Did you forget to call OpenEventDefinition()?')

    etree.SubElement(self.ElementStack[-1], 'parent', eventtype = EventTypeName, propertymap = PropertyMapping)

  def OpenEventDefinitionProperties(self):
    """Opens a <properties> element for defining eventtype properties."""
    if self.ElementStack[-1].tag != 'eventtype': self.Error('A <properties> tag must be child of an <eventtype> tag. Did you forget to call OpenEventDefinition()?')
    self.ElementStack.append(etree.SubElement(self.ElementStack[-1], 'properties'))

  def AddEventProperty(self, Name, ObjectTypeName, Description, DefinesEntity = False, EntityConfidence = 0, Unique = False, Merge = 'drop', Similar = None):
    """Adds a property to an event definition.
    Parameters:

    Name              -- Name of the property
    ObjectTypeName    -- Name of the object type
    Description       -- Description of the property
    DefinesEntity     -- Property is entity identifier or not (optional, default is False)
    EntityConfideuce  -- Floating point confidence (optional, default is zero)
    Unique            -- Property is unique or not (optional, default is False)
    Merge             -- Merge strategy (only for unique properties)
    Similar           -- Optional EDXML similar attribute value

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
    Parameters:

    PropertyName1     -- Name of first property
    PropertyName2     -- Name of second property
    Type              -- Relation type including predicate
    Description       -- Relation description
    Confidence        -- Floating point confidence value
    Directed          -- Boolean indicating if relation is directed or not

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

  def AddObjectType(self, Name, Description, ObjectDataType, FuzzyMatching = 'none', DisplayName = None, Compress = False, ENP = 0, Regex = None):
    """Adds a object type definition.
    Parameters:

    Name            -- Name of object type
    Description     -- Description of object type
    ObjectDataType  -- Data type
    FuzzyMatching   -- Fuzzy matching technique (optional, defaults to none)
    DisplayName     -- Display name (optional, defaults to none)
    Compress        -- Use data compression (True) or not (False) (optional, defaults to False)
    ENP             -- Entity Naming Priority (optional, defaults to zero)

    """

    if self.ElementStack[-1].tag != 'objecttypes': self.Error('A <objecttype> tag must be child of an <objecttypes> tag. Did you forget to call OpenObjectTypes()?')

    Attributes = {
      'name':           Name,
      'description':    Description,
      'data-type':      ObjectDataType,
      'fuzzy-matching': FuzzyMatching,
      'compress':       ['false', 'true'][int(Compress)],
      'enp':            str(ENP)
      }

    if DisplayName:
      Attributes['display-name'] = DisplayName
    if Regex:
      Attributes['regexp'] = Regex

    if 'regexp' in Attributes:
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
    Parameters:

    SourceId       -- Source Id
    URL            -- Source URL
    DateAcquired   -- Acquisition date (yyyymmdd)
    Description    -- Description of the source

    """

    if self.ElementStack[-1].tag != 'sources': self.Error('A <source> tag must be child of an <sources> tag. Did you forget to call OpenSourceDefinitions()?')

    Attributes = {
      'source-id':     str(SourceId),
      'url':           string.lower(URL),
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
    # element will raise an exception here.
    self.XMLWriter.send(self.ElementStack.pop())

    if self.EDXMLParser:
      # We survived validation. Create a backup copy of the definitions element,
      # which we can use to recover from generating invalid events.
      self.EDXMLParser.Definitions.GenerateXMLDefinitions(self.SaxGenerator)

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
    Parameters:

    EventTypeName  -- Name of the eventtype
    SourceId       -- Source Id

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

    Parameters:

    PropertyObjects      -- Object dictionary
    Content              -- Event content
    ParentHashes         -- List of explicit parent events
    IgnoreInvalidObjects -- Option to ignore invalid object values

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
          except EDXMLError:
            if IgnoreInvalidObjects:
              self.Warning("EDXMLWriter::AddObject: Object '%s' of property %s is invalid. Object will be ignored.\n" % (( ObjectValue, PropertyName )) )
              continue
            else:
              raise

        etree.SubElement(Event, 'object', property = PropertyName, value = unicode(ObjectValue))

    if Content:
      etree.SubElement(Event, 'content').text = Content

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

    if self.Validate and self.Bridge.ParseError != None:

      self.RecoverInvalidEvent()
      self.InvalidEvents += 1

      # Now we can throw an exception, which the
      # application can catch and recover from.
      self.Error('An invalid event was produced. The EDXML validator said: %s.\nNote that this exception is not fatal. You can recover by catching it and begin writing a new event.' % self.Bridge.ParseError)

    if self.Validate:
      # At this point, the event has been validated. We disable
      # buffering, which pushes it to the output.
      self.Bridge.DisableBuffering()

  def OpenEvent(self, ParentHashes = []):
    """Opens an event.

    The optional ParentHashes parameter may contain
    a list of sticky hashes of explicit parent events,
    in hexadecimal string representation.

    Parameters:

    ParentHashes -- List of explicit parent events

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
    Parameters:

    PropertyName       -- Name of object property
    Value              -- Object value string
    IgnoreInvalid      -- Generate a warning in stead of an error for invalid values (Optional, default is False)

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
    Parameters:

    ContentString -- Object value

    """
    if self.ElementStack[-1].tag != 'event': self.Error('A <content> tag must be child of an <event> tag. Did you forget to call OpenEvent()?')

    if len(ContentString) > 0:
      etree.SubElement(self.ElementStack[-1], 'content').text = ContentString

  def AddTranslation(self, Language, Interpreter, TranslationString):
    """Adds translated content to previously opened event.
    Parameters:

    Language           -- ISO 639-1 language code
    Interpreter        -- Name of interpreter
    TranslationString  -- The translation

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
    # CATCH: It looks like lxml eats the exceptions thrown by validator and spits
    # out a general IO error... We need to handle and report parser exceptions
    # in the Bridge..
    self.EventGroupXMLWriter.send(self.ElementStack.pop())

    if self.Validate:
      if self.Bridge.ParseError != None:

        self.RecoverInvalidEvent()
        self.InvalidEvents += 1

        # Now we can throw an exception, which the
        # application can catch and recover from.
        self.Error('An invalid event was produced. The EDXML validator said: %s.\nNote that this exception is not fatal. You can recover by catching it and begin writing a new event.' % self.Bridge.ParseError)

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
    self.Bridge.write('<events>\n%s\n  <eventgroups>\n' % self.Definitions.getvalue())

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

  def CloseEventGroups(self):
    """Closes a previously opened <eventgroups> section"""
    if self.ElementStack[-1] != 'eventgroups': self.Error('Unbalanced <eventgroups> tag. Did you forget to call CloseEventGroup()?')
    self.ElementStack.pop()

    self.XMLWriter.close()

    if self.SaxParser:
      # This triggers well-formedness validation
      # if validation is enabled.
      self.SaxParser.close()

