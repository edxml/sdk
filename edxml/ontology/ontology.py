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

from typing import Dict

from lxml import etree
from edxml.error import EDXMLOntologyValidationError
from .object_type import ObjectType
from .concept import Concept
from .event_type import EventType
from .event_source import EventSource
from .ontology_element import OntologyElement


class Ontology(OntologyElement):
    """
    Class representing an EDXML ontology
    """

    __bricks = {
        'object_types': None,
        'concepts': None
    }  # type: Dict[str, Ontology]

    def __init__(self):
        self.__version = 0
        self.__event_types = {}    # type: Dict[str, EventType]
        self.__object_types = {}   # type: Dict[str, ObjectType]
        self.__sources = {}        # type: Dict[str, EventSource]
        self.__concepts = {}       # type: Dict[str, Concept]

    def __repr__(self):
        return f"{len(self.__event_types)} event types, {len(self.__object_types)} object types, " \
               f"{len(self.__sources)} sources and {len(self.__concepts)} concepts"

    def __str__(self):
        return 'ontology'

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
            cls.__bricks['object_types'] = Ontology()
        if not cls.__bricks['concepts']:
            cls.__bricks['concepts'] = Ontology()

        ontology = Ontology()
        object_type_names = []
        for object_type in brick.generate_object_types(ontology):
            object_type_names.append(object_type.get_name())

        for object_type_name in object_type_names:
            if object_type_name in cls.__bricks['object_types'].get_object_types():
                existing_object_type = cls.__bricks['object_types'].get_object_type(object_type_name)
                if ontology.get_object_type(object_type_name) != existing_object_type:
                    raise Exception(
                        f"Ontology brick {brick.__name__} contains an object type named '{object_type_name}'. "
                        f"This object type has already been defined by another registered brick and that definition "
                        f"is not identical."
                    )
            else:
                cls.__bricks['object_types']._add_object_type(ontology.get_object_type(object_type_name))

        ontology = Ontology()
        concept_names = []
        for concept in brick.generate_concepts(ontology):
            concept_names.append(concept.get_name())

        for concept_name in concept_names:
            if concept_name in cls.__bricks['concepts'].get_concepts():
                existing_concept = cls.__bricks['concepts'].get_concept(concept_name)
                if ontology.get_concept(concept_name) != existing_concept:
                    raise Exception(
                        f"Ontology brick {brick.__name__} contains a concept named '{concept_name}'. "
                        f"This concept has already been defined by another registered brick and that definition "
                        f"is not identical."
                    )
            else:
                cls.__bricks['concepts']._add_concept(ontology.get_concept(concept_name))

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
                           data_type='string:0:mc:u'):
        """

        Creates and returns a new ObjectType instance. When no display
        names are specified, display names will be created from the
        object type name. If only a singular form is specified, the
        plural form will be auto-generated by appending an 's'.

        The object type is not validated on creation. This allows for creating
        a crude initial definition using this method and finish the definition
        later. If you do intend to create a valid definition from the start,
        it is recommended to validate it immediately.

        Args:
          name (str): object type name
          display_name_singular (str): display name (singular form)
          display_name_plural (str): display name (plural form)
          description (str): short description of the object type
          data_type (str): a valid EDXML data type

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """

        if name in self.__object_types:
            raise ValueError(f"Object type {name} already exists.")

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

        Args:
          name (str): concept name
          display_name_singular (str): display name (singular form)
          display_name_plural (str): display name (plural form)
          description (str): short description of the concept

        Returns:
          edxml.ontology.Concept: The Concept instance
        """

        if name in self.__concepts:
            raise ValueError(f"Concept {name} already exists.")

        self._add_concept(
            Concept(self, name, display_name_singular, display_name_plural, description),
            validate=False
        )

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

        Args:
          name (str): Event type name
          display_name_singular (str): Display name (singular form)
          display_name_plural (str): Display name (plural form)
          description (str): Event type description

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        if name in self.__event_types:
            raise ValueError(f"Event type {name} already exists.")

        self._add_event_type(
            EventType(self, name, display_name_singular, display_name_plural, description),
            validate=False
        )

        return self.__event_types[name]

    def create_event_source(self, uri, description='no description available', acquisition_date=None):
        """

        Creates a new event source definition.

        The source is not validated on creation. This allows for creating
        a crude initial definition using this method and finish the definition
        later. If you do intend to create a valid definition from the start,
        it is recommended to validate it immediately.

        If the URI is missing a leading and / or trailing slash, these will be
        appended automatically.

        Args:
         uri (str): The source URI
         description (str): Description of the source
         acquisition_date (Optional[str]): Acquisition date in format yyyymmdd

        Returns:
          edxml.ontology.EventSource:
        """

        if uri in self.__sources:
            raise ValueError(f"Event source {uri} already exists.")

        self._add_event_source(
            EventSource(self, uri, description, acquisition_date),
            validate=False
        )

        return self.__sources[uri]

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
        event_type_names = []
        for type_element in event_types_element:
            event_type = EventType.create_from_xml(type_element, self)
            self._add_event_type(event_type, validate)
            event_type_names.append(event_type.get_name())

    def __parse_object_types(self, object_types_element, validate=True):
        object_type_names = []
        for type_element in object_types_element:
            object_type = ObjectType.create_from_xml(type_element, self)
            self._add_object_type(object_type, validate)
            object_type_names.append(object_type.get_name())

    def __parse_concepts(self, concepts_element, validate=True):
        concept_names = []
        for concept_element in concepts_element:
            concept = Concept.create_from_xml(concept_element, self)
            self._add_concept(concept, validate)
            concept_names.append(concept.get_name())

    def __parse_sources(self, sources_element, validate=True):
        source_uris = []
        for source_element in sources_element:
            source = EventSource.create_from_xml(source_element, self)
            self._add_event_source(source, validate)
            source_uris.append(source.get_uri())

    def validate(self):
        """

        Checks if the defined ontology is a valid EDXML ontology.

        Raises:
          EDXMLOntologyValidationError

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
            if event_type.get_parent() is not None:
                if event_type.get_parent().get_event_type_name() not in self.__event_types:
                    raise EDXMLOntologyValidationError(
                        'Event type "%s" refers to parent event type "%s", which is not defined.' %
                        (event_type_name, event_type.get_parent().get_event_type_name()))

        # Check if the object type of each property exists
        for event_type_name, event_type in self.__event_types.items():
            for property_name, event_property in event_type.get_properties().items():
                object_type_name = event_property.get_object_type_name()
                if self.get_object_type(object_type_name) is None:
                    # Object type is not defined, try to load it from
                    # any registered ontology bricks
                    self._import_object_type_from_brick(object_type_name)
                if self.get_object_type(object_type_name) is None:
                    raise EDXMLOntologyValidationError(
                        'Property "%s" of event type "%s" refers to undefined object type "%s".' %
                        (property_name, event_type_name,
                         event_property.get_object_type_name())
                    )

        # Check if the concepts referred to by each property exists
        for event_type_name, event_type in self.__event_types.items():
            for property_name, event_property in event_type.get_properties().items():
                for concept_name in event_property.get_concept_associations().keys():
                    if self.get_concept(concept_name) is None:
                        # Concept is not defined, try to load it from
                        # any registered ontology bricks
                        self._import_concept_from_brick(concept_name)
                    if self.get_concept(concept_name) is None:
                        raise EDXMLOntologyValidationError(
                            'Property "%s" of event type "%s" refers to undefined concept "%s".' %
                            (property_name, event_type_name, concept_name)
                        )

        # Validate event parent definitions
        for event_type_name, event_type in self.__event_types.items():
            if event_type.get_parent() is None:
                continue

            # Check if all unique parent properties are present
            # in the property map
            parent_event_type = self.get_event_type(event_type.get_parent().get_event_type_name())
            for parent_property_name, parent_property in parent_event_type.get_properties().items():
                if parent_property.is_hashed():
                    if parent_property_name not in event_type.get_parent().get_property_map().values():
                        raise EDXMLOntologyValidationError(
                            'Event type %s contains a parent definition which lacks '
                            'a mapping for unique parent property \'%s\'.' %
                            (event_type_name, parent_property_name)
                        )

            for child_property, parent_property in event_type.get_parent().get_property_map().items():

                # Check if child property exists
                if child_property not in event_type.get_properties().keys():
                    raise EDXMLOntologyValidationError(
                        'Event type %s contains a parent definition which refers to unknown child property \'%s\'.' %
                        (event_type_name, child_property)
                    )

                # Check if parent property exists and if it is a hashed property
                parent_event_type = self.get_event_type(event_type.get_parent().get_event_type_name())
                if parent_property not in parent_event_type.get_properties() or \
                   parent_event_type[parent_property].get_merge_strategy() != 'match':
                    raise EDXMLOntologyValidationError(
                        'Event type %s contains a parent definition which refers '
                        'to parent property "%s" of event type %s, '
                        'but this property is either not a hashed property or it does not exist.' %
                        (event_type_name, parent_property, event_type.get_parent().get_event_type_name())
                    )

                # Check if child property has allowed merge strategy
                if event_type[child_property].get_merge_strategy() not in ('match', 'any'):
                    raise EDXMLOntologyValidationError(
                        'Event type %s contains a parent definition which refers to child property \'%s\'. '
                        'This property has merge strategy %s, which is not allowed for properties that are used in '
                        'parent definitions.' %
                        (event_type_name, child_property, event_type[child_property].get_merge_strategy())
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
            if element.tag == '{http://edxml.org/edxml}event-types':
                ontology.__parse_event_types(element)
            elif element.tag == '{http://edxml.org/edxml}object-types':
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

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

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
          EDXMLOntologyValidationError

        Returns:
          edxml.ontology.Ontology: The ontology
        """
        if isinstance(other_ontology, Ontology):
            if validate:
                other_ontology.validate()
            for object_type in other_ontology.get_object_types().values():
                self._add_object_type(object_type)
            for event_type in other_ontology.get_event_types().values():
                self._add_event_type(event_type)
            for concept in other_ontology.get_concepts().values():
                self._add_concept(concept)
            for source in other_ontology.get_event_sources().values():
                self._add_event_source(source)

        elif isinstance(other_ontology, etree._Element):
            for element in other_ontology:
                if element.tag == '{http://edxml.org/edxml}object-types':
                    self.__parse_object_types(element, validate)
                elif element.tag == '{http://edxml.org/edxml}concepts':
                    self.__parse_concepts(element, validate)
                elif element.tag == '{http://edxml.org/edxml}event-types':
                    self.__parse_event_types(element, validate)
                elif element.tag == '{http://edxml.org/edxml}sources':
                    self.__parse_sources(element, validate)
                else:
                    raise EDXMLOntologyValidationError('Unexpected ontology element: "%s"' % element.tag)

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
        object_types = etree.SubElement(ontology_element, 'object-types')
        concepts = etree.SubElement(ontology_element, 'concepts')
        event_types = etree.SubElement(ontology_element, 'event-types')
        event_sources = etree.SubElement(ontology_element, 'sources')

        for object_type_name in sorted(self.__object_types.keys()):
            object_types.append(self.__object_types[object_type_name].generate_xml())

        for concept_name in sorted(self.__concepts.keys()):
            concepts.append(self.__concepts[concept_name].generate_xml())

        for event_type_name in sorted(self.__event_types.keys()):
            event_types.append(self.__event_types[event_type_name].generate_xml())

        for uri in sorted(self.__sources.keys()):
            event_sources.append(self.__sources[uri].generate_xml())

        return ontology_element
