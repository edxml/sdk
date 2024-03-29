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

from edxml.error import EDXMLOntologyValidationError
from edxml.logger import log
from edxml.ontology import EventTypeParent, EventProperty, Ontology


class EventTypeFactory(object):
    """
    This class allows for the creation of event types in a declarative fashion. To
    this end it provides a collection of class constants from which one or more
    event types can be generated.
    """

    VERSION = 1
    """
    The VERSION attribute indicates the version of the event types that are
    generated by this record transcoder. It can be increased when the event types
    are changed. This allows merging of EDXML data that was generated by both
    older and newer versions of the record transcoder.
    """

    TYPES = []
    """
    The TYPES attribute contains the list of names of event types that will be
    generated by the factory.
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
    form, optionally followed by the plural form, like this::

        {'event-type-name': ['event', 'events']}

    The plural form may be omitted. This can be done by omitting the second item in the list or by
    using a string in stead of a list. In that case, the plural form will be assumed to be the singular
    form with an additional 's' appended.
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

      {'event-type-name': {'property-name': 'object-type-name'}}

    """

    TYPE_PROPERTY_CONCEPTS = {}
    """
    The TYPE_PROPERTY_CONCEPTS attribute is a dictionary mapping EDXML event type names to property
    concept associations. The associations are dictionaries mapping property names to their associated
    concepts. The associated concepts are specified as a dictionary containing the names of the associated
    concepts as keys and their association confidences as values.

    Example::

        {
          'event-type-name': {
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
          'event-type-name': {
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
          'event-type-name': {
            'property-a': {'concept.name': ['object.type.name:attribute.name-extension']},
            'property-b': {'concept.name': ['object.type.name:attribute.name-extension', 'singular', 'plural']},
          }
        }

    """

    TYPE_UNIVERSALS_NAMES = {}
    """
    The TYPE_UNIVERSALS_NAMES attribute is a dictionary mapping EDXML event type names to name relations.
    The name relations are dictionaries mapping properties containing object values (source properties) to
    other properties containing names for those object values (target properties). Name relations are
    discussed in detail in the EDXML specification.

    Note that the source properties are automatically marked as being single-valued.

    Example::

        {
          'event-type-name': {
            'product-id': 'product-name'
          }
        }

    """

    TYPE_UNIVERSALS_DESCRIPTIONS = {}
    """
    The TYPE_UNIVERSALS_DESCRIPTIONS attribute is a dictionary mapping EDXML event type names to description relations.
    The description relations are dictionaries mapping properties containing object values (source properties) to
    other properties containing description for those object values (target properties). Description relations are
    discussed in detail in the EDXML specification.

    Note that the source properties are automatically marked as being single-valued.

    Example::

        {
          'event-type-name': {
            'product-id': 'product-description'
          }
        }

    """

    TYPE_UNIVERSALS_CONTAINERS = {}
    """
    The TYPE_UNIVERSALS_CONTAINERS attribute is a dictionary mapping EDXML event type names to container relations.
    The container relations are dictionaries mapping properties containing object values (source properties) to
    other properties providing 'containers' for those object values (target properties). Container relations are
    discussed in detail in the EDXML specification.

    Note that the source properties are automatically marked as being single-valued.

    Example::

        {
          'event-type-name': {
            'product-name': 'product-category'
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
          'event-type-name': {
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
          'event-type-name': {
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
    which is 'match' for hashed properties and 'any' for all other properties.

    For convenience, the EventProperty class defines some class attributes representing the available
    merge strategies.

    Example::

      {
        'event-type-name': {
          'property-name': EventProperty.MERGE_ADD
        }
      }

    """

    TYPE_HASHED_PROPERTIES = {}
    """
    The TYPE_HASHED_PROPERTIES attribute is a dictionary mapping EDXML event type names to lists of hashed properties.
    The lists will be used to set the 'match' merge strategy for the listed properties. Example::

      {'event-type-name': ['hashed-property-a', 'hashed-property-b']}
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

    TYPE_TIME_SPANS = {}
    """
    The TYPE_TIME_SPANS attribute contains the names of the properties that define the start and the end
    of the time spans of the events. When no property is set that defines the start or end of the
    event time spans, the start or end is implicitly defined to be the smallest or largest datetime
    value in the event, regardless of the property that contains the datetime value. By setting
    specific properties for the start and / or end of the time span, only the datetime values of
    that property define the start or end of the event timespan.

    The attribute is a dictionary mapping EDXML event type names to tuples that define the time
    span properties. The first value in each tuple is the name of the property that defines the
    start of the event time spans, the second defines the end. By default, both are unset. Example::

      {'event-type-name': ['timespan-start', 'timespan-end']}
    """

    TYPE_VERSIONS = {}
    """
    The TYPE_VERSIONS attribute contains the names of the properties that define the versions of
    the events.

    The attribute is a dictionary mapping EDXML event type names to the names of the event properties
    that contain the version. Example::

      {'event-type-name': 'version'}
    """

    TYPE_SEQUENCES = {}
    """
    The TYPE_SEQUENCES attribute contains the names of the properties that define the sequence numbers of
    the events. Together with event time spans, sequence numbers determine logical event order.

    The attribute is a dictionary mapping EDXML event type names to the names of the event properties
    that contain the sequence number. Example::

      {'event-type-name': 'sequence'}
    """

    TYPE_ATTACHMENTS = {}
    """
    The TYPE_ATTACHMENTS attribute is a dictionary mapping EDXML event type names to attachment names.
    Example::

      {'event-type-name': ['my-attachment', 'another-attachment']}
    """

    TYPE_MULTI_VALUED_PROPERTIES = {}
    """
    The TYPE_MULTI_VALUED_PROPERTIES attribute is a dictionary mapping EDXML event type names to lists of
    property names that will be multi-valued.
    Example::

      {'event-type-name': ['my-property', 'another-property']}
    """

    TYPE_OPTIONAL_PROPERTIES = {}
    """
    The TYPE_OPTIONAL_PROPERTIES attribute is a dictionary mapping EDXML event type names to lists of
    property names that will be optional.
    Example::

      {'event-type-name': ['my-property', 'another-property']}

    It is also possible to indicate that all event properties of a particular event type will be optional, like this::

      {'event-type-name': True}

    In this case TYPE_MANDATORY_PROPERTIES can be used to specify exceptions.
    """

    TYPE_MANDATORY_PROPERTIES = {}
    """
    All event properties are created as mandatory properties by default, unless TYPE_OPTIONAL_PROPERTIES indicates
    otherwise. When TYPE_OPTIONAL_PROPERTIES indicates that all event properties of a specific event type must
    be optional, TYPE_MANDATORY_PROPERTIES can list exceptions. It is a dictionary mapping EDXML event type names
    to lists of property names that will be mandatory.
    Example::

      {'event-type-name': ['my-property', 'another-property']}
    """

    TYPE_ATTACHMENT_MEDIA_TYPES = {}
    """
    The TYPE_ATTACHMENT_MEDIA_TYPES attribute is a dictionary mapping EDXML event type names to attachment media
    types. The attachment media types are a dictionary mapping attachment names to its RFC 6838 media type.
    Example::

      {'event-type-name': {'my-attachment': 'text/plain'}}
    """

    TYPE_ATTACHMENT_DISPLAY_NAMES = {}
    """
    The TYPE_ATTACHMENT_DISPLAY_NAMES attribute is a dictionary mapping EDXML event type names
    to attachment display names. The attachment display names are a dictionary mapping attachment names
    to display names. Each display name is a list, containing the singular form, optionally followed
    by the plural form, like this::

        {'event-type-name': {'my-attachment': ['attachment', 'attachments']}}

    The plural form may be omitted. This can be done by omitting the second item in the list or by
    using a string in stead of a list. In that case, the plural form will be assumed to be the singular
    form with an additional 's' appended.
    """

    TYPE_ATTACHMENT_DESCRIPTIONS = {}
    """
    The TYPE_ATTACHMENT_DESCRIPTIONS attribute is a dictionary mapping EDXML event type names to attachment
    descriptions. The attachment descriptions are a dictionary mapping attachment names to its description.
    Example::

      {'event-type-name': {'my-attachment': 'Just some attachment'}}
    """

    TYPE_ATTACHMENT_ENCODINGS = {}
    """
    The TYPE_ATTACHMENT_ENCODINGS attribute is a dictionary mapping EDXML event type names to attachment
    encodings. The attachment encodings are a dictionary mapping attachment names their encodings. Valid
    encodings are either 'unicode' or 'base64'
    Example::

      {'event-type-name': {'my-attachment': 'unicode'}}
    """

    def generate_ontology(self, target_ontology=None):
        """

        Generates the ontology elements, adding them to a
        target ontology. The target ontology is returned.
        By default, the target ontology is an empty ontology
        which is not validated after populating it. When
        another target ontology is passed, it will be
        updated using the generated ontology elements. This
        update operation does trigger ontology validation.

        Args:
            target_ontology (edxml.ontology.Ontology)

        Returns:
            edxml.ontology.Ontology: The resulting ontology
        """
        self.check_class_attributes()

        ontology = Ontology()
        self.create_object_types(ontology)
        self.create_concepts(ontology)
        for event_type_name in set(self.TYPES):
            self.create_event_type(event_type_name, ontology)

        if target_ontology:
            target_ontology.update(ontology)
            return target_ontology

        return ontology

    def create_concepts(self, ontology):
        """
        This method may be used to define EDXML concepts that
        are referred to by the generated event types.
        """
        pass

    def create_object_types(self, ontology):
        """
        This method may be used to define EDXML object types that
        are referred to by the generated event types.
        """
        pass

    def create_event_types(self, ontology):
        """

        This method generates all event types using the class constants of this
        event type factory. The event types are created in specified ontology.
        This ontology must have all required object types and concepts.
        """

        self.check_class_attributes()

        for event_type_name in set(self.TYPES):
            self.create_event_type(event_type_name, ontology)

    @classmethod
    def create_event_type(cls, event_type_name, ontology):
        """

        Creates specified event type in the provided ontology using
        the class attributes of this factory. It returns the
        resulting event type. The resulting event types can optionally
        be tuned by overriding this method.

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
            event_type_dn = cls.TYPE_DISPLAY_NAMES[event_type_name]
            if isinstance(event_type_dn, str):
                event_type_dn = [event_type_dn]
            event_type.set_display_name(*event_type_dn)
        if cls.TYPE_SUMMARIES.get(event_type_name):
            event_type.set_summary_template(cls.TYPE_SUMMARIES[event_type_name])
        if cls.TYPE_STORIES.get(event_type_name):
            event_type.set_story_template(cls.TYPE_STORIES[event_type_name])
        if cls.TYPE_TIME_SPANS.get(event_type_name):
            event_type.set_timespan_property_name_start(cls.TYPE_TIME_SPANS[event_type_name][0])
            event_type.set_timespan_property_name_end(cls.TYPE_TIME_SPANS[event_type_name][1])
        if cls.TYPE_VERSIONS.get(event_type_name):
            event_type.set_version_property_name(cls.TYPE_VERSIONS.get(event_type_name))
        if cls.TYPE_SEQUENCES.get(event_type_name):
            event_type.set_sequence_property_name(cls.TYPE_SEQUENCES.get(event_type_name))

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
            else:
                event_type[property_name].set_description(property_name.replace('.', ' '))
            if property_name in cls.TYPE_PROPERTY_SIMILARITY.get(event_type_name, {}):
                event_type[property_name].hint_similar(
                    cls.TYPE_PROPERTY_SIMILARITY[event_type_name][property_name])
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
                            raise EDXMLOntologyValidationError(
                                f"The attribute name extension of concept {concept_name} associated with property "
                                f"'{property_name}' of event type '{event_type_name}' must begin with "
                                f"'{object_type_name}:' but it begins with '{attr_object_type_name}:'."
                            )
                        association.set_attribute(attr_name_extension, *attribute_details[1:])

        for target_property, source_property in cls.TYPE_UNIVERSALS_NAMES.get(event_type_name, {}).items():
            event_type.get_properties()[source_property].make_single_valued().relate_name(target_property)
        for target_property, source_property in cls.TYPE_UNIVERSALS_DESCRIPTIONS.get(event_type_name, {}).items():
            event_type.get_properties()[source_property].make_single_valued().relate_description(target_property)
        for target_property, source_property in cls.TYPE_UNIVERSALS_CONTAINERS.get(event_type_name, {}).items():
            event_type.get_properties()[source_property].make_single_valued().relate_container(target_property)

        for property_name, object_type_name in cls.TYPE_PROPERTIES.get(event_type_name, {}).items():
            if property_name in cls.TYPE_MULTI_VALUED_PROPERTIES.get(event_type_name, []):
                event_type[property_name].make_multivalued()

        for attachment_name in cls.TYPE_ATTACHMENTS.get(event_type_name, []):
            attachment = event_type.create_attachment(attachment_name)
            attachment_dn = None
            if attachment_name in cls.TYPE_ATTACHMENT_DISPLAY_NAMES.get(event_type_name, {}):
                attachment_dn = cls.TYPE_ATTACHMENT_DISPLAY_NAMES[event_type_name][attachment_name]
                if isinstance(attachment_dn, str):
                    attachment_dn = [attachment_dn]
                attachment.set_display_name(
                    attachment_dn[0],
                    attachment_dn[1] if len(attachment_dn) > 1 else None
                )
            if attachment_name in cls.TYPE_ATTACHMENT_DESCRIPTIONS.get(event_type_name, {}):
                attachment.set_description(cls.TYPE_ATTACHMENT_DESCRIPTIONS[event_type_name][attachment_name])
            elif attachment_dn:
                attachment.set_description(attachment_dn[0])
            if attachment_name in cls.TYPE_ATTACHMENT_MEDIA_TYPES.get(event_type_name, {}):
                attachment.set_media_type(cls.TYPE_ATTACHMENT_MEDIA_TYPES[event_type_name][attachment_name])
            if attachment_name in cls.TYPE_ATTACHMENT_ENCODINGS.get(event_type_name, {}):
                attachment.set_encoding(cls.TYPE_ATTACHMENT_ENCODINGS[event_type_name][attachment_name])

        if event_type_name in cls.PARENT_MAPPINGS:
            parent_event_type_name = None
            parent_description = None
            siblings_description = ''
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

        existing_types = set(cls.TYPES)

        const_with_property_sub_keys = [
            'TYPE_PROPERTY_DESCRIPTIONS', 'TYPE_PROPERTY_SIMILARITY',
            'TYPE_PROPERTY_MERGE_STRATEGIES', 'TYPE_PROPERTY_CONCEPTS', 'TYPE_PROPERTY_CONCEPTS_CNP',
            'TYPE_PROPERTY_ATTRIBUTES'
        ]

        const_with_property_lists = [
            'TYPE_MULTI_VALUED_PROPERTIES', 'TYPE_MANDATORY_PROPERTIES', 'TYPE_HASHED_PROPERTIES',
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
                        if concept_name not in cls.TYPE_PROPERTY_CONCEPTS.get(event_type_name, {}).get(property_name):
                            raise ValueError(
                                '%s.TYPE_PROPERTY_ATTRIBUTES contains a concept attribute name for property %s of '
                                'event type %s, associated with concept %s. According to the TYPE_PROPERTY_CONCEPTS '
                                'constant, that concept is not associated with the property.'
                                % (cls.__name__, property_name, event_type_name, concept_name)
                            )

            existing_properties = set(cls.TYPE_PROPERTIES.get(event_type_name, {}).keys())
            if event_type_name in cls.TYPE_UNIVERSALS_NAMES:
                for target_property_name, source_property_name in cls.TYPE_UNIVERSALS_NAMES[event_type_name].items():
                    if target_property_name not in existing_properties:
                        raise ValueError(
                            f"{cls.__name__}.TYPE_UNIVERSALS_NAMES contains target property {target_property_name} "
                            f"which is not in TYPE_PROPERTIES."
                        )
                    if source_property_name not in existing_properties:
                        raise ValueError(
                            f"{cls.__name__}.TYPE_UNIVERSALS_NAMES contains source property {target_property_name} "
                            f"which is not in TYPE_PROPERTIES."
                        )
            if event_type_name in cls.TYPE_UNIVERSALS_DESCRIPTIONS:
                for target_property_name, source_property_name in \
                        cls.TYPE_UNIVERSALS_DESCRIPTIONS[event_type_name].items():
                    if target_property_name not in existing_properties:
                        raise ValueError(
                            f"{cls.__name__}.TYPE_UNIVERSALS_DESCRIPTIONS contains target property "
                            f"{target_property_name} which is not in TYPE_PROPERTIES."
                        )
                    if source_property_name not in existing_properties:
                        raise ValueError(
                            f"{cls.__name__}.TYPE_UNIVERSALS_DESCRIPTIONS contains source property "
                            f"{target_property_name} which is not in TYPE_PROPERTIES."
                        )
            if event_type_name in cls.TYPE_UNIVERSALS_CONTAINERS:
                for target_property_name, source_property_name in \
                        cls.TYPE_UNIVERSALS_CONTAINERS[event_type_name].items():
                    if target_property_name not in existing_properties:
                        raise ValueError(
                            f"{cls.__name__}.TYPE_UNIVERSALS_CONTAINERS contains target property "
                            f"{target_property_name} which is not in TYPE_PROPERTIES."
                        )
                    if source_property_name not in existing_properties:
                        raise ValueError(
                            f"{cls.__name__}.TYPE_UNIVERSALS_CONTAINERS contains source property "
                            f"{target_property_name} which is not in TYPE_PROPERTIES."
                        )

            if event_type_name in cls.TYPE_VERSIONS:
                if not isinstance(cls.TYPE_VERSIONS[event_type_name], str):
                    raise ValueError(
                        f"{cls.__name__}.TYPE_VERSIONS contains a version property for event type {event_type_name} "
                        f"which is not a string."
                    )

            if event_type_name in cls.TYPE_PROPERTY_MERGE_STRATEGIES:
                for property_name, strategy in cls.TYPE_PROPERTY_MERGE_STRATEGIES[event_type_name].items():
                    if strategy == EventProperty.MERGE_ADD and \
                            property_name not in cls.TYPE_MULTI_VALUED_PROPERTIES.get(event_type_name, []):
                        raise ValueError(
                            f"{cls.__name__}.TYPE_PROPERTY_MERGE_STRATEGIES indicates that "
                            f"the {property_name} property of event type {event_type_name} has merge strategy 'add' "
                            f"while it is not listed in TYPE_MULTI_VALUED_PROPERTIES as a multi-valued property."
                        )

            if event_type_name in cls.PARENT_MAPPINGS:
                parent_event_type_name = None
                siblings_description = None
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
                        siblings_description = child_siblings[1]
                        if child_siblings[2] != parent_event_type_name:
                            raise ValueError(
                                '%s.CHILDREN_SIBLINGS contains an entry containing "%s" as parent '
                                'while that event type has no children according to the PARENTS_CHILDREN attribute.'
                                % (cls.__name__, child_siblings[2])
                            )
                if not siblings_description:
                    raise ValueError(
                        'Output event type "%s" of %s has an entry in the PARENT_MAPPINGS class attribute, '
                        'but not in the CHILDREN_SIBLINGS attribute.' % (event_type_name, cls.__name__)
                    )

        const_with_event_type_keys = [
            'TYPE_DESCRIPTIONS', 'TYPE_DISPLAY_NAMES', 'TYPE_SUMMARIES', 'TYPE_STORIES', 'TYPE_PROPERTIES',
            'TYPE_PROPERTY_DESCRIPTIONS', 'TYPE_PROPERTY_SIMILARITY',
            'TYPE_PROPERTY_MERGE_STRATEGIES', 'TYPE_HASHED_PROPERTIES', 'PARENTS_CHILDREN',
            'CHILDREN_SIBLINGS', 'PARENT_MAPPINGS', 'TYPE_TIME_SPANS', 'TYPE_VERSIONS', 'TYPE_ATTACHMENTS',
            'TYPE_MULTI_VALUED_PROPERTIES', 'TYPE_OPTIONAL_PROPERTIES', 'TYPE_MANDATORY_PROPERTIES',
            'TYPE_ATTACHMENT_MEDIA_TYPES', 'TYPE_ATTACHMENT_DISPLAY_NAMES', 'TYPE_ATTACHMENT_DESCRIPTIONS',
            'TYPE_ATTACHMENT_ENCODINGS',
            'TYPE_UNIVERSALS_NAMES', 'TYPE_UNIVERSALS_CONTAINERS',
            'TYPE_PROPERTY_CONCEPTS', 'TYPE_PROPERTY_CONCEPTS_CNP', 'TYPE_PROPERTY_ATTRIBUTES',
            'TYPE_UNIVERSALS_DESCRIPTIONS', 'TYPE_SEQUENCES'
        ]

        for constant_name in const_with_event_type_keys:
            constant = getattr(cls, constant_name)
            if isinstance(constant, dict) and set(constant.keys()).difference(existing_types) != set():
                raise ValueError(
                    f"{cls.__name__}.{constant_name} contains event type names that are not in the TYPES attribute."
                )
