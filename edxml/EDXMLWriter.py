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
from collections import deque
import sys

import edxml

from lxml import etree
from copy import deepcopy
from EDXMLBase import EDXMLBase, EvilCharacterFilter, EDXMLValidationError


class EDXMLWriter(EDXMLBase, EvilCharacterFilter):

    class OutputBuffer(object):
        """
        A buffer for collecting the output of the lxml xml writer.
        """

        def __init__(self):
            self.buffer = deque()

            self.mode = 'a'

        def write(self, data):
            # For some reason, lxml write regular strings rather than
            # unicode strings. We need to tell Python that it is
            # actually unicode data.
            self.buffer.append(unicode(data, encoding='utf-8'))

    """Class for generating EDXML streams

  The Output parameter is a file-like object that will be used to send the XML data to.
  This file-like object can be pretty much anything, as long as it has a write() method
  and a mode containing 'a' (opened for appending). When the Output parameter is omitted,
  the generated XML data will be returned by the methods that generate output.

  The optional Validate parameter controls if the generated EDXML stream should be auto-validated
  or not. Automatic validation is enabled by default.

  Args:
    Output (file, optional): File-like output object
    Validate (bool, optional): Enable output validation (True) or not (False)
    LogRepairedEvents (bool, optional): Log repaired events (True) or not (False)
  """

    def __init__(self, Output=None, Validate=True, LogRepairedEvents=False):

        super(EDXMLWriter, self).__init__()

        self._ontology = None
        self.__schema = None                 # type: etree.RelaxNG
        self.__eventTypeSchemaCache = {}     # type: Dict[str, etree.RelaxNG]
        self.__eventTypeSchema = None        # type: etree.RelaxNG
        self.__justWroteOntology = False
        self._log_repaired_events = LogRepairedEvents
        self.InvalidEvents = 0
        self.Validate = Validate
        self.Output = Output
        self.ElementStack = []
        self.CurrentEventTypeName = None
        self.CurrentEventSourceUri = None

        self._numEventsRepaired = 0
        self._numEventsProduced = 0

        if self.Output is None:
            # Create an output buffer to capture XML data
            self.Output = self.OutputBuffer()

        # Passing a file name as output will make lxml open the file, and it will open it with mode 'w'. Since
        # we use multiple lxml file writers to produce output, the output will be truncated mid stream. Therefore,
        # we only accept files and file-like objects as output, allowing us to verify if we can append to the file.
        if not hasattr(self.Output, 'write'):
            raise IOError(
                'The output of the EDXML writer does not look like an open file: ' + repr(self.Output))

        # If the output is not opened for appending,
        # we raise an error for the reason outlined above.
        if 'a' not in self.Output.mode:
            if self.Output == sys.stdout:
                # Unless the output is standard output, which cannot
                # be truncated. We make this exception because sys.stdout
                # object has mode 'w', which would normally qualify as unsafe.
                pass
            else:
                raise IOError(
                    'The mode attribute of the output of the EDXML writer must contain "a" (opened for appending).')

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
                self._ontology.GetEventType(
                    eventTypeName).generateRelaxNG(self._ontology)
            )
        return self.__eventTypeSchemaCache.get(eventTypeName)

    def __generateEventValidationException(self, event, eventElement):
        try:
            self._ontology.GetEventType(
                self.CurrentEventTypeName).validateEventStructure(event)

            # EventType structure checks out alright. Let us check the object values.
            self._ontology.GetEventType(
                self.CurrentEventTypeName).validateEventObjects(event)

            # EventType validation did not find the issue. We have
            # no other option than to raise a RelaxNG error containing
            # a undoubtedly cryptic error message.
            # TODO: In lxml 3.8, the error_log has a path attribute, which is an xpath
            # pointing to the exact location of the problem. Show that in the exception.
            raise EDXMLValidationError(
                self.__eventTypeSchema.error_log.last_error.message)

        except EDXMLValidationError as exception:
            self.InvalidEvents += 1
            raise EDXMLValidationError('An invalid event was produced:\n%s\n\nThe EDXML validator said: %s\n\n%s' % (
                etree.tostring(eventElement, pretty_print=True).encode(
                    'utf-8'), exception,
                'Note that this exception is not fatal. You can recover by catching the EDXMLValidationError '
                'and begin writing a new event.'), sys.exc_info()[2])

    def __OuterXMLSerialiserCoRoutine(self):
        """Coroutine which performs the actual XML serialisation"""
        with etree.xmlfile(self.Output, encoding='utf-8') as Writer:
            if 'flush' not in dir(Writer):
                raise Exception(
                    'The installed version of lxml is too old. Please install version >= 3.4.')
            Writer.write_declaration()
            with Writer.element('edxml', version='3.0.0'):
                Writer.flush()
                try:
                    while True:
                        # This is the main loop which generates eventgroups elements.
                        Element = (yield)
                        if Element is None:
                            # Sending None signals the end of the generation of
                            # the ontology element, and the beginning of the
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

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Args:
          edxmlOntology (edxml.ontology.Ontology): The ontology

        Returns:
          unicode: Generated output XML data

        """
        reOpenEventGroups = False
        prevEventTypeName = None
        prevEventSource = None

        if len(self.ElementStack) > 0:
            if self.ElementStack[-1] == 'eventgroup':
                prevEventTypeName = self.CurrentEventTypeName
                prevEventSource = self.CurrentEventSourceUri
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

        try:
            self.XMLWriter.send(edxmlOntology.GenerateXml())
        except StopIteration:
            # When the co-routine dropped out of its wrote loop while
            # processing data, the next attempt to send() anything
            # raises this exception.
            raise IOError('Failed to write EDXML data to output.')

        self.__eventTypeSchemaCache = {}
        self.__justWroteOntology = True

        if reOpenEventGroups:
            self.OpenEventGroups()
        if prevEventTypeName is not None and prevEventSource is not None:
            self.OpenEventGroup(prevEventTypeName, prevEventSource)

        if isinstance(self.Output, self.OutputBuffer):
            output = u''.join(self.Output.buffer)
            self.Output.buffer.clear()
            return output
        else:
            return u''

    def OpenEventGroups(self):
        """
        Opens the <eventgroups> element, containing all eventgroups

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Returns:
          unicode: Generated output XML data
        """
        if len(self.ElementStack) > 0:
            self.Error(
                'An <eventgroups> tag must be child of the <events> tag. Did you forget to call CloseDefinitions()?')

        if not self.__justWroteOntology:
            self.Error(
                'Attempt to output an eventgroups element without a preceding ontology element.')
        self.__justWroteOntology = False

        # We send None to the outer XML generator, to
        # hint it that the ontology element has been
        # completed and we want it to generate the
        # eventgroups opening tag.
        try:
            self.XMLWriter.send(None)
        except StopIteration:
            # When the co-routine dropped out of its wrote loop while
            # processing data, the next attempt to send() anything
            # raises this exception.
            raise IOError('Failed to write EDXML data to output.')

        self.ElementStack.append('eventgroups')

        if isinstance(self.Output, self.OutputBuffer):
            output = u''.join(self.Output.buffer)
            self.Output.buffer.clear()
            return output
        else:
            return u''

    def OpenEventGroup(self, EventTypeName, SourceUri):
        """
        Opens an event group.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Args:
          EventTypeName (str): Name of the eventtype
          SourceUri (str): EDXML event source URI

        Returns:
          unicode: Generated output XML data

        """

        if len(self.ElementStack) == 0:
            self.OpenEventGroups()
        self.ElementStack.append('eventgroup')

        if self._ontology.GetEventType(EventTypeName) is None:
            raise EDXMLValidationError(
                'Attempt to open an event group using unknown event type: "%s"' % EventTypeName)
        if self._ontology.GetEventSource(SourceUri) is None:
            raise EDXMLValidationError(
                'Attempt to open an event group using unknown source URI: "%s"' % SourceUri)

        self.CurrentEventTypeName = EventTypeName
        self.CurrentEventSourceUri = SourceUri

        if self.Validate:
            self.__eventTypeSchema = self.getEventTypeSchema(
                self.CurrentEventTypeName)

        self.EventGroupXMLWriter = self.__InnerXMLSerialiserCoRoutine(
            self.CurrentEventTypeName, SourceUri)
        self.EventGroupXMLWriter.next()

        if isinstance(self.Output, self.OutputBuffer):
            output = u''.join(self.Output.buffer)
            self.Output.buffer.clear()
            return output
        else:
            return u''

    def Close(self):
        """

        Finalizes the output data stream.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Returns:
          unicode: Generated output XML data
        """
        if self.__justWroteOntology:
            # EDXML data streams must contain sequences of pairs of
            # an <ontology> element followed by an <eventgroups>
            # element. Apparently, we just wrote an <ontology>
            # element, so we must open a new eventgroups tag.
            self.OpenEventGroups()
        if len(self.ElementStack) > 0 and self.ElementStack[-1] == 'eventgroup':
            self.CloseEventGroup()
        if len(self.ElementStack) > 0 and self.ElementStack[-1] == 'eventgroups':
            self.CloseEventGroups()
        self.XMLWriter.close()

        if self._numEventsProduced > 0 and (100 * self._numEventsRepaired) / self._numEventsProduced > 10:
            sys.stderr.write(
                'WARNING: %d out of %d events were automatically repaired because they were invalid. '
                'If performance is important, verify your event generator code to produce valid events.\n' %
                (self._numEventsRepaired, self._numEventsProduced)
            )

        if isinstance(self.Output, self.OutputBuffer):
            output = u''.join(self.Output.buffer)
            self.Output.buffer.clear()
            return output
        else:
            return u''

    def CloseEventGroup(self):
        """

        Closes a previously opened event group.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Returns:
          unicode: Generated output XML data
        """
        if self.ElementStack[-1] != 'eventgroup':
            self.Error(
                'Unbalanced <eventgroup> tag. Did you forget to call CloseEvent()?')
        self.ElementStack.pop()

        # This closes the generator, writing the closing eventgroup tag.
        self.EventGroupXMLWriter.close()

        if isinstance(self.Output, self.OutputBuffer):
            output = u''.join(self.Output.buffer)
            self.Output.buffer.clear()
            return output
        else:
            return u''

    def AddEvent(self, event):
        """

        Adds specified event to the output data stream.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Args:
          event (edxml.EDXMLEvent): The event

        Returns:
          unicode: Generated output XML data

        """
        if self.ElementStack[-1] != 'eventgroup':
            self.Error(
                'A <event> tag must be child of an <eventgroup> tag. Did you forget to call OpenEventGroup()?')

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
                # Event does not validate.
                try:
                    # Try to repair the event by normalizing the object
                    # values.
                    if self._log_repaired_events:
                        originalEvent = deepcopy(event)
                        self._ontology.GetEventType(
                            self.CurrentEventTypeName).normalizeEventObjects(event)
                        for propertyName in originalEvent.keys():
                            if event[propertyName] != originalEvent[propertyName]:
                                sys.stderr.write(
                                    'Repaired invalid property %s of event type %s: %s => %s\n' %
                                    (propertyName, self.CurrentEventTypeName, repr(
                                        originalEvent[propertyName]), repr(event[propertyName]))
                                )
                    else:
                        self._ontology.GetEventType(
                            self.CurrentEventTypeName).normalizeEventObjects(event)

                except EDXMLValidationError:
                    # Repairing failed.
                    self.__generateEventValidationException(
                        event, eventElement)
                else:
                    # Repairing succeeded. For the time being, just to be sure,
                    # we validate the event again.
                    # TODO: Remove this second validation once normalizeEventObjects()
                    # is known to yield valid object values in all cases.
                    if not self.__eventTypeSchema.validate(eventElement):
                        self.__generateEventValidationException(
                            event, eventElement)
                    self._numEventsRepaired += 1

        try:
            self.EventGroupXMLWriter.send(eventElement)
        except StopIteration:
            # When the co-routine dropped out of its wrote loop while
            # processing data, the next attempt to send() anything
            # raises this exception.
            raise IOError('Failed to write EDXML data to output.')

        self._numEventsProduced += 1

        if isinstance(self.Output, self.OutputBuffer):
            output = u''.join(self.Output.buffer)
            self.Output.buffer.clear()
            return output
        else:
            return u''

    def CloseEventGroups(self):
        """

        Closes a previously opened <eventgroups> element.

        If no output was specified while instantiating this class,
        the generated XML data will be returned as unicode string.

        Returns:
          unicode: Generated output XML data

        """
        if self.ElementStack[-1] != 'eventgroups':
            self.Error(
                'Unbalanced <eventgroups> tag. Did you forget to call CloseEventGroup()?')
        self.ElementStack.pop()
        # We send None to the outer XML generator, to
        # hint it that the eventgroups element has been
        # completed and we want it to generate the
        # eventgroups closing tag.
        try:
            self.XMLWriter.send(None)
        except StopIteration:
            # When the co-routine dropped out of its wrote loop while
            # processing data, the next attempt to send() anything
            # raises this exception.
            raise IOError('Failed to write EDXML data to output.')

        if isinstance(self.Output, self.OutputBuffer):
            output = u''.join(self.Output.buffer)
            self.Output.buffer.clear()
            return output
        else:
            return u''
