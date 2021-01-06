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

#  This utility reads an EDXML stream from standard input and filters it according
#  to the user supplied parameters. The result is sent to standard output.


import argparse
import sys
import re

from edxml.cli import configure_logger
from edxml.filter import EDXMLPullFilter


class EDXMLEventGroupFilter(EDXMLPullFilter):
    def __init__(self, source_uri_pattern, event_type_name):
        super().__init__(sys.stdout, False)
        self.__source_uri_pattern = source_uri_pattern
        self.__event_type_name = event_type_name
        self.__pass_through = True

    def _parsed_ontology(self, parsed_ontology):
        filtered_event_types = []
        filtered_sources = []

        if self.__event_type_name:
            for event_type_name in parsed_ontology.get_event_type_names():
                if event_type_name != self.__event_type_name:
                    filtered_event_types.append(event_type_name)

        for sourceUri, source in parsed_ontology.get_event_sources().items():
            if re.match(self.__source_uri_pattern, sourceUri) is not None:
                filtered_sources.append(sourceUri)

        for event_type_name in filtered_event_types:
            parsed_ontology.delete_event_type(event_type_name)
        for eventSource in filtered_sources:
            parsed_ontology.delete_event_source(eventSource)

        parsed_ontology.validate()

        super()._parsed_ontology(parsed_ontology)

    def _open_event_group(self, event_type_name, event_source_uri):

        if self.get_ontology().get_event_source(event_source_uri) is None:
            # Source is gone, turn filter output off.
            self.__pass_through = False
            event_type_name = None
            event_source_uri = None

        if self.get_ontology().get_event_type(event_type_name) is None:
            # Event type is gone, turn filter output off.
            self.__pass_through = False
            event_type_name = None
            event_source_uri = None

        if self.__pass_through:
            super()._open_event_group(event_type_name, event_source_uri)

    def _parsed_event(self, event):
        if self.__pass_through:
            super()._parsed_event(event)


def parse_args():
    parser = argparse.ArgumentParser(
        description='This utility reads an EDXML stream from standard input and filters it according '
                    'to the user supplied parameters. The result is sent to standard output.'
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='By default, input is read from standard input. This option can be used to read from a '
             'file in stead.'
    )

    parser.add_argument(
        '-s',
        '--source-uri',
        type=str,
        help='A regular expression that will be used to filter the event source URI in the input events.'
    )

    parser.add_argument(
        '-e',
        '--event-type',
        type=str,
        help='An event type name that will be used to filter the event types in the input events.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    return parser.parse_args()


def main():
    args = parse_args()

    configure_logger(args)

    event_input = open(args.file, 'rb') if args.file else sys.stdin.buffer

    source_filter = re.compile(args.source_uri or '.*')

    with EDXMLEventGroupFilter(source_filter, args.event_type) as event_filter:
        try:
            event_filter.parse(event_input)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
