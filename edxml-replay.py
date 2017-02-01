#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                         EDXML time shifting utility
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
# 
#  This script accepts EDXML data as input and writes time shifted events to standard
#  output. Timestamps of input events are shifted to the current time. This is useful
#  for simulating live EDXML data sources using previously recorded data. Note that
#  the script assumes that the events in the input stream are time ordered.

import sys
import time
from datetime import datetime

import pytz
from dateutil.parser import parse

from edxml.EDXMLFilter import EDXMLPullFilter
from edxml.ontology import DataType


class EDXMLReplay(EDXMLPullFilter):

  class UnbufferedStdout(object):
    # This is a wrapper to create an unbuffered
    # version of sys.stdout.
    def __init__(self, Stream):
      self.Stream = Stream

    def write(self, Data):
      self.Stream.write(Data)
      self.Stream.flush()

    def __getattr__(self, Attr):
      return getattr(self.Stream, Attr)

  def __init__(self, SpeedMultiplier, BufferStufferEnabled):

    self.TimeShift = None
    self.SpeedMultiplier = SpeedMultiplier
    self.BufferStufferEnabled = BufferStufferEnabled
    self.DateTimeProperties = []
    self.KnownProperties = []
    self.CurrentEventTypeName = None

    # Call parent class constructor
    super(EDXMLReplay, self).__init__(EDXMLReplay.UnbufferedStdout(sys.stdout))

  def _openEventGroup(self, eventTypeName, eventSourceUri):
    self.CurrentEventTypeName = eventTypeName
    EDXMLPullFilter._openEventGroup(self, eventTypeName, eventSourceUri)

  def _parsedEvent(self, edxmlEvent):

    DateTimeStrings = []
    DateTimeObjects = []
    NewEventObjects = []

    if self.BufferStufferEnabled:
      # Generate a 4K comment.
      print('<!-- ' + 'x' * 4096 + ' -->')

    # Find all timestamps in event
    for PropertyName, Objects in edxmlEvent.GetProperties().items():
      if PropertyName not in self.KnownProperties:
        if str(self._ontology.GetEventType(self.CurrentEventTypeName)[PropertyName].GetDataType()) == 'datetime':
          self.DateTimeProperties.append(PropertyName)
        self.KnownProperties.append(PropertyName)

      if PropertyName in self.DateTimeProperties:
        DateTimeObjects.append((PropertyName, Objects))
        DateTimeStrings.extend(Objects)
      else:
        # We copy all event objects, except
        # for the timestamps
        NewEventObjects.extend(Objects)

    if len(DateTimeStrings) > 0:
      # We will use the smallest timestamp
      # as the event timestamp. Note that we
      # use lexicographical ordering here.
      CurrentEventDateTime = parse(min(DateTimeStrings))
      if self.TimeShift:

        # Determine how much time remains before
        # the event should be output.
        Delay = (CurrentEventDateTime - datetime.now(pytz.UTC)).total_seconds() + self.TimeShift
        if Delay >= 0:
          time.sleep(Delay * SpeedMultiplier)

          # If SpeedMultiplier < 1, it means we will wait shorter
          # than the time between current and previous event. That
          # means that the next event will be farther away in the
          # future, and require longer delays. All delays that we
          # skip due to the SpeedMultiplier will add up, event output
          # speed will drop. To compensate for this effect, we also
          # shift the entire dataset back in time. If SpeedMultiplier
          # is larger than 1, the opposite effect occurs.
          self.TimeShift += (SpeedMultiplier - 1.0) * Delay
      else:
        # Determine the global time shift between
        # the input dataset and the current time.
        self.TimeShift = (datetime.now(pytz.UTC) - CurrentEventDateTime).total_seconds()

      # Now we add the timestamp objects, replacing
      # their values with the current time.
      for PropertyName, Objects in DateTimeObjects:
        edxmlEvent[PropertyName] = [DataType.FormatUtcDateTime(datetime.now(tz=pytz.utc)) for Object in Objects]

    EDXMLPullFilter._parsedEvent(self, edxmlEvent)


def PrintHelp():

  print """

   This script accepts EDXML data as input and writes time shifted events to standard
   output. Timestamps of input events are shifted to the current time. This is useful
   for simulating live EDXML data sources using previously recorded data. Note that
   the script assumes that the events in the input stream are time ordered.

   Options:

     -h, --help       Prints this help text

     -f               Used to specify an input EDXML file. If omitted, EDXML data
                      is expected on standard input.

     -s               Optional speed multiplier. A value greater than 1.0 will make
                      time appear to pass faster, a value smaller than 1.0 slows down
                      event output. Default value is 1.0.

     -b               Enable the "Buffer Stuffer", which inserts bogus comments between
                      the output events. Some applications may buffer their input, resulting
                      in high response latency when feeding them with events at very low rates.
                      This option may help to "write through" their input buffer.

   Example:

     cat data.edxml | edxml-replay.py -s 10

"""

Input = sys.stdin
SpeedMultiplier = 1.0
CurrOption = 1
BufferStufferEnabled = False

while CurrOption < len(sys.argv):

  if sys.argv[CurrOption] in ('-h', '--help'):
    PrintHelp()
    sys.exit(0)

  elif sys.argv[CurrOption] == '-f':
    CurrOption += 1
    Input = open(sys.argv[CurrOption])

  elif sys.argv[CurrOption] == '-s':
    CurrOption += 1
    SpeedMultiplier = 1.0 / (1e-9 + float(sys.argv[CurrOption]))

  elif sys.argv[CurrOption] == '-b':
    BufferStufferEnabled = True

  else:
    sys.stderr.write("Unknown commandline argument: %s\n" % sys.argv[CurrOption])
    sys.exit()

  CurrOption += 1

if Input == sys.stdin:
  sys.stderr.write('Waiting for EDXML data on standard input... (use --help option to get help)\n')

with EDXMLReplay(SpeedMultiplier, BufferStufferEnabled) as Replay:
  try:
    Replay.parse(Input)
  except KeyboardInterrupt:
    sys.exit()
