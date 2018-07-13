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

import sys
import re
from edxml.EDXMLFilter import EDXMLPullFilter


class EDXMLEventGroupFilter(EDXMLPullFilter):
    def __init__(self, source_uri_pattern, event_type_name):

        super(EDXMLEventGroupFilter, self).__init__(sys.stdout, False)
        self.__source_uri_pattern = source_uri_pattern
        self.__event_type_name = event_type_name
        self.__pass_through = True

    def _parsed_ontology(self, parsed_ontology):
        filtered_event_types = []
        filtered_sources = []

        if self.__event_type_name:
            for event_type_name in parsed_ontology.get_event_type_names():
                if event_type_name != self.__event_type_name:
                    filtered_event_types.append(event_type_name)

        for sourceUri, source in parsed_ontology.get_event_sources().items():
            if re.match(self.__source_uri_pattern, sourceUri) is not None:
                filtered_sources.append(sourceUri)

        for event_type_name in filtered_event_types:
            parsed_ontology.delete_event_type(event_type_name)
        for eventSource in filtered_sources:
            parsed_ontology.delete_event_source(eventSource)

        parsed_ontology.validate()

        super(EDXMLEventGroupFilter, self)._parsed_ontology(parsed_ontology)

    def _open_event_group(self, event_type_name, event_source_uri):

        if self.get_ontology().get_event_source(event_source_uri) is None:
            # Source is gone, turn filter output off.
            self.__pass_through = False
            event_type_name = None
            event_source_uri = None

        if self.get_ontology().get_event_type(event_type_name) is None:
            # Event type is gone, turn filter output off.
            self.__pass_through = False
            event_type_name = None
            event_source_uri = None

        if self.__pass_through:
            super(EDXMLEventGroupFilter, self)._open_event_group(
                event_type_name, event_source_uri)

    def _close_event_group(self, event_type_name, event_source_id):

        if self.__pass_through:
            super(EDXMLEventGroupFilter, self)._close_event_group(
                event_type_name, event_source_id)
        else:
            self.__pass_through = True

    def _parsed_event(self, event):
        if self.__pass_through:
            super(EDXMLEventGroupFilter, self)._parsed_event(event)


def print_help():

    print("""

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

""")

# Program starts here.


argument_count = len(sys.argv)
current_argument = 1
event_input = sys.stdin
source_filter = re.compile('.*')
event_type_filter = None

# Parse commandline arguments

while current_argument < argument_count:

    if sys.argv[current_argument] in ('-h', '--help'):
        print_help()
        sys.exit(0)

    elif sys.argv[current_argument] == '-s':
        current_argument += 1
        source_filter = re.compile(sys.argv[current_argument])

    elif sys.argv[current_argument] == '-e':
        current_argument += 1
        event_type_filter = sys.argv[current_argument]

    elif sys.argv[current_argument] == '-f':
        current_argument += 1
        event_input = open(sys.argv[current_argument])

    else:
        sys.stderr.write("Unknown commandline argument: %s\n" %
                         sys.argv[current_argument])
        sys.exit()

    current_argument += 1

if event_input == sys.stdin:
    sys.stderr.write(
        'Waiting for EDXML data on standard input... (use --help option to get help)\n')

with EDXMLEventGroupFilter(source_filter, event_type_filter) as eventFilter:
    try:
        eventFilter.parse(event_input)
    except KeyboardInterrupt:
        pass
