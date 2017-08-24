# -*- coding: utf-8 -*-
import edxml
from edxml.EDXMLBase import EDXMLBase
from edxml import EDXMLEvent
from edxml.ontology import EventTypeParent


class Transcoder(EDXMLBase):
  """
  This is a base class that can be extended to implement transcoders
  for the various input data record types that are generated by a
  particular TranscoderMediator implementation. The class features
  a GenerateEventTypes() method that can generate the event type definitions
  for the events that the transcoder intends to produce. Transcoders can
  override this method to generate their own event types.

  Alternatively, transcoders can populate a number of class constants describing
  the event types. The default implementation of GenerateEventTypes() will read these
  constants to generate the event types for you. Any details of the event type
  definitions that cannot be specified using the class constants can be set on
  the generated event types by overriding the GenerateEventTypes() method
  and edit the event type definitions that it generates.

  Except for the TYPES constant, all constants are optional. They
  just provide a means for developers to replace code with constants,
  improving the readability of the transcoder.
  """

  TYPES = []
  """
  The TYPES attribute must contain a list of EDXML event type names
  of the event types that will be generated by the transcoder.

  Note:
    Overriding and populating this attribute is mandatory.
  """

  TYPE_MAP = {}
  """
  The TYPE_MAP attribute is a dictionary mapping EDXML event type names
  to the corresponding input record type selectors. This mapping is used
  by the transcoder mediator to find the correct transcoder for each input
  data record.

  Note:
    When no EDXML event type name is specified for a particular input record
    type selector, it is up to the transcoder to set the event type on the events
    that it generates.

  Note:
    The fallback transcoder must set the None key to the name of the EDXML
    fallback event type.
  """

  TYPE_DESCRIPTIONS = {}
  """
  The TYPE_DESCRIPTIONS attribute is a dictionary mapping EDXML event type names
  to event type descriptions.
  """

  TYPE_DISPLAY_NAMES = {}
  """
  The TYPE_DISPLAY_NAMES attribute is a dictionary mapping EDXML event type names
  to event type display names. Each display name is a list, containing the singular
  form, optionally followed by the plural form, like this:

      {'event-type-name': ['event', 'events']}

  The plural form may be omitted. In that case, the plural form will be assumed
  to be the singular form with an additional 's' appended.
  """

  TYPE_REPORTERS_SHORT = {}
  """
  The TYPE_REPORTERS_SHORT attribute is a dictionary mapping EDXML event type names to
  short EDXML reporter strings.
  """

  TYPE_REPORTERS_LONG = {}
  """
  The TYPE_REPORTERS_LONG attribute is a dictionary mapping EDXML event type names to
  long EDXML reporter strings.
  """

  TYPE_PROPERTIES = {}
  """
  The TYPE_PROPERTIES attribute is a dictionary mapping EDXML event type names to
  their properties. For each key (the event type name) there should be a dictionary containing
  the desired property. A property dictionary must have a key containing the property name and
  a value containing the name of the object type. Properties will automatically be generated
  when this constant is populated.

  Example::

    {'event_type_name': {'property_name': 'object_type_name'}}

  """

  TYPE_PROPERTY_DESCRIPTIONS = {}
  """
  The TYPE_PROPERTY_DESCRIPTIONS attribute is a dictionary mapping EDXML event type names to property
  descriptions. Each property description is a dictionary mapping property names to descriptions.
  It will be used to automatically set the descriptions of any automatically generated properties.

  Example::

      {
        'event_type_name': {
          'property-a': 'description',
          'property-b': 'description'
        }
      }

  """

  TYPE_PROPERTY_SIMILARITY = {}
  """
  The TYPE_PROPERTY_SIMILARITY attribute is a dictionary mapping EDXML event type names to property
  similarities. Each property similarity is a dictionary mapping property names to EDXML 'similar'
  attributes. It will be used to automatically set the similar attributes of any automatically
  generated properties.

  Example::

      {
        'event_type_name': {
          'property-a': 'similar attribute',
          'property-b': 'similar attribute'
        }
      }

  """

  TYPE_PROPERTY_MERGE_STRATEGIES = {}
  """
  The TYPE_PROPERTY_MERGE_STRATEGIES attribute is a dictionary mapping EDXML event type names to property
  merge strategies. Each property merge strategy is a dictionary mapping property names to EDXML 'merge'
  attributes, which indicate the merge strategy of the property. It will be used to set the merge attribute
  for any automatically generated properties.

  When no merge strategy is given, automatically generated properties will have the default strategy,
  which is 'match' for unique properties and 'drop' for all other properties.

  For convenience, the EventProperty class defines some class attributes representing the available
  merge strategies.

  Example::

    {
      'event_type_name': {
        'property_name': EventProperty.MERGE_ADD
      }
    }

  """

  TYPE_UNIQUE_PROPERTIES = {}
  """
  The TYPE_UNIQUE_PROPERTIES attribute is a dictionary mapping EDXML event type names to lists of unique properties.
  The lists will be used to mark the listed properties as unique in automatically generated properties. Example::

    {'event_type_name': ['unique-property-a', 'unique-property-b']}
  """

  PARENTS_CHILDREN = []
  """
  The PARENTS_CHILDREN attribute is a list containing parent-child event type relations. Each relation
  is a list containing the event type name of the parent, the EDXML 'parent-description' attribute and the
  event type name of the child event type, in that order. It will be used in conjunction with the CHILDREN_SIBLINGS
  and PARENT_MAPPINGS attributes to configure event type parents for any automatically generated event
  types. Example::

    PARENTS_CHILDREN = [
      ['parent-event-type-name', 'containing', 'child-event-type-name']
    ]

  Note:
    Please refer to the EDXML specification for details about how to choose a proper value for the
    parent-description attribute.
  """

  CHILDREN_SIBLINGS = []
  """
  The CHILDREN_SIBLINGS attribute is a list containing child-siblings event type relations. Each relation
  is a list containing the event type name of the child, the EDXML 'siblings-description' attribute and the
  event type name of the parent event type, in that order. Example::

    CHILDREN_SIBLINGS = [
      ['child-event-type-name', 'contained in', 'parent-event-type-name']
    ]

  Note:
    Please refer to the EDXML specification for details about how to choose a proper value for the
    siblings-description attribute.
  """

  PARENT_MAPPINGS = {}
  """
  The PARENT_MAPPINGS attribute is a dictionary mapping EDXML event type names to parent property
  mappings. Each mapping is a dictionary containing properties of the event type as keys and properties
  of the parent event type as values. Example:

    PARENT_MAPPINGS = {
      'child-event-type-name': {
        'child-property-name-a': 'parent-property-name-a',
        'child-property-name-b': 'parent-property-name-b',
      }
    }

  Note:
    Please refer to the EDXML specification for details about how parent property mappings work.
  """

  def __init__(self):
    super(Transcoder, self).__init__()

    self._ontology = None  # type: edxml.ontology.Ontology
    self.reporter_strings = [
      'short',
      'long'
    ]

  def SetOntology(self, ontology):
    self._ontology = ontology
    return self

  def Generate(self, Json, RecordSelector, **kwargs):
    """

    Generates one or more EDXML events from the
    given input record

    Args:
      Record: Input data record
      RecordSelector (str): The selector matching the input record
      **kwargs: Arbitrary keyword arguments

    Yields:
      EDXMLEvent:
    """
    return
    yield

  def PostProcess(self, Event):
    """

    Generates zero or more EDXML events from the
    given EDXML input event. If this method is overridden by
    an extension of the Transcoder class, all events generated
    by the Generate() method are passed through this method for
    post processing. This allows the generated events to be
    modified or omitted. Or, multiple derivative events can be
    created from a single input event.

    Args:
      Event (EDXMLEvent): Input event

    Yields:
      EDXMLEvent:
    """
    return
    yield

  @staticmethod
  def GetAutoMergeEventTypes():
    """

    Returns a list of names of event types
    that should be automatically merged while
    generating them. This may be useful to
    reduce the event output rate when generating
    large numbers of colliding events.

    Returns:
       list[str]:
    """
    return []

  def GenerateConcepts(self):
    """

    This method may be used to generate generic EDXML
    concepts that are used by all transcoders.

    Yields:
      edxml.ontology.Concept:
    """
    return
    yield

  def GenerateObjectTypes(self):
    """

    This method may be used to generate generic EDXML
    object types that are used by all transcoders.

    Yields:
      edxml.ontology.ObjectType:
    """
    return
    yield

  def GenerateEventTypes(self):
    """

    This method generates event types using the attributes of the
    various transcoders. This yields a set of preconfigured event types
    that may optionally be tuned by each of the transcoders. Yields
    tuples containing pairs of event type names and event
    type instances.

    Yields:
      tuple[str, EventType]:
    """
    for EventTypeName in self.TYPES:
      Type = self._ontology.CreateEventType(EventTypeName, Description=self.TYPE_DESCRIPTIONS.get(EventTypeName))\
        .SetDisplayName(*self.TYPE_DISPLAY_NAMES.get(EventTypeName, [None, None]))\
        .SetReporterShort(self.TYPE_REPORTERS_SHORT.get(EventTypeName))\
        .SetReporterLong(self.TYPE_REPORTERS_LONG.get(EventTypeName))

      if EventTypeName in self.TYPE_PROPERTIES:
        for PropertyName, ObjectTypeName in self.TYPE_PROPERTIES[EventTypeName].iteritems():
          Type.CreateProperty(PropertyName, ObjectTypeName)
          if PropertyName in self.TYPE_PROPERTY_DESCRIPTIONS.get(EventTypeName, {}):
            Type[PropertyName].SetDescription(self.TYPE_PROPERTY_DESCRIPTIONS[EventTypeName][PropertyName])
          if PropertyName in self.TYPE_PROPERTY_SIMILARITY.get(EventTypeName, {}):
            Type[PropertyName].HintSimilar(self.TYPE_PROPERTY_SIMILARITY[EventTypeName][PropertyName])
          if PropertyName in self.TYPE_PROPERTY_MERGE_STRATEGIES.get(EventTypeName, {}):
            Type[PropertyName].SetMergeStrategy(self.TYPE_PROPERTY_MERGE_STRATEGIES[EventTypeName][PropertyName])
          if PropertyName in self.TYPE_UNIQUE_PROPERTIES.get(EventTypeName, {}):
            Type[PropertyName].Unique()

    for EventTypeName in self.TYPES:
      if EventTypeName in self.PARENT_MAPPINGS:
        ParentEventTypeName = None
        ParentDescription = None
        SiblingsDescription = None
        PropertyMap = self.PARENT_MAPPINGS[EventTypeName]
        for ParentChild in self.PARENTS_CHILDREN:
          if ParentChild[2] == EventTypeName:
            ParentEventTypeName, ParentDescription = ParentChild[0:2]
            break
        for ChildSiblings in self.CHILDREN_SIBLINGS:
          if ChildSiblings[0] == EventTypeName:
            if ChildSiblings[2] != ParentEventTypeName:
              self.Error('Class properties PARENTS_CHILDREN and CHILDREN_SIBLINGS are inconsistent for output event type "%s".' % EventTypeName)
            SiblingsDescription = ChildSiblings[1]
            break

        if ParentEventTypeName:
          Type.SetParent(EventTypeParent.Create(ParentEventTypeName, PropertyMap, ParentDescription, SiblingsDescription))
        else:
          self.Error('Output event type "%s" has an entry in the PARENT_MAPPINGS class attribute, but not in the PARENTS_CHILDREN attribute.' % EventTypeName)

      yield EventTypeName, Type
