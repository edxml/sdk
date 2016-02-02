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
#  Note that this script needs to store one event for each sticky hash of  the input
#  events in RAM. For large event streams that contain events with many different
#  sticky hashes, it will eventually run out of memory. Extending this example to use
#  a storage backend in order to overcome this limitation is left as an exercise to
#  the user.

import sys
from xml.sax import make_parser
from edxml.EDXMLFilter import EDXMLEventEditor

# We create a class based on EDXMLEventEditor,
# overriding the EditEvent to process
# the events in the EDXML stream.

class EDXMLEventMerger(EDXMLEventEditor):

  def __init__ (self, upstream):

    EDXMLEventEditor.__init__(self, upstream)
    self.HashBuffer = {}

  # Override of EDXMLEventEditor implementation
  def EditEvent(self, SourceId, EventTypeName, EventObjects, EventContent, EventAttributes):

    # Use the EDXMLDefinitions instance in the 
    # EDXMLEventEditor class to compute the sticky hash
    Hash = self.Definitions.ComputeStickyHash(EventTypeName, EventObjects, EventContent)

    Properties = [Object['property'] for Object in EventObjects]
    EventProperties = {Property: [Object['value'] for Object in EventObjects if Object['property'] == Property] for Property in Properties}

    if Hash in self.HashBuffer:
      self.Definitions.MergeEvents(EventTypeName, self.HashBuffer[Hash]['Objects'], EventProperties)

      EventObjects = []
      for Property, Values in self.HashBuffer[Hash]['Objects'].items():
        for Value in Values:
          EventObjects.append({'property': Property, 'value': Value})
    else:
      self.HashBuffer[Hash] = {
        'Objects': EventProperties
      }

    return EventObjects, EventContent, EventAttributes

def PrintHelp():

  print """

   This utility reads an EDXML stream from standard input or from a file and outputs
   that same stream after resolving event hash collisions in the input. Every time an
   input event collides with a preceding event, the event will be merged and an updated
   version is output. That means that the number of output events equals the number of
   input events.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. If this option is not specified,
                       input will be read from standard input.

   Example:

     edxml-event-merger.py -f input.edxml > output.edxml

"""

CurrOption = 1
InputFileName = None

while CurrOption < len(sys.argv):

  if sys.argv[CurrOption] in ('-h', '--help'):
    PrintHelp()
    sys.exit(0)

  elif sys.argv[CurrOption] == '-f':
    CurrOption += 1
    InputFileName = sys.argv[CurrOption]

  else:
    sys.stderr.write("Unknown commandline argument: %s\n" % sys.argv[CurrOption])
    sys.exit()

  CurrOption += 1

# Create a SAX parser, and provide it with
# an EDXMLEventMerger instance as content handler.
# This places the EDXMLEventMerger instance in the
# XML processing chain, just after SaxParser.

SaxParser = make_parser()
SaxParser.setContentHandler(EDXMLEventMerger(SaxParser))

# Now we feed EDXML data into the Sax parser. This will trigger
# calls to ProcessEvent in our EDXMLEventMerger, producing output.

if InputFileName == None:
  sys.stderr.write("\nNo filename was given, waiting for EDXML data on STDIN...(use --help to get help)")
  sys.stdout.flush()
  SaxParser.parse(sys.stdin)
else:
  sys.stderr.write("\nProcessing file %s:" % InputFileName );
  SaxParser.parse(open(InputFileName))
