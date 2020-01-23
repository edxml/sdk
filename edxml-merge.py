#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                          EDXML Merging Utility
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
#  This utility reads multiple compatible EDXML files and merges them into
#  one new EDXML file, which is then printed on standard output. It works in
#  two passes. First, it compiles and integrates all <ontology> elements
#  from all EDXML files into a EDXMLParser instance. Then, in a second pass,
#  it outputs the unified <ontology> element and outputs the eventgroups
#  in each of the EDXML files.
#
#  The script demonstrates the use of EDXMLStreamFilter and merging of
#  <ontology> elements from multiple EDXML sources.
import argparse
import sys
from xml.sax import make_parser
from xml.sax.xmlreader import AttributesImpl
from edxml.error import EDXMLError
from edxml.EDXMLFilter import EDXMLPullFilter

# This class is based on the EDXMLStreamFilter class,
# and filters out <eventgroup> sections, omitting
# all other content. It needs a dictionary which
# translates Source URLs to a new set of unique
# Source Identifiers. This mapping is used to translate
# the source-id attributes in the <eventgroup> tags,
# assuring the uniqueness of Source ID.
from edxml.EDXMLParser import ProcessingInterrupted


class EDXMLMerger(EDXMLPullFilter):
    def __init__(self, upstream, merged_definitions, source_uri_id_mapping):

        # Call parent constructor
        EDXMLPullFilter.__init__(self, upstream, False)

        # Initialize source id / url mappings
        self.source_url_id_mapping = source_uri_id_mapping
        self.source_id_url_mapping = {}

        self.feedback = False
        self.definitions_written = False
        self.merged_definitions = merged_definitions

    def close(self):
        self.SetOutputEnabled(True)
        EDXMLPullFilter.end_element(self, 'eventgroups')
        EDXMLPullFilter.end_element(self, 'events')

    def start_element(self, name, attrs):
        attribute_items = {}
        # Populate the AttributeItems dictionary.
        for attribute_name, attribute_value in attrs.items():
            attribute_items[attribute_name] = attribute_value

        if self.feedback:
            # We are in the process of feeding ourselves
            # with merged definitions. Just pass through
            # whatever it is.
            EDXMLPullFilter.start_element(
                self, name, AttributesImpl(attribute_items))
            return

        if name == 'events':
            if self.definitions_written:
                # This is the <events> tag from a second, third, ...
                # EDXML stream that is fed to us. Turn output off
                # until we get to a <eventgroup> tag.
                self.SetOutputEnabled(False)
                return

        if name == 'definitions' and not self.feedback:
            # Turn filter output off.
            self.SetOutputEnabled(False)
            return

        if name == 'source' and not self.feedback:
            # Store the relations between source URL and ID
            self.source_id_url_mapping[attribute_items['source-id']] = attribute_items['url']

        if name == 'eventgroup':

            # Edit the AttributeItems dictionary to ensure that the
            # source IDs in the output stream are unique.
            group_source_uri = self.source_id_url_mapping[attribute_items['source-id']]
            attribute_items['source-id'] = self.source_url_id_mapping[group_source_uri]

            # Turn output back on.
            self.SetOutputEnabled(True)

        if name == 'eventgroups' and self.definitions_written:
            self.SetOutputEnabled(True)
            return

        EDXMLPullFilter.start_element(
            self, name, AttributesImpl(attribute_items))

    def end_element(self, name):

        if name == 'definitions' and not self.definitions_written and not self.feedback:
            self.feedback = True
            self.SetOutputEnabled(True)
            self.merged_definitions.GenerateXMLDefinitions(self)
            self.feedback = False

            # Output a <eventgroups> tag
            EDXMLPullFilter.start_element(
                self, 'eventgroups', AttributesImpl({}))

            self.definitions_written = True

            # Turn filter output off.
            # self.SetOutputEnabled(False)
            return

        if name == 'eventgroups':
            self.SetOutputEnabled(False)
            return

        # Call parent implementation
        EDXMLPullFilter.end_element(self, name)

parser = argparse.ArgumentParser(
    description='This utility outputs sticky hashes for every event in a given '
                'EDXML file or input stream. The hashes are printed to standard output.'
)

parser.add_argument(
    '-f',
    '--file',
    type=str,
    action='append',
    help='A file name to be used as input for the merge operation.'
)

# Program starts here. Check commandline arguments.

args = parser.parse_args()

if len(args.file) < 2:
    sys.stderr.write("Please specify at least two EDXML files for merging.\n")
    sys.exit()

# Create a SAX parser, and provide it with
# an EDXMLParser instance as content handler.
# This places the EDXMLParser instance in the
# XML processing chain, just after SaxParser.

sax_parser = make_parser()
edxml_parser = EDXMLPullFilter(sax_parser, True)

sax_parser.setContentHandler(edxml_parser)

# First, we parse all specified EDXML files
# using the EDXMLParser, which will compile
# and merge all event type, object type
# and source definitions in the EDXML files.

for file_name in args.file:
    sys.stderr.write("\nParsing file %s:" % file_name)

    try:
        sax_parser.parse(file_name)
    except ProcessingInterrupted:
        pass
    except EDXMLError as Error:
        sys.stderr.write("\n\nEDXML file %s is inconsistent with previous files:\n\n%s" % (
            file_name, str(Error)))
        sys.exit(1)
    except Exception:
        raise

# Use the EDXMLDefinitions instance of EDXMLParser to
# generate a set of new, unique source IDs. The resulting
# dictionary maps Source URLs to source IDs.

source_id_mapping = edxml_parser.Definitions.UniqueSourceIDs()

sax_parser = make_parser()
merger = EDXMLMerger(sax_parser, edxml_parser.Definitions, source_id_mapping)

sax_parser.setContentHandler(merger)

# Now we process each of the specified EDXML files
# a second time. We will feed each file into the
# Merger, which will output the merged
# definitions and translate event source IDs.

for file_name in input_file_names:
    sys.stderr.write("\nMerging file %s:" % file_name)

    try:
        sax_parser.parse(open(file_name))
    except ProcessingInterrupted:
        pass
    except EDXMLError as Error:
        sys.stderr.write("\n\nEDXML file %s is incompatible with previous files:\n\n%s" % (
            (file_name, str(Error))))
        sys.exit(1)
    except Exception:
        raise

# Finish the EDXML stream.
merger.close()
