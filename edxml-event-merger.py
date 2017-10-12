#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                            EDXML Event Merger
#
#                            EXAMPLE APPLICATION
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
#  This script reads an EDXML stream from standard input or from a file and outputs
#  that same stream after resolving event hash collisions in the input. Every time an
#  input event collides with a preceding event, the event will be merged and an updated
#  version is output. That means that the number of output events equals the number of
#  input events.
#
#  Note that, unless buffering is used, this script needs to store one event for each
#  sticky hash of the input events in RAM. For large event streams that contain events
#  with many different sticky hashes, it will eventually run out of memory. Extending
#  this example to use an external storage backend in order to overcome this limitation
#  is left as an exercise to the user.

import sys
import time
from edxml.EDXMLFilter import EDXMLPullFilter, EDXMLPushFilter


class EDXMLEventMerger(EDXMLPullFilter):

  def __init__(self):

    super(EDXMLEventMerger, self).__init__(sys.stdout)
    self.HashBuffer = {}

  def _parsedEvent(self, edxmlEvent):

    Hash = edxmlEvent.ComputeStickyHash(self.getOntology())

    if Hash in self.HashBuffer:
      edxmlEvent.MergeWith([self.HashBuffer[Hash]], self.getOntology())

    self.HashBuffer[Hash] = edxmlEvent

    EDXMLPullFilter._parsedEvent(self, edxmlEvent)


class BufferingEDXMLEventMerger(EDXMLPushFilter):

  def __init__(self, EventBufferSize, Latency):

    super(BufferingEDXMLEventMerger, self).__init__(sys.stdout)
    self.BufferSize = 0
    self.MaxLatency = Latency
    self.MaxBufferSize = EventBufferSize
    self.LastOutputTime = time.time()
    self.HashBuffer = {}

  def _closeEventGroup(self, eventTypeName, eventSourceId):

    self._flushBuffer()

    EDXMLPushFilter._closeEventGroup(self, eventTypeName, eventSourceId)

  def _parsedEvent(self, edxmlEvent):

    Hash = edxmlEvent.ComputeStickyHash(self.getOntology())

    if Hash in self.HashBuffer:
      # This hash is in our buffer, which means
      # we have a collision. Add the event for
      # merging later.
      self.HashBuffer[Hash].append(edxmlEvent)
    else:
      # We have a new hash, add it to
      # the buffer.
      self.HashBuffer[Hash] = [edxmlEvent]

    self.BufferSize += 1
    if self.BufferSize >= self.MaxBufferSize:
      self._flushBuffer()

    if self.BufferSize > 0 and 0 < self.MaxLatency <= (time.time() - self.LastOutputTime):
      self._flushBuffer()

  def _flushBuffer(self):
    for eventHash, events in self.HashBuffer.iteritems():
      if len(events) > 1:
        outputEvent = events.pop()
        outputEvent.MergeWith(events, self.getOntology())
        self._writer.AddEvent(outputEvent)

    self.BufferSize = 0
    self.LastOutputTime = time.time()
    self.Buffer = {}


def PrintHelp():

  print """

   This utility reads an EDXML stream from standard input or from a file and outputs
   that same stream after resolving event hash collisions in the input.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. If this option is not specified,
                       input will be read from standard input.

     -b                By default, input events are not buffered, which means that
                       every input event is either passed through unmodified or
                       results in a merged version of input event. By setting this
                       option to a positive integer, the specified number of input
                       events will be buffed and merged when the buffer is full. That
                       means that, depending on the buffer size, the number of output
                       events may be significantly reduced.

     -l                When input events are buffered, input event streams having low
                       event throughput may result in output streams that stay silent
                       for a long time. Setting this option to a number of (fractional)
                       seconds, the output latency can be controlled, forcing it to
                       flush its buffer at regular intervals.
   Example:

     edxml-event-merger.py -b 1000 -l 10 -f input.edxml > output.edxml

"""

CurrOption = 1
BufferSize = 1
OutputLatency = 0
InputFileName = None

while CurrOption < len(sys.argv):

  if sys.argv[CurrOption] in ('-h', '--help'):
    PrintHelp()
    sys.exit(0)

  elif sys.argv[CurrOption] == '-f':
    CurrOption += 1
    InputFileName = sys.argv[CurrOption]

  elif sys.argv[CurrOption] == '-b':
    CurrOption += 1
    BufferSize = int(sys.argv[CurrOption])

  elif sys.argv[CurrOption] == '-l':
    CurrOption += 1
    OutputLatency = float(sys.argv[CurrOption])

  else:
    sys.stderr.write("Unknown commandline argument: %s\n" % sys.argv[CurrOption])
    sys.exit()

  CurrOption += 1

if InputFileName is None:
  sys.stderr.write("\nNo filename was given, waiting for EDXML data on STDIN...(use --help to get help)")
  Input = sys.stdin
else:
  sys.stderr.write("\nProcessing file %s:" % InputFileName )
  Input = open(InputFileName)

sys.stdout.flush()

if BufferSize > 1:
  # We need to read input with minimal
  # input buffering. This works best
  # when using the readline() method.
  with BufferingEDXMLEventMerger(BufferSize, OutputLatency) as Merger:
    try:
      while 1:
        Line = Input.readline()
        if not Line:
          break
        Merger.feed(Line)
    except KeyboardInterrupt:
      sys.exit()
else:
  with EDXMLEventMerger() as Merger:
    try:
      Merger.parse(open('demo.edxml'))
    except KeyboardInterrupt:
      sys.exit()
