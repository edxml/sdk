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
from datetime import datetime

import pytz
from dateutil.parser import parse

from edxml.cli import configure_logger
from edxml.filter import EDXMLPullFilter
from edxml.ontology import DataType


class EDXMLReplay(EDXMLPullFilter):

    class UnbufferedStdout(object):
        # This is a wrapper to create an unbuffered
        # version of sys.stdout.

        def __init__(self, stream):
            self.stream = stream

        def write(self, data):
            self.stream.write(data)
            self.stream.flush()

        def __getattr__(self, attr):
            return getattr(self.stream, attr)

    def __init__(self, speed_multiplier, buffer_stuffer_enabled):

        self.time_shift = None
        self.speed_multiplier = speed_multiplier
        self.buffer_stuffer_enabled = buffer_stuffer_enabled
        self.date_time_properties = []
        self.known_properties = []
        self.current_event_type_name = None

        # Call parent class constructor
        super().__init__(EDXMLReplay.UnbufferedStdout(sys.stdout))

    def _parsed_event(self, event):

        date_time_strings = []
        date_time_objects = []
        new_event_objects = []

        if self.buffer_stuffer_enabled:
            # Generate a 4K comment.
            print('<!-- ' + 'x' * 4096 + ' -->')

        # Find all timestamps in event
        for property_name, objects in event.get_properties().items():
            if property_name not in self.known_properties:
                datatype = self._ontology.get_event_type(self.current_event_type_name)[property_name].get_data_type()
                if str(datatype) == 'datetime':
                    self.date_time_properties.append(property_name)
                self.known_properties.append(property_name)

            if property_name in self.date_time_properties:
                date_time_objects.append((property_name, objects))
                date_time_strings.extend(objects)
            else:
                # We copy all event objects, except
                # for the timestamps
                new_event_objects.extend(objects)

        if len(date_time_strings) > 0:
            # We will use the smallest timestamp
            # as the event timestamp. Note that we
            # use lexicographical ordering here.
            current_event_date_time = parse(min(date_time_strings))
            if self.time_shift:

                # Determine how much time remains before
                # the event should be output.
                delay = (current_event_date_time - datetime.now(pytz.UTC)
                         ).total_seconds() + self.time_shift
                if delay >= 0:
                    time.sleep(delay * self.speed_multiplier)

                    # If SpeedMultiplier < 1, it means we will wait shorter
                    # than the time between current and previous event. That
                    # means that the next event will be farther away in the
                    # future, and require longer delays. All delays that we
                    # skip due to the SpeedMultiplier will add up, event output
                    # speed will drop. To compensate for this effect, we also
                    # shift the entire dataset back in time. If SpeedMultiplier
                    # is larger than 1, the opposite effect occurs.
                    self.time_shift += (self.speed_multiplier - 1.0) * delay
            else:
                # Determine the global time shift between
                # the input dataset and the current time.
                self.time_shift = (datetime.now(pytz.UTC) -
                                   current_event_date_time).total_seconds()

            # Now we add the timestamp objects, replacing
            # their values with the current time.
            for property_name, objects in date_time_objects:
                event[property_name] = [DataType.format_utc_datetime(
                    datetime.now(tz=pytz.utc)) for _ in objects]

        EDXMLPullFilter._parsed_event(self, event)


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
        '-b',
        '--with-buffer-stuffer',
        action='store_true',
        help='Enable the "Buffer Stuffer", which inserts bogus comments between the output events. '
             'Some applications may buffer their input, resulting in high response latency when '
             'feeding them with events at very low rates. This option may help to "write through" '
             'their input buffer.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    args = parser.parse_args()

    configure_logger(args)

    input = open(args.file, 'rb') if args.file else sys.stdin

    with EDXMLReplay(args.speed, args.with_buffer_stuffer) as replay:
        try:
            replay.parse(input)
        except KeyboardInterrupt:
            sys.exit()


if __name__ == "__main__":
    main()
