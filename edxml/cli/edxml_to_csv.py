#!/usr/bin/env python3

# ========================================================================================
#                                                                                        =
#              Copyright (c) 2010 D.H.J. Takken (d.h.j.takken@xs4all.nl)                 =
#                      Copyright (c) 2020 the EDXML Foundation                           =
#                                                                                        =
#                                   http://edxml.org                                     =
#                                                                                        =
#             This file is part of the EDXML Software Development Kit (SDK)              =
#                       and is released under the MIT License:                           =
#                         https://opensource.org/licenses/MIT                            =
#                                                                                        =
# ========================================================================================

#  This script accepts EDXML data as input and writes the events to standard
#  output, formatted in rows and columns. For every event property, a output
#  column is generated. If one property has multiple objects, multiple output
#  lines are generated.

import argparse
import sys

from edxml.cli import configure_logger
from edxml.parser import EDXMLPullParser


class EDXML2CSV(EDXMLPullParser):

    def __init__(self, event_type_name, column_names, attachment_names, column_separator, print_header_line):

        self.__event_type_name = event_type_name
        self.__property_names = []
        self.__attachment_names = []
        self.__column_separator = column_separator
        self.__output_column_names = column_names
        self.__output_attachment_names = attachment_names or []
        self.__print_header_line = print_header_line
        self.__first_line_written = False
        super().__init__()

    def _parsed_ontology(self, ontology):

        # Compile a list of output columns,
        # one column per event property.
        event_type = ontology.get_event_type(self.__event_type_name)
        if event_type is None:
            # The requested event type was not found, maybe the
            # next ontology element will define it.
            return

        property_names = event_type.get_properties().keys()

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

        attachment_names = event_type.get_attachments().keys()

        # Filter the available attachments using
        # the list of requested output columns.
        if len(self.__output_attachment_names) > 0:
            for attachment_name in self.__output_attachment_names:
                if attachment_name in attachment_names:
                    self.__attachment_names.append(attachment_name)

        # Output a header line containing the output column names
        if self.__print_header_line and not self.__first_line_written:
            print(
                'event type' +
                self.__column_separator +
                self.__column_separator.join(self.__property_names) +
                self.__column_separator.join(self.__attachment_names)
            )

    def _parsed_event(self, event):

        if event.get_type_name() != self.__event_type_name:
            return

        column_values = {}
        for property_name in self.__property_names:
            column_values[property_name] = []

        for attachment_name in self.__attachment_names:
            escaped_value = event.get_attachments().get(attachment_name).replace(
                        self.__column_separator, '\\' + self.__column_separator
            )
            escaped_value = escaped_value.replace('\n', '\\n').replace('\r', '\\r')
            column_values['a:' + attachment_name] = [escaped_value]

        for property_name, objects in event.get_properties().items():
            if property_name in self.__property_names:
                for event_object in objects:
                    escaped_value = event_object.replace(
                        self.__column_separator, '\\' + self.__column_separator)
                    column_values[property_name].append(escaped_value)

                self.__iterate_generate_lines(
                    self.__property_names + ['a:' + a for a in self.__attachment_names],
                    column_values,
                    line_start=event.get_type_name() + self.__column_separator,
                    line_end='',
                    start_column=0
                )

    def __iterate_generate_lines(self, columns, column_values, line_start, line_end, start_column):

        start_col_property_name = columns[start_column]

        if len(column_values[start_col_property_name]) == 0:
            # Property has no objects, iterate.
            line = line_start + self.__column_separator
            if len(columns) > start_column + 1:
                self.__iterate_generate_lines(
                    columns, column_values, line, line_end, start_column + 1)
            return

        for object_value in column_values[start_col_property_name]:

            # Add object value to the current output line
            line = line_start + object_value + self.__column_separator

            for column in range(start_column + 1, len(columns)):

                column_property = columns[column]
                num_property_objects = len(column_values[column_property])

                if num_property_objects == 0:

                    # Property has no objects.
                    line += self.__column_separator

                elif num_property_objects == 1:

                    # We have exactly one object for this property.
                    line += column_values[column_property][0] + \
                            self.__column_separator

                else:

                    # We have multiple objects for this property,
                    # which means we need to generate multiple output
                    # lines. Iterate.
                    self.__iterate_generate_lines(
                        columns, column_values, line, line_end, column)
                    return

            print(line + line_end)
            self.__first_line_written = True


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
        '-e',
        '--event-type',
        type=str,
        help='The name of the event type of that will be output.'
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
        '-a',
        '--attachments',
        type=str,
        help='By default the event attachments are not included as output columns. This option specifies which '
             'event attachments to include and in what order. The argument should be a comma separated list of '
             'attachment names.'
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

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    args = parser.parse_args()

    configure_logger(args)

    event_input = args.file or sys.stdin.buffer

    if args.columns is None or args.columns == '':
        columns = None
    else:
        columns = args.columns.split(',')

    if args.attachments is None or args.attachments == '':
        attachments = None
    else:
        attachments = args.attachments.split(',')

    try:
        EDXML2CSV(args.event_type, columns, attachments, args.separator, args.with_header).parse(event_input)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()
