# -*- coding: utf-8 -*-
import edxml
from edxml.error import EDXMLValidationError
from edxml.logger import log
from edxml.ontology import EventTypeParent


class Transcoder(object):
    """
    This is a base class that can be extended to implement transcoders
    for the various input data record types that are generated by a
    particular TranscoderMediator implementation. The class features
    a generate_event_types() method that can generate the event type definitions
    for the events that the transcoder intends to produce. Transcoders can
    override this method to generate their own event types.

    Alternatively, transcoders can populate a number of class constants describing
    the event types. The default implementation of generate_event_types() will read these
    constants to generate the event types for you. Any details of the event type
    definitions that cannot be specified using the class constants can be set on
    the generated event types by overriding the generate_event_types() method
    and edit the event type definitions that it generates.

    Except for the TYPES constant, all constants are optional. They
    just provide a means for developers to replace code with constants,
    improving the readability of the transcoder.
    """

    VERSION = 1
    """
    The VERSION attribute indicates the version of the event types that are
    generated by the transcoder. It can be increased when the event types
    are changed. This allows merging of EDXML data that was generated by both
    older and newer versions of the transcoder.
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

    PROPERTY_MAP = {}
    """
    The PROPERTY_MAP attribute is a dictionary mapping event type names to the property
    value selectors for finding property objects in input records. Each value in the
    dictionary is another dictionary that maps value selectors to property names. The
    exact nature of the value selectors differs between transcoder implementations.
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

    TYPE_SUMMARIES = {}
    """
    The TYPE_SUMMARIES attribute is a dictionary mapping EDXML event type names to
    event summary templates.
    """

    TYPE_STORIES = {}
    """
    The TYPE_STORIES attribute is a dictionary mapping EDXML event type names to
    event story templates.
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

    TYPE_PROPERTY_POST_PROCESSORS = {}
    """
    The TYPE_PROPERTY_POST_PROCESSORS attribute is a dictionary mapping EDXML event type names to property
    processors. The property processors are a dictionary mapping property names to processors. A processor
    is a function that accepts a value from the input field that corresponds with the property and returns
    an iterable yielding zero or more values which will be stored in the output event.
    The processors will be applied to input record values before using them to create output events.

    Example::

        {
          'event_type_name': {
            'property-a': lambda x: yield x.lower()
          }
        }

    """

    TYPE_PROPERTY_CONCEPTS = {}
    """
    The TYPE_PROPERTY_CONCEPTS attribute is a dictionary mapping EDXML event type names to property
    concept associations. The associations are dictionaries mapping property names to their associated
    concepts. The associated concepts are specified as a dictionary containing the names of the associated
    concepts as keys and their association confidences as values.

    Example::

        {
          'event.type.name': {
            'property-a': {'concept.name': 8},
            'property-b': {'concept.name': 8}, {'another.concept.name': 7},
          }
        }

    """

    TYPE_PROPERTY_CONCEPTS_CNP = {}
    """
    The TYPE_PROPERTY_CONCEPTS_CNP attribute is a dictionary mapping EDXML event type names to property
    concept naming priorities (CNP). The priorities are specified as dictionaries mapping property names
    to concept CNPs. The concept CNPs are specified as a dictionary containing the names of the associated
    concepts as keys and their CNPs as values.
    When the CNP of a concept association is not specified, it will have the default value of 128.

    Example::

        {
          'event.type.name': {
            'property-a': {'concept.name': 192},
            'property-b': {'concept.name': 64}, {'another.concept.name': 0},
          }
        }

    """

    TYPE_PROPERTY_ATTRIBUTES = {}
    """
    The TYPE_PROPERTY_ATTRIBUTES attribute is a dictionary mapping EDXML event type names to concept
    attributes. The concept attributes are specified as a dictionary mapping property names to attributes.
    Each attribute is a list containing the full attribute name, the singular display name and the
    plural display name, in that order. When the plural display name is omitted, it will be guessed by
    taking the singular form and appending an 's' to it. When both singular and plural display names are
    omitted, they will be inherited from the object type.
    When the attribute of a concept association is not specified, it will inherit from the object type
    as per the EDXML specification.

    Example::

        {
          'event.type.name': {
            'property-a': {'concept.name': ['object.type.name:attribute.name-extension']},
            'property-b': {'concept.name': ['object.type.name:attribute.name-extension', 'singular', 'plural']},
          }
        }

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
    which is 'match' for hashed properties and 'drop' for all other properties.

    For convenience, the EventProperty class defines some class attributes representing the available
    merge strategies.

    Example::

      {
        'event_type_name': {
          'property_name': EventProperty.MERGE_ADD
        }
      }

    """

    TYPE_HASHED_PROPERTIES = {}
    """
    The TYPE_HASHED_PROPERTIES attribute is a dictionary mapping EDXML event type names to lists of hashed properties.
    The lists will be used to set the 'match' merge strategy for the listed properties. Example::

      {'event_type_name': ['hashed-property-a', 'hashed-property-b']}
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
    of the parent event type as values. Example::

      PARENT_MAPPINGS = {
        'child-event-type-name': {
          'child-property-name-a': 'parent-property-name-a',
          'child-property-name-b': 'parent-property-name-b',
        }
      }

    Note:
      Please refer to the EDXML specification for details about how parent property mappings work.
    """

    TYPE_TIMESPANS = {}
    """
    The TYPE_TIMESPANS attribute contains the names of the properties that define the start and the end
    of the time spans of the events. When no property is set that defines the start or end of the
    event time spans, the start or end is implicitly defined to be the smallest or largest datetime
    value in the event, regardless of the property that contains the datetime value. By setting
    specific properties for the start and / or end of the time span, only the datetime values of
    that property define the start or end of the event timespan.

    The attribute is a dictionary mapping EDXML event type names to tuples that define the time
    span properties. The first value in each tuple is the name of the property that defines the
    start of the event time spans, the second defines the end. By default, both are unset. Example::

      {'event_type_name': ['timespan-start', 'timespan-end']}
    """

    TYPE_ATTACHMENTS = {}
    """
    The TYPE_ATTACHMENTS attribute is a dictionary mapping EDXML event type names to attachment names.
    Example::

      {'event_type_name': ['my-attachment', 'another-attachment']}
    """

    TYPE_MULTI_VALUED_PROPERTIES = {}
    """
    The TYPE_MULTI_VALUED_PROPERTIES attribute is a dictionary mapping EDXML event type names to lists of
    property names that will be multi-valued.
    Example::

      {'event_type_name': ['my-property', 'another-property']}
    """

    TYPE_OPTIONAL_PROPERTIES = {}
    """
    The TYPE_OPTIONAL_PROPERTIES attribute is a dictionary mapping EDXML event type names to lists of
    property names that will be optional.
    Example::

      {'event_type_name': ['my-property', 'another-property']}

    It is also possible to indicate that all event properties of a particular event type will be optional, like this::

      {'event_type_name': True}

    In this case TYPE_MANDATORY_PROPERTIES can be used to specify exceptions.
    """

    TYPE_MANDATORY_PROPERTIES = {}
    """
    All event properties are created as mandatory properties by default, unless TYPE_OPTIONAL_PROPERTIES indicates
    otherwise. When TYPE_OPTIONAL_PROPERTIES indicates that all event properties of a specific event type must
    be optional, TYPE_MANDATORY_PROPERTIES can list exceptions. It is a dictionary mapping EDXML event type names
    to lists of property names that will be mandatory.
    Example::

      {'event_type_name': ['my-property', 'another-property']}
    """

    TYPE_ATTACHMENT_MEDIA_TYPES = {}
    """
    The TYPE_ATTACHMENT_MEDIA_TYPES attribute is a dictionary mapping EDXML event type names to attachment media
    types. The attachment media types are a dictionary mapping attachment names to its RFC 6838 media type.
    Example::

      {'event_type_name': {'my-attachment': 'text/plain'}}
    """

    TYPE_ATTACHMENT_DISPLAY_NAMES = {}
    """
    The TYPE_ATTACHMENT_DISPLAY_NAMES attribute is a dictionary mapping EDXML event type names
    to attachment display names. The attachment display names are a dictionary mapping attachment names
    to display names. Each display name is a list, containing the singular form, optionally followed
    by the plural form, like this:

        {'event-type-name': {'my-attachment': ['attachment', 'attachments']}}

    The plural form may be omitted. In that case, the plural form will be assumed
    to be the singular form with an additional 's' appended.
    """

    TYPE_ATTACHMENT_DESCRIPTIONS = {}
    """
    The TYPE_ATTACHMENT_DESCRIPTIONS attribute is a dictionary mapping EDXML event type names to attachment
    descriptions. The attachment descriptions are a dictionary mapping attachment names to its description.
    Example::

      {'event_type_name': {'my-attachment': 'Just some attachment'}}
    """

    TYPE_ATTACHMENT_ENCODINGS = {}
    """
    The TYPE_ATTACHMENT_ENCODINGS attribute is a dictionary mapping EDXML event type names to attachment
    encodings. The attachment encodings are a dictionary mapping attachment names their encodings. Valid
    encodings are either 'unicode' or 'base64'
    Example::

      {'event_type_name': {'my-attachment': 'unicode'}}
    """

    TYPE_AUTO_REPAIR_NORMALIZE = {}
    """
    The TYPE_AUTO_REPAIR_NORMALIZE attribute is a dictionary mapping EDXML event type names to properties
    which should be repaired automatically by normalizing their object values. This means that the transcoder
    is not required to store valid EDXML string representations in its output events. Rather, it may store any
    type of value which can be normalized into valid string representations automatically. Please refer to the
    :func:`~edxml.ontology.DataType.normalize_objects` method for a list of supported value types.
    The names of properties for which values may be normalized are specified as a list.
    Example::

      {'event-type-name': ['some-property']}
    """

    TYPE_AUTO_REPAIR_DROP = {}
    """
    The TYPE_AUTO_REPAIR_DROP attribute is a dictionary mapping EDXML event type names to properties
    which should be repaired automatically by dropping invalid object values. This means that the transcoder
    is permitted to store object values which cause the output event to be invalid. The EDXML writer will
    attempt to repair invalid output events. First, it will try to normalize object values when configured
    to do so. As a last resort, it can try to drop any offending object values.
    The names of properties for which values may be dropped are specified as a list.
    Example::

      {'event-type-name': ['some-property']}
    """

    def __init__(self):
        super().__init__()

        self._ontology = None  # type: edxml.ontology.Ontology

    def set_ontology(self, ontology):
        self._ontology = ontology
        return self

    def update_ontology(self, ontology, validate=True):
        self._ontology.update(ontology, validate)

    def generate(self, record, record_selector, **kwargs):
        """

        Generates one or more EDXML events from the
        given input record

        Args:
          record: Input data record
          record_selector (str): The selector matching the input record
          **kwargs: Arbitrary keyword arguments

        Yields:
          EDXMLEvent:
        """
        yield from ()

    def post_process(self, event, input_record):
        """

        Generates zero or more EDXML output events from the
        given EDXML input event. If this method is overridden by
        an extension of the Transcoder class, all events generated
        by the generate() method are passed through this method for
        post processing. This allows the generated events to be
        modified or omitted. Or, multiple derivative events can be
        created from a single input event.

        The input record that was used to generate the input event
        is also passed as a parameter. Post processors can use this
        to extract additional information and add it to the input event.

        Args:
          event (EDXMLEvent): Input event
          input_record: Input record

        Yields:
          EDXMLEvent:
        """
        yield from ()

    def create_concepts(self):
        """
        This method may be used to generate generic EDXML
        concepts that are used by all transcoders.
        """
        pass

    def create_object_types(self):
        """
        This method may be used to generate generic EDXML
        object types that are used by all transcoders.
        """
        pass

    def generate_event_types(self):
        """

        This method generates all event types using the attributes of the
        various transcoders. Yields tuples containing pairs of event type
        names and event type instances.

        Yields:
          tuple[str, edxml.ontology.EventType]:
        """

        self.check_class_attributes()

        for event_type_name in set(self.TYPE_MAP.values()):
            yield event_type_name, self.create_event_type(event_type_name, self._ontology)

    @classmethod
    def create_event_type(cls, event_type_name, ontology):
        """

        Creates specified event type in the provided ontology using
        the class attributes of the transcoder. It returns the
        resulting event type. Transcoders can optionally tune the
        resulting event type definition by overriding this method.

        Args:
            event_type_name (str): Name of the desired event type
            ontology (edxml.ontology.Ontology): Ontology to add the event type to

        Returns:
            edxml.ontology.EventType

        """
        event_type = ontology.create_event_type(event_type_name).set_version(cls.VERSION)
        if cls.TYPE_DESCRIPTIONS.get(event_type_name):
            event_type.set_description(cls.TYPE_DESCRIPTIONS[event_type_name])
        if cls.TYPE_DISPLAY_NAMES.get(event_type_name):
            event_type.set_display_name(*cls.TYPE_DISPLAY_NAMES[event_type_name])
        if cls.TYPE_SUMMARIES.get(event_type_name):
            event_type.set_summary_template(cls.TYPE_SUMMARIES[event_type_name])
        if cls.TYPE_STORIES.get(event_type_name):
            event_type.set_story_template(cls.TYPE_STORIES[event_type_name])
        if cls.TYPE_TIMESPANS.get(event_type_name):
            event_type.set_timespan_property_name_start(cls.TYPE_TIMESPANS[event_type_name][0])
            event_type.set_timespan_property_name_end(cls.TYPE_TIMESPANS[event_type_name][1])

        if cls.TYPE_HASHED_PROPERTIES.get(event_type_name, {}) == {}:
            log.warning(
                'No hashed properties have been specified for event type %s. Since this means that all events of this '
                'type that share a source URI will regarded as a single logical event, this is most likely a bug. ' %
                event_type_name
            )

        for property_name, object_type_name in cls.TYPE_PROPERTIES.get(event_type_name, {}).items():
            event_type.create_property(property_name, object_type_name)
            if property_name in cls.TYPE_PROPERTY_DESCRIPTIONS.get(event_type_name, {}):
                event_type[property_name].set_description(
                    cls.TYPE_PROPERTY_DESCRIPTIONS[event_type_name][property_name])
            if property_name in cls.TYPE_PROPERTY_SIMILARITY.get(event_type_name, {}):
                event_type[property_name].hint_similar(
                    cls.TYPE_PROPERTY_SIMILARITY[event_type_name][property_name])
            if property_name in cls.TYPE_MULTI_VALUED_PROPERTIES.get(event_type_name, []):
                event_type[property_name].make_multivalued()
            if cls.TYPE_OPTIONAL_PROPERTIES.get(event_type_name) is True:
                if property_name not in cls.TYPE_MANDATORY_PROPERTIES.get(event_type_name, []):
                    event_type[property_name].make_optional()
            elif property_name in cls.TYPE_OPTIONAL_PROPERTIES.get(event_type_name, []):
                event_type[property_name].make_optional()
            if property_name in cls.TYPE_PROPERTY_MERGE_STRATEGIES.get(event_type_name, {}):
                event_type[property_name].set_merge_strategy(
                    cls.TYPE_PROPERTY_MERGE_STRATEGIES[event_type_name][property_name])
            if property_name in cls.TYPE_HASHED_PROPERTIES.get(event_type_name, {}):
                event_type[property_name].make_hashed()
            if property_name in cls.TYPE_PROPERTY_CONCEPTS.get(event_type_name, {}):
                concept_associations = cls.TYPE_PROPERTY_CONCEPTS[event_type_name][property_name]
                for concept_name, confidence in concept_associations.items():
                    cnp = cls.TYPE_PROPERTY_CONCEPTS_CNP\
                        .get(event_type_name, {})\
                        .get(property_name, {})\
                        .get(concept_name, 128)
                    association = event_type[property_name].identifies(concept_name, confidence, cnp)
                    attribute_details = cls.TYPE_PROPERTY_ATTRIBUTES\
                        .get(event_type_name, {})\
                        .get(property_name, {})\
                        .get(concept_name)
                    if attribute_details:
                        attr_object_type_name, attr_name_extension = attribute_details[0].split(':')
                        if event_type[property_name].get_object_type_name() != attr_object_type_name:
                            raise EDXMLValidationError(
                                f"The attribute name extension of concept {concept_name} associated with property "
                                f"'{property_name}' of event type '{event_type_name}' must begin with "
                                f"'{object_type_name}:' but it begins with '{attr_object_type_name}:'."
                            )
                        association.set_attribute(attr_name_extension, *attribute_details[1:])

        for attachment_name in cls.TYPE_ATTACHMENTS.get(event_type_name, []):
            attachment = event_type.create_attachment(attachment_name)
            if attachment_name in cls.TYPE_ATTACHMENT_DESCRIPTIONS.get(event_type_name, {}):
                attachment.set_description(cls.TYPE_ATTACHMENT_DESCRIPTIONS[event_type_name][attachment_name])
            if attachment_name in cls.TYPE_ATTACHMENT_DISPLAY_NAMES.get(event_type_name, {}):
                attachment.set_display_name(
                    cls.TYPE_ATTACHMENT_DISPLAY_NAMES[event_type_name][attachment_name][0],
                    cls.TYPE_ATTACHMENT_DISPLAY_NAMES[event_type_name][attachment_name][1]
                    if len(cls.TYPE_ATTACHMENT_DISPLAY_NAMES[event_type_name][attachment_name]) > 1 else None
                )
            if attachment_name in cls.TYPE_ATTACHMENT_MEDIA_TYPES.get(event_type_name, {}):
                attachment.set_media_type(cls.TYPE_ATTACHMENT_MEDIA_TYPES[event_type_name][attachment_name])
            if attachment_name in cls.TYPE_ATTACHMENT_ENCODINGS.get(event_type_name, {}):
                attachment.set_encoding(cls.TYPE_ATTACHMENT_ENCODINGS[event_type_name][attachment_name])

        if event_type_name in cls.PARENT_MAPPINGS:
            parent_event_type_name = None
            parent_description = None
            siblings_description = None
            property_map = cls.PARENT_MAPPINGS[event_type_name]
            for parent_child in cls.PARENTS_CHILDREN:
                if parent_child[2] == event_type_name:
                    parent_event_type_name, parent_description = parent_child[0:2]
                    break
            for child_siblings in cls.CHILDREN_SIBLINGS:
                if child_siblings[0] == event_type_name:
                    siblings_description = child_siblings[1]
                    break

            if parent_event_type_name:
                event_type.set_parent(
                    EventTypeParent.create(
                        event_type,
                        parent_event_type_name,
                        property_map,
                        parent_description,
                        siblings_description
                    )
                )

        return event_type

    @classmethod
    def check_class_attributes(cls):

        existing_types = set(cls.TYPE_MAP.values())

        for event_type_name, properties in cls.TYPE_PROPERTIES.items():
            for property_name in properties.keys():
                if property_name not in cls.TYPE_PROPERTY_DESCRIPTIONS.get(event_type_name, {}):
                    log.warning(
                        'Property %s of event type %s of %s is missing a description.' %
                        (property_name, event_type_name, cls.__name__)
                    )

        const_with_property_sub_keys = [
            'TYPE_PROPERTY_POST_PROCESSORS', 'TYPE_PROPERTY_DESCRIPTIONS', 'TYPE_PROPERTY_SIMILARITY',
            'TYPE_PROPERTY_MERGE_STRATEGIES', 'TYPE_PROPERTY_CONCEPTS', 'TYPE_PROPERTY_CONCEPTS_CNP',
            'TYPE_PROPERTY_ATTRIBUTES'
        ]

        const_with_property_lists = [
            'TYPE_MULTI_VALUED_PROPERTIES', 'TYPE_MANDATORY_PROPERTIES', 'TYPE_HASHED_PROPERTIES',
            'TYPE_AUTO_REPAIR_NORMALIZE', 'TYPE_AUTO_REPAIR_DROP'
        ]

        for event_type_name in existing_types:
            existing_properties = set(cls.TYPE_PROPERTIES.get(event_type_name, {}).keys())

            if existing_properties == set():
                raise ValueError(
                    '%s.TYPE_PROPERTIES contains no properties for event type %s in TYPE_MAP.'
                    % (cls.__name__, event_type_name)
                )

            for constant_name in const_with_property_sub_keys:
                constant = getattr(cls, constant_name)
                if set(constant.get(event_type_name, {}).keys()).difference(existing_properties) != set():
                    raise ValueError(
                        f"{cls.__name__}.{constant_name} contains property names that are not in TYPE_PROPERTIES."
                    )

            for constant_name in const_with_property_lists:
                constant = getattr(cls, constant_name)
                if set(constant.get(event_type_name, [])).difference(existing_properties) != set():
                    raise ValueError(
                        f"{cls.__name__}.{constant_name} contains property names that are not in TYPE_PROPERTIES."
                    )

            optional_properties = cls.TYPE_OPTIONAL_PROPERTIES.get(event_type_name, [])
            if optional_properties is not True and set(optional_properties).difference(existing_properties) != set():
                raise ValueError(
                    '%s.TYPE_OPTIONAL_PROPERTIES contains property names that are not in TYPE_PROPERTIES.' %
                    cls.__name__
                )

            if event_type_name in cls.TYPE_PROPERTY_ATTRIBUTES:
                for property_name, concept_attr in cls.TYPE_PROPERTY_ATTRIBUTES[event_type_name].items():
                    for concept_name, attr in concept_attr.items():
                        if not isinstance(attr, list):
                            raise ValueError(
                                '%s.TYPE_PROPERTY_ATTRIBUTES contains a concept attribute that is not a list.' %
                                cls.__name__
                            )
                        if len(attr) not in [1, 2, 3]:
                            raise ValueError(
                                '%s.TYPE_PROPERTY_ATTRIBUTES contains a concept attribute that is not '
                                'a list of length 1, 2 or 3.' %
                                cls.__name__
                            )
                        if ':' not in attr[0]:
                            raise ValueError(
                                '%s.TYPE_PROPERTY_ATTRIBUTES contains a concept attribute name that does not contain a '
                                'colon (":"). You must specify full attribute names which include the object type name.'
                                % cls.__name__
                            )

            if event_type_name in cls.PARENT_MAPPINGS:
                parent_event_type_name = None
                for parent_child in cls.PARENTS_CHILDREN:
                    if not isinstance(parent_child, list):
                        raise ValueError('Class attribute PARENTS_CHILDREN contains a value that is not a list.')
                    if len(parent_child) != 3:
                        raise ValueError(
                            '%s.PARENTS_CHILDREN contains a list that has an incorrect number of items. '
                            'It must contain exactly three items.' % cls.__name__
                        )
                    if parent_child[2] == event_type_name:
                        parent_event_type_name, parent_description = parent_child[0:2]
                        break
                if parent_event_type_name is None:
                    raise ValueError(
                        'Output event type "%s" of %s has an entry in the PARENT_MAPPINGS class attribute, '
                        'but not in the PARENTS_CHILDREN attribute.' % (event_type_name, cls.__name__)
                    )
                for child_siblings in cls.CHILDREN_SIBLINGS:
                    if child_siblings[0] == event_type_name:
                        if child_siblings[2] != parent_event_type_name:
                            raise ValueError(
                                '%s.CHILDREN_SIBLINGS contains an entry containing "%s" as parent '
                                'while that event type has no children according to the PARENTS_CHILDREN attribute.'
                                % (cls.__name__, child_siblings[2])
                            )

        const_with_event_type_keys = [
            'TYPE_DESCRIPTIONS', 'TYPE_DISPLAY_NAMES', 'TYPE_SUMMARIES', 'TYPE_STORIES', 'TYPE_PROPERTIES',
            'TYPE_PROPERTY_POST_PROCESSORS', 'TYPE_PROPERTY_DESCRIPTIONS', 'TYPE_PROPERTY_SIMILARITY',
            'TYPE_PROPERTY_MERGE_STRATEGIES', 'TYPE_HASHED_PROPERTIES', 'PARENTS_CHILDREN',
            'CHILDREN_SIBLINGS', 'PARENT_MAPPINGS', 'TYPE_TIMESPANS', 'TYPE_ATTACHMENTS',
            'TYPE_MULTI_VALUED_PROPERTIES', 'TYPE_OPTIONAL_PROPERTIES', 'TYPE_MANDATORY_PROPERTIES',
            'TYPE_ATTACHMENT_MEDIA_TYPES', 'TYPE_ATTACHMENT_DISPLAY_NAMES', 'TYPE_ATTACHMENT_DESCRIPTIONS',
            'TYPE_ATTACHMENT_ENCODINGS', 'TYPE_AUTO_REPAIR_NORMALIZE', 'TYPE_AUTO_REPAIR_DROP'
        ]

        for constant_name in const_with_event_type_keys:
            constant = getattr(cls, constant_name)
            if isinstance(constant, dict) and set(constant.keys()).difference(existing_types) != set():
                raise ValueError(
                    f"{cls.__name__}.{constant_name} contains event type names that are not in TYPE_MAP."
                )

    def _post_process_properties(self, event_type_name, properties):
        for property_name in properties:
            if self.TYPE_PROPERTY_POST_PROCESSORS.get(event_type_name, {}).get(property_name):
                processed = []
                for value in properties[property_name]:
                    processed.extend(self.TYPE_PROPERTY_POST_PROCESSORS[event_type_name][property_name](value))
                properties[property_name] = processed
        return properties
