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
from StringIO import StringIO

from lxml import etree
from lxml.etree import SerialisationError

import EDXMLParser
import edxml
from EDXMLBase import *


class EDXMLWriter(EDXMLBase, EvilCharacterFilter):
  """Class for generating EDXML streams

  The Output parameter is a file-like object
  that will be used to send the XML data to.
  This file-like object can be pretty much 
  anything, as long as it has a write() method.

  The optional Validate parameter controls if
  the generated EDXML stream should be auto-validated
  or not. Automatic validation is enabled by default.

  Args:
    Output (file): File-like output object
    Validate (bool, optional): Enable output validation (True) or not (False)
  """
  def __init__(self, Output, Validate=True):

    super(EDXMLWriter, self).__init__()

    self.InvalidEvents = 0
    self.Validate = Validate
    self.Output = Output
    self.ElementStack = []
    self.EDXMLParser = None  # type: EDXMLParser.EDXMLPushParser
    self.Bridge = None       # type: EDXMLWriter.XMLParserBridge

    if self.Validate:

      # Construct validating EDXML parser
      self.EDXMLParser = EDXMLParser.EDXMLPushParser(Validate)

      # Construct a bridge that will be used to connect the
      # output of the XML Generator to the parser / validator.
      # We use the Bridge to output the XML to, so we have built
      # a chain that automatically validates the EDXML stream while
      # it is being generated. The full chain looks like this:
      #
      # lxml.etree generator => EDXMLParser => Output

      self.Bridge = EDXMLWriter.XMLParserBridge(self.EDXMLParser, Output)  # type: EDXMLWriter.XMLParserBridge

    else:

      # Validation is disabled. 
      self.Bridge = Output       # type: EDXMLWriter.XMLParserBridge
      self.EDXMLParser = None

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

  # The XML parser bridge connects the XML generator to
  # the XML parser for validating the output. Also, it buffers
  # output until the output is known to be valid. This helper
  # class acts like a file object, passing through to a validator.

  class XMLParserBridge(object):

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
        except Exception:
          # We catch parsing exceptions here, because lxml does
          # not handle them correctly: When the file-like object
          # that it writes into raises an exception, it will initially
          # ignore it. On the next write attempt, a generic IO error
          # is raised, which means that the information about the
          # original exception is lost. So, we store the original
          # exception here to allow EDXMLWriter to check for it and
          # raise a proper, informative exception.
          self.ParseError = sys.exc_info()
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

  def AddOntology(self, edxmlOntology):
    """

    Writes an EDXML ontology element into the output.

    Args:
      edxmlOntology (edxml.ontology.Ontology): The ontology

    Returns:
      EDXMLWriter: The writer

    """
    if len(self.ElementStack) > 0:
      raise EDXMLValidationError(
        'A <definitions> tag must be child of the <events> tag. Did you forget to call CloseEventGroups()?'
      )

    self.XMLWriter.send(edxmlOntology.GenerateXml())

    return self

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
        raise self.Bridge.ParseError[0], self.Bridge.ParseError[1], self.Bridge.ParseError[2]

  def Close(self):
    if len(self.ElementStack) > 0 and self.ElementStack[-1] == 'eventgroup':
      self.CloseEventGroup()
    if len(self.ElementStack) > 0 and self.ElementStack[-1] == 'eventgroups':
      self.CloseEventGroups()

  def CloseEventGroup(self):
    """Closes a previously opened event group"""
    if self.ElementStack[-1] != 'eventgroup': self.Error('Unbalanced <eventgroup> tag. Did you forget to call CloseEvent()?')
    self.ElementStack.pop()

    # This closes the generator, writing the closing eventgroup tag.
    self.EventGroupXMLWriter.close()

  def AddEvent(self, event):
    """

    Args:
      event (edxml.EDXMLEvent.EDXMLEvent): The event

    Returns:
      EDXMLWriter:

    """
    if self.ElementStack[-1] != 'eventgroup':
      self.Error('A <event> tag must be child of an <eventgroup> tag. Did you forget to call OpenEventGroup()?')

    if isinstance(event, edxml.EventElement):
      event = event.element
    if not isinstance(event, etree._Element):
      event = edxml.EventElement(
        event.GetProperties(), Parents=event.GetExplicitParents(), Content=event.GetContent()
      ).element

    if self.Validate:
      # We enable buffering at this point, until we know
      # for certain that the event is valid. If the event
      # turns out to be invalid, the application can continue
      # generating the EDXML stream, skipping the invalid event.
      self.Bridge.ParseError = None
      self.Bridge.EnableBuffering()

    # Send element to co-routine, which will use lxml.etree
    # to write the event.
    try:
      self.EventGroupXMLWriter.send(event)
    except SerialisationError:
      if self.Bridge.ParseError:
        # We will handle this below.
        pass
      else:
        # TODO: Occasionally, it still happens that for instance a
        # keyboard interrupt yields a SerialisationError here, without
        # saving the original exception in self.Bridge.ParseError.
        # Figure out why these exceptions are not caught.
        raise

    if self.Validate and self.Bridge.ParseError is not None:
      self.RecoverInvalidEvent()
      self.InvalidEvents += 1

      InvalidEventException = self.Bridge.ParseError
      self.Bridge.ParseError = None
      if InvalidEventException[0] == EDXMLValidationError:
        Message = (
          'An invalid event was produced. The EDXML validator said: %s.\nNote that this exception is not fatal. '
          'You can recover by catching the EDXMLValidationError and begin writing a new event.'
        ) % InvalidEventException[1]
      else:
        Message = InvalidEventException[1]

      raise InvalidEventException[0], Message, InvalidEventException[2]

    if self.Validate:
      # At this point, the event has been validated. We disable
      # buffering, which pushes it to the output.
      self.Bridge.DisableBuffering()

    return self

  def RecoverInvalidEvent(self):
    # Ok, the EDXMLParser instance that handles the content
    # from the SAX parser has borked on an invalid event.
    # This means that the SAX parser cannot continue. We
    # have no other choice than rebuild the data processing
    # chain from scratch and restore the state of both the
    # EDXMLParser instance and XML Generator to the point
    # where it can output events again.

    DefinitionsBackup = StringIO()
    EDXMLWriter(DefinitionsBackup, False).AddOntology(self.EDXMLParser.getOntology())

    # Create new SAX parser and validating EDXML parser
    self.EDXMLParser = EDXMLParser.EDXMLPushParser()

    # Replace the parser in the bridge
    self.Bridge.ReplaceParser(self.EDXMLParser)

    # We need to push some XML into the XMLGenerator and into
    # the bridge, but we do not want that to end up in the
    # output. So, we enable buffering and clear the buffer later.
    self.Bridge.EnableBuffering()

    # Push the EDXML definitions header into the bridge, which
    # will restore the state of the EDXMLParser instance.
    self.Bridge.write('%s<eventgroups>' % DefinitionsBackup.getvalue())

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

    if self.EDXMLParser:
      # This triggers well-formedness validation
      # if validation is enabled.
      self.EDXMLParser._close()

