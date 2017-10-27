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

import sys, time, random

import edxml.ontology
from edxml import EDXMLEvent
from edxml.EDXMLWriter import EDXMLWriter
from edxml.ontology import EventProperty
from edxml.ontology import EventSource
from edxml.ontology import EventType
from edxml.ontology import ObjectType


class EDXMLDummyDataGenerator(EDXMLWriter):

  def __init__ (self, EventRate, MaxEvents, PropertySize, RandomizeProperties, EventContentSize,
                RandomizeEventContent, GenerateCollisions, CollisionPercentage, EventTypeName,
                ObjectTypeNamePrefix, EventGroupSize, Diversity, Ordered):

    self.EventCounter = 0
    self.MaxEvents = MaxEvents
    self.EventGroupCounter = 0
    self.CurrentEventGroupSize = 0
    self.Ordered = Ordered
    self.GenerateCollisions = GenerateCollisions and CollisionPercentage > 0
    self.CollisionPercentage = CollisionPercentage
    self.RandomizeEventContent = RandomizeEventContent
    self.EventRate = EventRate
    self.EventContentSize = EventContentSize
    self.PropertyStringLength = PropertySize
    self.RandomizeProperties = RandomizeProperties
    self.EventTypeName = EventTypeName
    self.ObjectTypeNamePrefix = ObjectTypeNamePrefix
    self.Diversity = Diversity
    self.EventGroupSize = EventGroupSize
    self.EventSourceUriList = ('/source-a/', '/source-b/')
    self.RandomContentCharacters = u'abcdefghijklmnop  '
    self.RandomContentCharactersLength = len(self.RandomContentCharacters)
    self.TimeStart = time.time()

    # Call parent class constructor
    EDXMLWriter.__init__(self, sys.stdout, Validate=False)

  def Start(self):
    self.WriteDefinitions()
    self.OpenEventGroups()
    self.OpenEventGroup(self.EventTypeName, self.EventSourceUriList[self.EventGroupCounter % 2])
    self.WriteEvents()
    self.Close()

    TimeElapsed = time.time() - self.TimeStart + 1e-9
    sys.stderr.write("Wrote %d events in %d seconds, %d events per second.\n" % (( self.EventCounter, TimeElapsed, (self.EventCounter / TimeElapsed) )))

  def WriteEvents(self):

    IntervalCorrection = 0
    RandomContentCharacters = self.RandomContentCharacters * (int(self.EventContentSize / self.RandomContentCharactersLength) + 1)
    RandomPropertyCharacters = self.RandomContentCharacters * (int(self.PropertyStringLength / self.RandomContentCharactersLength) + 1)

    # By default, event content is just a
    # string of asterisks.
    Content = '*' * self.EventContentSize

    # Set the default object values
    PropertyObjects = {
      'property-a': [u'value'],
      'property-c': [u'value'],
      'property-d': [u'10'],
      'property-e': [u'1'],
      'property-f': [u'1.000'],
      'property-g': [u'10.000'],
      'property-h': [u'100.000']
    }

    if self.Ordered:
      # This property requires ordering to be
      # preserved.
      PropertyObjects['property-b'] = [u'value']

    # To prevent colliding events from accumulating arbitrary
    # numbers of property 'property-c' (which has merge
    # strategy 'add'), we generate a small collection of random
    # strings for assigning to this property.
    AddPropertyValues = [u''.join(random.sample(RandomPropertyCharacters, self.PropertyStringLength)) for _ in range(10)]

    if self.GenerateCollisions:
      UniquePropertyValues = [u''.join(random.sample(RandomPropertyCharacters, self.PropertyStringLength)) for _ in range(self.Diversity)]
      RandomUniquePropertyValues = random.sample(range(self.Diversity), int(self.Diversity * (1.0 - (self.CollisionPercentage/100.0))))
    else:
      RandomUniquePropertyValues = []

    if self.EventRate > 0:
      RequestedTimeInterval = 1.0 / self.EventRate

    try:
      while self.EventCounter < self.MaxEvents or self.MaxEvents == 0:

        # Generate random content
        if self.RandomizeEventContent:
          Content = ''.join(random.sample(RandomContentCharacters, self.EventContentSize))

        # Generate random property values for the entries
        # in the random value table that have been selected
        # as being random.
        if self.GenerateCollisions:
          for ValueIndex in RandomUniquePropertyValues:
            UniquePropertyValues[ValueIndex] = u''.join(random.sample(RandomPropertyCharacters, self.PropertyStringLength))

        # Generate random property values
        if self.RandomizeProperties:

          # The unique property is a completely random string
          PropertyObjects['property-a'] = [u''.join(random.sample(self.RandomContentCharacters * (int(self.PropertyStringLength / self.RandomContentCharactersLength) + 1), self.PropertyStringLength))]

          if self.Ordered and random.random() < 0.9:
            # We add the 'property-b' only if the output requires
            # the ordering of the events to be preserved. And even
            # then, we omit the property once in a while, removing
            # it in case of a collision.
            PropertyObjects['property-b'] = [u''.join(random.sample(self.RandomContentCharacters * (int(self.PropertyStringLength / self.RandomContentCharactersLength) + 1), self.PropertyStringLength))]

          # A random string from a fixed set
          PropertyObjects['property-c'] = [random.choice(AddPropertyValues)]

          # Random values in range [-10,10]
          PropertyObjects['property-d'] = [unicode(random.randint(-100, 100))]

          # Random values near 1.0
          PropertyObjects['property-f'] = [u'%1.9f' % (1 + (random.random() - 0.5)/1000)]

          for Property in ['g', 'h']:
            # Random values in range [-0.5,0.5]
            PropertyObjects['property-' + Property] = [u'%1.9f' % (random.random() - 0.5)]

        if self.GenerateCollisions:
          # For property-a, which is the unique property, we
          # need to pick values from our random value table,
          # which has been prepared to generate collisions
          # at the requested rate.
          PropertyObjects['property-a'] = [random.choice(UniquePropertyValues)]
          pass

        # Take time measurement for rate control
        if self.EventRate > 0:
          TimeStart = time.time()

        # Output one event
        self.AddEvent(EDXMLEvent(PropertyObjects, Content=Content))
        self.EventCounter += 1
        self.CurrentEventGroupSize += 1

        if self.EventGroupSize > 0 and self.CurrentEventGroupSize >= self.EventGroupSize:
          # Event group has grown to the desired size. We close
          # the group, switch to another event source and open
          # a new event group.
          self.EventGroupCounter += 1
          self.CurrentEventGroupSize = 0
          self.CloseEventGroup()
          self.OpenEventGroup(self.EventTypeName, self.EventSourceUriList[self.EventGroupCounter % 2])

        if self.EventRate > 0:
          # An event rate is specified, which means we
          # need to keep track of time and use time.sleep()
          # to generate delays between events.

          CurrentTime = time.time()
          TimeDelay = RequestedTimeInterval - ( CurrentTime - TimeStart )
          if TimeDelay + IntervalCorrection > 0:
            sys.stdout.flush()
            time.sleep(TimeDelay + IntervalCorrection)

          # Check if our output rate is significantly lower than requested,
          # print informative message is rate is too low.
          if (self.EventCounter / (CurrentTime - self.TimeStart) ) < 0.8 * self.EventRate:
            sys.stdout.write('Cannot keep up with requested event rate!\n')

          # Compute correction, to be added to the delay we pass to sleep.sleep().
          # We compare the mean time interval between events with the time interval
          # we are trying to achieve. Based on that, we compute the next time
          # interval correction. We need a correction, because the accuracy of our
          # time measurements is limited, which means time.sleep() may sleep slightly
          # longer than necessary.
          MeanTimeInterval = ( CurrentTime - self.TimeStart ) / self.EventCounter
          IntervalCorrection = 0.5 * ((IntervalCorrection + (RequestedTimeInterval - MeanTimeInterval)) + IntervalCorrection)

    except KeyboardInterrupt:
      # Abort event generation.
      return

    def WriteDefinitions(self):

    # In case event collisions will be generated, we will adjust
    # the merge strategies of all properties to cause collisions
    # requiring all possible merge strategies to be applied in
    # order to merge them. The event merges effectively compute
    # the sum, product, minimum value, maximum value etc from
    # the individual objects in all input events.

    if self.GenerateCollisions:
      DropOrMatch    = 'match'
      DropOrReplace  = 'replace'
      DropOrAdd      = 'add'
      DropOrSum      = 'sum'
      DropOrMultiply = 'multiply'
      DropOrMin      = 'min'
      DropOrMax      = 'max'
      DropOrInc      = 'increment'
    else:
      DropOrMatch    = 'drop'
      DropOrReplace  = 'drop'
      DropOrAdd      = 'drop'
      DropOrSum      = 'drop'
      DropOrMultiply = 'drop'
      DropOrMin      = 'drop'
      DropOrMax      = 'drop'
      DropOrInc      = 'drop'

    ontology = edxml.ontology.Ontology()

    ontology.CreateObjectType(self.ObjectTypeNamePrefix + '.a', DataType='string:%d:cs' % self.PropertyStringLength)
    ontology.CreateObjectType(self.ObjectTypeNamePrefix + '.b', DataType='number:bigint:signed')
    ontology.CreateObjectType(self.ObjectTypeNamePrefix + '.c', DataType='number:decimal:10:9:signed')

    eventType = ontology.CreateEventType(self.EventTypeName)
    eventType.CreateProperty('property-a', self.ObjectTypeNamePrefix + '.a').SetMergeStrategy(DropOrMatch)

    if self.Ordered:
      eventType.CreateProperty('property-b', self.ObjectTypeNamePrefix + '.a').SetMergeStrategy(DropOrReplace)

    eventType.CreateProperty('property-c', self.ObjectTypeNamePrefix + '.a').SetMergeStrategy(DropOrAdd)
    eventType.CreateProperty('property-d', self.ObjectTypeNamePrefix + '.b').SetMergeStrategy(DropOrSum)
    eventType.CreateProperty('property-e', self.ObjectTypeNamePrefix + '.b').SetMergeStrategy(DropOrInc)
    eventType.CreateProperty('property-f', self.ObjectTypeNamePrefix + '.c').SetMergeStrategy(DropOrMultiply)
    eventType.CreateProperty('property-g', self.ObjectTypeNamePrefix + '.c').SetMergeStrategy(DropOrMin)
    eventType.CreateProperty('property-h', self.ObjectTypeNamePrefix + '.c').SetMergeStrategy(DropOrMax)

    for uri in self.EventSourceUriList:
      ontology.CreateEventSource(uri)

    self.AddOntology(ontology)


def PrintHelp():

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


CurrOption = 1
EventGroupSize = 0
EventContentSize = 0
PropertySize = 16
MaxEventCount = 0
RandomizeProperties = False
RandomizeEventContent = False
GenerateCollisions = False
CollisionPercentage = 0
EventTypeName = 'eventtype-a'
ObjectTypeNamePrefix = 'objecttype'
OutputDiversity = 100
OrderedOutput = True

EventRate = 0

while CurrOption < len(sys.argv):

  if sys.argv[CurrOption] in ('-h', '--help'):
    PrintHelp()
    sys.exit(0)

  elif sys.argv[CurrOption] == '-r':
    CurrOption += 1
    EventRate = int(sys.argv[CurrOption])

  elif sys.argv[CurrOption] == '-c':
    CurrOption += 1
    GenerateCollisions = True
    CollisionPercentage = int(sys.argv[CurrOption])

  elif sys.argv[CurrOption] == '-d':
    CurrOption += 1
    OutputDiversity = int(sys.argv[CurrOption])

  elif sys.argv[CurrOption] == '--object-size':
    CurrOption += 1
    PropertySize = int(sys.argv[CurrOption])

  elif sys.argv[CurrOption] == '--with-content':
    CurrOption += 1
    EventContentSize = int(sys.argv[CurrOption])

  elif sys.argv[CurrOption] == '--limit':
    CurrOption += 1
    MaxEventCount = int(sys.argv[CurrOption])

  elif sys.argv[CurrOption] == '--eventtype-name':
    CurrOption += 1
    EventTypeName = sys.argv[CurrOption]

  elif sys.argv[CurrOption] == '--objecttype-name':
    CurrOption += 1
    ObjectTypeNamePrefix = sys.argv[CurrOption]

  elif sys.argv[CurrOption] == '--unordered':
    OrderedOutput = False

  elif sys.argv[CurrOption] == '--eventgroup-size':
    CurrOption += 1
    EventGroupSize = int(sys.argv[CurrOption])

  elif sys.argv[CurrOption] == '--random-objects':
    RandomizeProperties = True

  elif sys.argv[CurrOption] == '--random-content':
    RandomizeEventContent = True

  else:
    sys.stderr.write("Unknown commandline argument: %s\n" % sys.argv[CurrOption])
    sys.exit()

  CurrOption += 1

generator = EDXMLDummyDataGenerator(EventRate, MaxEventCount, PropertySize, RandomizeProperties,
                                    EventContentSize, RandomizeEventContent, GenerateCollisions,
                                    CollisionPercentage, EventTypeName, ObjectTypeNamePrefix,
                                    EventGroupSize, OutputDiversity, OrderedOutput)
try:
  generator.Start()
except KeyboardInterrupt:
  generator.Close()
