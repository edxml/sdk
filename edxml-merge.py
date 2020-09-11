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

from edxml import EDXMLOntologyPullParser
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
    def __init__(self, merged_definitions):
        # Initialize source id / url mappings
        super().__init__(sys.stdout)
        self.merged_definitions = merged_definitions

    def _parsed_ontology(self, parsed_ontology):
        super()._parsed_ontology(self.merged_definitions)


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

parser = EDXMLOntologyPullParser()

# First, we parse all specified EDXML files
# using the EDXMLParser, which will compile
# and merge all event type, object type
# and source definitions in the EDXML files.

for file_name in args.file:
    sys.stderr.write("\nParsing file %s:" % file_name)

    try:
        parser.parse(file_name)
    except ProcessingInterrupted:
        pass
    except EDXMLError as Error:
        sys.stderr.write("\n\nEDXML file %s is inconsistent with previous files:\n\n%s" % (
            file_name, str(Error)))
        sys.exit(1)
    except Exception:
        raise

# Now we process each of the specified EDXML files
# a second time. We will feed each file into the
# Merger, which will output the merged ontology
# and pass through the event groups translate event source IDs.

with EDXMLMerger(parser.get_ontology()) as merger:
    for file_name in args.file:
        sys.stderr.write("\nMerging file %s:" % file_name)
        try:
            merger.parse(open(file_name))
        except ProcessingInterrupted:
            pass
        except EDXMLError as Error:
            sys.stderr.write("\n\nEDXML file %s is incompatible with previous files:\n\n%s" % (
                (file_name, str(Error))))
            sys.exit(1)
        except Exception:
            raise
