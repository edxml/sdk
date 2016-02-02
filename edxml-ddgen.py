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
#  testing EDXML processing systems and storage backends.

import sys, time, random
from edxml.EDXMLWriter import EDXMLWriter

# We create a class based on EDXMLEventEditor,
# overriding the EditEvent callback to inspect
# the event timestamps, wait a little and
# output the event.

class EDXMLDummyDataGenerator(EDXMLWriter):

  def __init__ (self, EventRate, MaxEvents, PropertySize, RandomizeProperties, EventContentSize, RandomizeEventContent, GenerateCollisions, CollisionPercentage, EventTypeName, ObjectTypeName, EventGroupSize):

    self.EventCounter = 0
    self.MaxEvents = MaxEvents
    self.EventGroupCounter = 0
    self.CurrentEventGroupSize = 0
    self.GenerateCollisions = GenerateCollisions
    self.CollisionPercentage = CollisionPercentage
    self.RandomizeEventContent = RandomizeEventContent
    self.EventRate = EventRate
    self.EventContentSize = EventContentSize
    self.PropertyStringLength = PropertySize
    self.RandomizeProperties = RandomizeProperties
    self.EventTypeName = EventTypeName
    self.ObjectTypeName = ObjectTypeName
    self.EventGroupSize = EventGroupSize
    self.EventSourceIdDict = {'0': '/source-a/', '1': '/source-b/'}
    self.RandomContentCharacters = 'abcdefghijklmnop  '
    self.RandomContentCharactersLength = len(self.RandomContentCharacters)

    # Call parent class constructor
    EDXMLWriter.__init__(self, sys.stdout, False)

    self.TimeStart = time.time()
    self.WriteDefinitions()
    self.OpenEventGroups()
    self.OpenEventGroup(self.EventTypeName, str(self.EventGroupCounter % 2))
    self.WriteEvents()
    self.CloseEventGroup()
    self.CloseEventGroups()

    TimeElapsed = time.time() - self.TimeStart + 1e-9
    sys.stderr.write("Wrote %d events in % seconds, %d events per second.\n" % (( self.EventCounter, TimeElapsed, (self.EventCounter / TimeElapsed) )))

  def WriteEvents(self):

    DelayFactor = 1.0
    IntervalCorrection = 0
    Content = '*' * self.EventContentSize
    RandomContentCharacters = self.RandomContentCharacters * (int(self.EventContentSize / self.RandomContentCharactersLength) + 1)
    RandomPropertyCharacters = self.RandomContentCharacters * (int(self.PropertyStringLength / self.RandomContentCharactersLength) + 1)

    PropertyObjects = {
      'property-a': ['value'],
      'property-b': ['value'],
      'property-c': ['value'],
      'property-d': ['value'],
      'property-e': ['value'],
      'property-f': ['value']
    }

    if self.GenerateCollisions:
      UniquePropertyValues = [''.join(random.sample(RandomPropertyCharacters, self.PropertyStringLength)) for _ in range(100)]
      RandomUniquePropertyValues = random.sample(range(99), 100 - self.CollisionPercentage)

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
            UniquePropertyValues[ValueIndex] = ''.join(random.sample(RandomPropertyCharacters, self.PropertyStringLength))

        # Generate random property values
        if self.RandomizeProperties:
          for Property in ['a', 'b', 'c', 'd', 'e', 'f']:
            PropertyObjects['property-' + Property] = [''.join(random.sample(self.RandomContentCharacters * (int(self.PropertyStringLength / self.RandomContentCharactersLength) + 1), self.PropertyStringLength))]
        if self.GenerateCollisions:
          # For property-a, which is the unique property, we
          # need to pick values from our random value table,
          # which has been prepared to generate collisions
          # at the requested rate.
          PropertyObjects['property-a'] = [random.choice(UniquePropertyValues)]

        # Take time measurement for rate control
        if self.EventRate > 0:
          TimeStart = time.time()

        # Output one event
        self.AddEvent(PropertyObjects, Content, ParentHashes = [], IgnoreInvalidObjects = False)
        self.EventCounter += 1
        self.CurrentEventGroupSize += 1

        if self.EventGroupSize > 0 and self.CurrentEventGroupSize >= self.EventGroupSize:
          # Event group has grown to the desired size. We close
          # the group, switch to another event source and open
          # a new event group.
          self.EventGroupCounter += 1
          self.CurrentEventGroupSize = 0
          self.CloseEventGroup()
          self.OpenEventGroup(self.EventTypeName, str(self.EventGroupCounter % 2))

        if self.EventRate > 0:
          # An event rate is specified, which means we
          # need to keep track of time and use time.sleep()
          # to generate delays between events.

          CurrentTime = time.time()
          TimeDelay = RequestedTimeInterval - ( CurrentTime - TimeStart )
          if TimeDelay + IntervalCorrection > 0:
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

    if self.GenerateCollisions:
      DropOrMatch = 'match'
      DropOrReplace = 'replace'
    else:
      DropOrMatch = 'drop'
      DropOrReplace = 'drop'

    self.OpenDefinitions()
    self.OpenEventDefinitions()
    self.OpenEventDefinition(self.EventTypeName, 'a', '', '[[a]]', '[[a]]')
    self.OpenEventDefinitionProperties()
    self.AddEventProperty('property-a', self.ObjectTypeName, 'a', Merge = DropOrMatch, Unique = self.GenerateCollisions)
    self.AddEventProperty('property-b', self.ObjectTypeName, 'b', Merge = DropOrReplace)
    self.AddEventProperty('property-c', self.ObjectTypeName, 'c', Merge = 'drop')
    self.AddEventProperty('property-d', self.ObjectTypeName, 'd', Merge = 'drop')
    self.AddEventProperty('property-e', self.ObjectTypeName, 'e', Merge = 'drop')
    self.AddEventProperty('property-f', self.ObjectTypeName, 'f', Merge = 'drop')
    self.CloseEventDefinitionProperties()
    self.OpenEventDefinitionRelations()
    self.CloseEventDefinitionRelations()
    self.CloseEventDefinition()
    self.CloseEventDefinitions()
    self.OpenObjectTypes()
    self.AddObjectType(self.ObjectTypeName, 'a', 'string:%d' % self.PropertyStringLength)
    self.CloseObjectTypes()
    self.OpenSourceDefinitions()
    for SourceId, SourceUrl in self.EventSourceIdDict.items():
      self.AddSource(SourceId, SourceUrl, '00000000', 'dummy source')
    self.CloseSourceDefinitions()
    self.CloseDefinitions()


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

     --objecttype-name By default, all generated objects are of object type 'objecttype-a'. This
                       option allows the default object type name to be overridden, which may be
                       useful when running multiple instances in parallel. The option expects the
                       desired name as its argument.

     --limit           By default, data will be generated until interrupted. This option allows
                       you to limit the number of output events to the specified amount. A limit
                       of zero is interpreted as no limit.

   Example:

     edxml-ddgen.py -r 1000 -c 25 --with-content 1024 --eventtype-name 'my-custom-eventtype'

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
ObjectTypeName = 'objecttype-a'

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
    ObjectTypeName = sys.argv[CurrOption]

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

Generator = EDXMLDummyDataGenerator(EventRate, MaxEventCount, PropertySize, RandomizeProperties, EventContentSize, RandomizeEventContent, GenerateCollisions, CollisionPercentage, EventTypeName, ObjectTypeName, EventGroupSize)
