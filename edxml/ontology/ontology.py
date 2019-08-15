# -*- coding: utf-8 -*-
from typing import Dict

import edxml.ontology

from lxml import etree
from edxml.EDXMLBase import EDXMLValidationError
from edxml.ontology import ObjectType, Concept, EventType, EventSource, OntologyElement


class Ontology(OntologyElement):
    """
    Class representing an EDXML ontology
    """

    __bricks = {
        'object_types': None,
        'concepts': None
    }  # type: Dict[str, edxml.ontology.Ontology]

    def __init__(self):
        self.__version = 0
        self.__event_types = {}    # type: Dict[str, edxml.ontology.EventType]
        self.__object_types = {}   # type: Dict[str, edxml.ontology.ObjectType]
        self.__sources = {}        # type: Dict[str, edxml.ontology.EventSource]
        self.__concepts = {}       # type: Dict[str, edxml.ontology.Concept]

    def clear(self):
        """

        Removes all event types, object types, concepts
        and event source definitions from the ontology.

        Returns:
          edxml.ontology.Ontology: The ontology
        """
        self.__version = 0
        self.__event_types = {}
        self.__object_types = {}
        self.__sources = {}
        self.__concepts = {}

        return self

    def get_version(self):
        """

        Returns the current ontology version. The initial
        version of a newly created empty ontology is zero.
        On each change, the version is incremented.

        Note that this has nothing to do with versioning, upgrading
        and downgrading of EDXML ontologies. EDXML ontologies have no
        global version. The version that we return here is for change
        tracking.

        Returns:
          int: Ontology version

        """
        return self.__version

    def is_modified_since(self, version):
        """

        Returns True if the ontology is newer than
        the specified version. Returns False if the
        ontology version is equal or older.

        Returns:
          bool:

        """
        return self.__version > version

    @classmethod
    def register_brick(cls, brick):
        """

        Registers an ontology brick with the Ontology class, allowing
        Ontology instances to use any definitions offered by that brick.
        Ontology brick packages expose a register() method, which calls
        this method to register itself with the Ontology class.

        Args:
          brick (edxml.ontology.Brick): Ontology brick

        """

        if not cls.__bricks['object_types']:
            cls.__bricks['object_types'] = edxml.ontology.Ontology()
        if not cls.__bricks['concepts']:
            cls.__bricks['concepts'] = edxml.ontology.Ontology()

        for _ in brick.generate_object_types(cls.__bricks['object_types']):
            pass

        for _ in brick.generate_concepts(cls.__bricks['concepts']):
            pass

    def _import_object_type_from_brick(self, object_type_name):

        if Ontology.__bricks['object_types'] is not None:
            object_type = Ontology.__bricks['object_types'].get_object_type(object_type_name, False)
            if object_type:
                self._add_object_type(object_type)

    def _import_concept_from_brick(self, concept_name):

        if Ontology.__bricks['concepts'] is not None:
            brick_concept = Ontology.__bricks['concepts'].get_concept(concept_name, False)
            if brick_concept:
                self._add_concept(brick_concept)

    def create_object_type(self, name, display_name_singular=None, display_name_plural=None, description=None,
                           data_type='string:0:cs:u'):
        """

        Creates and returns a new ObjectType instance. When no display
        names are specified, display names will be created from the
        object type name. If only a singular form is specified, the
        plural form will be auto-generated by appending an 's'.

        The object type is not validated on creation. This allows for creating
        a crude initial definition using this method and finish the definition
        later. If you do intend to create a valid definition from the start,
        it is recommended to validate it immediately.

        If an object type with the same name already exists in the ontology,
        the new definition is ignored and the existing one returned.

        Args:
          name (str): object type name
          display_name_singular (str): display name (singular form)
          display_name_plural (str): display name (plural form)
          description (str): short description of the object type
          data_type (str): a valid EDXML data type

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """

        if name not in self.__object_types:
            self._add_object_type(
                ObjectType(
                    self, name, display_name_singular, display_name_plural, description, data_type
                ), validate=False
            )

        return self.__object_types[name]

    def create_concept(self, name, display_name_singular=None, display_name_plural=None, description=None):
        """

        Creates and returns a new Concept instance. When no display
        names are specified, display names will be created from the
        concept name. If only a singular form is specified, the
        plural form will be auto-generated by appending an 's'.

        The concept is not validated on creation. This allows for creating
        a crude initial definition using this method and finish the definition
        later. If you do intend to create a valid definition from the start,
        it is recommended to validate it immediately.

        If a concept with the same name already exists in the ontology,
        the new definition is ignored and the existing one returned.

        Args:
          name (str): concept name
          display_name_singular (str): display name (singular form)
          display_name_plural (str): display name (plural form)
          description (str): short description of the concept

        Returns:
          edxml.ontology.Concept: The Concept instance
        """

        if display_name_singular:
            display_name = '%s/%s' % (display_name_singular,
                                      display_name_plural if display_name_plural else '%ss' % display_name_singular)
        else:
            display_name = None

        if name not in self.__concepts:
            self._add_concept(Concept(self, name, display_name, description), validate=False)

        return self.__concepts[name]

    def create_event_type(self, name, display_name_singular=None, display_name_plural=None, description=None):
        """

        Creates and returns a new EventType instance. When no display
        names are specified, display names will be created from the
        event type name. If only a singular form is specified, the
        plural form will be auto-generated by appending an 's'.

        The event type is not validated on creation. This allows for creating
        a crude initial definition using this method and finish the definition
        later. If you do intend to create a valid definition from the start,
        it is recommended to validate it immediately.

        If an event type with the same name already exists in the ontology,
        the new definition is ignored and the existing one returned.

        Args:
          name (str): Event type name
          display_name_singular (str): Display name (singular form)
          display_name_plural (str): Display name (plural form)
          description (str): Event type description

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        if display_name_singular:
            display_name = '%s/%s' % (display_name_singular,
                                      display_name_plural if display_name_plural else '%ss' % display_name_singular)
        else:
            display_name = None

        if name not in self.__event_types:
            self._add_event_type(EventType(self, name, display_name, description), validate=False)

        return self.__event_types[name]

    def create_event_source(self, uri, description='no description available', acquisition_date='00000000'):
        """

        Creates a new event source definition. If no acquisition date
        is specified, it will be assumed that the acquisition date
        is today.

        The source is not validated on creation. This allows for creating
        a crude initial definition using this method and finish the definition
        later. If you do intend to create a valid definition from the start,
        it is recommended to validate it immediately.

        If the URI is missing a leading and / or trailing slash, these will be
        appended automatically.

        If a source with the same URI already exists in the ontology,
        the new definition is ignored and the existing one returned.

        Note:
          Choose your source URIs wisely. The source URIs are used in
          sticky hash computations, so changing the URI may have quite
          a few consequences if the hash is referred to anywhere. Also,
          pay attention to the URI in the context of URIs generated by
          other EDXML data sources, to obtain a consistent, well structured
          source URI tree.

        Args:
         uri (str): The source URI
         description (str): Description of the source
         acquisition_date (str): Acquisition date in format yyyymmdd

        Returns:
          edxml.ontology.EventSource:
        """
        source = EventSource(self, uri, description, acquisition_date)

        if source.get_uri() not in self.__sources:
            self._add_event_source(source, validate=False)

        return source

    def delete_object_type(self, object_type_name):
        """

        Deletes specified object type from the ontology, if
        it exists.

        Warnings:
          Deleting object types may result in an invalid ontology.

        Args:
          object_type_name (str): An EDXML object type name

        Returns:
          edxml.ontology.Ontology: The ontology
        """

        if object_type_name in self.__object_types:
            del self.__object_types[object_type_name]
            self._child_modified_callback()

        return self

    def delete_concept(self, concept_name):
        """

        Deletes specified concept from the ontology, if
        it exists.

        Warnings:
          Deleting concepts may result in an invalid ontology.

        Args:
          concept_name (str): An EDXML concept name

        Returns:
          edxml.ontology.Ontology: The ontology
        """

        if concept_name in self.__concepts:
            del self.__concepts[concept_name]
            self._child_modified_callback()

        return self

    def delete_event_type(self, event_type_name):
        """

        Deletes specified event type from the ontology, if
        it exists.

        Warnings:
          Deleting event types may result in an invalid ontology.

        Args:
          event_type_name (str): An EDXML event type name

        Returns:
          edxml.ontology.Ontology: The ontology
        """

        if event_type_name in self.__event_types:
            del self.__event_types[event_type_name]
            self._child_modified_callback()

        return self

    def delete_event_source(self, source_uri):
        """

        Deletes specified event source definition from the
        ontology, if it exists.

        Args:
          source_uri (str): An EDXML event source URI

        Returns:
          edxml.ontology.Ontology: The ontology
        """

        if source_uri in self.__sources:
            del self.__sources[source_uri]
            self._child_modified_callback()

        return self

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self.__version += 1
        return self

    def _add_event_type(self, event_type, validate=True):
        """

        Adds specified event type to the ontology. If the
        event type exists in the ontology, it will be checked
        for consistency with the existing definition.

        Args:
          event_type (edxml.ontology.EventType): An EventType instance
          validate (bool): Validate definition (True) or not (False)

        Returns:
          edxml.ontology.Ontology: The ontology
        """
        name = event_type.get_name()

        if name in self.__event_types:
            self.__event_types[name].update(event_type)
        else:
            if validate:
                event_type.validate()
            self.__event_types[name] = event_type
            self._child_modified_callback()

        return self

    def _add_object_type(self, object_type, validate=True):
        """

        Adds specified object type to the ontology. If the
        object type exists in the ontology, it will be checked
        for consistency with the existing definition.

        Args:
          object_type (edxml.ontology.ObjectType): An ObjectType instance
          validate (bool): Validate definition (True) or not (False)

        Returns:
          edxml.ontology.Ontology: The ontology
        """
        name = object_type.get_name()

        if name in self.__object_types:
            self.__object_types[name].update(object_type)
        else:
            if validate:
                object_type.validate()
            self.__object_types[name] = object_type
            self._child_modified_callback()

        return self

    def _add_concept(self, concept, validate=True):
        """

        Adds specified concept to the ontology. If the
        concept exists in the ontology, it will be checked
        for consistency with the existing definition.

        Args:
          concept (edxml.ontology.Concept): A Concept instance
          validate (bool): Validate definition (True) or not (False)

        Returns:
          edxml.ontology.Ontology: The ontology
        """
        name = concept.get_name()

        if name in self.__concepts:
            self.__concepts[name].update(concept)
        else:
            if validate:
                concept.validate()
            self.__concepts[name] = concept
            self._child_modified_callback()

        return self

    def _add_event_source(self, event_source, validate=True):
        """

        Adds specified event source to the ontology. If the
        event source exists in the ontology, it will be checked
        for consistency with the existing definition.

        Args:
          event_source (edxml.ontology.EventSource): An EventSource instance
          validate (bool): Validate definition (True) or not (False)

        Returns:
          edxml.ontology.Ontology: The ontology
        """
        uri = event_source.get_uri()

        if uri in self.__sources:
            self.__sources[uri].update(event_source)
        else:
            if validate:
                event_source.validate()
            self.__sources[uri] = event_source
            self._child_modified_callback()

        return self

    def get_event_types(self):
        """

        Returns a dictionary containing all event types
        in the ontology. The keys are the event type
        names, the values are EventType instances.

        Returns:
          Dict[str, edxml.ontology.EventType]: EventType instances
        """
        return self.__event_types

    def get_object_types(self):
        """

        Returns a dictionary containing all object types
        in the ontology. The keys are the object type
        names, the values are ObjectType instances.

        Returns:
          Dict[str, edxml.ontology.ObjectType]: ObjectType instances
        """
        return self.__object_types

    def get_concepts(self):
        """

        Returns a dictionary containing all concepts
        in the ontology. The keys are the concept
        names, the values are Concept instances.

        Returns:
          Dict[str, edxml.ontology.Concept]: Concept instances
        """
        return self.__concepts

    def get_event_sources(self):
        """

        Returns a dictionary containing all event sources
        in the ontology. The keys are the event source
        URIs, the values are EventSource instances.

        Returns:
          Dict[str, edxml.ontology.EventSource]: EventSource instances
        """
        return self.__sources

    def get_event_type_names(self):
        """

        Returns the list of names of all defined
        event types.

        Returns:
           List[str]: List of event type names
        """
        return self.__event_types.keys()

    def get_object_type_names(self):
        """

        Returns the list of names of all defined
        object types.

        Returns:
           List[str]: List of object type names
        """
        return self.__object_types.keys()

    def get_event_source_uris(self):
        """

        Returns the list of URIs of all defined
        event sources.

        Returns:
           List[str]: List of source URIs
        """
        return self.__sources.keys()

    def get_concept_names(self):
        """

        Returns the list of names of all defined
        concepts.

        Returns:
           List[str]: List of concept names
        """
        return self.__concepts.keys()

    def get_event_type(self, name):
        """

        Returns the EventType instance having
        specified event type name, or None if
        no event type with that name exists.

        Args:
          name (str): Event type name

        Returns:
          edxml.ontology.EventType: The event type instance
        """
        return self.__event_types.get(name)

    def get_object_type(self, name, import_brick=True):
        """

        Returns the ObjectType instance having
        specified object type name, or None if
        no object type with that name exists.

        When the ontology does not contain the
        requested concept it will attempt to find
        the concept in any registered ontology
        bricks and import it. This can be turned
        off by setting import_brick to False.

        Args:
          name (str): Object type name
          import_brick (bool): Brick import flag

        Returns:
          edxml.ontology.ObjectType: The object type instance
        """
        if import_brick and name not in self.__object_types.keys():
            self._import_object_type_from_brick(name)

        return self.__object_types.get(name)

    def get_concept(self, name, import_brick=True):
        """

        Returns the Concept instance having
        specified concept name, or None if
        no concept with that name exists.

        When the ontology does not contain the
        requested concept it will attempt to find
        the concept in any registered ontology
        bricks and import it. This can be turned
        off by setting import_brick to False.

        Args:
          name (str): Concept name
          import_brick (bool): Brick import flag

        Returns:
          edxml.ontology.Concept: The Concept instance
        """
        if import_brick and name not in self.__concepts.keys():
            self._import_concept_from_brick(name)

        return self.__concepts.get(name)

    def get_event_source(self, uri):
        """

        Returns the EventSource instance having
        specified event source URI, or None if
        no event source with that URI exists.

        Args:
          uri (str): Event source URI

        Returns:
          edxml.ontology.EventSource: The event source instance
        """
        return self.__sources.get(uri)

    def __parse_event_types(self, event_types_element, validate=True):
        for typeElement in event_types_element:
            self._add_event_type(EventType.create_from_xml(typeElement, self), validate)

    def __parse_object_types(self, object_types_element, validate=True):
        for typeElement in object_types_element:
            self._add_object_type(ObjectType.create_from_xml(typeElement, self), validate)

    def __parse_concepts(self, concepts_element, validate=True):
        for conceptElement in concepts_element:
            self._add_concept(
                Concept.create_from_xml(conceptElement, self), validate
            )

    def __parse_sources(self, sources_element, validate=True):
        for sourceElement in sources_element:
            self._add_event_source(EventSource.create_from_xml(sourceElement, self), validate)

    def validate(self):
        """

        Checks if the defined ontology is a valid EDXML ontology.

        Raises:
          EDXMLValidationError

        Returns:
          edxml.ontology.Ontology: The ontology

        """
        # Validate all object types
        for object_type_name, object_type in self.__object_types.items():
            object_type.validate()

        # Validate all event types
        for event_type_name, event_type in self.__event_types.items():
            event_type.validate()

        # Check if all event type parents are defined
        for event_type_name, event_type in self.__event_types.items():
            event_type.validate()
            if event_type.get_parent() is not None:
                if event_type.get_parent().get_event_type() not in self.__event_types:
                    raise EDXMLValidationError(
                        'Event type "%s" refers to parent event type "%s", which is not defined.' %
                        (event_type_name, event_type.get_parent().get_event_type()))

        # Check if the object type of each property exists
        for event_type_name, event_type in self.__event_types.iteritems():
            for property_name, event_property in event_type.iteritems():
                object_type_name = event_property.get_object_type_name()
                if self.get_object_type(object_type_name) is None:
                    # Object type is not defined, try to load it from
                    # any registered ontology bricks
                    self._import_object_type_from_brick(object_type_name)
                if self.get_object_type(object_type_name) is None:
                    raise EDXMLValidationError(
                        'Property "%s" of event type "%s" refers to undefined object type "%s".' %
                        (property_name, event_type_name,
                         event_property.get_object_type_name())
                    )

        # Check if the concepts referred to by each property exists
        for event_type_name, event_type in self.__event_types.iteritems():
            for property_name, event_property in event_type.iteritems():
                for concept_name in event_property.get_concept_associations().keys():
                    if self.get_concept(concept_name) is None:
                        # Concept is not defined, try to load it from
                        # any registered ontology bricks
                        self._import_concept_from_brick(concept_name)
                    if self.get_concept(concept_name) is None:
                        raise EDXMLValidationError(
                            'Property "%s" of event type "%s" refers to undefined concept "%s".' %
                            (property_name, event_type_name, concept_name)
                        )

        # Check if merge strategies make sense for the
        # configured property merge strategies
        for event_type_name, event_type in self.__event_types.iteritems():
            for property_name, event_property in event_type.iteritems():
                if event_property.get_merge_strategy() in ('min', 'max'):
                    if not event_property.get_data_type().is_numerical():
                        if not event_property.get_data_type().is_datetime():
                            raise EDXMLValidationError(
                                'Property "%s" of event type "%s" has data type %s, which '
                                'cannot be used with merge strategy %s.'
                                % (property_name, event_type_name, event_property.get_data_type(),
                                   event_property.get_merge_strategy())
                            )

        # Check if unique properties have their merge strategies set
        # to 'match'
        # TODO: Still needed for EDXML 3?
        for event_type_name, event_type in self.__event_types.iteritems():
            for property_name, event_property in event_type.iteritems():
                if event_property.is_unique():
                    if event_property.get_merge_strategy() != 'match':
                        raise EDXMLValidationError(
                            'Unique property "%s" of event type "%s" does not have its merge strategy set to "match".' %
                            (property_name, event_type_name)
                        )
                else:
                    if event_property.get_merge_strategy() == 'match':
                        raise EDXMLValidationError(
                            'Property "%s" of event type "%s" is not unique but it does '
                            'have its merge strategy set to "match".' %
                            (property_name, event_type_name)
                        )

        # Verify that non-unique event type only have
        # properties with merge strategy 'drop'.
        for event_type_name, event_type in self.__event_types.iteritems():
            if not event_type.is_unique():
                for property_name, event_property in event_type.iteritems():
                    if event_property.get_merge_strategy() != 'drop':
                        raise EDXMLValidationError(
                            'Event type "%s" is not unique, but property "%s" has merge strategy %s.' %
                            (event_type_name, property_name,
                             event_property.get_merge_strategy())
                        )

        # Validate event parent definitions
        for event_type_name, event_type in self.__event_types.items():
            if event_type.get_parent() is None:
                continue

            # Check if all unique parent properties are present
            # in the property map
            parent_event_type = self.get_event_type(event_type.get_parent().get_event_type())
            for parent_property_name, parent_property in parent_event_type.iteritems():
                if parent_property.is_unique():
                    if parent_property_name not in event_type.get_parent().get_property_map().values():
                        raise EDXMLValidationError(
                            'Event type %s contains a parent definition which lacks '
                            'a mapping for unique parent property \'%s\'.' %
                            (event_type_name, parent_property_name)
                        )

            for childProperty, parent_property in event_type.get_parent().get_property_map().items():

                # Check if child property exists
                if childProperty not in event_type.keys():
                    raise EDXMLValidationError(
                        'Event type %s contains a parent definition which refers to unknown child property \'%s\'.' %
                        (event_type_name, childProperty)
                    )

                # Check if parent property exists and if it is a unique property
                parent_event_type = self.get_event_type(event_type.get_parent().get_event_type())
                if parent_property not in parent_event_type.keys() or \
                   parent_event_type[parent_property].get_merge_strategy() != 'match':
                    raise EDXMLValidationError(
                        ('Event type %s contains a parent definition which refers '
                         'to parent property "%s" of event type %s, '
                         'but this property is not unique, or it does not exist.') %
                        (event_type_name, parent_property,
                            event_type.get_parent().get_event_type())
                    )

                # Check if child property has allowed merge strategy
                if event_type[childProperty].get_merge_strategy() not in ('match', 'drop'):
                    raise EDXMLValidationError(
                        ('Event type %s contains a parent definition which refers to child property \'%s\'. '
                         'This property has merge strategy %s, which is not allowed for properties that are used in '
                         'parent definitions.') %
                        (event_type_name, childProperty,
                            event_type[childProperty].get_merge_strategy())
                    )

                # Check if child property is single valued
                if event_type[childProperty].is_multi_valued():
                    raise EDXMLValidationError(
                        ('Event type %s contains a parent definition which refers to child property \'%s\'. '
                         'This property is multi-valued, which is not allowed for properties that are used in '
                         'parent definitions.') %
                        (event_type_name, childProperty,
                         event_type[childProperty].get_merge_strategy())
                    )

        # Verify that inter / intra relations are defined between
        # properties that refer to concepts, in the right way
        for event_type_name, event_type in self.__event_types.items():
            for relation in event_type.get_property_relations().values():
                if relation.get_type() in ('inter', 'intra'):
                    source_concepts = event_type[relation.get_source(
                    )].get_concept_associations()
                    target_concepts = event_type[relation.get_target(
                    )].get_concept_associations()

                    if len(source_concepts) == 0 or len(target_concepts) == 0:
                        raise EDXMLValidationError(
                            ('Both properties %s and %s in the inter/intra-concept relation in event type %s must '
                             'refer to a concept.') %
                            (relation.get_source(),
                             relation.get_target(), event_type_name)
                        )

                    for source_concept_name in source_concepts:
                        for target_concept_name in target_concepts:
                            if relation.get_type() == 'intra':
                                source_primitive = relation.get_source_concept().split('.', 2)[0]
                                target_primitive = relation.get_target_concept().split('.', 2)[0]
                                if source_primitive != target_primitive:
                                    raise EDXMLValidationError(
                                        ('Properties %s and %s in the intra-concept relation in event type %s must '
                                         'both refer to the same primitive concept.') %
                                        (relation.get_source(),
                                         relation.get_target(), event_type_name)
                                    )

        return self

    @classmethod
    def create_from_xml(cls, ontology_element):
        """

        Args:
          ontology_element (lxml.etree.Element):

        Returns:
          edxml.ontology.Ontology: The ontology
        """

        ontology = cls()

        for element in ontology_element:
            if element.tag == '{http://edxml.org/edxml}eventtypes':
                ontology.__parse_event_types(element)
            elif element.tag == '{http://edxml.org/edxml}objecttypes':
                ontology.__parse_object_types(element)
            elif element.tag == '{http://edxml.org/edxml}concepts':
                ontology.__parse_concepts(element)
            elif element.tag == '{http://edxml.org/edxml}sources':
                ontology.__parse_sources(element)
            else:
                raise TypeError('Unexpected element: "%s"' % element.tag)

        return ontology

    def __cmp__(self, other):

        if not isinstance(other, type(self)):
            raise TypeError("Cannot compare different types of ontology elements.")

        self.validate()
        other.validate()

        # EDXML ontologies do not have versions, only their sub-elements do. An ontology is always a valid upgrade
        # when all of its sub-elements are. So, comparing the object types, concepts, event types and sources
        # contained in both ontologies should be sufficient to determine if the ontology upgrade is valid. However,
        # in theory an ontology could contain a mix of sub-element upgrades and downgrades. When updating an
        # ontology, we only perform upgrades. Downgrades are ignored as long as these are valid downgrades.
        # Long story short: When two ontologies differ and the ontology elements they contain are
        # either valid upgrades or downgrades of one another, the two ontologies are considered valud upgrades
        # of each other. This method will only return 0 or 1 as a result.

        equal = True

        equal &= set(self.get_concept_names()) == set(other.get_concept_names())
        equal &= set(self.get_object_type_names()) == set(other.get_object_type_names())
        equal &= set(self.get_event_source_uris()) == set(other.get_event_source_uris())
        equal &= set(self.get_event_type_names()) == set(other.get_event_type_names())

        for object_type_name, object_type in self.get_object_types().items():
            if object_type_name not in other.get_object_type_names():
                # Other ontology does not have this object type,
                # which is no problem for upgrading / downgrading.
                equal = False
                continue

            equal &= other.get_object_types()[object_type_name] == object_type

        for concept_name, concept in self.get_concepts().items():
            if concept_name not in other.get_concept_names():
                # Other ontology does not have this concept,
                # which is no problem for upgrading / downgrading.
                equal = False
                continue

            equal &= other.get_concepts()[concept_name] == concept

        for event_type_name, event_type in self.get_event_types().items():
            if event_type_name not in other.get_event_type_names():
                # Other ontology does not have this event type,
                # which is no problem for upgrading / downgrading.
                equal = False
                continue

            equal &= other.get_event_types()[event_type_name] == event_type

        for source_uri, source in self.get_event_sources().items():
            if source_uri not in other.get_event_source_uris():
                # Other ontology does not have this event source,
                # which is no problem for upgrading / downgrading.
                equal = False
                continue

            equal &= other.get_event_sources()[source_uri] == source

        if equal:
            return 0

        return 1

    def update(self, other_ontology, validate=True):
        """

        Updates the ontology using the definitions contained
        in another ontology. The other ontology may be specified
        in the form of an Ontology instance or an lxml Element
        containing a full ontology element.

        Args:
          other_ontology (Union[lxml.etree.Element,edxml.ontology.Ontology]):
          validate (bool): Validate the resulting ontology

        Raises:
          EDXMLValidationError

        Returns:
          edxml.ontology.Ontology: The ontology
        """

        if isinstance(other_ontology, Ontology):
            if validate:
                other_ontology.validate()
            for ObjectTypeName, objectType in other_ontology.get_object_types().items():
                self._add_object_type(objectType)
            for EventTypeName, eventType in other_ontology.get_event_types().items():
                self._add_event_type(eventType)
            for ConceptName, concept in other_ontology.get_concepts().items():
                self._add_concept(concept)
            for uri, source in other_ontology.get_event_sources().items():
                self._add_event_source(source)

        elif isinstance(other_ontology, etree._Element):
            for element in other_ontology:
                if element.tag == '{http://edxml.org/edxml}objecttypes':
                    self.__parse_object_types(element, validate)
                elif element.tag == '{http://edxml.org/edxml}concepts':
                    self.__parse_concepts(element, validate)
                elif element.tag == '{http://edxml.org/edxml}eventtypes':
                    self.__parse_event_types(element, validate)
                elif element.tag == '{http://edxml.org/edxml}sources':
                    self.__parse_sources(element, validate)
                else:
                    raise EDXMLValidationError(
                        'Unexpected ontology element: "%s"' % element.tag)

            if validate:
                self.validate()
        else:
            raise TypeError('Cannot update ontology from %s',
                            str(type(other_ontology)))

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <ontology> tag for this ontology.

        Returns:
          etree.Element: The element

        """
        ontology_element = etree.Element('ontology')
        object_types = etree.SubElement(ontology_element, 'objecttypes')
        concepts = etree.SubElement(ontology_element, 'concepts')
        event_types = etree.SubElement(ontology_element, 'eventtypes')
        event_sources = etree.SubElement(ontology_element, 'sources')

        for objectTypeName, objectType in self.__object_types.iteritems():
            object_types.append(objectType.generate_xml())

        for conceptName, concept in self.__concepts.iteritems():
            concepts.append(concept.generate_xml())

        for eventTypeName, eventType in self.__event_types.iteritems():
            event_types.append(eventType.generate_xml())

        for uri, source in self.__sources.iteritems():
            event_sources.append(source.generate_xml())

        return ontology_element
