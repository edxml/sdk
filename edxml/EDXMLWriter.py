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
#  This class generates EDXML streams. It uses the EDXMLValidatingParser
#  class to automatically validate the generated EDXML stream. The generated
#  XML can be sent to any file-like object, like standard output, a file
#  on disk, or a network socket.


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

  def __init__(self, Output):

    EDXMLBase.__init__(self)
  
    self.Indent = 0
    self.ElementStack = []
    
    # Expression used for replacing invalid XML unicode characters
    self.XMLReplaceRegexp = re.compile(u'[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD\u10000-\u10FFFF]')


    # Construct validating EDXML parser
    self.SaxParser = make_parser()
    self.SaxParser.setContentHandler(EDXMLValidatingParser(self.SaxParser))

    # Construct a bridge that will be used to connect the
    # output of the XML Generator to the parser / validator.
    
    Bridge = SaxGeneratorParserBridge(self.SaxParser, Output)
    
    # Create an XML generator. We use the Bridge to output the
    # XML to, so we have built a chain that automatically validates
    # the EDXML stream while it is being generated. The chain now 
    # looks like this:
    #
    # XMLGenerator => EDXMLValidatingParser => Output
    
    self.XMLGenerator = XMLGenerator(Bridge, 'utf-8')

    # Write XML declaration
    Bridge.write('<?xml version="1.0" encoding="UTF-8" ?>')
    
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
    
  # Opens a <definitions> block
  def OpenDefinitions(self):
    self.OpenElement("definitions")

  # Opens an <eventtypes> block
  def OpenEventDefinitions(self):
    self.OpenElement("eventtypes")

  # Defines an event type
  #
  #  Name:          Unique name of the event type. 
  #                 To allow easy searching, construct names in a hierarchial
  #                 fashion. A name like "communication-chat-message" is easier to
  #                 find than a name like "message".
  #  Description:   Guess what
  #  ClassList:     Comma seperated list of class names. A class name is a short string
  #                 representing a category that the eventtype belongs to. Example:
  #
  #                 "communication,email"
  #
  #  ShortReporter: String to translate an event into a human readable text. The string
  #                 can contain placeholders which are replaced with object values. For
  #                 instance, when the event has a property named "phone-caller", you
  #                 could construct a reporter like:
  #
  #                   "The caller history contains phonenumber [[phone-caller]]."
  #
  #  LongReporter:  Long version of ShortReporter. The short version should be as brief
  #                 as possible, containing only the one or two most important objects.
  #                 The long version should contain ALL objects, as it is used to generate
  #                 complete human readable version of the event.
  #
  #                 => Please be sure to read the EDXML specification for details about
  #                    designing reporter strings.

  def OpenEventDefinition(self, Name, Description, ClassList, ReporterShort, ReporterLong):

    self.OpenElement("eventtype", {
      'name': Name, 
      'description': Description,
      'classlist': ClassList,
      'reporter-short': ReporterShort,
      'reporter-long': ReporterLong
      })


  def OpenEventDefinitionProperties(self):

    self.OpenElement("properties")

  # Add a property to an eventtype
  #
  #  Name:             Name of the property. Property names MUST be unique, but
  #                    multiple eventtypes are allowed to have the same property.
  #                    When you re-use a property, be sure to match the other
  #                    function arguments (objecttype, ...) EXACTLY.
  #                    In case you define eventtypes that share properties,
  #                    be SURE that their definitions are identical.
  #                    To allow easy searching, construct names in a hierarchial
  #                    fashion. A name like "communication-chat-message" is easier to
  #                    find than a name like "message".
  #  ObjectTypeName:   Name of the objecttype of the property.
  #  DefinesEntity:    Set to TRUE if the property could be used to define an entity. 
  #  EntityConfidence: FLOAT number between 0.0 and 1.0 which indicates how strongly
  #                    or weakly this property defines an entity. A social security
  #                    number is usually strongly tied to a person (confidence = 1.0)
  #                    while a shoe size is weak (confidence < 0.1 or so)
  #                    Value is not relevant when DefinesEntity = FALSE.
  #  Unique:           Indicates if the property is unique or not. There can be only one
  #                    event in the database having a specific value of a unique property.
  #                    Set to TRUE of FALSE.
  #  Merge:            Any event having a Unique property must indicate a merge strategy
  #                    for ALL of its properties. This strategy will be used by databases
  #                    when unique events need to be merged.
  #                    Indicate one of the following strategies:
  #
  #                    'drop'    (ignore new value)
  #                    'add'     (add each new property value to the event)
  #                    'replace' (replace previous property value)
  #                    'min'     (keep lowest property value)
  #                    'max'     (keep highest property value)
  
  def AddEventProperty(self, Name, ObjectTypeName, Description, DefinesEntity = False, EntityConfidence = 0, Unique = False, Merge = ''):

    Attributes = {
      'name': Name,
      'object-type': ObjectTypeName,
      'description': Description,
      'unique': 'false',
      'defines-entity': 'false',
      'entity-confidence': '0'
      }
  
    if Unique:
      Attributes['unique'] = 'true'

    if DefinesEntity:
      Attributes['defines-entity'] = 'true'
      Attributes['entity-confidence'] = "%1.2f" % float(EntityConfidence)

    if len(Merge) > 0:
      Attributes['merge'] = Merge

    self.AddElement("property", Attributes)
      
  def CloseEventDefinitionProperties(self):
    self.CloseElement()

  def OpenEventDefinitionRelations(self):
    self.OpenElement("relations")

  # Adds a relation between two event properties
  #
  #  PropertyName1/2:  Names of the two event properties
  #  Type:             Type indicates in what way the two properties relate
  #                    to each other. It is a string that exists of two parts seperated
  #                    by a colon. The string in the left part may contain one of the strings
  #                    
  #                    "intra"
  #                    "inter"
  #                    "parent"
  #                    "child"
  #                    "other"
  #                    
  #                    which indicate the relation type in a generic way. An "intra" relation
  #                    associates two different properties of the same entity. For example,
  #                    when person A sends an email message to person B, one could relate the
  #                    name of person A to the email adress of person A. This is a typical
  #                    "intra" relation. Relating the email adresses of A and B should
  #                    be done using a "inter" relation, connecting one entity to another.
  #                    
  #                    The part of the type string to the right of the colon should contain
  #                    a very short characterization of the type of relation, describing how
  #                    the two properties are related. Examples are:
  #                    
  #                    "makes use of"
  #                    "is called"
  #                    "is acquainted with"
  #                    "is part of"
  #                    "communicates with"
  #  Description:      Describes how the two properties are related.
  #  Confidence:       Indicates the odds of the relation being real, when
  #                    the associated event is seen _once_.
  #                    Example: The caller and callee in a single telephone call 
  #                    will usually be related in some way. Unless the caller
  #                    dialled the wrong number. Let's say the odds of a real
  #                    actual relation is 0.9.
  #                    FLOAT number between 0.0 and 1.0
  
  def AddRelation(self, PropertyName1, PropertyName2, Type, Description, Strength):


    self.AddElement("relation", {
      'property1': PropertyName1,
      'property2': PropertyName2,
      'description': Description,
      'confidence': "%1.2f" % float(Strength),
      'type': Type
      })

  # Closes a relations block
  def CloseEventDefinitionRelations(self):
    self.CloseElement()

  # Closes an event definition
  def CloseEventDefinition(self):
    self.CloseElement()

  # Closes the event definitions block
  def CloseEventDefinitions(self):
    self.CloseElement()

  # Open an object types definition block
  def OpenObjectTypes(self):
    self.OpenElement("objecttypes")

  # Define an object type
  #
  #  Name:                  Unique name of the object type. Whenever possible, existing
  #                         names in the XML database should be re-used. When you re-use
  #                         an existing name, be sure to match the other function argu-
  #                         ments (description, fuzzy matching, ...) EXACTLY.
  #                         To allow easy searching, construct names in a hierarchial
  #                         fashion. A name like "communication-chat-message" is easier to
  #                         find than a name like "message".
  #  Description:           You know what
  #  ObjectDataType:        Data type. Refer to EDXML specification for details.
  #                         Example: "string:0:ci:u"
  #
  #  FuzzyMatching:         Indicates if and how string objects can be matched in a fuzzy manner.
  #                         Refer to EDXML specification for details.


  def AddObjectType(self, Name, Description, ObjectDataType, FuzzyMatching = ''):

    Attributes = {
      'name':        Name,
      'description': Description,
      'data-type':   ObjectDataType
      }
      
    if len(FuzzyMatching) > 0:
      Attributes['fuzzy-matching'] = FuzzyMatching
        
    self.AddElement("objecttype", Attributes)
    

  # Close an object type definition
  def CloseObjectTypes(self):
    self.CloseElement()

  # Close the source definitions block
  def OpenSourceDefinitions(self):
    self.OpenElement("sources")

  # Adds a source definition, which describes where the data
  # came from.
  #
  #  SourceID:      Any string or number of choice, used to identify
  #                 this source. You need this ID when creating eventgroups.
  #                 NOTE: This ID is used only to create cross-references
  #                       inside the XML file. It should be unique only in
  #                       the scope of one specific XML output file. You can
  #                       use '1','2', 'foo', 'bar', or whatever you want.
  #  URL:           The source location of the data, in URL form.
  #                 Example:
  #                           /company/offices/stuttgart/clientrecords/2009/
  #
  #  Description:   Guess what
  #  DateAcquired:  The acquisition date, written as yyyymmdd.
  #                 Example:
  #                           20090228

  def AddSource(self, SourceID, URL, DateAcquired, Description):

    self.AddElement("source", {
      'source-id':     str(SourceID),
      'url':           string.lower(URL),
      'date-acquired': DateAcquired,
      'description':   Description
      })
      
  # Close source definitions
  def CloseSourceDefinitions(self):
    self.CloseElement()

  # Close the definitions block
  def CloseDefinitions(self):
    self.CloseElement()

  # Open the eventgroups block
  def OpenEventGroups(self):
    self.OpenElement("eventgroups")

  # Open an eventgroup
  def OpenEventGroup(self, EventTypeName, SourceID):

    self.OpenElement("eventgroup", {
      'event-type': EventTypeName,
      'source-id' : str(SourceID)
      })

  # Close an eventgroup
  def CloseEventGroup(self):
    self.CloseElement()

  # Open an event
  def OpenEvent(self):

    self.OpenElement("event")

  # Add a object to an event
  #
  #  PropertyName:    name of the event property
  #                   To allow easy searching, construct names in a hierarchial
  #                   fashion. A name like "communication-chat-message" is easier to
  #                   find than a name like "message".
  #  Value:           guess what
  #
  #    You can provide zero or more objects for every event property. So, omitting
  #    an object for one or more properties is allowed. Also, you can specify
  #    multiple objects that all have the same property. Note that it is not possible
  #    to indicate how these objects are related to each other, because they all
  #    have the same property.
  #
  #    NOTE: Timestamps MUST be given in the UTC!!

  def AddObject(self, PropertyName, Value):

      if ( isinstance(Value, str) or isinstance(Value, unicode) ) and len(Value) == 0:
        self.Warning("EDXMLWriter::AddObject: Object of property %s is empty. Object will be ignored.\n" % PropertyName)

      self.AddElement("object", {
        'property': PropertyName,
        'value'   : self.Escape(Value)
        })
        
  # Add text content to an event. Must be UTF8 encoded.
  def AddContent(self, Text):

    if len(Text) > 0:
      self.OpenElement('content')
      self.XMLGenerator.characters(self.Escape(Text))
      self.CloseElement()

  # Add a content translation to an event
  #
  #  Language:    2-character ISO 639-1 language code
  #  Interpreter: Name or alias of interpreter
  #  Text:        The translation

  def AddTranslation(self, Language, Interpreter, Text):

    if len(Text) > 0:
      self.OpenElement("translation", {'language': Language, 'interpreter': Interpreter})
      self.XMLGenerator.characters(self.Escape(Text))
      self.CloseElement()
    else:
      self.Warning("EDXMLWriter::AddTranslation: Empty content encountered. Content will be ignored!\n")

  # Close an event
  def CloseEvent(self):
    self.CloseElement()

  # Close eventgroups
  def CloseEventGroups(self):
    self.CloseElement()
    self.CloseElement()
    self.SaxParser.close()

