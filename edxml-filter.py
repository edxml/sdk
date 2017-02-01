#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
# 
#                          EDXML Filtering Utility
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
#  This utility reads an EDXML stream from standard input and filters it according
#  to the user supplied parameters. The result is sent to standard output.
#
#  Parameters:
#
#  -s    Takes a regular expression for filtering source URIs (optional).
#  -e    Takes an event type name for filtering on events of a certain type (optional).
#
#  Examples:
#
# cat test.edxml | edxml-filter -s "/offices/stuttgart/.*"
# cat test.edxml | edxml-filter -s ".*clientrecords.*" -e "client-supportticket"
# cat test.edxml | edxml-filter -e "client-order"
#
#

import sys, re
from edxml.EDXMLFilter import EDXMLPullFilter


class EDXMLEventGroupFilter(EDXMLPullFilter):
  def __init__(self, SourceUriPattern, EventTypeName):

    super(EDXMLEventGroupFilter, self).__init__(sys.stdout, False)
    self.SourceUriPattern = SourceUriPattern
    self.EventTypeName = EventTypeName
    self.passThrough = True

  def _parsedOntology(self, parsedOntology):
    filteredEventTypes = []
    filteredSources = []

    if self.EventTypeName:
      for eventTypeName in parsedOntology.GetEventTypeNames():
        if eventTypeName != self.EventTypeName:
          filteredEventTypes.append(eventTypeName)

    for sourceUri, source in parsedOntology.GetEventSources():
      if re.match(self.SourceUriPattern, sourceUri) is not None:
        filteredSources.append(sourceUri)

    for eventTypeName in filteredEventTypes:
      parsedOntology.DeleteEventType(eventTypeName)
    for eventSource in filteredSources:
      parsedOntology.DeleteEventSource(eventSource)

    parsedOntology.Validate()

    super(EDXMLEventGroupFilter, self)._parsedOntology(parsedOntology)

  def _openEventGroup(self, eventTypeName, eventSourceUri):

    if self.getOntology().GetEventSource(eventSourceUri) is None:
      # Source is gone, turn filter output off.
      self.passThrough = False
      eventTypeName = None
      eventSourceUri = None

    if self.getOntology().GetEventType(eventTypeName) is None:
      # Event type is gone, turn filter output off.
      self.passThrough = False
      eventTypeName = None
      eventSourceUri = None

    if self.passThrough:
      super(EDXMLEventGroupFilter, self)._openEventGroup(eventTypeName, eventSourceUri)

  def _closeEventGroup(self, eventTypeName, eventSourceId):

    if self.passThrough:
      super(EDXMLEventGroupFilter, self)._closeEventGroup(eventTypeName, eventSourceId)
    else:
      self.passThrough = True

  def _parsedEvent(self, edxmlEvent):
    if self.passThrough:
      super(EDXMLEventGroupFilter, self)._parsedEvent(edxmlEvent)


def PrintHelp():

  print """

   This utility reads an EDXML stream from standard input and filters it according
   to the user supplied parameters. The result is sent to standard output.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. If this option is not specified,
                       input will be read from standard input.

     -s                When specified, this option must be followed by a regular
                       expression. Only events that have a source URL that matches
                       this expression will be copied to the output stream.

     -e                When specified, this option must be followed by an EDXML
                       event type name. Only events of specified type will be
                       copied to the output stream.

   Examples:

     cat test.edxml | edxml-filter.py -s "/offices/stuttgart/.*"
     cat test.edxml | edxml-filter.py -s ".*clientrecords.*" -e "client-supportticket"
     cat test.edxml | edxml-filter.py -e "client-order"

"""

# Program starts here. 

ArgumentCount = len(sys.argv)
CurrentArgument = 1
Input = sys.stdin
SourceFilter = re.compile('.*')
EventTypeFilter = None

# Parse commandline arguments

while CurrentArgument < ArgumentCount:


  if sys.argv[CurrentArgument] in ('-h', '--help'):
    PrintHelp()
    sys.exit(0)

  elif sys.argv[CurrentArgument] == '-s':
    CurrentArgument += 1
    SourceFilter = re.compile(sys.argv[CurrentArgument])

  elif sys.argv[CurrentArgument] == '-e':
    CurrentArgument += 1
    EventTypeFilter = sys.argv[CurrentArgument]

  elif sys.argv[CurrentArgument] == '-f':
    CurrentArgument += 1
    Input = open(sys.argv[CurrentArgument])

  else:
    sys.stderr.write("Unknown commandline argument: %s\n" % sys.argv[CurrentArgument])
    sys.exit()

  CurrentArgument += 1

if Input == sys.stdin:
  sys.stderr.write('Waiting for EDXML data on standard input... (use --help option to get help)\n')

with EDXMLEventGroupFilter(SourceFilter, EventTypeFilter) as eventFilter:
  try:
    eventFilter.parse(Input)
  except KeyboardInterrupt:
    pass
