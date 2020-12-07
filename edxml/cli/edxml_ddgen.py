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

import edxml.ontology
from edxml import EDXMLEvent
from edxml.cli import configure_logger
from edxml.writer import EDXMLWriter


class EDXMLDummyDataGenerator(EDXMLWriter):

    def __init__(self, args):

        self.event_counter = 0

        self.args = args

        self.generate_collisions = args.collision_rate > 0
        self.event_source_uri_list = ('/source-a/', '/source-b/')
        self.random_content_characters = 'abcdefghijklmnop  '
        self.random_content_characters_length = len(self.random_content_characters)
        self.time_start = time.time()

        # Call parent class constructor
        EDXMLWriter.__init__(self, sys.stdout.buffer, validate=False)

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
            'property-c': ['value'],
            'property-g': ['10.000000000'],
            'property-h': ['100.000000000']
        }

        if not self.args.unordered:
            # This property requires ordering to be
            # preserved.
            property_objects['property-b'] = ['value']

        # To prevent colliding events from accumulating arbitrary
        # numbers of property 'property-c' (which has merge
        # strategy 'add'), we generate a small collection of random
        # strings for assigning to this property.
        add_property_values = [''.join(random.sample(
            random_property_characters, self.args.object_size)) for _ in range(10)]

        if self.generate_collisions:
            unique_property_values = [''.join(random.sample(
                random_property_characters, self.args.object_size)) for _ in range(self.args.collision_diversity)]
            random_unique_property_values = random.sample(list(range(self.args.collision_diversity)), int(
                self.args.collision_diversity * (1.0 - (self.args.collision_rate / 100.0))))
        else:
            random_unique_property_values = []

        if self.args.rate > 0:
            requested_time_interval = 1.0 / self.args.rate

        try:
            while self.event_counter < self.args.limit or self.args.limit == 0:

                # Generate random content
                if self.args.random_content:
                    content = ''.join(random.sample(
                        random_content_characters, self.args.content_size))

                # Generate random property values for the entries
                # in the random value table that have been selected
                # as being random.
                if self.generate_collisions:
                    for ValueIndex in random_unique_property_values:
                        unique_property_values[ValueIndex] = ''.join(random.sample(
                            random_property_characters, self.args.object_size))

                # Generate random property values
                if self.args.random_objects:

                    # The unique property is a completely random string
                    property_objects['property-a'] = [''.join(random.sample(self.random_content_characters * (int(
                        self.args.object_size / self.random_content_characters_length) + 1),
                        self.args.object_size))]

                    if not self.args.unordered and random.random() < 0.9:
                        # We add the 'property-b' only if the output requires
                        # the ordering of the events to be preserved. And even
                        # then, we omit the property once in a while, removing
                        # it in case of a collision.
                        property_objects['property-b'] = [''.join(random.sample(self.random_content_characters * (int(
                            self.args.object_size / self.random_content_characters_length) + 1),
                            self.args.object_size))]

                    # A random string from a fixed set
                    property_objects['property-c'] = [
                        random.choice(add_property_values)]

                    for property_name in ['g', 'h']:
                        # Random values in range [-0.5,0.5]
                        property_objects['property-' + property_name] = ['%1.9f' % (random.random() - 0.5)]

                if self.generate_collisions:
                    # For property-a, which is the unique property, we
                    # need to pick values from our random value table,
                    # which has been prepared to generate collisions
                    # at the requested rate.
                    property_objects['property-a'] = [
                        random.choice(unique_property_values)]
                    pass

                # Take time measurement for rate control
                if self.args.rate > 0:
                    time_start = time.time()

                # Output one event
                self.add_event(
                    EDXMLEvent(
                        property_objects,
                        event_type_name=self.args.event_type_name,
                        source_uri=self.event_source_uri_list[self.event_counter % 2],
                        attachments={'content': content}
                    )
                )
                self.event_counter += 1

                if self.args.rate > 0:
                    # An event rate is specified, which means we
                    # need to keep track of time and use time.sleep()
                    # to generate delays between events.

                    current_time = time.time()
                    time_delay = requested_time_interval - \
                        (current_time - time_start)
                    if time_delay + interval_correction > 0:
                        sys.stdout.flush()
                        time.sleep(time_delay + interval_correction)

                    # Check if our output rate is significantly lower than requested,
                    # print informative message is rate is too low.
                    if (self.event_counter / (current_time - self.time_start)) < 0.8 * self.args.rate:
                        sys.stdout.write(
                            'Cannot keep up with requested event rate!\n')

                    # Compute correction, to be added to the delay we pass to sleep.sleep().
                    # We compare the mean time interval between events with the time interval
                    # we are trying to achieve. Based on that, we compute the next time
                    # interval correction. We need a correction, because the accuracy of our
                    # time measurements is limited, which means time.sleep() may sleep slightly
                    # longer than necessary.
                    mean_time_interval = (
                        current_time - self.time_start) / self.event_counter
                    interval_correction = 0.5 * \
                        ((interval_correction + (requested_time_interval -
                                                 mean_time_interval)) + interval_correction)

        except KeyboardInterrupt:
            # Abort event generation.
            return

    def write_definitions(self):

        # In case event collisions will be generated, we will adjust
        # the merge strategies of all properties to cause collisions
        # requiring all possible merge strategies to be applied in
        # order to merge them. The event merges effectively compute
        # the product, minimum value, maximum value etc from
        # the individual objects in all input events.

        if self.generate_collisions:
            any_or_match = 'match'
            any_or_replace = 'replace'
            any_or_add = 'add'
            any_or_min = 'min'
            any_or_max = 'max'
        else:
            any_or_match = 'any'
            any_or_replace = 'any'
            any_or_add = 'any'
            any_or_min = 'any'
            any_or_max = 'any'

        ontology = edxml.ontology.Ontology()

        ontology.create_object_type(self.args.object_type_name + '.a',
                                    data_type='string:%d:cs' % self.args.object_size)
        ontology.create_object_type(self.args.object_type_name + '.b', data_type='number:bigint:signed')
        ontology.create_object_type(self.args.object_type_name + '.c', data_type='number:decimal:12:9:signed')

        event_type = ontology.create_event_type(self.args.event_type_name)
        event_type.create_property('property-a', self.args.object_type_name + '.a').set_merge_strategy(any_or_match)

        if not self.args.unordered:
            event_type.create_property('property-b', self.args.object_type_name +
                                       '.a').set_merge_strategy(any_or_replace)

        event_type.create_property('property-c', self.args.object_type_name + '.a').set_merge_strategy(any_or_add)
        event_type.create_property('property-g', self.args.object_type_name + '.c').set_merge_strategy(any_or_min)
        event_type.create_property('property-h', self.args.object_type_name + '.c').set_merge_strategy(any_or_max)

        event_type.create_attachment('content')

        for uri in self.event_source_uri_list:
            ontology.create_event_source(uri)

        self.add_ontology(ontology)


def main():
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

    parser.add_argument(
        '--unordered',
        action='store_true',
        help='By default, output events will feature an implicit ordering in case event '
             'collisions are generated. When this switch is added, no event properties '
             'with merge strategy "replace" will be generated, which means that colliding '
             'events will not change when they are merged in a different order. This may be '
             'useful for testing parallel EDXML stream processing.'
    )

    args = parser.parse_args()

    configure_logger(args)

    with EDXMLDummyDataGenerator(args) as generator:
        generator.start()


if __name__ == "__main__":
    main()
