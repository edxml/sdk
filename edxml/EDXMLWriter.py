# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                 Python class for EDXML data stream generation
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

"""EDXMLWriter

This module contains the EDXMLWriter class, which is used
to generate EDXML streams.

"""

import string, sys

from xml.sax import make_parser
from xml.sax.saxutils import escape
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesImpl

from EDXMLBase import *
from EDXMLParser import EDXMLValidatingParser


# SaxParser instances can only be fed using the
# feed() function. On the other hand, XMLGenerator
# instances can only write to file like objects.
# This helper class acts like a file object, passing
# through to a SaxParser instance.

class SaxGeneratorParserBridge():
  
  def __init__(self, Parser, Passthrough = None):
    self.Parser = Parser
    self.Passthrough = Passthrough
  
  def write(self, Buffer):
    self.Parser.feed(Buffer)
    if self.Passthrough:
      self.Passthrough.write(Buffer)

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
  
    self.Indent = 0
    self.ElementStack = []
    
    # Expression used for replacing invalid XML unicode characters
    self.XMLReplaceRegexp = re.compile(u'[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD\u10000-\u10FFFF]')

    if Validate:

      # Construct validating EDXML parser
      self.SaxParser = make_parser()
      self.EDXMLParser = EDXMLValidatingParser(self.SaxParser)
      self.SaxParser.setContentHandler(self.EDXMLParser)

      # Construct a bridge that will be used to connect the
      # output of the XML Generator to the parser / validator.
    
      self.Bridge = SaxGeneratorParserBridge(self.SaxParser, Output)
    
      # Create an XML generator. We use the Bridge to output the
      # XML to, so we have built a chain that automatically validates
      # the EDXML stream while it is being generated. The chain now 
      # looks like this:
      #
      # XMLGenerator => EDXMLValidatingParser => Output
    
      self.XMLGenerator = XMLGenerator(self.Bridge, 'utf-8')

    else:
      
      # Validation is disabled
      self.XMLGenerator = XMLGenerator(Output, 'utf-8')
      self.Bridge = Output
      self.EDXMLParser = None
      self.SaxParser = None

    # Write XML declaration
    self.Bridge.write('<?xml version="1.0" encoding="UTF-8" ?>')
    
    self.OpenElement('events')

    self.CurrentEventType = ""
    self.EventTypes = {}
    self.ObjectTypes = {}

  # String escaping, for internal use only.
  def Escape(self, String):

    if not isinstance(String, unicode):
    
      if not isinstance(String, str): String = str(String)
    
      try:
        String = String.decode('utf-8')
      except UnicodeDecodeError:
        # String is not proper UTF8. Lets try to decode it as Latin1
        try:
          String = String.decode('latin-1').encode('utf-8').decode('utf-8')
        except:
          # That did not work either. We have no other choice but to replace the invalid
          # characters with the Unicode replacement character.
          String = unicode(String, errors='replace')

    return re.sub(self.XMLReplaceRegexp, '?', String)

  # For internal use only.
  def OpenElement(self, ElementName, Attributes = {}):
    
    self.XMLGenerator.ignorableWhitespace('\n'.ljust(self.Indent))
    self.ElementStack.append(ElementName)
    self.Indent += 2
    
    return self.XMLGenerator.startElement(ElementName, AttributesImpl(Attributes))

  # For internal use only.
  def CloseElement(self):
    self.Indent -= 2
    self.XMLGenerator.ignorableWhitespace('\n'.ljust(self.Indent))
    self.XMLGenerator.endElement(self.ElementStack.pop())
    
  
  # For internal use only.
  def AddElement(self, ElementName, Attributes = {}):
    
    self.XMLGenerator.ignorableWhitespace('\n'.ljust(self.Indent))
    self.XMLGenerator.startElement(ElementName, AttributesImpl(Attributes))
    self.XMLGenerator.endElement(ElementName)

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
    """Opens a <definitions> block"""
    self.OpenElement("definitions")

  def OpenEventDefinitions(self):
    """Opens an <eventtypes> block"""
    self.OpenElement("eventtypes")

  def OpenEventDefinition(self, Name, Description, ClassList, ReporterShort, ReporterLong):
    """Opens an event type definition.
    Parameters:
    
    Name          -- Name of the eventtype
    Description   -- Description of the eventtype
    ClassList     -- String containing a comma seperated list of class names
    ReporterShort -- Short reporter string. Please refer to the specification for details.
    LongReporter  -- Long reporter string. Please refer to the specification for details.
    
    """

    self.OpenElement("eventtype", {
      'name': Name, 
      'description': Description,
      'classlist': ClassList,
      'reporter-short': ReporterShort,
      'reporter-long': ReporterLong
      })


  def OpenEventDefinitionProperties(self):
    """Opens a <properties> section for defining eventtype properties."""
    self.OpenElement("properties")

  def AddEventProperty(self, Name, ObjectTypeName, Description, DefinesEntity = False, EntityConfidence = 0, Unique = False, Merge = 'drop'):
    """Adds a property to an event definition.
    Parameters:
    
    Name              -- Name of the property
    ObjectTypeName    -- Name of the object type
    Description       -- Description of the property
    DefinesEntity     -- Property is entity identifier or not (optional, default is False)
    EntityConfideuce  -- Floating point confidence (optional, default is zero)
    Unique            -- Property is unique or not (optional, default is False)
    Merge             -- Merge strategy (only for unique properties)
    
    """

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

    self.AddElement("property", Attributes)
      
  def CloseEventDefinitionProperties(self):
    """Closes a previously opened <properties> section"""
    self.CloseElement()

  def OpenEventDefinitionRelations(self):
    """Opens a <relations> section for defining property relations."""
    self.OpenElement("relations")

  def AddRelation(self, PropertyName1, PropertyName2, Type, Description, Confidence):
    """Adds a property relation to an event definition.
    Parameters:
    
    PropertyName1     -- Name of first property
    PropertyName2     -- Name of second property
    Type              -- Relation type including predicate
    Description       -- Relation description
    Confidence        -- Floating point confidence value
    
    """

    self.AddElement("relation", {
      'property1': PropertyName1,
      'property2': PropertyName2,
      'description': Description,
      'confidence': "%1.2f" % float(Confidence),
      'type': Type
      })

  def CloseEventDefinitionRelations(self):
    """Closes a previously opened <relations> section"""
    self.CloseElement()

  def CloseEventDefinition(self):
    """Closes a previously opened event definition"""
    self.CloseElement()

  def CloseEventDefinitions(self):
    """Closes a previously opened <eventtypes> section"""
    self.CloseElement()

  def OpenObjectTypes(self):
    """Opens a <objecttypes> section for defining object types."""
    self.OpenElement("objecttypes")

  def AddObjectType(self, Name, Description, ObjectDataType, FuzzyMatching = 'none'):
    """Adds a object type definition.
    Parameters:
    
    Name            -- Name of object type
    Description     -- Description of object type
    ObjectDataType  -- Data type
    FuzzyMatching   -- Fuzzy matching technique (optional, defaults to none)
    
    """

    Attributes = {
      'name':           Name,
      'description':    Description,
      'data-type':      ObjectDataType
      'fuzzy-matching': FuzzyMatching
      }
    
    self.AddElement("objecttype", Attributes)
    
  def CloseObjectTypes(self):
    """Closes a previously opened <objecttypes> section"""
    self.CloseElement()

  def OpenSourceDefinitions(self):
    """Opens a <sources> section for defining event sources."""
    self.OpenElement("sources")

  def AddSource(self, SourceId, URL, DateAcquired, Description):
    """Adds a source definition.
    Parameters:
    
    SourceId       -- Source Id
    URL            -- Source URL
    DateAcquired   -- Acquisition date (yyyymmdd)
    Description    -- Description of the source

    """

    self.AddElement("source", {
      'source-id':     str(SourceId),
      'url':           string.lower(URL),
      'date-acquired': DateAcquired,
      'description':   Description
      })
      
  def CloseSourceDefinitions(self):
    """Closes a previously opened <sources> section"""
    self.CloseElement()

  def CloseDefinitions(self):
    """Closes the <definitions> section"""
    self.CloseElement()

  def OpenEventGroups(self):
    """Opens the <eventgroups> section, containing all eventgroups"""
    self.OpenElement("eventgroups")

  def OpenEventGroup(self, EventTypeName, SourceId):
    """Opens an event group.
    Parameters:
    
    EventTypeName  -- Name of the eventtype
    SourceId       -- Source Id
    
    """

    self.CurrentEventTypeName = EventTypeName
    self.OpenElement("eventgroup", {
      'event-type': EventTypeName,
      'source-id' : str(SourceId)
      })

  def CloseEventGroup(self):
    """Closes a previously opened event group"""
    self.CloseElement()

  def OpenEvent(self):
    """Opens an event."""
    self.OpenElement("event")

  def AddObject(self, PropertyName, Value, IgnoreInvalid = False):
    """Adds an object to previously opened event.
    Parameters:
    
    PropertyName       -- Name of object property
    Value              -- Object value string
    IgnoreInvalid      -- Generate a warning in stead of an error for invalid values (Optional, default is False)

    """

    if ( isinstance(Value, str) or isinstance(Value, unicode) ) and len(Value) == 0:
      self.Warning("EDXMLWriter::AddObject: Object of property %s is empty. Object will be ignored.\n" % PropertyName)

    try:
      
      if self.EDXMLParser:
      
        # Even though the call to AddElement will already result
        # in an object value validation, we actually need to 
        # validate *before* the actual XML is generated. So, we 
        # actually validate twice. If the first ValidateObject
        # call fails, we can ignore the object if requested,
        # omitting it from the XML stream. This allows users of
        # the EDXMLWriter class to be sloppy about generating
        # object values.
      
        ObjectTypeName = self.EDXMLParser.Definitions.GetPropertyObjectType(self.CurrentEventTypeName, PropertyName)
        ObjectTypeAttributes = self.EDXMLParser.Definitions.GetObjectTypeAttributes(ObjectTypeName)
        self.ValidateObject(Value, ObjectTypeName, ObjectTypeAttributes['data-type'])
      
      # This statement will generate the actual XML and
      # trigger EDXMLValidatingParser.
      
      self.AddElement("object", {
      'property': PropertyName,
      'value'   : self.Escape(Value)
      })

    except EDXMLError:
      
      if IgnoreInvalid:
        self.Warning("EDXMLWriter::AddObject: Object '%s' of property %s is invalid. Object will be ignored.\n" % (( Value, PropertyName )) )
      else:
        raise
      
  def AddContent(self, ContentString):
    """Adds plain text content to previously opened event.
    Parameters:
    
    ContentString -- Object value
    
    """
    if len(ContentString) > 0:
      self.OpenElement('content')
      self.XMLGenerator.characters(self.Escape(ContentString))
      self.CloseElement()

  def AddTranslation(self, Language, Interpreter, TranslationString):
    """Adds translated content to previously opened event.
    Parameters:
    
    Language           -- ISO 639-1 language code
    Interpreter        -- Name of interpreter
    TranslationString  -- The translation
    
    """

    if len(TranslationString) > 0:
      self.OpenElement("translation", {'language': Language, 'interpreter': Interpreter})
      self.XMLGenerator.characters(self.Escape(TranslationString))
      self.CloseElement()
    else:
      self.Warning("EDXMLWriter::AddTranslation: Empty content encountered. Content will be ignored!\n")

  def CloseEvent(self):
    """Closes a previously opened event"""
    self.CloseElement()

  def CloseEventGroups(self):
    """Closes a previously opened <eventgroups> section"""
    self.CloseElement()
    self.CloseElement()
    
    if self.SaxParser:
      # This triggers well-formedness validation
      # if validation is enabled.
      self.SaxParser.close()

