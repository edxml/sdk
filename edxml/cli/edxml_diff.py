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

#  This script shows the semantic difference between two EDXML data files (A and B)
#  showing only the differences that would actually result in the EDXML data being
#  interpreted in a different way by EDXML parsers. For example, the ordering of
#  events is not relevant. Also, when data file A contains a series of updates of
#  an event while data file B contains a single events having all updated merged
#  into it, then there is no difference.
#  The utility needs to load both data files into memory and is intended for use
#  in automated tests, comparing a small EDXML output file with expected output.

import argparse
import sys
from io import BytesIO
from difflib import unified_diff

from edxml import EDXMLPullParser
from edxml.cli import configure_logger
from edxml.writer import EDXMLWriter
from edxml.event import EventElement


class SortingParser(EDXMLPullParser):

    def __init__(self):
        super().__init__()
        self._events_by_hash = {}

    def _parsed_event(self, event):
        event_type = self.get_ontology().get_event_type(event.get_type_name())
        event_hash = event.compute_sticky_hash(event_type)
        if event_hash in self._events_by_hash:
            # Since we compute a semantic, logical difference, we merge data
            # from all physical events that constitute the same logical event.
            self._events_by_hash[event_hash] = event_type.merge_events([self._events_by_hash[event_hash], event])
        else:
            self._events_by_hash[event_hash] = event

    def generate_sorted_edxml(self):
        edxml = BytesIO()

        # Generate EDXML data by adding the events sorted by sticky hash.
        with EDXMLWriter(edxml) as writer:
            writer.add_ontology(self.get_ontology())
            for hash, event in sorted(self._events_by_hash.items()):
                # NOTE: Below we use EventElement.create_from_event() to get rid of the
                #       XML namespaces that all ParsedEvent instances have.
                writer.add_event(EventElement.create_from_event(event), sort=True)

        return edxml.getvalue()


class EdxmlDiffer(object):
    _a = SortingParser()
    _b = SortingParser()

    def parse_a_from(self, edxml_file):
        self._a.parse(edxml_file)

    def parse_b_from(self, edxml_file):
        self._b.parse(edxml_file)

    def print_diff(self):
        edxml_a = self._a.generate_sorted_edxml()
        edxml_b = self._b.generate_sorted_edxml()

        diff = list(unified_diff(edxml_a.split(b'\n'), edxml_b.split(b'\n')))

        print('\n'.join(diff))

        return diff != []


def main():
    parser = argparse.ArgumentParser(
        description="Computes the semantic difference between two EDXML data files, outputting the differences on "
                    "standard output. Exit status is zero when the data files are semantically identical."
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        action='append',
        help='Reads specified EDXML file to compute the diff. When it is used just once, '
             'EDXML data will be read from standard input to compute the difference.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    args = parser.parse_args()

    configure_logger(args)

    if not args.file or len(args.file) < 1:
        parser.error('You must specify at least one file.')

    if len(args.file) > 2:
        parser.error('You cannot specify more than two files.')

    if len(args.file) == 1:
        args.file.append(sys.stdin.buffer)

    differ = EdxmlDiffer()

    try:
        differ.parse_a_from(args.file[0])
        differ.parse_b_from(args.file[1])
    except KeyboardInterrupt:
        exit()

    exit(differ.print_diff())


if __name__ == "__main__":
    main()
