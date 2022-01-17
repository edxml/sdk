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

#  This script accepts EDXML data as input and writes time shifted events to standard
#  output. Timestamps of input events are shifted to the current time. This is useful
#  for simulating live EDXML data sources using previously recorded data. Note that
#  the script assumes that the events in the input stream are time ordered.

import argparse
import sys
import time
from collections import defaultdict
from datetime import datetime

import pytz
from dateutil.parser import parse

from edxml.cli import configure_logger
from edxml.filter import EDXMLPushFilter
from edxml.ontology import DataType


class EDXMLReplay(EDXMLPushFilter):

    class UnbufferedStdout(object):
        # This is a wrapper to create an unbuffered
        # version of sys.stdout.

        def __init__(self, stream):
            self.stream = stream

        def write(self, data):
            self.stream.write(data)
            self.stream.flush()

    def __init__(self, speed_multiplier):

        self.time_prev_event_input = None
        self.speed_multiplier = speed_multiplier
        self.date_time_properties = defaultdict(list)
        self.known_properties = defaultdict(list)

        # Call parent class constructor
        super().__init__(EDXMLReplay.UnbufferedStdout(sys.stdout.buffer))

    def _parsed_ontology(self, parsed_ontology, filtered_ontology=None):
        self.known_properties = defaultdict(list)
        self.date_time_properties = defaultdict(list)
        super()._parsed_ontology(parsed_ontology)

    def _parsed_event(self, event):

        timespan_start, timespan_end = self._get_event_timespan_info(event)

        if timespan_start is not None:
            timespan_start_property, start = timespan_start
            if start is not None:
                if self.time_prev_event_input:
                    delay = (start - self.time_prev_event_input).total_seconds() / self.speed_multiplier

                    if delay >= 0:
                        time.sleep(delay)

                # Now we set the event property that represents
                # the start of the event time span to the current
                # time. Then we also time shift any other datetime
                # properties accordingly. This way we keep relative
                # time within the event intact, except that we do take
                # the speed multiplier into account.
                now = datetime.now(tz=pytz.utc)
                event[timespan_start_property] = DataType.format_utc_datetime(now)

                if timespan_end is not None:
                    timespan_end_property, end = timespan_end
                    event[timespan_end_property] = DataType.format_utc_datetime(
                        now + (end - start) / self.speed_multiplier
                    )

                self.time_prev_event_input = start

        EDXMLPushFilter._parsed_event(self, event)

    def _get_event_timespan_info(self, event):
        event_type_name = event.get_type_name()
        event_type = self._ontology.get_event_type(event.get_type_name())
        start, end = event_type.get_timespan_property_names()

        timespan_start = None
        timespan_end = None

        if start is not None and start in event:
            timespan_start = (start, parse(next(iter(event[start]))))
        if end is not None and end in event:
            timespan_end = (end, max([parse(value) for value in event[end]]))

        if timespan_start is not None and timespan_end is not None:
            return timespan_start, timespan_end

        # We do not have a complete time span yet as
        # the time span is not fully defined explicitly.
        # We will proceed to consider all datetime values
        # in the event and find their range.

        if event_type_name not in self.known_properties:
            for property_name, objects in event.get_properties().items():
                datatype = self._ontology.get_event_type(event.get_type_name())[property_name].get_data_type()
                if str(datatype) == 'datetime':
                    self.date_time_properties[event_type_name].append(property_name)
                self.known_properties[event_type_name].append(property_name)

        date_time_strings = []

        for property_name in self.date_time_properties[event_type_name]:
            if property_name in event:
                date_time_strings.append((property_name, [parse(value) for value in event[property_name]]))

        if len(date_time_strings) == 0:
            # There is no time data in the event.
            return None, None

        # Find the smallest / greatest datetime value for
        # any missing timespan start or end.
        # Note that we use lexicographical ordering here.

        if timespan_start is None:
            date_time_strings = list(sorted(date_time_strings, key=lambda item: min(item[1])))
            timespan_start = (date_time_strings[0][0], min(date_time_strings[0][1]))

        if timespan_end is None:
            date_time_strings = list(sorted(date_time_strings, key=lambda item: max(item[1])))
            timespan_end = (date_time_strings[-1][0], max(date_time_strings[-1][1]))

        return timespan_start, timespan_end


def main():
    parser = argparse.ArgumentParser(
        description="This utility accepts EDXML data as input and writes time shifted events to standard "
                    "output. Timestamps of input events are shifted to the current time. This is useful "
                    "for simulating live EDXML data sources using previously recorded data. Note that "
                    "the script assumes that the events in the input stream are time ordered."
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
        '--speed',
        default=1.0,
        type=float,
        help='Optional speed multiplier. A value greater than 1.0 will make time appear to pass '
             'faster, a value smaller than 1.0 slows down event output. Default value is 1.0.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    args = parser.parse_args()

    configure_logger(args)

    data = open(args.file, 'rb') if args.file else sys.stdin.buffer

    with EDXMLReplay(args.speed) as replay:
        line = None
        while line != b'':
            line = data.readline()
            replay.feed(line)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        sys.exit()
