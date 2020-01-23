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
import argparse
import json
import sys

from edxml.EDXMLParser import EDXMLPullParser


class EDXML2CSV(EDXMLPullParser):

    def __init__(self, output_column_names, column_separator, print_header_line):

        self.__property_names = []
        self.__column_separator = column_separator
        self.__output_column_names = output_column_names
        self.__print_header_line = print_header_line
        super(EDXML2CSV, self).__init__(sys.stdout.buffer)

    def _parsed_ontology(self, ontology):

        # Compile a list of output columns,
        # one column per event property.
        property_names = set()
        for event_type_name, event_type in self.get_ontology().get_event_types().items():
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
        escaped_event_content = json.dumps(
            {name: attachment
                .replace('\n', '\\n')
                .replace(self.__column_separator, '\\' + self.__column_separator)
             for name, attachment in event.get_attachments().items()}
        )

        for property_name in self.__property_names:
            property_objects[property_name] = []

        for property_name, objects in event.get_properties().items():
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

            sys.stdout.write(line + line_end + '\n')

def main():
    parser = argparse.ArgumentParser(
        description='This utility accepts EDXML data as input and writes the events to standard output, formatted '
                    'in rows and columns. For every event property, a output column is generated. If one property '
                    'has multiple objects, multiple  output lines are generated.'
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='By default, input is read from standard input. This option can be used to read from a '
             'file in stead.'
    )

    parser.add_argument(
        '-c',
        '--columns',
        type=str,
        help='Specifies which columns to produce, and in what order. By default, all columns are printed. '
             'When this option is used, only the specified columns are printed, in the order you specify. '
             'The argument should be a comma separated list of property names.'
    )

    parser.add_argument(
        '-s',
        '--separator',
        type=str,
        default='\t',
        help='By default, columns are separated by tabs. Using this option, you can specify a different separator.'
    )

    parser.add_argument(
        '--with-header',
        action='store_true',
        help='Prints a header row containing the names of each of the columns.'
    )

    args = parser.parse_args()

    event_input = args.file or sys.stdin.buffer

    if args.columns is None or args.columns == '':
        columns = None
    else:
        columns = args.columns.split(',')

    try:
        EDXML2CSV(columns, args.separator, args.with_header).parse(event_input)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()
