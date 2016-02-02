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

import sys, time
from xml.sax import make_parser
from edxml.EDXMLFilter import EDXMLEventEditor

# This is a wrapper to create an unbuffered
# version of sys.stdout.

class UnbufferedStdout(object):
   def __init__(self, Stream):
       self.Stream = Stream
   def write(self, Data):
       self.Stream.write(Data)
       self.Stream.flush()
   def __getattr__(self, Attr):
       return getattr(self.Stream, Attr)

# We create a class based on EDXMLEventEditor,
# overriding the EditEvent callback to inspect
# the event timestamps, wait a little and
# output the event.

class EDXMLReplay(EDXMLEventEditor):
  def __init__ (self, SpeedMultiplier, BufferStufferEnabled):

    self.TimeShift = None
    self.SpeedMultiplier = SpeedMultiplier
    self.BufferStufferEnabled = BufferStufferEnabled
    self.TimestampProperties = []
    self.KnownProperties = []

    # Create Sax parser
    self.SaxParser = make_parser()
    # Call parent class constructor
    EDXMLEventEditor.__init__(self, self.SaxParser, UnbufferedStdout(sys.stdout))
    # Set self as content handler
    self.SaxParser.setContentHandler(self)

  def EditEvent(self, SourceId, EventTypeName, EventObjects, EventContent, EventAttributes):

    Timestamps = []
    TimestampObjects = []
    NewEventObjects = []
    CurrentEventTimestamp = 0

    if self.BufferStufferEnabled:
      # Generate a 4K comment.
      print('<!-- ' + 'x' * 4096 +' -->')

    # Find all timestamps in event
    for Object in EventObjects:
      if not Object['property'] in self.KnownProperties:
        ObjectTypeName = self.Definitions.GetPropertyObjectType(EventTypeName, Object['property'])
        if self.Definitions.GetObjectTypeDataType(ObjectTypeName) == 'timestamp':
          self.TimestampProperties.append(Object['property'])
        self.KnownProperties.append(Object['property'])

      if Object['property'] in self.TimestampProperties:
        TimestampObjects.append(Object)
        Timestamps.append(float(Object['value']))
      else:
        # We copy all event objects, except
        # for the timestamps
        NewEventObjects.append(Object)

    if len(Timestamps) > 0:
      # We will use the smallest timestamp
      # as the event timestamp.
      CurrentEventTimestamp = min(Timestamps)
      if self.TimeShift:

        # Determine how much time remains before
        # the event should be output.
        Delay = CurrentEventTimestamp + self.TimeShift - time.time()
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
        self.TimeShift = time.time() - CurrentEventTimestamp

      # Now we add the timestamp objects, replacing
      # their values with the current time.
      for Object in TimestampObjects:
        NewEventObjects.append(
          {
            'property': Object['property'],
            'value': u'%.6f' % time.time()
          }
        )

    return NewEventObjects, EventContent, EventAttributes

def PrintHelp():

  print """

   This utility accepts EDXML data as input and writes the events to standard
   output, formatted in rows and columns. For every event property, a output
   column is generated. If one property has multiple objects, multiple  output
   lines are generated.

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

ReplayFilter = EDXMLReplay(SpeedMultiplier, BufferStufferEnabled)

# Now we feed EDXML data into the Sax parser from EDXMLReplay. This
# will trigger calls to ProcessEvent in our EDXMLReplay class, producing output.

if Input == sys.stdin:
  sys.stderr.write('Waiting for EDXML data on standard input... (use --help option to get help)\n')

ReplayFilter.SaxParser.parse(Input)
