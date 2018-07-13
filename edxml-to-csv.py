#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                   EDXML to column separated text converter
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
#  This script accepts EDXML data as input and writes the events to standard
#  output, formatted in rows and columns. For every event property, a output
#  column is generated. If one property has multiple objects, multiple output
#  lines are generated.

import sys

from edxml.EDXMLParser import EDXMLPullParser


class EDXML2CSV(EDXMLPullParser):

    def __init__(self, output_column_names, column_separator, print_header_line):

        self.__property_names = []
        self.__column_separator = column_separator
        self.__output_column_names = output_column_names
        self.__print_header_line = print_header_line
        super(EDXML2CSV, self).__init__(sys.stdout)

    def _parsed_ontology(self, ontology):

        # Compile a list of output columns,
        # one column per event property.
        property_names = set()
        for event_type_name, event_type in self.get_ontology().get_event_types().iteritems():
            property_names.update(event_type.get_properties().keys())

        # Filter the available properties using
        # the list of requested output columns.
        if len(self.__output_column_names) > 0:
            for property_name in self.__output_column_names:
                if property_name in property_names:
                    self.__property_names.append(property_name)
        else:
            # No output column specification was given,
            # just output all of them.
            self.__property_names = list(property_names)

        # Output a header line containing the output column names
        if self.__print_header_line:
            sys.stdout.write('event type' + self.__column_separator +
                             self.__column_separator.join(self.__property_names) + '\n')

    def _parsed_event(self, event):

        property_objects = {}
        escaped_event_content = event.get_content().replace(
            '\n', '\\n').replace(self.__column_separator, '\\' + self.__column_separator)

        for property_name in self.__property_names:
            property_objects[property_name] = []

        for property_name, objects in event.get_properties().iteritems():
            if property_name in self.__property_names:
                for event_object in objects:
                    escaped_value = event_object.replace(
                        self.__column_separator, '\\' + self.__column_separator)
                    property_objects[property_name].append(escaped_value)

                self.__iterate_generate_lines(self.__property_names, property_objects,
                                              event.get_type_name() + self.__column_separator,
                                              escaped_event_content, 0)

    def __iterate_generate_lines(self, columns, property_objects, line_start, line_end, start_column):

        start_col_property_name = columns[start_column]

        if len(property_objects[start_col_property_name]) == 0:
            # Property has no objects, iterate.
            line = line_start + self.__column_separator
            if len(columns) > start_column + 1:
                self.__iterate_generate_lines(
                    columns, property_objects, line, line_end, start_column + 1)
            return

        for object_value in property_objects[start_col_property_name]:

            # Add object value to the current output line
            line = line_start + object_value + self.__column_separator

            for column in range(start_column + 1, len(columns)):

                column_property = columns[column]
                num_property_objects = len(property_objects[column_property])

                if num_property_objects == 0:

                    # Property has no objects.
                    line += self.__column_separator

                elif num_property_objects == 1:

                    # We have exactly one object for this property.
                    line += property_objects[column_property][0] + \
                            self.__column_separator

                else:

                    # We have multiple objects for this property,
                    # which means we need to generate multiple output
                    # lines. Iterate.
                    self.__iterate_generate_lines(
                        columns, property_objects, line, line_end, column)
                    return

            sys.stdout.write(unicode(line + line_end + '\n').encode('utf-8'))


def print_help():

    print("""

   This utility accepts EDXML data as input and writes the events to standard
   output, formatted in rows and columns. For every event property, a output
   column is generated. If one property has multiple objects, multiple  output
   lines are generated.

   Options:

     -h, --help       Prints this help text

     -f               This option must be followed by a filename, which will be
                      used as input. If this option is not specified, EDXML data
                      will be read from standard input.

     -c, --columns    Specifies which columns to produce, and in what order. By
                      default, all columns are printed. When this option is used,
                      only the specified columns are printed, in the order you
                      specify. The argument should be a comma separated list of
                      property names.

     -s --separator   By default, columns are separated by tabs. Using this option,
                      you can specify a different separator.

     -s --noheader    By default, the first row is a header containing the names of
                      each column. Using this option, this header will be suppressed.

   Example:

     cat data.edxml | edxml-to-csv.py -c property-a,property-b -s ';'

""")


output_columns = []
event_input = sys.stdin
column_separator = '\t'
suppress_header_line = False
curr_option = 1

while curr_option < len(sys.argv):

    if sys.argv[curr_option] in ('-h', '--help'):
        print_help()
        sys.exit(0)

    elif sys.argv[curr_option] == '-f':
        curr_option += 1
        event_input = open(sys.argv[curr_option])

    elif sys.argv[curr_option] in ('-c', '--columns'):
        curr_option += 1
        output_columns = sys.argv[curr_option].split(',')

    elif sys.argv[curr_option] in ('-s', '--separator'):
        curr_option += 1
        column_separator = sys.argv[curr_option]

    elif sys.argv[curr_option] == '--noheader':
        curr_option += 1
        suppress_header_line = True

    else:
        sys.stderr.write("Unknown commandline argument: %s\n" %
                         sys.argv[curr_option])
        sys.exit()

    curr_option += 1

if event_input == sys.stdin:
    sys.stderr.write(
        'Waiting for EDXML data on standard input... (use --help option to get help)\n')

try:
    EDXML2CSV(output_columns, column_separator,
              not suppress_header_line).parse(event_input)
except KeyboardInterrupt:
    sys.exit()
