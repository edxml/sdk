#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                      EDXML Ontology Replacement Utility
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
#  This utility replaces the eventtype definition of one EDXML file with those
#  contained in another EDXML file. The resulting EDXML stream is validated
#  against the new ontology and written to standard output.

import sys

from edxml.error import EDXMLValidationError
from edxml.EDXMLFilter import EDXMLPullFilter
from edxml.EDXMLParser import EDXMLOntologyPullParser, ProcessingInterrupted


class EDXMLDefinitionSwapper(EDXMLPullFilter):

    def __init__(self, other_ontology, output=sys.stdout):

        super(EDXMLDefinitionSwapper, self).__init__(output)
        self.otherOntology = other_ontology

    def _parsed_ontology(self, parsed_ontology):
        EDXMLPullFilter._parsed_ontology(self, self.otherOntology)


def print_help():

    print("""

   This utility replaces the eventtype definitions of one EDXML file with those
   contained in another EDXML file. The resulting EDXML stream is validated
   against the new ontology and written to standard output.

   Options:

     -h, --help        Prints this help text

     -f                This option must be followed by a filename, which
                       will be used as input. If this option is not specified,
                       input will be read from standard input.

   Example:

     cat input.edxml | edxml-replace-ontology.py -o ontology-source.edxml > output.edxml

""")

# Program starts here.


argument_count = len(sys.argv)
current_argument = 1
ontology_file_name = None
event_input = sys.stdin

# Parse commandline arguments

while current_argument < argument_count:

    if sys.argv[current_argument] in ('-h', '--help'):
        print_help()
        sys.exit(0)

    elif sys.argv[current_argument] == '-f':
        current_argument += 1
        event_input = open(sys.argv[current_argument])

    elif sys.argv[current_argument] == '-o':
        current_argument += 1
        ontology_file_name = sys.argv[current_argument]

    else:
        sys.stderr.write("Unknown commandline argument: %s\n" %
                         sys.argv[current_argument])
        sys.exit()

    current_argument += 1

# Program starts here. Check commandline arguments.

if ontology_file_name is None:
    sys.stderr.write(
        "No ontology source was specified. Use the --help option to get help.\n")
    sys.exit()

sys.stderr.write("\nUsing file '%s' as ontology source." % ontology_file_name)

parser = EDXMLOntologyPullParser()

# Parse the ontology from the specified
# EDXML file.

if event_input == sys.stdin:
    sys.stderr.write(
        'Waiting for EDXML data on standard input... (use --help option to get help)\n')

try:
    parser.parse(open(ontology_file_name))
except ProcessingInterrupted:
    pass
except EDXMLValidationError as Error:
    sys.stderr.write("\n\nOntology source file '%s' is invalid EDXML:\n\n%s" % (
        ontology_file_name, str(Error)))
    sys.exit(1)
except Exception:
    raise

# Now parse the input while swapping the ontology.
with EDXMLDefinitionSwapper(parser.get_ontology()) as swapper:
    try:
        swapper.parse(event_input)
    except KeyboardInterrupt:
        pass
