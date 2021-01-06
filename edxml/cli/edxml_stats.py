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

#  This python script outputs various statistics for a set of EDXML files.
#  It prints event counts, lists defined event types, object types, source
#  URLs, and so on.

import argparse
import logging
import operator
import sys
from collections import defaultdict
from typing import Dict, List, Optional

from dateutil.parser import parse
from edxml.cli import configure_logger
from edxml.parser import EDXMLPullParser


class StatsParser(EDXMLPullParser):

    def __init__(self):
        super().__init__(validate=False)
        self.event_type_counters = defaultdict(int)
        self.property_stats = defaultdict(lambda: defaultdict(lambda: {'total': 0, '0': 0, '1': 0, '>1': 0}))
        self.source_uris = defaultdict(int)
        self.object_type_counters = defaultdict(int)
        self.object_value_counters = defaultdict(lambda: defaultdict(int))
        self.property_value_counters = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        self.concepts = defaultdict(set)
        self.timespan = [None, None]  # type: List[Optional[str], Optional[str]]
        self.type_time_spans = defaultdict(lambda: [None, None])  # type: Dict[str, List[Optional[str], Optional[str]]]

    def _parsed_event(self, event):
        event_type_name = event.get_type_name()
        event_type = self.get_ontology().get_event_type(event_type_name)

        self.event_type_counters[event_type_name] += 1
        self.source_uris[event.get_source_uri()] += 1

        for property_name in event_type.get_properties().keys():
            objects = event[property_name]
            self.property_stats[event_type_name][property_name]['total'] += len(objects)
            if len(objects) == 0:
                self.property_stats[event_type_name][property_name]['0'] += 1
            elif len(objects) == 1:
                self.property_stats[event_type_name][property_name]['1'] += 1
            else:
                self.property_stats[event_type_name][property_name]['>1'] += 1

            prop = event_type.get_properties()[property_name]
            concept_associations = prop.get_concept_associations()
            for concept_name in concept_associations.keys():
                for object_value in objects:
                    self.concepts[concept_name].add(object_value)

            object_type_name = prop.get_object_type_name()
            self.object_type_counters[object_type_name] += len(objects)
            for object_value in objects:
                self.object_value_counters[object_type_name][object_value] += 1
                self.property_value_counters[event_type_name][property_name][object_value] += 1

        timespan_start, timespan_end = event_type.get_timespan_property_names()

        timespan_start_objects = event.properties[timespan_start] if timespan_start else set()
        timespan_end_objects = event.properties[timespan_end] if timespan_end else set()

        if timespan_start:
            # Event time span has a beginning and possibly an end.
            if self.timespan[0] is None:
                self.timespan[0] = min(timespan_start_objects)
            if self.type_time_spans[event_type_name][0] is None:
                self.type_time_spans[event_type_name][0] = min(timespan_start_objects)

            self.timespan[0] = min(self.timespan[0], *timespan_start_objects)
            self.type_time_spans[event_type_name][0] = min(
                self.type_time_spans[event_type_name][0], *timespan_start_objects
            )

            if timespan_end is None:
                # Event time span has a beginning but no end. It is a point in time.
                # The start and end of the time span will be identical.
                timespan_end_objects = timespan_start_objects

            if self.timespan[1] is None:
                self.timespan[1] = max(timespan_end_objects)
            if self.type_time_spans[event_type_name][1] is None:
                self.type_time_spans[event_type_name][1] = max(timespan_end_objects)
            self.timespan[1] = max(self.timespan[1], *timespan_end_objects)
            self.type_time_spans[event_type_name][1] = max(
                self.type_time_spans[event_type_name][1], *timespan_end_objects
            )
        else:
            # Event has no defined time span. It can still contain datetime
            # values, from which we will take the min / max values.
            for property_name, objects in event.properties.items():
                prop = event_type.get_properties()[property_name]
                if prop.get_object_type().get_data_type().is_datetime():
                    if self.timespan[0] is None:
                        self.timespan[0] = min(objects)
                    if self.timespan[1] is None:
                        self.timespan[1] = max(objects)
                    self.timespan[0] = min(self.timespan[0], *objects)
                    self.timespan[1] = max(self.timespan[1], *objects)
                    if self.type_time_spans[event_type_name][0] is None:
                        self.type_time_spans[event_type_name][0] = min(objects)
                    if self.type_time_spans[event_type_name][1] is None:
                        self.type_time_spans[event_type_name][1] = max(objects)
                    self.type_time_spans[event_type_name][0] = min(self.type_time_spans[event_type_name][0], *objects)
                    self.type_time_spans[event_type_name][1] = max(self.type_time_spans[event_type_name][1], *objects)


def format_timespan(timespan):
    return [
        parse(timespan[0]).strftime('%Y-%m-%d %H:%M:%S') if timespan[0] else '-∞',
        parse(timespan[1]).strftime('%Y-%m-%d %H:%M:%S') if timespan[1] else '+∞'
    ]


def format_count(count):
    if count >= 1000000:
        return '%.1fM' % (float(count) / 1000000)
    elif count >= 10000:
        return '%.1fk' % (float(count) / 1000)
    else:
        return '%d' % count


def print_covered_time_spans(parser):
    for event_type_name, timespan in parser.type_time_spans.items():
        if parser.get_ontology().get_event_type(event_type_name).is_timeless():
            continue
        start, end = format_timespan(timespan)
        print('%s: %s - %s' % (event_type_name.ljust(64), start, end))


def print_event_counts_per_type(parser):
    counts = {}
    for event_type_name in parser.get_ontology().get_event_type_names():
        counts[event_type_name] = parser.get_event_type_counter(event_type_name)

    for event_type_name, count in reversed(sorted(counts.items(), key=operator.itemgetter(1))):
        print('%s: %s' % (event_type_name.ljust(64), count))


def print_property_stats(parser, event_type_name):
    total = parser.event_type_counters.get(event_type_name)
    for property_name, stats in parser.property_stats.get(event_type_name, {}).items():
        print(
            '%s %-6s %-6s %-6s %-6s %-6s %-6s' %
            (
                property_name.ljust(32),
                format_count(total),
                sum(parser.property_value_counters[event_type_name][property_name].values()),
                len(parser.property_value_counters[event_type_name][property_name]),
                format_count(stats['0']),
                format_count(stats['1']),
                format_count(stats['>1'])
             )
        )


def print_object_type_stats(parser):
    for object_type_name, count in reversed(sorted(parser.object_type_counters.items(), key=operator.itemgetter(1))):
        distinct_count = len(parser.object_value_counters[object_type_name])
        print('%s: %d (%d)' % (object_type_name.ljust(64), count, distinct_count))


def print_object_values(parser, object_type_name):
    values = parser.object_value_counters.get(object_type_name, [])
    for value, count in reversed(sorted(values.items(), key=operator.itemgetter(1))):
        print('%d\t%s' % (count, value))


def print_concept_stats(parser):
    for concept_name, values in sorted(parser.concepts.items()):
        print('%s: %d' % (concept_name.ljust(64), len(values)))


def print_source_stats(parser):
    for uri in sorted(parser.get_ontology().get_event_sources().keys()):
        print('%s: %s' % (uri.ljust(64), parser.source_uris.get(uri)))


def parse_args():
    parser = argparse.ArgumentParser(
        description="This utility prints various statistics for one or more EDXML input files."
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        action='append',
        help='By default, input is read from standard input. This option can be used to read from a '
             'file in stead. The argument can be used multiple times to compute aggregate statistics'
             'of multiple input files.'
    )

    parser.add_argument(
        '-c',
        '--count',
        action='store_true',
        help='Prints the total number of events in the input. All other output is suppressed.'
    )

    parser.add_argument(
        '--event-types',
        action='store_true',
        help='Prints the event types that are defined in the data. All other output is suppressed.'
    )

    parser.add_argument(
        '--object-types',
        action='store_true',
        help='Prints the object types that are defined in the data. All other output is suppressed.'
    )

    parser.add_argument(
        '--source-uris',
        action='store_true',
        help='Prints the event source URIs that are defined in the data. All other output is suppressed.'
    )

    parser.add_argument(
        '--concepts',
        action='store_true',
        help='Prints the concepts that are defined in the data. All other output is suppressed.'
    )

    parser.add_argument(
        '--object-values',
        type=str,
        help='Prints the values of specified object type and their occurrence frequencies in the input. '
             'The output is two tab separated columns containing frequency and value, in that order. '
             'All other output is suppressed.'
    )

    parser.add_argument(
        '--property-stats',
        type=str,
        help='Prints statistics for each of the properties of specified event type. The printed statistics '
             'are the total number of events, the total number of values for the property, the number of '
             'events that have no values for the property, '
             'the number of events that have exactly one value and the number of events that have multiple '
             'values for the property, in that order. All other output is suppressed.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    return parser.parse_args()


def print_full_stats(parser):
    print('\nTotal event count: %s' % parser.get_event_counter())

    print('\nTotal covered time span: %s - %s\n' % tuple(format_timespan(parser.timespan)))
    print_covered_time_spans(parser)

    print('\nEvent counts per type:\n')
    print_event_counts_per_type(parser)

    print("\nSource URIs:\n")
    print_source_stats(parser)

    print("\nGenerated values per object type (unique in parenthesis):\n")
    print_object_type_stats(parser)

    print("\nConcept seeds:\n")
    print_concept_stats(parser)


def main():
    args = parse_args()

    configure_logger(args)

    if args.file is None:

        # Feed the parser from standard input.
        args.file = [sys.stdin.buffer]

    parser = StatsParser()

    # We repeatedly use the same parser to process all EDXML files in succession.

    for file in args.file:
        logging.info(
            "edxml-stats: processing %s..." % (file if isinstance(file, str) else 'data from standard input')
        )

        try:
            parser.parse(file).close()
        except KeyboardInterrupt:
            sys.exit(0)

    if args.count:
        print(parser.get_event_counter())
    elif args.event_types:
        print('\n'.join(parser.get_ontology().get_event_type_names()))
    elif args.object_types:
        print('\n'.join(parser.get_ontology().get_object_type_names()))
    elif args.source_uris:
        print('\n'.join(parser.get_ontology().get_event_source_uris()))
    elif args.concepts:
        print('\n'.join(parser.get_ontology().get_concept_names()))
    elif args.object_values:
        print_object_values(parser, args.object_values)
    elif args.property_stats:
        print_property_stats(parser, args.property_stats)
    else:
        print_full_stats(parser)


if __name__ == "__main__":
    main()
