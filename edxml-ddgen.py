#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#
#  ===========================================================================
#
#                         EDXML dummy data generator
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
#  This script generates dummy EDXML data streams, which may be useful for stress
#  testing EDXML processing systems and storage back ends.

import sys
import time
import random

import edxml.ontology
from edxml import EDXMLEvent
from edxml.EDXMLWriter import EDXMLWriter


class EDXMLDummyDataGenerator(EDXMLWriter):

    def __init__(self, event_rate, max_events, property_size, randomize_properties, event_content_size,
                 randomize_event_content, generate_collisions, collision_percentage, event_type_name,
                 object_type_name_prefix, event_group_size, diversity, ordered):

        self.event_counter = 0
        self.max_events = max_events
        self.event_group_counter = 0
        self.current_event_group_size = 0
        self.ordered = ordered
        self.generate_collisions = generate_collisions and collision_percentage > 0
        self.collision_percentage = collision_percentage
        self.randomize_event_content = randomize_event_content
        self.event_rate = event_rate
        self.event_content_size = event_content_size
        self.property_string_length = property_size
        self.randomize_properties = randomize_properties
        self.event_type_name = event_type_name
        self.object_type_name_prefix = object_type_name_prefix
        self.diversity = diversity
        self.event_group_size = event_group_size
        self.event_source_uri_list = ('/source-a/', '/source-b/')
        self.random_content_characters = u'abcdefghijklmnop  '
        self.random_content_characters_length = len(self.random_content_characters)
        self.time_start = time.time()

        # Call parent class constructor
        EDXMLWriter.__init__(self, sys.stdout, validate=False)

    def start(self):
        self.write_definitions()
        self.open_event_groups()
        self.open_event_group(
            self.event_type_name, self.event_source_uri_list[self.event_group_counter % 2])
        self.write_events()
        self.close()

        time_elapsed = time.time() - self.time_start + 1e-9
        sys.stderr.write("Wrote %d events in %d seconds, %d events per second.\n" % (
            (self.event_counter, time_elapsed, (self.event_counter / time_elapsed))))

    def write_events(self):

        interval_correction = 0
        random_content_characters = self.random_content_characters * \
            (int(self.event_content_size / self.random_content_characters_length) + 1)
        random_property_characters = self.random_content_characters * \
            (int(self.property_string_length / self.random_content_characters_length) + 1)

        # By default, event content is just a
        # string of asterisks.
        content = '*' * self.event_content_size

        # Set the default object values
        property_objects = {
            'property-a': [u'value'],
            'property-c': [u'value'],
            'property-g': [u'10.000000000'],
            'property-h': [u'100.000000000']
        }

        if self.ordered:
            # This property requires ordering to be
            # preserved.
            property_objects['property-b'] = [u'value']

        # To prevent colliding events from accumulating arbitrary
        # numbers of property 'property-c' (which has merge
        # strategy 'add'), we generate a small collection of random
        # strings for assigning to this property.
        add_property_values = [u''.join(random.sample(
            random_property_characters, self.property_string_length)) for _ in range(10)]

        if self.generate_collisions:
            unique_property_values = [u''.join(random.sample(
                random_property_characters, self.property_string_length)) for _ in range(self.diversity)]
            random_unique_property_values = random.sample(range(self.diversity), int(
                self.diversity * (1.0 - (self.collision_percentage / 100.0))))
        else:
            random_unique_property_values = []

        if self.event_rate > 0:
            requested_time_interval = 1.0 / self.event_rate

        try:
            while self.event_counter < self.max_events or self.max_events == 0:

                # Generate random content
                if self.randomize_event_content:
                    content = ''.join(random.sample(
                        random_content_characters, self.event_content_size))

                # Generate random property values for the entries
                # in the random value table that have been selected
                # as being random.
                if self.generate_collisions:
                    for ValueIndex in random_unique_property_values:
                        unique_property_values[ValueIndex] = u''.join(random.sample(
                            random_property_characters, self.property_string_length))

                # Generate random property values
                if self.randomize_properties:

                    # The unique property is a completely random string
                    property_objects['property-a'] = [u''.join(random.sample(self.random_content_characters * (int(
                        self.property_string_length / self.random_content_characters_length) + 1),
                        self.property_string_length))]

                    if self.ordered and random.random() < 0.9:
                        # We add the 'property-b' only if the output requires
                        # the ordering of the events to be preserved. And even
                        # then, we omit the property once in a while, removing
                        # it in case of a collision.
                        property_objects['property-b'] = [u''.join(random.sample(self.random_content_characters * (int(
                            self.property_string_length / self.random_content_characters_length) + 1),
                            self.property_string_length))]

                    # A random string from a fixed set
                    property_objects['property-c'] = [
                        random.choice(add_property_values)]

                    for property_name in ['g', 'h']:
                        # Random values in range [-0.5,0.5]
                        property_objects['property-' +
                                         property_name] = [u'%1.9f' % (random.random() - 0.5)]

                if self.generate_collisions:
                    # For property-a, which is the unique property, we
                    # need to pick values from our random value table,
                    # which has been prepared to generate collisions
                    # at the requested rate.
                    property_objects['property-a'] = [
                        random.choice(unique_property_values)]
                    pass

                # Take time measurement for rate control
                if self.event_rate > 0:
                    time_start = time.time()

                # Output one event
                self.add_event(EDXMLEvent(property_objects, content=content))
                self.event_counter += 1
                self.current_event_group_size += 1

                if self.event_group_size > 0 and self.current_event_group_size >= self.event_group_size:
                    # Event group has grown to the desired size. We close
                    # the group, switch to another event source and open
                    # a new event group.
                    self.event_group_counter += 1
                    self.current_event_group_size = 0
                    self.close_event_group()
                    self.open_event_group(
                        self.event_type_name, self.event_source_uri_list[self.event_group_counter % 2])

                if self.event_rate > 0:
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
                    if (self.event_counter / (current_time - self.time_start)) < 0.8 * self.event_rate:
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
            drop_or_match = 'match'
            drop_or_replace = 'replace'
            drop_or_add = 'add'
            drop_or_min = 'min'
            drop_or_max = 'max'
        else:
            drop_or_match = 'drop'
            drop_or_replace = 'drop'
            drop_or_add = 'drop'
            drop_or_min = 'drop'
            drop_or_max = 'drop'

        ontology = edxml.ontology.Ontology()

        ontology.create_object_type(self.object_type_name_prefix + '.a',
                                    data_type='string:%d:cs' % self.property_string_length)
        ontology.create_object_type(self.object_type_name_prefix + '.b', data_type='number:bigint:signed')
        ontology.create_object_type(self.object_type_name_prefix + '.c', data_type='number:decimal:12:9:signed')

        event_type = ontology.create_event_type(self.event_type_name)
        event_type.create_property('property-a', self.object_type_name_prefix + '.a').set_merge_strategy(drop_or_match)

        if self.ordered:
            event_type.create_property('property-b', self.object_type_name_prefix +
                                       '.a').set_merge_strategy(drop_or_replace)

        event_type.create_property('property-c', self.object_type_name_prefix + '.a').set_merge_strategy(drop_or_add)
        event_type.create_property('property-g', self.object_type_name_prefix + '.c').set_merge_strategy(drop_or_min)
        event_type.create_property('property-h', self.object_type_name_prefix + '.c').set_merge_strategy(drop_or_max)

        for uri in self.event_source_uri_list:
            ontology.create_event_source(uri)

        self.add_ontology(ontology)


def print_help():

    print """

   This utility generates dummy EDXML data streams, which may be useful for
   stress testing EDXML processing systems and storage backends. The generated EDXML
   stream is written to standard output.

   Options:

     -h, --help        Prints this help text

     -r                By default, events will be generated at fast as possible. This option
                       can be used to limit the rate to the specified number of events per
                       second.

     -c                This option triggers generation of event collisions. It must be followed
                       by an integer percentage, which configures how often an event will collide
                       with a previously generated event. A value of 100 makes all events collide,
                       while a value of zero effectively disables collision generation. By default,
                       no event collisions will be generated. Note: This has a performance impact.

     -d                This option controls the number of different colliding events that will
                       be generated. It has no effect, unless -c is used as well. For example,
                       using a collision percentage of 100% and a diversity of 1, the output
                       stream will represent a stream of updates for a single event. A collision
                       percentage of 50% and a diversity of 10 generates a stream of which half
                       of the output events are updates of just 10 distinct events.

     --with-content    Used to indicate that event content should be generated. This option
                       requires the desired content size (in bytes) as argument. If this
                       option is omitted, no event content will be generated.

     --eventgroup-size By default, only one event group is generated. This option allows the size
                       of generated event groups to be limited. In general, smaller event groups
                       makes efficient processing of the EDXML streams more difficult. The option
                       expects the desired size (event count) as its argument.

     --object-size     By default, all generated object values are strings with a length of 16
                       characters. You can use this option to override this length by specifying
                       a length (in bytes) following the option argument.

     --random-objects  By default, all generated object values are fixed valued strings. This option
                       enables generation of random object values. Note that when event collisions
                       are generated, the unique property of each event is more or less random,
                       ragardless of the use of the --random-objects option. Note: This has a
                       performance impact.

     --random-content  By default, all generated event content values are fixed valued strings.
                       This option enables generation of random event content. Note: This has a
                       performance impact.

     --eventtype-name  By default, all generated events are of event type 'eventtype-a'. This
                       option allows the default event type name to be overridden, which may be
                       useful when running multiple instances in parallel. The option expects the
                       desired name as its argument.

     --objecttype-name By default, all generated objects are of object types that have names
                       prefixed with 'objecttype' (for instance 'objecttype.a'). This option allows
                       the default object type name prefix to be overridden, which may be
                       useful when running multiple instances in parallel. The option expects the
                       desired object type name prefix as its argument.

     --unordered       By default, output events will feature an implicit ordering in case event
                       collisions are generated. When this switch is added, no event properties
                       with merge strategy 'replace' will be generated, which means that colliding
                       events will not change when they are merged in a different order. This may be
                       useful for testing parallel EDXML stream processing.

     --limit           By default, data will be generated until interrupted. This option allows
                       you to limit the number of output events to the specified amount. A limit
                       of zero is interpreted as no limit.

   Example:

     edxml-ddgen.py -r 1000 -c 25 --with-content 1024 --eventtype-name 'my.custom.eventtype'

"""


curr_option = 1
event_group_size = 0
event_content_size = 0
property_size = 16
max_event_count = 0
randomize_properties = False
randomize_event_content = False
generate_collisions = False
collision_percentage = 0
event_type_name = 'eventtype.a'
object_type_name_prefix = 'objecttype'
output_diversity = 100
ordered_output = True

event_rate = 0

while curr_option < len(sys.argv):

    if sys.argv[curr_option] in ('-h', '--help'):
        print_help()
        sys.exit(0)

    elif sys.argv[curr_option] == '-r':
        curr_option += 1
        event_rate = int(sys.argv[curr_option])

    elif sys.argv[curr_option] == '-c':
        curr_option += 1
        generate_collisions = True
        collision_percentage = int(sys.argv[curr_option])

    elif sys.argv[curr_option] == '-d':
        curr_option += 1
        output_diversity = int(sys.argv[curr_option])

    elif sys.argv[curr_option] == '--object-size':
        curr_option += 1
        property_size = int(sys.argv[curr_option])

    elif sys.argv[curr_option] == '--with-content':
        curr_option += 1
        event_content_size = int(sys.argv[curr_option])

    elif sys.argv[curr_option] == '--limit':
        curr_option += 1
        max_event_count = int(sys.argv[curr_option])

    elif sys.argv[curr_option] == '--eventtype-name':
        curr_option += 1
        event_type_name = sys.argv[curr_option]

    elif sys.argv[curr_option] == '--objecttype-name':
        curr_option += 1
        object_type_name_prefix = sys.argv[curr_option]

    elif sys.argv[curr_option] == '--unordered':
        ordered_output = False

    elif sys.argv[curr_option] == '--eventgroup-size':
        curr_option += 1
        event_group_size = int(sys.argv[curr_option])

    elif sys.argv[curr_option] == '--random-objects':
        randomize_properties = True

    elif sys.argv[curr_option] == '--random-content':
        randomize_event_content = True

    else:
        sys.stderr.write("Unknown commandline argument: %s\n" %
                         sys.argv[curr_option])
        sys.exit()

    curr_option += 1

generator = EDXMLDummyDataGenerator(
    event_rate, max_event_count, property_size, randomize_properties,
    event_content_size, randomize_event_content, generate_collisions,
    collision_percentage, event_type_name, object_type_name_prefix,
    event_group_size, output_diversity, ordered_output)
try:
    generator.start()
except KeyboardInterrupt:
    generator.close()
