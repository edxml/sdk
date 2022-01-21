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


def escape(value, delimiter):
    return value.replace(delimiter, '\\' + delimiter).replace('\n', '\\n').replace('\r', '\\r')


class EDXML2DelimitedText(EDXMLPullParser):

    def __init__(self, event_type_name, column_names, attachment_names, column_delimiter, print_header_line):

        self.__event_type_name = event_type_name
        self.__property_names = []
        self.__attachment_names = []
        self.__column_delimiter = column_delimiter
        self.__output_column_names = column_names
        self.__output_attachment_names = attachment_names or []
        self.__print_header_line = print_header_line
        self.__header_written = False
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
        if self.__output_column_names is not None:
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
        for attachment_name in self.__output_attachment_names:
            if attachment_name in attachment_names:
                self.__attachment_names.append(attachment_name)

        # Output a header line containing the output column names
        if self.__print_header_line and not self.__header_written:
            print(self.__column_delimiter.join(self.__property_names + self.__attachment_names))
            self.__header_written = True

    def _parsed_event(self, event):

        if event.get_type_name() != self.__event_type_name:
            return

        column_values = {}
        for property_name in self.__property_names:
            column_values[property_name] = []
        for attachment_name in self.__attachment_names:
            column_values['a:' + attachment_name] = []

        for property_name, objects in event.get_properties().items():
            if property_name in self.__property_names:
                column_values[property_name].extend([escape(value, self.__column_delimiter) for value in objects])

        for attachment_name in self.__attachment_names:
            for attachment in event.get_attachments().get(attachment_name, {}).values():
                column_values['a:' + attachment_name].append(escape(attachment, self.__column_delimiter))

        for line in self.__recurse_generate_lines(
                    list(column_values.keys()),
                    column_values,
                    line=[],
                    start_column=0
                ):
            print(self.__column_delimiter.join(line))

    def __recurse_generate_lines(self, column_names, column_values, line, start_column):

        if start_column >= len(column_names):
            yield line
            return

        for column_index in range(start_column, len(column_names)):

            column_name = column_names[column_index]
            num_property_objects = len(column_values[column_name])

            if num_property_objects == 0:
                # Property has no objects. Produce empty column value.
                line.append('')
            elif num_property_objects == 1:
                # We have exactly one object for this property.
                line.append(column_values[column_name][0])
            else:
                # We have multiple objects for this property,
                # which means we need to generate multiple output
                # lines. For each object value we recurse taking
                # the previously processed columns plus
                # the current object value as starting point.
                for value in column_values[column_name]:
                    yield from self.__recurse_generate_lines(
                        column_names, column_values, line + [value], column_index + 1
                    )
                return

        yield line


def main():
    parser = argparse.ArgumentParser(
        description='This utility accepts EDXML data as input and writes the events to standard output, formatted '
                    'in rows and columns. For every event property, an output column is generated. If one property '
                    'has multiple objects, multiple lines of output are generated.'
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='By default, input is read from standard input. This option can be used to read from a file in stead.'
    )

    parser.add_argument(
        'event_type',
        type=str,
        help='The name of the type of event that will be output.'
    )

    parser.add_argument(
        '-p',
        '--properties',
        type=str,
        help='Specifies which properties to output, and in what order. By default, all properties are printed. '
             'When this option is used, only the specified properties are printed, in the order you specify. '
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
        '-d',
        '--delimiter',
        type=str,
        default='\t',
        help='By default, columns are tab delimited. Using this option, you can specify a different delimiter.'
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

    if args.properties is None:
        property_columns = None
    elif args.properties == '':
        property_columns = []
    else:
        property_columns = args.properties.split(',')

    if args.attachments is None or args.attachments == '':
        attachment_columns = None
    else:
        attachment_columns = args.attachments.split(',')

    try:
        EDXML2DelimitedText(
            args.event_type, property_columns, attachment_columns, args.delimiter, args.with_header
        ).parse(event_input)
    except KeyboardInterrupt:
        sys.exit()


if __name__ == "__main__":
    main()
