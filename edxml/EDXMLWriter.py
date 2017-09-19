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

from lxml import etree
from typing import Dict

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

    self._ontology = None
    self.__schema = None                 # type: etree.RelaxNG
    self.__eventTypeSchemaCache = {}     # type: Dict[str, etree.RelaxNG]
    self.__eventTypeSchema = None        # type: etree.RelaxNG
    self.__justWroteOntology = False
    self.InvalidEvents = 0
    self.Validate = Validate
    self.Output = Output
    self.ElementStack = []
    self.CurrentEventTypeName = None
    self.CurrentEventSourceUri = None

    # Since we use multiple lxml file writers to produce output, passing a file name
    # as output will truncate the output while writing data. Therefore, we only accept
    # files, file-like objects as output.
    if 'write' not in dir(self.Output):
      raise IOError('The output of the EDXML writer does not look like an open file: ' + repr(self.Output))

    # The lxml file writer will raise rather cryptic exceptions when the output is
    # open file that is opened for reading, which is the default in Python. Check
    # and raise an exception if needed.
    if 'w' not in self.Output.mode and 'a' not in self.Output.mode:
      raise IOError('The output of the EDXML writer does not appear to be writable.')

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

  def getEventTypeSchema(self, eventTypeName):
    if eventTypeName not in self.__eventTypeSchemaCache:
      self.__eventTypeSchemaCache[eventTypeName] = etree.RelaxNG(
        self._ontology.GetEventType(eventTypeName).generateRelaxNG(self._ontology)
      )
    return self.__eventTypeSchemaCache.get(eventTypeName)

  def __OuterXMLSerialiserCoRoutine(self):
    """Coroutine which performs the actual XML serialisation"""
    with etree.xmlfile(self.Output, encoding='utf-8') as Writer:
      if not 'flush' in dir(Writer):
        raise Exception('The installed version of lxml is too old. Please install version >= 3.4.')
      Writer.write_declaration()
      with Writer.element('events'):
        Writer.flush()
        try:
          while True:
            # This is the main loop which generates eventgroups elements.
            Element = (yield)
            if Element is None:
              # Sending None signals the end of the generation of
              # the definitions element, and the beginning of the
              # eventgroups element.
              with Writer.element('eventgroups'):
                Writer.flush()
                while True:
                  Element = (yield)
                  if Element is None:
                    # Sending None signals the end of the generation of
                    # the eventgroups element. We break out of the loop,
                    # causing the context manager to write the closing
                    # tag of the eventgroups element. We then fall back
                    # into the outer while loop.
                    break
                  Writer.write(Element, pretty_print=True)
                  Writer.flush()
            else:
              Writer.write(Element, pretty_print=True)
              Writer.flush()
        except GeneratorExit:
          pass

  def __InnerXMLSerialiserCoRoutine(self, EventTypeName, EventSourceUri):
    """Coroutine which performs the actual XML serialisation of eventgroups"""
    with etree.xmlfile(self.Output, encoding='utf-8') as Writer:
      with Writer.element('eventgroup', **{'event-type': EventTypeName, 'source-uri': EventSourceUri}):
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

    Writes an EDXML ontology element into the output. This method
    may be called at any point in the EDXML generation process, it
    will automatically close and reopen the current eventgroup and
    eventgroups elements if necessary.

    Args:
      edxmlOntology (edxml.ontology.Ontology): The ontology

    Returns:
      EDXMLWriter: The writer

    """
    reOpenEventGroups = False
    prevEventTypeName = None
    prevEventSource = None

    if len(self.ElementStack) > 0:
      if self.ElementStack[-1] == 'eventgroup':
        prevEventTypeName = self.CurrentEventTypeName
        prevEventSource   = self.CurrentEventSourceUri
        self.CloseEventGroup()

    if len(self.ElementStack) > 0:
      if self.ElementStack[-1] == 'eventgroups':
        reOpenEventGroups = True
        self.CloseEventGroups()

    if self._ontology is None:
      self._ontology = edxmlOntology.Validate()
    else:
      # We update our existing ontology, to make sure
      # that both are compatible.
      self._ontology.Update(edxmlOntology)

    self.XMLWriter.send(edxmlOntology.GenerateXml())
    self.__eventTypeSchemaCache = {}

    if reOpenEventGroups:
      self.OpenEventGroups()
    if prevEventTypeName is not None and prevEventSource is not None:
      self.OpenEventGroup(prevEventTypeName, prevEventSource)

    self.__justWroteOntology = True

    return self

  def OpenEventGroups(self):
    """Opens the <eventgroups> section, containing all eventgroups"""
    if len(self.ElementStack) > 0: self.Error('An <eventgroups> tag must be child of the <events> tag. Did you forget to call CloseDefinitions()?')

    if not self.__justWroteOntology:
      self.Error('Attempt to output an eventgroups element without a preceding definitions element.')
    self.__justWroteOntology = False

    # We send None to the outer XML generator, to
    # hint it that the definitions element has been
    # completed and we want it to generate the
    # eventgroups opening tag.
    self.XMLWriter.send(None)

    self.ElementStack.append('eventgroups')

  def OpenEventGroup(self, EventTypeName, SourceUri):
    """Opens an event group.

    Args:
      EventTypeName (str): Name of the eventtype

      SourceUri (str): EDXML event source URI

    """

    if len(self.ElementStack) == 0:
      self.OpenEventGroups()
    self.ElementStack.append('eventgroup')

    if self._ontology.GetEventType(EventTypeName) is None:
      raise EDXMLValidationError('Attempt to open an event group using unknown event type: "%s"' % EventTypeName)
    if self._ontology.GetEventSource(SourceUri) is None:
      raise EDXMLValidationError('Attempt to open an event group using unknown source URI: "%s"' % SourceUri)

    self.CurrentEventTypeName = EventTypeName
    self.CurrentEventSourceUri = SourceUri

    if self.Validate:
      self.__eventTypeSchema = self.getEventTypeSchema(self.CurrentEventTypeName)

    self.EventGroupXMLWriter = self.__InnerXMLSerialiserCoRoutine(self.CurrentEventTypeName, SourceUri)
    self.EventGroupXMLWriter.next()

  def Close(self):
    if len(self.ElementStack) > 0 and self.ElementStack[-1] == 'eventgroup':
      self.CloseEventGroup()
    if len(self.ElementStack) > 0 and self.ElementStack[-1] == 'eventgroups':
      self.CloseEventGroups()
    self.XMLWriter.close()

  def CloseEventGroup(self):
    """Closes a previously opened event group"""
    if self.ElementStack[-1] != 'eventgroup': self.Error('Unbalanced <eventgroup> tag. Did you forget to call CloseEvent()?')
    self.ElementStack.pop()

    # This closes the generator, writing the closing eventgroup tag.
    self.EventGroupXMLWriter.close()

  def AddEvent(self, event):
    """

    Args:
      event (edxml.EDXMLEvent): The event

    Returns:
      EDXMLWriter:

    """
    if self.ElementStack[-1] != 'eventgroup':
      self.Error('A <event> tag must be child of an <eventgroup> tag. Did you forget to call OpenEventGroup()?')

    if isinstance(event, etree._Element):
      eventElement = event
    elif isinstance(event, edxml.EDXMLEvent):
      event = edxml.EventElement(
        event.GetProperties(), Parents=event.GetExplicitParents(), Content=event.GetContent()
      )
      eventElement = event.element
    elif isinstance(event, edxml.EventElement):
      eventElement = event.element
    else:
      raise TypeError('Unknown type of event: %s' % str(type(event)))

    if self.Validate:
      if not self.__eventTypeSchema.validate(eventElement):
        # Event does not validate. Try to generate a validation
        # exception that is more readable than the RelaxNG
        # error is, by validating using the EventType class.
        try:
          self._ontology.GetEventType(self.CurrentEventTypeName).validateEventStructure(event)

          # EventType structure checks out alright. Let us check the object values.
          self._ontology.GetEventType(self.CurrentEventTypeName).validateEventObjects(event)

          # EventType validation did not find the issue. We have
          # no other option than to raise a RelaxNG error containing
          # a undoubtedly cryptic error message.
          raise EDXMLValidationError(self.__eventTypeSchema.error_log.last_error.message)

        except EDXMLValidationError as exception:
          self.InvalidEvents += 1
          raise EDXMLValidationError, 'An invalid event was produced:\n%s\n\nThe EDXML validator said: %s\n\n%s' % (
            etree.tostring(eventElement, pretty_print=True).encode('utf-8'), exception,
            'Note that this exception is not fatal. You can recover by catching the EDXMLValidationError '
            'and begin writing a new event.'), sys.exc_info()[2]

    self.EventGroupXMLWriter.send(eventElement)

    return self

  def CloseEventGroups(self):
    """Closes a previously opened <eventgroups> section"""
    if self.ElementStack[-1] != 'eventgroups': self.Error('Unbalanced <eventgroups> tag. Did you forget to call CloseEventGroup()?')
    self.ElementStack.pop()
    # We send None to the outer XML generator, to
    # hint it that the eventgroups element has been
    # completed and we want it to generate the
    # eventgroups closing tag.
    self.XMLWriter.send(None)
