#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                  column separated text to EDXML converter
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
#  This script accepts column separated text as input and writes a EDXML data
#  stream to standard output. It uses the ontology from an existing EDXML file
#  to generate output. The input should have column names on the very first row,
#  where the column names match the names of the event type properties.

import sys
import time
from edxml.error import EDXMLValidationError

import edxml
from edxml.EDXMLParser import ProcessingInterrupted


def print_help():

    print("""

   This utility accepts column separated text as input and wraps the input data
   into an EDXML output stream, which is printed on standard output. The input
   data must contain a header line, which contains the names of the event properties
   that each column represents. An existing EDXML file is used to extract the event
   type definition from. Optionally, a column can be specified which contains the
   name of the event type that each input line represents. This allows multiple event
   types to be generated from a single CSV input stream.

   Options:

     -h, --help       Prints this help text

     -f               This option must be followed by a filename, which will be used to
                      read CSV input data from. If this option is not specified, data
                      will be read from standard input.

     -o               This option must be followed by a filename, which must contain
                      an EDXML stream which holds the ontology, containing the eventtype
                      definition that matches the CVS input data.

     -u --source-uri  This option must be followed by the EDXML source URI that represents
                      the origin of the input data.

     -e --event-type  This option must be followed by the name of the event type that the
                      CSV data represents.

     -t --type-column This option must be followed by a column number of the column that
                      contains the name of the event type represented by each input line.
                      By default, unless -t is used, it is assumed that column #0 contains
                      the event type.

     -s --separator   By default, columns are assumed to be separated by tabs. Using this
                      option, you can specify a different separator.

   Example:

     cat data.csv | edxml-from-csv.py -o ontology.edxml -t my-eventtype -s ';'

""")


csv_input = sys.stdin
ontology_input_file = None
column_separator = '\t'
output_event_type = None
event_type_column = None
output_source_uri = None
curr_option = 1
time_acquired = time.gmtime()
date_acquired = "%04d%02d%02d" % (
    (time_acquired.tm_year, time_acquired.tm_mon, time_acquired.tm_mday))

while curr_option < len(sys.argv):

    if sys.argv[curr_option] in ('-h', '--help'):
        print_help()
        sys.exit(0)

    elif sys.argv[curr_option] == '-f':
        curr_option += 1
        csv_input = open(sys.argv[curr_option])

    elif sys.argv[curr_option] == '-o':
        curr_option += 1
        ontology_input_file = open(sys.argv[curr_option])

    elif sys.argv[curr_option] in ('-u', '--source-uri'):
        curr_option += 1
        output_source_uri = sys.argv[curr_option]

    elif sys.argv[curr_option] in ('-e', '--event-type'):
        curr_option += 1
        output_event_type = sys.argv[curr_option]

    elif sys.argv[curr_option] in ('-t', '--type-column'):
        curr_option += 1
        event_type_column = int(sys.argv[curr_option])

    elif sys.argv[curr_option] in ('-s', '--separator'):
        curr_option += 1
        column_separator = sys.argv[curr_option]

    else:
        sys.stderr.write("Unknown commandline argument: %s\n" %
                         sys.argv[curr_option])
        sys.exit()

    curr_option += 1

if ontology_input_file is None:
    sys.stderr.write(
        'No ontology source was specified. (use --help option to get help)\n')
    sys.exit(1)

if output_source_uri is None:
    sys.stderr.write(
        'No source URI was specified. (use --help option to get help)\n')
    sys.exit(1)

if event_type_column is None and output_event_type is None:
    sys.stderr.write(
        'I cannot determine the event type of the input data. Either specify an event type or a '
        'column that contains event type names. (use --help option to get help)\n')
    sys.exit(1)

parser = edxml.EDXMLOntologyPullParser()

try:
    parser.parse(ontology_input_file)
except ProcessingInterrupted:
    pass

# Remove the existing source definitions, we will
# define our own data source.
for uri, source in parser.get_ontology().get_event_sources():
    parser.get_ontology().delete_event_source(uri)

# Define new data source.
parser.get_ontology().create_event_source(output_source_uri, description='Imported from CSV data',
                                          acquisition_date=date_acquired)

if csv_input == sys.stdin:
    sys.stderr.write(
        'Waiting for CSV data on standard input... (use --help option to get help)\n')

# Instantiate an EDXMLWriter and insert the <ontology> element
# from the input EDXML file. This duplicates the <ontology>
# element from the input EDXML file, except for the source
# definitions that we replaced with our own.
writer = edxml.EDXMLWriter(sys.stdout)
writer.add_ontology(parser.get_ontology())

current_output_event_type = None
column_property_mapping = None
previous_split_line = None
previous_line_properties = None
output_event = edxml.EventElement({}, output_event_type, output_source_uri)
output_properties = {}
unique_output_properties = {}

for line in csv_input:
    if column_property_mapping is None:
        # Read header line.
        column_property_mapping = line.rstrip('\n').split(column_separator)

        if event_type_column is not None:
            # We have a column containing the event type name.
            del column_property_mapping[event_type_column]

        # Build a dictionary containing a mapping from
        # property names to column indexes.
        property_column_mapping = {property_name: index for index, property_name in dict(
            enumerate(column_property_mapping)).items()}

        # Since this is a header line, we stop
        # processing at this point.
        continue

    split_line = line.rstrip('\n').split(column_separator)

    if event_type_column is not None:
        # We have a column containing the event type name.
        output_event_type = split_line[event_type_column]
        del split_line[event_type_column]

    if output_event_type not in output_properties:
        output_properties[output_event_type] = parser.get_ontology(
        ).get_event_type(output_event_type).get_properties()
        unique_output_properties[output_event_type] = parser.get_ontology(
        ).get_event_type(output_event_type).get_unique_properties()

        output_properties[output_event_type] = [
            output_property for output_property in output_properties[output_event_type]
            if output_property in property_column_mapping]
        unique_output_properties[output_event_type] = [
            output_property for output_property in unique_output_properties[output_event_type]
            if output_property in property_column_mapping]

    # Create dictionary of properties and their objects
    line_properties = {}
    for output_property in output_properties[output_event_type]:
        if split_line[property_column_mapping[output_property]] != '':
            line_properties[output_property] = [
                split_line[property_column_mapping[output_property]]]

    if previous_split_line is not None:

        # Compare with previous line, maybe
        # the lines form a single event having
        # multiple objects for the same property,
        # scattered over multiple consecutive lines.
        difference = set(split_line) ^ set(previous_split_line)

        if len(difference) == 2:
            # This line is suspicious. Figure out which property
            # is different.
            diff_properties = [
                output_property for output_property in line_properties
                if line_properties[output_property] != previous_line_properties[output_property]]

            # Check if we have exactly one differing property, which
            # must NOT be a unique property. Differing unique properties
            # always mean that we are looking at two different events.
            if len(diff_properties) > 0 and diff_properties[0] not in unique_output_properties[output_event_type]:
                output_property = diff_properties[0]

                # Add the value to existing dictionary and move on to the next line.
                previous_line_properties[output_property].extend(
                    line_properties[output_property])
                continue

        if output_event_type != current_output_event_type:
            if current_output_event_type is not None:
                if previous_line_properties is not None:
                    try:
                        writer.add_event(
                            output_event.set_properties(previous_line_properties))
                    except EDXMLValidationError as Error:
                        # Invalid event, just skip it.
                        sys.stderr.write(
                            "WARNING: Skipped one output event: %s\n" % Error)
            else:
                if previous_line_properties is not None:
                    try:
                        writer.add_event(
                            output_event.set_properties(previous_line_properties))
                    except EDXMLValidationError as Error:
                        # Invalid event, just skip it.
                        sys.stderr.write(
                            "WARNING: Skipped one output event: %s\n" % Error)
            current_output_event_type = output_event_type
        else:
            try:
                writer.add_event(
                    output_event.set_properties(previous_line_properties))
            except EDXMLValidationError as Error:
                # Invalid event, just skip it.
                sys.stderr.write(
                    "WARNING: Skipped one output event: %s\n" % Error)

    previous_split_line = split_line
    previous_line_properties = line_properties

if previous_split_line is not None:
    if output_event_type != current_output_event_type:
        current_output_event_type = output_event_type
        if output_event_type not in output_properties:
            output_properties[output_event_type] = parser.get_ontology(
            ).get_event_type(output_event_type).get_properties()
            unique_output_properties[output_event_type] = parser.get_ontology(
            ).get_event_type(output_event_type).get_unique_properties()

            output_properties[output_event_type] = [
                p for p in output_properties if p in property_column_mapping]
            unique_output_properties[output_event_type] = [
                p for p in unique_output_properties if p in property_column_mapping]

        output_event.set_type(output_event_type)
    try:
        writer.add_event(output_event.set_properties(previous_line_properties))
    except EDXMLValidationError as Error:
        # Invalid event, just skip it.
        sys.stderr.write("WARNING: Skipped one output event: %s\n" % Error)

writer.close()
