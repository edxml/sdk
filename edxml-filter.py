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
#  -s    Takes a regular expression for filtering source URLs (optional).
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
from xml.sax import make_parser
from edxml.EDXMLFilter import EDXMLStreamFilter

# This class is based on the EDXMLStreamFilter class,
# and filters out <eventgroup> sections based on their
# source and event type.

class EDXMLEventGroupFilter(EDXMLStreamFilter):
  def __init__ (self, SourceUrlPattern, EventTypeName):

    self.SourceUrlPattern = SourceUrlPattern
    self.EventTypeName = EventTypeName
    self.SourceUrlMapping = {}

    # Create Sax parser
    self.SaxParser = make_parser()
    # Call parent class constructor
    EDXMLStreamFilter.__init__(self, self.SaxParser, False)
    # Set self as content handler
    self.SaxParser.setContentHandler(self)

  def startElement(self, name, attrs):

    if name == 'eventgroup':

      SourceUrl = self.SourceUrlMapping[attrs.get('source-id')]
      if re.match(self.SourceUrlPattern, SourceUrl) is None:
        # No match, turn filter output off.
        self.SetOutputEnabled(False)

      if self.EventTypeName and attrs.get('event-type') != self.EventTypeName:
        # No match, turn filter output off.
        self.SetOutputEnabled(False)

    elif name == 'source':
      # Remember which Source ID belongs to which URL
      self.SourceUrlMapping[attrs.get('source-id')] = attrs.get('url')

      if re.match(self.SourceUrlPattern, attrs.get('url')) is None:
        # No match, turn filter output off.
        self.SetOutputEnabled(False)
      else:
        # Turn filter output back on
        self.SetOutputEnabled(True)

    elif name == 'eventtype':

      if self.EventTypeName and attrs.get('name') != self.EventTypeName:
        # No match, turn filter output off.
        self.SetOutputEnabled(False)
      else:
        # Turn filter output back on
        self.SetOutputEnabled(True)

    # Call parent startElement to generate the output XML element.
    EDXMLStreamFilter.startElement(self, name, attrs)

  def endElement(self, name):
    # Call parent implementation
    EDXMLStreamFilter.endElement(self, name)

    if name == 'eventgroup':
      # Turn filter output back on
      self.SetOutputEnabled(True)

    if name == 'sources':
      # Turn filter output back on
      self.SetOutputEnabled(True)

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

# Instantiate EDXMLEventGroupFilter
EventGroupFilter = EDXMLEventGroupFilter(SourceFilter, EventTypeFilter)

# Push input into the Sax parser.
EventGroupFilter.SaxParser.parse(Input)

