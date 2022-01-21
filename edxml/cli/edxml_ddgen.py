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

#  This script generates dummy EDXML data streams, which may be useful for stress
#  testing EDXML processing systems and storage back ends.

import argparse
import logging
import sys
import time
import random
from datetime import datetime

import edxml.ontology
from edxml import EDXMLEvent
from edxml.cli import configure_logger
from edxml.ontology import DataType
from edxml.writer import EDXMLWriter


class EDXMLDummyDataGenerator(EDXMLWriter):

    def __init__(self, args, validate=False):

        self.event_counter = 0
        self.args = args
        self.generate_collisions = args.collision_rate > 0
        self.random_content_characters = 'abcdefghijklmnop  '
        self.random_content_characters_length = len(self.random_content_characters)
        self.time_start = time.time()

        # Call parent class constructor
        EDXMLWriter.__init__(self, validate=validate)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def start(self):
        self.write_definitions()
        self.write_events()
        self.close()

        time_elapsed = time.time() - self.time_start + 1e-9
        logging.info("Wrote %d events in %d seconds, %d events per second.\n" % (
            self.event_counter, time_elapsed, (self.event_counter / time_elapsed))
        )

    def write_events(self):

        interval_correction = 0
        requested_time_interval = 0

        random_content_characters = self.random_content_characters * \
            (int(self.args.content_size / self.random_content_characters_length) + 1)
        random_property_characters = self.random_content_characters * \
            (int(self.args.object_size / self.random_content_characters_length) + 1)

        # By default, event content is just a
        # string of asterisks.
        content = '*' * self.args.content_size

        # Set the default object values
        property_objects = {
            'property-a': ['value'],
            'property-b': ['value'],
            'property-c': ['10.000000000'],
            'property-d': ['100.000000000']
        }

        # To prevent colliding events from accumulating arbitrary
        # numbers of property 'property-b' (which has merge
        # strategy 'add'), we generate a small collection of random
        # strings for assigning to this property.
        add_property_values = [''.join(random.sample(
            random_property_characters, self.args.object_size)) for _ in range(10)]

        colliding_unique_property_values = [
            ''.join(random.sample(random_property_characters, self.args.object_size))
            for _ in range(self.args.collision_diversity)
        ]

        if self.args.rate > 0:
            requested_time_interval = 1.0 / self.args.rate

        time_start = time.time()

        while self.event_counter < self.args.limit or self.args.limit == 0:

            # Generate random content
            if self.args.random_content:
                content = ''.join(random.sample(
                    random_content_characters, self.args.content_size))

            # Generate random property values
            if self.args.random_objects:

                # A random string from a fixed set
                property_objects['property-b'] = [
                    random.choice(add_property_values)]

                for property_name in ['c', 'd']:
                    # Random values in range [-0.5,0.5]
                    property_objects['property-' + property_name] = ['%1.9f' % (random.random() - 0.5)]

            if self.generate_collisions:
                property_objects['version'] = self.event_counter

            if self.generate_collisions and random.random() * 100.0 < self.args.collision_rate:
                # The unique property is picked from a list of possible values, which
                # results in event collisions.
                property_objects['property-a'] = random.choice(colliding_unique_property_values)
            else:
                # The unique property is a completely random string
                property_objects['property-a'] = ''.join(random.sample(self.random_content_characters * (int(
                    self.args.object_size / self.random_content_characters_length) + 1),
                    self.args.object_size))

            property_objects['property-e'] = DataType.format_utc_datetime(datetime.utcnow())

            # Output one event
            self.add_event(
                EDXMLEvent(
                    property_objects,
                    event_type_name=self.args.event_type_name,
                    source_uri='/edxml-ddgen/',
                    attachments={'content': content} if content != '' else {}
                )
            )
            self.event_counter += 1

            if self.args.rate > 0:
                # An event rate is specified, which means we
                # need to keep track of time and use time.sleep()
                # to generate delays between events.

                current_time = time.time()
                time_delay = self.event_counter * requested_time_interval - (current_time - time_start)
                if time_delay + interval_correction > 0:
                    sys.stdout.flush()
                    time.sleep(time_delay + interval_correction)

                # Check if our output rate is significantly lower than requested,
                # print informative message is rate is too low.
                if self.event_counter > 10:
                    if (self.event_counter / (current_time - self.time_start)) < 0.8 * self.args.rate:
                        sys.stderr.write('Cannot keep up with requested event rate!\n')

                # Compute correction, to be added to the delay we pass to sleep.sleep().
                # We compare the mean time interval between events with the time interval
                # we are trying to achieve. Based on that, we compute the next time
                # interval correction. We need a correction, because the accuracy of our
                # time measurements is limited, which means time.sleep() may sleep slightly
                # longer than necessary.
                if self.event_counter > 0:
                    current_time = time.time()
                    mean_time_interval = (current_time - self.time_start) / self.event_counter
                    interval_correction = 0.5 * (interval_correction + (requested_time_interval - mean_time_interval))

    def write_definitions(self):

        # In case event collisions will be generated, we will adjust
        # the merge strategies of all properties to cause collisions
        # requiring all possible merge strategies to be applied in
        # order to merge them. The event merges effectively compute
        # the product, minimum value, maximum value etc. from
        # the individual objects in all input events.

        if self.generate_collisions:
            any_or_add = 'add'
            any_or_min = 'min'
            any_or_max = 'max'
        else:
            any_or_add = 'any'
            any_or_min = 'any'
            any_or_max = 'any'

        ontology = edxml.ontology.Ontology()

        ontology.create_object_type(self.args.object_type_name + '.a',
                                    data_type='string:%d:mc' % self.args.object_size)
        ontology.create_object_type(self.args.object_type_name + '.b', data_type='number:bigint:signed')
        ontology.create_object_type(self.args.object_type_name + '.c', data_type='number:decimal:12:9:signed')
        ontology.create_object_type('time', data_type='datetime')

        event_type = ontology.create_event_type(self.args.event_type_name)
        event_type.create_property('property-a', self.args.object_type_name + '.a').set_merge_strategy('match')
        event_type.create_property('property-b', self.args.object_type_name + '.a').set_merge_strategy(any_or_add)
        event_type.create_property('property-c', self.args.object_type_name + '.c').set_merge_strategy(any_or_min)
        event_type.create_property('property-d', self.args.object_type_name + '.c').set_merge_strategy(any_or_max)
        event_type.create_property('property-e', 'time').set_merge_strategy(any_or_min)

        event_type.set_timespan_property_name_start('property-e')
        event_type.set_timespan_property_name_end('property-e')

        if self.generate_collisions:
            ontology.create_object_type('version-number', data_type='sequence')
            event_type.create_property('version', 'version-number').set_merge_strategy('max')
            event_type.set_version_property_name('version')

        event_type.create_attachment('content')

        ontology.create_event_source('/edxml-ddgen/')

        self.add_ontology(ontology)


def main(validate=False):
    parser = argparse.ArgumentParser(description="Generate dummy events for testing purposes.")

    parser.add_argument(
        '-r',
        '--rate',
        default=0,
        type=float,
        help='By default, events will be generated at fast as possible. This option can be used to limit the '
             'rate to the specified number of events per second.'
    )

    parser.add_argument(
        '-c',
        '--collision-rate',
        default=0,
        type=int,
        help='This option triggers generation of event collisions. It must be followed '
             'by an integer percentage, which configures how often an event will collide '
             'with a previously generated event. A value of 100 makes all events collide, '
             'while a value of zero effectively disables collision generation. By default, '
             'no event collisions will be generated. Note: This has a performance impact.'
    )

    parser.add_argument(
        '-d',
        '--collision-diversity',
        default=100,
        type=int,
        help='This option controls the number of different colliding events that will '
             'be generated. It has no effect, unless -c is used as well. For example, '
             'using a collision percentage of 100%% and a diversity of 1, the output '
             'stream will represent a stream of updates for a single event. A collision '
             'percentage of 50%% and a diversity of 10 generates a stream of which half '
             'of the output events are updates of just 10 distinct events.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    parser.add_argument(
        '--limit',
        default=0,
        type=int,
        help='By default, data will be generated until interrupted. This option allows '
             'you to limit the number of output events to the specified amount. A limit '
             'of zero is interpreted as no limit.'
    )

    parser.add_argument(
        '--content-size',
        default=0,
        type=int,
        help='Used to indicate that event content should be generated. This option '
             'requires the desired content size (in bytes) as argument. If this '
             'option is omitted, no event content will be generated.'
    )

    parser.add_argument(
        '--object-size',
        default=16,
        type=int,
        help='By default, all generated object values are strings with a length of 16'
             'characters. You can use this option to override this length by specifying'
             'a length (in bytes) following the option argument.'
    )

    parser.add_argument(
        '--random-objects',
        action='store_true',
        help='By default, all generated object values are fixed valued strings. This option '
             'enables generation of random object values. Note that when event collisions '
             'are generated, the unique property of each event is more or less random, '
             'regardless of the use of the --random-objects option. Note: This has a '
             'performance impact.'
    )

    parser.add_argument(
        '--random-content',
        action='store_true',
        help='By default, all generated event content values are fixed valued strings. '
             'This option enables generation of random event content. Note: This has a '
             'performance impact.'
    )

    parser.add_argument(
        '--event-type-name',
        default='eventtype.a',
        type=str,
        help='By default, all generated events are of event type "eventtype.a". This '
             'option allows the default event type name to be overridden, which may be '
             'useful when running multiple instances in parallel. The option expects the '
             'desired name as its argument.'
    )

    parser.add_argument(
        '--object-type-name',
        default='objecttype.a',
        type=str,
        help='By default, all generated objects are of object types that have names '
             'prefixed with "objecttype" (for instance "objecttype.a"). This option allows '
             'the default object type name prefix to be overridden, which may be '
             'useful when running multiple instances in parallel. The option expects the '
             'desired object type name prefix as its argument.'
    )

    args = parser.parse_args()

    configure_logger(args)

    with EDXMLDummyDataGenerator(args, validate) as generator:
        generator.start()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        sys.exit(1)
