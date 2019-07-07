#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                          EDXML Statistics Utility
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
#  This python script outputs various statistics for a set of EDXML files.
#  It prints event counts, lists defined event types, object types, source
#  URLs, and so on.
import argparse
import string
import sys

from edxml.EDXMLParser import EDXMLPullParser

# Program starts here.

parser = argparse.ArgumentParser(
    description="This utility prints various statistics for a given EDXML input file."
)

parser.add_argument(
    '-f',
    '--file',
    type=str,
    action='append',
    help='By default, input is read from standard input. This option can be used to read from a'
         'file in stead. The argument can be used multiple times to compute aggregate statistics'
         'of multiple input files.'
)

args = parser.parse_args()

if args.file is None:

    # Feed the parser from standard input.
    args.file = [sys.stdin]

parser = EDXMLPullParser(validate=False)

# We repeatedly use the same parser to process all EDXML files in succession.

for file in args.file:
    sys.stderr.write("edxml-stats: processing %s..." % (file if isinstance(file, str) else 'data from standard input'))

    try:
        parser.parse(file)
    except KeyboardInterrupt:
        sys.exit(0)

print("\n")
print("Total event count: %s\n" % parser.get_event_counter())
print("Event counts per type:\n")

for event_type_name in sorted(parser.get_ontology().get_event_type_names()):
    print("%s: %s" % (string.ljust(event_type_name, 40),
                      parser.get_event_type_counter(event_type_name)))

print("\nObject Types:\n")

for object_type_name in sorted(parser.get_ontology().get_object_type_names()):
    data_type = parser.get_ontology().get_object_type(object_type_name).get_data_type()
    print("%s: %s" % (string.ljust(object_type_name, 40), str(data_type)))

predicates = set()
for event_type_name, event_type in parser.get_ontology().get_event_types().items():
    for relation in event_type.get_property_relations().values():
        predicates.add(relation.get_predicate())

print("\nProperty relation predicates:\n")
for Predicate in sorted(predicates):
    print(Predicate)

print("\nSource URLs:\n")
for uri in sorted(parser.get_ontology().get_event_sources().keys()):
    print(uri)
