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

import string
import sys

from edxml.EDXMLParser import EDXMLPullParser


def print_help():

    print("""

   This utility outputs various statistics for a set of EDXML files. It
   prints event counts, lists defined event types, object types, source
   URLs, and so on.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. It can be specified multiple
                       times to get aggregated statistics for multiple
                       input files. If the argument is not used, input
                       data is read from standard input.

   Example:

     edxml-stats.py -f input01.edxml -f input02.edxml

""")

# Program starts here.


argument_count = len(sys.argv)
current_argument = 1
input_files = []

# Parse commandline arguments

while current_argument < argument_count:

    if sys.argv[current_argument] in ('-h', '--help'):
        print_help()
        sys.exit(0)

    elif sys.argv[current_argument] == '-f':
        current_argument += 1
        input_files.append((current_argument, sys.argv[current_argument]))

    else:
        sys.stderr.write("Unknown commandline argument: %s\n" %
                         sys.argv[current_argument])
        sys.exit()

    current_argument += 1

parser = EDXMLPullParser(validate=False)

if len(input_files) == 0:

    # Feed the parser from standard input.
    input_files = [('standard input', sys.stdin)]
    sys.stderr.write(
        'Waiting for EDXML data on standard input... (use --help option to get help)\n')

# We repeatedly use the same parser to process all EDXML files in succession.

for file_name, file in input_files:
    sys.stderr.write("Processing %s..." % file_name)

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
    for relation in event_type.get_property_relations():
        predicates.add(relation.get_type_predicate())

print("\nProperty relation predicates:\n")
for Predicate in sorted(predicates):
    print(Predicate)

print("\nSource URLs:\n")
for uri in sorted(parser.get_ontology().get_event_sources().keys()):
    print(uri)
