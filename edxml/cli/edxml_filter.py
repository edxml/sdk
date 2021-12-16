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

#  This utility reads an EDXML document from a file or from standard input and filters it
#  according to the user supplied parameters. The result is sent to standard output.


import argparse
import sys
import re

from copy import deepcopy
from edxml.cli import configure_logger
from edxml.filter import EDXMLPullFilter
from edxml.logger import log


class EDXMLFilter(EDXMLPullFilter):
    def __init__(self, source_uri_regex, event_type_name_regex):
        super().__init__(output=sys.stdout.buffer)
        self.__source_uri_regex = source_uri_regex
        self.__event_type_name_regex = event_type_name_regex
        self.__deleted_event_types = []
        self.__deleted_sources = []
        self.__num_processed = 0
        self.__num_deleted = 0

    def _parsed_ontology(self, parsed_ontology, filtered_ontology=None):
        for event_type_name in parsed_ontology.get_event_type_names():
            if re.match(self.__event_type_name_regex, event_type_name) is None:
                self.__deleted_event_types.append(event_type_name)

        for source_uri, source in parsed_ontology.get_event_sources().items():
            if re.match(self.__source_uri_regex, source_uri) is None:
                self.__deleted_sources.append(source_uri)

        # Now we need to check for any event types that were removed while
        # being the parent of another event type. That yields an invalid
        # ontology.

        for event_type_name, event_type in parsed_ontology.get_event_types().items():
            if event_type.get_parent() is not None:
                if event_type.get_parent().get_event_type_name() in self.__deleted_event_types:
                    # The parent of a child event type is about to be deleted. That would yield
                    # an invalid ontology, so we will not delete it.
                    self.__deleted_event_types.remove(event_type.get_parent().get_event_type_name())

        filtered_ontology = deepcopy(parsed_ontology)

        for event_type_name in self.__deleted_event_types:
            filtered_ontology.delete_event_type(event_type_name)
        for uri in self.__deleted_sources:
            filtered_ontology.delete_event_source(uri)

        filtered_ontology.validate()

        super()._parsed_ontology(parsed_ontology, filtered_ontology)

    def _parsed_event(self, event):
        self.__num_processed += 1

        if event.get_type_name() in self.__deleted_event_types:
            self.__num_deleted += 1
            return
        if event.get_source_uri() in self.__deleted_sources:
            self.__num_deleted += 1
            return

        super()._parsed_event(event)

    def _close(self):
        super()._close()
        log.info(f"Processed {self.__num_processed} events, deleted {self.__num_deleted}.")


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
        help='A regular expression matching the source URIs of events that will be copied to the output.'
    )

    parser.add_argument(
        '-e',
        '--event-type',
        type=str,
        help='A regular expression matching the types of events that will be copied to the output.'
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
    type_filter = re.compile(args.event_type or '.*')

    with EDXMLFilter(source_filter, type_filter) as event_filter:
        try:
            event_filter.parse(event_input)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        exit(1)
