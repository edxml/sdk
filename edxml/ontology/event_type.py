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

import base64
import binascii
from decimal import Decimal
from typing import Dict

import re

from io import BytesIO
from collections import defaultdict
from collections.abc import MutableMapping
from lxml import etree
from lxml.builder import ElementMaker

import edxml.template
import edxml.ontology

from .ontology_element import VersionedOntologyElement, ontology_element_upgrade_error
from .event_property import EventProperty
from .event_type_parent import EventTypeParent
from .event_property_relation import PropertyRelation
from .event_type_attachment import EventTypeAttachment
from .util import normalize_xml_token
from edxml.error import EDXMLOntologyValidationError, EDXMLEventValidationError, EDXMLMergeConflictError


def _check_sub_element_upgrade(old, new, equal, is_valid_upgrade):
    """

    Checks if the given event type instances are mutually valid upgrades.
    Returns updated values for two flags which track equality and upgrade validity.

    Args:
        old (EventType): Old event type
        new (EventType): New event type
        equal (bool): Instances are equal yes / no
        is_valid_upgrade (bool): Instances are valid upgrades yes / no

    Returns:
        Tuple[bool, bool]:

    """
    if old.get_parent() is None and new.get_parent() is not None:
        # New version adds a parent.
        equal = False

    if new.get_parent() is None and old.get_parent() is not None:
        # New version is missing the parent definition that
        # the old one has. No upgrade possible.
        equal = is_valid_upgrade = False

    if old.get_parent() is not None and new.get_parent() is not None:
        if old.get_parent() != new.get_parent():
            # Parent definitions differ, check that new definition is
            # a valid upgrade of the old definition.
            equal = False
            is_valid_upgrade &= new.get_parent() > old.get_parent()

    if old.get_properties().keys() != new.get_properties().keys():
        # Adding a property is possible, removing one is not.
        equal = False
        missing_property_names = set(old.get_properties().keys()) - set(new.get_properties().keys())
        new_property_names = set(new.get_properties().keys()) - set(old.get_properties().keys())
        is_valid_upgrade &= len(missing_property_names) == 0

        for property_name in new_property_names:
            # Newly added properties must be optional.
            is_valid_upgrade &= new.get_properties()[property_name].is_optional()
            # A timeless event type must remain timeless.
            if old.is_timeless():
                is_valid_upgrade &= new.is_timeless()

    for property_name in new.get_properties().keys():
        if property_name in old:
            if old[property_name] != new[property_name]:
                # Property definitions differ, check that new definition is
                # a valid upgrade of the old definition.
                equal = False
                is_valid_upgrade &= new[property_name] > old[property_name]

    if old.get_property_relations().keys() != new.get_property_relations().keys():
        # Adding a relation is possible, removing one is not.
        equal = False
        missing_relation_ids = set(old.get_property_relations().keys()) - set(new.get_property_relations().keys())
        is_valid_upgrade &= len(missing_relation_ids) == 0

    for relation_id, relation in new.get_property_relations().items():
        if relation_id in old.get_property_relations():
            if new.get_property_relations()[relation_id] != old.get_property_relations()[relation_id]:
                # Relation definitions differ, check that new definition is
                # a valid upgrade of the old definition.
                equal = False
                is_valid_upgrade &= \
                    new.get_property_relations()[relation_id] > old.get_property_relations()[relation_id]

    if set(old.get_attachments().keys()) - set(new.get_attachments().keys()) != set():
        # New version removes attachments. No upgrade possible.
        equal = is_valid_upgrade = False

    for name, attachment in new.get_attachments().items():
        if name in old.get_attachments():
            if new.get_attachments()[name] != old.get_attachments()[name]:
                # Attachment definitions differ, check that new definition is
                # a valid upgrade of the old definition.
                equal = False
                is_valid_upgrade &= new.get_attachments()[name] > old.get_attachments()[name]

    return equal, is_valid_upgrade


class EventType(VersionedOntologyElement, MutableMapping):
    """
    Class representing an EDXML event type. The class provides
    access to event properties by means of a dictionary interface.
    For each of the properties there is a key matching the name of
    the event property, the value is the property itself.
    """

    NAME_PATTERN = re.compile("^[a-z0-9.-]*$")
    CLASS_LIST_PATTERN = re.compile("^[a-z0-9, ]*$")

    def __init__(self, ontology, name, display_name_singular=None, display_name_plural=None, description=None,
                 summary='no description available', story='no description available', parent=None):

        display_name_singular = display_name_singular or name.replace('.', ' ')
        display_name_plural = display_name_plural or display_name_singular + 's'

        self.__attr = {
            'name': name,
            'display-name-singular': display_name_singular,
            'display-name-plural': display_name_plural,
            'description': description or name,
            'summary': summary,
            'story': story,
            'timespan-start': None,
            'timespan-end': None,
            'event-version': None,
            'sequence': None,
            'version': 1
        }

        self.__properties = {}      # type: Dict[str, EventProperty]
        self.__relations = {}       # type: Dict[str, PropertyRelation]
        self.__parent = parent      # type: EventTypeParent
        self.__attachments = {}     # type: Dict[str, EventTypeAttachment]
        self.__relax_ng = None      # type: etree.RelaxNG
        self.__ontology = ontology  # type: edxml.ontology.Ontology

        self.__parent_description = None  # type: str

        self.__cached_is_timeless = None
        self.__cached_hash_properties = None

    def __delitem__(self, property_name):
        if property_name in self.__properties:
            del self.__properties[property_name]
            self._child_modified_callback()

    def __setitem__(self, property_name, property_instance):
        if isinstance(property_instance, EventProperty):
            self.__properties[property_name] = property_instance
            self._child_modified_callback()
        else:
            raise TypeError('Not an event property: %s' %
                            repr(property_instance))

    def __len__(self):
        return len(self.__properties)

    def __getitem__(self, property_name):
        """

        Args:
          property_name (str): Name of an event property

        Returns:
          EventProperty:
        """
        try:
            return self.__properties[property_name]
        except KeyError:
            raise Exception('Event type %s has no property named %s.' %
                            (self.__attr['name'], property_name))

    def __contains__(self, property_name):
        try:
            self.__properties[property_name]
        except (KeyError, IndexError):
            return False
        else:
            return True

    def __iter__(self):
        """

        Yields:
          Dict[str, EventProperty]
        """
        for propertyName, prop in self.__properties.items():
            yield propertyName

    def __repr__(self):
        return f"{self.__attr['name']} ({self.__attr['display-name-singular']})"

    def __str__(self):
        return self.__attr['name']

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self.__cached_is_timeless = None
        self.__cached_hash_properties = None
        self.__ontology._child_modified_callback()
        return self

    def _set_attr(self, key, value):
        if self.__attr[key] != value:
            self.__attr[key] = value
            self._child_modified_callback()

    @property
    def relations(self):
        """

        Returns:
            Iterable[PropertyRelation]
        """
        return self.__relations.values()

    def get_name(self):
        """

        Returns the event type name

        Returns:
          str:
        """
        return self.__attr['name']

    def get_description(self):
        """

        Returns the event type description

        Returns:
          str:
        """
        return self.__attr['description']

    def get_display_name_singular(self):
        """

        Returns the event type display name, in singular form.

        Returns:
          str:
        """
        return self.__attr['display-name-singular']

    def get_display_name_plural(self):
        """

        Returns the event type display name, in plural form.

        Returns:
          Optional[str]:
        """
        return self.__attr['display-name-plural']

    def get_timespan_property_name_start(self):
        """

        Returns the name of the property that defines the start
        of the time span of the events. Returns None when the start
        of the event time span is the smallest of the event timestamps.

        Returns:
            Optional[str]:
        """
        return self.__attr['timespan-start']

    def get_timespan_property_name_end(self):
        """

        Returns the name of the property that defines the end
        of the time span of the events. Returns None when the end
        of the event time span is the largest of the event timestamps.

        Returns:
            str:
        """
        return self.__attr['timespan-end']

    def get_version_property_name(self):
        """

        Returns the name of the property that defines the version of
        the events that is used to merge colliding events. Returns
        None when the event type does not define an event version.

        Returns:
            Optional[str]:
        """
        return self.__attr['event-version']

    def get_sequence_property_name(self):
        """

        Returns the name of the property that defines the sequence
        numbers of the events. Returns None when the event type does
        not define a sequence number.

        Returns:
            Optional[str]:
        """
        return self.__attr['sequence']

    def get_properties(self):
        """

        Returns a dictionary containing all properties
        of the event type. The keys in the dictionary
        are the property names, the values are the
        EDXMLProperty instances.

        Returns:
           Dict[str,EventProperty]: Properties
        """
        return self.__properties

    def get_hashed_properties(self):
        """

        Returns a dictionary containing all properties
        of the event type that are used to compute event
        hashes. The keys in the dictionary are the property
        names, the values are the EDXMLProperty instances.

        Returns:
           Dict[str, EventProperty]: Properties
        """
        if self.__cached_hash_properties is None:
            self.__cached_hash_properties = {name: prop for name, prop in self.__properties.items() if prop.is_hashed()}

        return self.__cached_hash_properties

    def get_property_relations(self, relation_type=None, source=None, target=None):
        """

        Returns a dictionary containing the property relations that
        are defined in the event type. The keys are relation IDs that
        should be considered opaque.

        Optionally, the relations can be filtered on type, source and  target.

        Args:
            relation_type (str): Relation type
            source (str): Name of source property
            target (str): Name of target property

        Returns:
          Dict[str,PropertyRelation]:
        """
        relations = self.__relations
        if relation_type is not None:
            relations = {k: r for k, r in relations.items() if r.get_type() == relation_type}
        if source is not None:
            relations = {k: r for k, r in relations.items() if r.get_source() == source}
        if target is not None:
            relations = {k: r for k, r in relations.items() if r.get_target() == target}
        return relations

    def get_attachment(self, name):
        """

        Returns the specified attachment definition.

        Raises:
            KeyError

        Returns:
          EventTypeAttachment:
        """
        return self.__attachments[name]

    def get_attachments(self):
        """

        Returns a dictionary containing the attachments that
        are defined for the event type. The keys are attachment IDs.

        Returns:
          Dict[str,EventTypeAttachment]:
        """
        return self.__attachments

    def get_timespan_property_names(self):
        """
        Returns a tuple containing the names of the properties that
        determine the start and end of the event time spans, in that order.
        Note that either may be None.

        Returns:
            Tuple[Optional[str], Optional[str]]

        """
        return self.__attr['timespan-start'], self.__attr['timespan-end']

    def is_timeless(self):
        """

        Returns True when the event type is timeless, which
        means that it has no properties that are associated with
        the datetime data type. Returns False otherwise.

        Returns:
            bool:
        """
        if self.__cached_is_timeless is None:
            self.__cached_is_timeless = True
            for property_name, event_property in self.__properties.items():
                if event_property.get_data_type().is_datetime():
                    self.__cached_is_timeless = False

        return self.__cached_is_timeless

    def is_timeful(self):
        """

        Returns True when the event type is timeful, which
        means that it has at least one property that is
        associated with the datetime data type. Returns
        False otherwise.

        Returns:
            bool:
        """
        return not self.is_timeless()

    def get_summary_template(self):
        """

        Returns the event summary template.

        Returns:
          str:
        """
        return self.__attr['summary']

    def get_story_template(self):
        """

        Returns the event story template.

        Returns:
          str:
        """
        return self.__attr['story']

    def get_parent(self):
        """

        Returns the parent event type, or None
        if no parent has been defined.

        Returns:
          EventTypeParent: The parent event type
        """
        return self.__parent

    def get_version(self):
        """

        Returns the version of the source definition.

        Returns:
          int:
        """

        return self.__attr['version']

    def create_property(self, name, object_type_name, description=None):
        """

        Create a new event property.

        Note:
           The description should be really short, indicating
           which role the object has in the event type.

        Args:
          name (str): Property name
          object_type_name (str): Name of the object type
          description (str): Property description

        Returns:
          EventProperty: The EventProperty instance
        """
        if name not in self.__properties:
            object_type = self.__ontology.get_object_type(object_type_name)
            if not object_type:
                # Object type is not defined, try to load it from
                # any registered ontology bricks
                self.__ontology._import_object_type_from_brick(object_type_name)
                object_type = self.__ontology.get_object_type(object_type_name)
            if object_type:
                self.__properties[name] = EventProperty(self, name, object_type, description).validate()
            else:
                raise Exception(
                    'Attempt to create property "%s" of event type "%s" referring to undefined object type "%s".' %
                    (name, self.get_name(), object_type_name)
                )
        else:
            raise Exception(
                'Attempt to create existing property "%s" of event type "%s".' %
                (name, self.get_name())
            )

        self._child_modified_callback()
        return self.__properties[name]

    def add_property(self, prop):
        """

        Add specified property

        Args:
          prop (EventProperty): EventProperty instance

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        self.__properties[prop.get_name()] = prop.validate()
        self._child_modified_callback()
        return self

    def remove_property(self, property_name):
        """

        Removes specified property from the event type.

        Notes:
          Since the EventType class has a dictionary interface
          for accessing event type properties, you can also use
          the del operator to delete a property.

        Args:
          property_name (str): The name of the property

        Returns:
          edxml.ontology.EventType: The EventType instance

        """
        if property_name in self.__properties:
            del self.__properties[property_name]
            self._child_modified_callback()

        return self

    def _select_relation_concepts(self, relation_type, source, target, source_concept_name, target_concept_name):
        for property_name, concept_name in ((source, source_concept_name), (target, target_concept_name)):
            if concept_name is None:
                if len(self[property_name].get_concept_associations()) == 0:
                    raise ValueError(
                        "Attempt to create an %s-concept relation between the %s and %s properties of a %s while "
                        "property %s is not associated with any concepts." %
                        (relation_type, source, target, self.get_display_name_singular(), property_name)
                    )

                if len(self[property_name].get_concept_associations()) > 1:
                    raise ValueError(
                        "Attempt to create an %s-concept relation between the %s and %s of a %s while "
                        "property %s is associated with multiple concepts. Creation failed because "
                        "it was not specified  which concept to relate to." %
                        (relation_type, source, target, self.get_display_name_singular(), property_name)
                    )

        # If any of the two concepts are unspecified, pick the first one. We can safely
        # do that because we just verified that there is just one associated concept.
        if source_concept_name is None:
            source_concept_name = next(iter(self[source].get_concept_associations().keys()))
        if target_concept_name is None:
            target_concept_name = next(iter(self[target].get_concept_associations().keys()))

        source_concept = self.__ontology.get_concept(source_concept_name)
        target_concept = self.__ontology.get_concept(target_concept_name)

        for concept in (source_concept, target_concept):
            if concept is None:
                raise EDXMLOntologyValidationError(
                    "Attempt to create an %s-concept relation between the %s and %s properties of a %s while "
                    "one of the associated concepts (%s) is not defined." %
                    (relation_type, source, target, self.get_display_name_singular(), source_concept_name)
                )

        return source_concept, target_concept

    def create_relation(self, relation_type, source, target, description=None, predicate=None, source_concept_name=None,
                        target_concept_name=None, confidence=None):
        """

        Create a new property relation

        Args:
          relation_type (str): Relation relation_type ('inter', 'intra', ...)
          source (str): Name of source property
          target (str): Name of target property
          description (Optional[str]): Relation description, with property placeholders
          predicate (Optional[str]): free form predicate
          source_concept_name (Optional[str]): Name of the source concept
          target_concept_name (Optional[str]): Name of the target concept
          confidence (Optional[float]): Relation confidence [0.0,1.0]

        Returns:
          PropertyRelation: The PropertyRelation instance
        """

        if source not in self:
            raise KeyError('Cannot find property %s in event relation_type %s.' % (source, self.__attr['name']))

        if target not in self:
            raise KeyError('Cannot find property %s in event relation_type %s.' % (target, self.__attr['name']))

        if relation_type in ('inter', 'intra'):
            source_concept, target_concept = self._select_relation_concepts(
                relation_type, source, target, source_concept_name, target_concept_name
            )
        else:
            source_concept = None
            target_concept = None

        relation = PropertyRelation(
            self, self[source], self[target],
            source_concept, target_concept,
            description, relation_type, predicate, confidence
        )

        self.__relations[relation.get_persistent_id()] = relation.validate()

        self._child_modified_callback()
        return relation

    def add_relation(self, relation):
        """

        Add specified property relation. It is recommended to use the methods
        from the EventProperty class in stead, to create property relations using
        a syntax that yields more readable code.

        Args:
          relation (PropertyRelation): Property relation

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        self.__relations[relation.get_persistent_id()] = relation.validate()

        self._child_modified_callback()
        return self

    def create_attachment(self, name):
        """

        Create a new attachment and add it to the event type. The description
        and singular display name are set to the attachment name. The plural
        form of the display name is constructed by appending an 's' to the
        singular form.

        Args:
            name (str): attachment name

        Returns:
            EventTypeAttachment
        """
        attachment = EventTypeAttachment(self, name)
        self.add_attachment(attachment)

        return attachment

    def add_attachment(self, attachment):
        """

        Add specified attachment definition to the event type.

        Args:
            attachment (EventTypeAttachment): attachment definition

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        self.__attachments[attachment.get_name()] = attachment

        self._child_modified_callback()
        return self

    def make_child(self, siblings_description, parent):
        """

        Marks this event type as child of the specified parent event type. In
        case all hashed properties of the parent also exist in the child, a
        default property mapping will be generated, mapping properties based
        on identical property names.

        Notes:
          You must call is_parent() on the parent before calling make_children()

        Args:
          siblings_description (str): EDXML siblings-description attribute
          parent (edxml.ontology.EventType): Parent event type

        Returns:
          EventTypeParent: The event type parent definition
        """

        if self.__parent_description:
            self.__parent = EventTypeParent(self, parent.get_name(), '', self.__parent_description,
                                            siblings_description)
        else:
            raise Exception('You must call is_parent() on the parent before calling make_child().')

        # If all hashed properties of the parent event type
        # also exist in the child event type, we can create
        # a default property map.
        property_map = {}
        for property_name, event_property in parent.get_hashed_properties().items():
            if property_name in self:
                property_map[property_name] = property_name
            else:
                property_map = {}
                break

        for child_property, parent_property in property_map.items():
            self.__parent.map(child_property, parent_property)

        self._child_modified_callback()
        return self.__parent

    def make_parent(self, parent_description, child):
        """

        Marks this event type as parent of the specified child event type.

        Notes:
          To be used in conjunction with the make_children() method.

        Args:
          parent_description (str): EDXML parent-description attribute
          child (edxml.ontology.EventType): Child event type

        Returns:
          edxml.ontology.EventType: The EventType instance

        """

        child.__parent_description = parent_description
        child._child_modified_callback()
        return self

    def set_description(self, description):
        """

        Sets the event type description

        Args:
          description (str): Description

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        self._set_attr('description', str(description))
        return self

    def set_parent(self, parent):
        """

        Set the parent event type

        Notes:
          It is recommended to use the make_children() and
          is_parent() methods in stead whenever possible,
          which results in more readable code.

        Args:
          parent (EventTypeParent): Parent event type

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        self.__parent = parent

        self._child_modified_callback()
        return self

    def set_name(self, event_type_name):
        """

        Sets the name of the event type.

        Args:
         event_type_name (str): Event type name

        Returns:
          edxml.ontology.EventType: The EventType instance
        """
        self._set_attr('name', event_type_name)
        return self

    def set_display_name(self, singular, plural=None):
        """

        Configure the display name. If the plural form
        is omitted, it will be auto-generated by
        appending an 's' to the singular form.

        Args:
          singular (str): Singular display name
          plural (str): Plural display name

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        self._set_attr('display-name-singular', singular)
        self._set_attr('display-name-plural', plural or (singular + 's'))
        return self

    def set_summary_template(self, summary):
        """

        Set the event summary template

        Args:
          summary (str): The event summary template

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        self._set_attr('summary', summary)
        return self

    def set_story_template(self, story):
        """

        Set the event story template.

        Args:
          story (str): The event story template

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        self._set_attr('story', story)
        return self

    def set_version(self, version):
        """

        Sets the concept version

        Args:
          version (int): Version

        Returns:
          edxml.ontology.Concept: The Concept instance
        """

        self._set_attr('version', int(version))
        return self

    def set_timespan_property_name_start(self, property_name):
        """

        Sets the name of the property that defines the start of
        the time spans of the events.

        Args:
            property_name (str):

        Returns:
          edxml.ontology.EventType: The EventType instance

        """
        self._set_attr('timespan-start', property_name)
        return self

    def set_timespan_property_name_end(self, property_name):
        """

        Sets the name of the property that defines the end of
        the time spans of the events.

        Args:
            property_name (str):

        Returns:
          edxml.ontology.EventType: The EventType instance

        """
        self._set_attr('timespan-end', property_name)
        return self

    def set_version_property_name(self, property_name):
        """

        Sets the name of the property that defines the versions
        of the events that is used to merge colliding events.

        Args:
            property_name (str):

        Returns:
          edxml.ontology.EventType: The EventType instance

        """
        self._set_attr('event-version', property_name)
        return self

    def set_sequence_property_name(self, property_name):
        """

        Sets the name of the property that defines the sequence
        numbers of the events.

        Args:
            property_name (str):

        Returns:
          edxml.ontology.EventType: The EventType instance

        """
        self._set_attr('sequence', property_name)
        return self

    def evaluate_template(self, edxml_event, which='story', capitalize=True, colorize=False):
        """

        Evaluates the event story or summary template of an event type using
        specified event, returning the result.

        By default, the story template is evaluated, unless which is
        set to 'summary'.

        By default, we will try to capitalize the first letter of the resulting
        string, unless capitalize is set to False.

        Optionally, the output can be colorized. At his time this means that,
        when printed on the terminal, the objects in the evaluated string will
        be displayed using bold white characters.

        Args:
          edxml_event (edxml.EDXMLEvent): the EDXML event to use
          which (bool): which template to evaluate
          capitalize (bool): Capitalize output or not
          colorize (bool): Colorize output or not

        Returns:
          str:
        """
        return edxml.Template(self.__attr[which]).evaluate(
            self, edxml_event.get_properties(), edxml_event.get_attachments(), capitalize, colorize
        )

    def _validate_event_versioning(self):
        if self.__attr['event-version'] is None:
            # Nothing to do.
            return
        if not self.__attr['event-version'] in self.get_properties().keys():
            raise EDXMLOntologyValidationError(
                'Event type "%s" defines the event version '
                'by means of property "%s", which does not exist.' %
                (self.__attr['name'], self.__attr['event-version'])
            )
        if self.get_properties()[self.__attr['event-version']].get_data_type().get_family() != 'sequence':
            raise EDXMLOntologyValidationError(
                'Event type "%s" defines the event version '
                'by means of property "%s", which does not have the sequence data type.' %
                (self.__attr['name'], self.__attr['event-version'])
            )
        if self.get_properties()[self.__attr['event-version']].get_merge_strategy() != 'max':
            raise EDXMLOntologyValidationError(
                'Event type "%s" defines the event version '
                'by means of property "%s", which does not have the "max" merge strategy.' %
                (self.__attr['name'], self.__attr['event-version'])
            )
        if self.get_properties()[self.__attr['event-version']].is_optional():
            raise EDXMLOntologyValidationError(
                'Event type "%s" defines the event version '
                'by means of property "%s", which is optional. Version properties must not be optional.' %
                (self.__attr['name'], self.__attr['event-version'])
            )
        if self.get_properties()[self.__attr['event-version']].is_multi_valued():
            raise EDXMLOntologyValidationError(
                'Event type "%s" defines the event version '
                'by means of property "%s", which is multi-valued. Version properties must not be multi-valued.' %
                (self.__attr['name'], self.__attr['event-version'])
            )

    def _validate_event_sequencing(self):
        if self.__attr['sequence'] is None:
            # Nothing to do.
            return
        if not self.__attr['sequence'] in self.get_properties().keys():
            raise EDXMLOntologyValidationError(
                'Event type "%s" defines the event sequence numbers '
                'by means of property "%s", which does not exist.' %
                (self.__attr['name'], self.__attr['sequence'])
            )
        if self.get_properties()[self.__attr['sequence']].get_data_type().get_family() != 'sequence':
            raise EDXMLOntologyValidationError(
                'Event type "%s" defines the event sequence numbers '
                'by means of property "%s", which does not have the sequence data type.' %
                (self.__attr['name'], self.__attr['sequence'])
            )
        if self.get_properties()[self.__attr['sequence']].is_optional():
            raise EDXMLOntologyValidationError(
                'Event type "%s" defines the event sequence numbers '
                'by means of property "%s", which is optional. Sequences must not be optional.' %
                (self.__attr['name'], self.__attr['sequence'])
            )
        if self.get_properties()[self.__attr['sequence']].is_multi_valued():
            raise EDXMLOntologyValidationError(
                'Event type "%s" defines the event sequence numbers '
                'by means of property "%s", which is multi-valued. Sequences must not be multi-valued.' %
                (self.__attr['name'], self.__attr['sequence'])
            )

    def validate(self):
        """

        Checks if the event type definition is valid. Since it does
        not have access to the full ontology, the context of
        the event type is not considered. For example, it does not
        check if the event type definition refers to a parent event
        type that actually exists. Also, templates are not validated.

        Raises:
          EDXMLOntologyValidationError
        Returns:
          EventType: The EventType instance

        """

        attribute_lengths = {'name': 64, 'display-name-singular': 32, 'display-name-plural': 32, 'description': 128}

        for attribute_name, max_length in attribute_lengths.items():
            if len(self.__attr[attribute_name]) > max_length:
                raise EDXMLOntologyValidationError(
                    'The %s attribute of event type "%s" is too long.' % attribute_name
                )

        if not re.match(self.NAME_PATTERN, self.__attr['name']):
            raise EDXMLOntologyValidationError(
                'Event type "%s" has an invalid name.' % self.__attr['name'])

        token_attributes = (
            'summary', 'display-name-singular', 'display-name-plural', 'description'
        )

        for token_attribute in token_attributes:
            if normalize_xml_token(self.__attr[token_attribute]) != self.__attr[token_attribute]:
                raise EDXMLOntologyValidationError(
                    'The %s attribute of event type "%s" contains illegal whitespace characters: "%s"' %
                    (token_attribute, self.__attr['name'], self.__attr[token_attribute])
                )

        for attribute_name in ('timespan-start', 'timespan-end'):
            if self.__attr[attribute_name] is not None:
                if not self.__attr[attribute_name] in self.get_properties().keys():
                    raise EDXMLOntologyValidationError(
                        'Event type "%s" defines its event time spans '
                        'by means of property "%s", which does not exist.' %
                        (self.__attr['name'], self.__attr[attribute_name])
                    )
                if not self.get_properties()[self.__attr[attribute_name]].get_data_type().is_datetime():
                    raise EDXMLOntologyValidationError(
                        'Event type "%s" defines its event time spans '
                        'by means of property "%s", which does not have a datetime data type.' %
                        (self.__attr['name'], self.__attr[attribute_name])
                    )

        self._validate_event_versioning()
        self._validate_event_sequencing()

        if [p for p in self.get_properties().values() if p.get_merge_strategy() == 'replace']:
            if self.get_version_property_name() is None:
                raise EDXMLOntologyValidationError(
                    'Event type "%s" defines one or more properties with merge strategy "replace" '
                    'but it does not have a property containing event versions.' % self.__attr['name']
                )

        for attribute_name in ('summary', 'story'):
            try:
                edxml.Template(self.__attr[attribute_name]).validate(self)
            except EDXMLOntologyValidationError as e:
                raise EDXMLOntologyValidationError(
                    'The %s template of event type "%s" is invalid: "%s"\nThe validator said: %s' %
                    (attribute_name, self.__attr['name'], self.__attr['summary'], str(e))
                )

        try:
            for property_name, event_property in self.get_properties().items():
                event_property.validate()

            for relation in self.__relations.values():
                relation.validate()

            for attachment in self.__attachments.values():
                attachment.validate()
        except EDXMLOntologyValidationError as exception:
            exception.args = ('Event type "%s" is invalid: %s' % (self.__attr['name'], str(exception)),)
            raise

        return self

    @classmethod
    def create_from_xml(cls, type_element, ontology):
        try:
            event_type = cls(
                ontology,
                type_element.attrib['name'],
                type_element.attrib['display-name-singular'],
                type_element.attrib['display-name-plural'],
                type_element.attrib['description'],
                type_element.attrib['summary'],
                type_element.attrib['story']
            ).set_version(type_element.attrib['version'])\
             .set_timespan_property_name_start(type_element.attrib.get('timespan-start'))\
             .set_timespan_property_name_end(type_element.attrib.get('timespan-end'))\
             .set_version_property_name(type_element.attrib.get('event-version'))\
             .set_sequence_property_name(type_element.attrib.get('sequence'))
        except KeyError as e:
            raise EDXMLOntologyValidationError(
                "Failed to instantiate an event type from the following definition:\n" +
                etree.tostring(type_element, pretty_print=True, encoding='unicode') +
                "\nMissing attribute: " + str(e)
            )

        property_names = []
        relation_ids = []
        attachments = []
        for element in type_element:
            if element.tag == '{http://edxml.org/edxml}parent':
                event_type.set_parent(EventTypeParent.create_from_xml(element, event_type))
            elif element.tag == '{http://edxml.org/edxml}properties':
                for property_element in element:
                    prop = EventProperty.create_from_xml(property_element, ontology, event_type)
                    if prop.get_name() in property_names:
                        raise EDXMLOntologyValidationError(
                            'EDXML <properties> element contains duplicate definition of "%s"' % prop.get_name()
                        )
                    event_type.add_property(prop)
                    property_names.append(prop.get_name())

            elif element.tag == '{http://edxml.org/edxml}relations':
                for relation_element in element:
                    relation = PropertyRelation.create_from_xml(relation_element, event_type, ontology)
                    if relation.get_persistent_id() in relation_ids:
                        raise EDXMLOntologyValidationError(
                            'EDXML <relations> element contains duplicate definition '
                            'of a "%s" relation between "%s" and "%s".' % (
                                relation.get_type(),
                                event_type.get_properties()[relation.get_source()].get_name(),
                                event_type.get_properties()[relation.get_target()].get_name(),
                            )
                        )
                    event_type.add_relation(relation)
                    relation_ids.append(relation.get_persistent_id())

            elif element.tag == '{http://edxml.org/edxml}attachments':
                for attachment_element in element:
                    attachment = EventTypeAttachment.create_from_xml(attachment_element, event_type)
                    if attachment.get_name() in attachments:
                        raise EDXMLOntologyValidationError(
                            'EDXML <attachments> element contains duplicate definition of "%s"' % attachment.get_name()
                        )
                    event_type.add_attachment(attachment)
                    attachments.append(attachment.get_name())

        return event_type

    def __cmp__(self, other):

        if not isinstance(other, type(self)):
            raise TypeError("Cannot compare different types of ontology elements.")

        other_is_newer = other.get_version() > self.get_version()
        versions_differ = other.get_version() != self.get_version()

        if other_is_newer:
            new = other
            old = self
        else:
            new = self
            old = other

        old.validate()
        new.validate()

        equal = not versions_differ
        is_valid_upgrade = True

        if old.get_name() != new.get_name():
            raise ValueError("Event types with different names are not comparable.")

        # Compare attributes that cannot produce illegal upgrades because they can
        # be changed freely between versions. We only need to know if they changed.

        for attr in ['display-name-singular', 'display-name-plural', 'description', 'summary', 'story']:
            equal &= old.__attr[attr] == new.__attr[attr]

        # Check for illegal upgrade paths:

        if new.get_version_property_name() != old.get_version_property_name():
            # The version properties differ, no upgrade possible.
            equal = is_valid_upgrade = False

        if new.get_sequence_property_name() != old.get_sequence_property_name():
            # The sequence properties differ, no upgrade possible.
            equal = is_valid_upgrade = False

        if old.get_timespan_property_name_start() != new.get_timespan_property_name_start():
            # Versions do not agree on their timespan definitions. No upgrade possible.
            equal = is_valid_upgrade = False

        if old.get_timespan_property_name_end() != new.get_timespan_property_name_end():
            # Versions do not agree on their timespan definitions. No upgrade possible.
            equal = is_valid_upgrade = False

        # Check upgrade paths for sub-elements:
        equal, is_valid_upgrade = _check_sub_element_upgrade(old, new, equal, is_valid_upgrade)

        if equal:
            return 0

        if is_valid_upgrade and versions_differ:
            return -1 if other_is_newer else 1

        ontology_element_upgrade_error('event type', old, new)

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def _update_sub_elements(self, event_type):
        if event_type.get_parent() is not None:
            if self.get_parent() is not None:
                self.get_parent().update(event_type.get_parent())
            else:
                self.set_parent(event_type.get_parent())

        for property_name in self.get_properties().keys():
            self[property_name].update(event_type[property_name])

        for property_name in set(event_type.get_properties().keys()) - set(self.get_properties().keys()):
            self.add_property(event_type.get_properties()[property_name])

        for relation_id in self.get_property_relations().keys():
            self.get_property_relations()[relation_id].update(event_type.get_property_relations()[relation_id])

        for relation_id in set(event_type.get_property_relations().keys()) - set(self.get_property_relations().keys()):
            self.add_relation(event_type.get_property_relations()[relation_id])

        for attachment_name, attachment in event_type.get_attachments().items():
            if attachment_name in self.get_attachments().keys():
                self.get_attachments()[attachment_name].update(event_type.get_attachments()[attachment_name])
            else:
                self.add_attachment(attachment)

    def update(self, event_type):
        """

        Updates the event type to match the EventType
        instance passed to this method, returning the
        updated instance.

        Args:
          event_type (edxml.ontology.EventType): The new EventType instance

        Returns:
          edxml.ontology.EventType: The updated EventType instance

        """
        if not isinstance(event_type, type(self)):
            raise TypeError("Can only update using an ontology element of the same type.")

        if event_type > self:
            # The new definition is indeed newer. Update self.
            self._update_sub_elements(event_type)

            self.set_description(event_type.get_description())
            self.set_display_name(event_type.get_display_name_singular(), event_type.get_display_name_plural())
            self.set_summary_template(event_type.get_summary_template())
            self.set_story_template(event_type.get_story_template())
            self.set_version(event_type.get_version())

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <event-type> tag for this event type.

        Returns:
          etree.Element: The element

        """
        attribs = dict(self.__attr)
        attribs['version'] = str(attribs['version'])

        element = etree.Element('event-type', {k: v for k, v in attribs.items() if v})
        if self.__parent:
            element.append(self.__parent.generate_xml())

        properties = etree.Element('properties')
        for property_name in sorted(self.__properties.keys()):
            properties.append(self.__properties[property_name].generate_xml())
        element.append(properties)

        if len(self.__relations) > 0:
            relations = etree.Element('relations')
            for relation_id in sorted(self.__relations.keys()):
                relations.append(self.__relations[relation_id].generate_xml())
            element.append(relations)

        if len(self.__attachments) > 0:
            attachments = etree.Element('attachments')
            for attachment_name in sorted(self.__attachments.keys()):
                attachments.append(self.__attachments[attachment_name].generate_xml())
            element.append(attachments)

        return element

    def get_singular_property_names(self):
        """

        Returns a list of properties that cannot have multiple values.

        Returns:
           list(str): List of property names
        """
        return [property_name for property_name, prop in self.__properties.items() if prop.is_single_valued()]

    def get_mandatory_property_names(self):
        """

        Returns a list of properties that must have a value

        Returns:
           list(str): List of property names
        """
        return [property_name for property_name, prop in self.__properties.items() if prop.is_mandatory()]

    def validate_event_structure(self, edxml_event):
        """

        Validates the structure of the event by comparing its
        properties and their object count to the requirements
        of the event type. Generates exceptions that are much
        more readable than standard XML validation exceptions.

        Args:
          edxml_event (edxml.EDXMLEvent):

        Raises:
          EDXMLEventValidationError

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        for property_name, objects in edxml_event.items():
            if property_name not in self.get_properties():
                raise EDXMLEventValidationError(
                    ('An event of type %s contains an object of property %s, '
                     'but this property does not belong to the event type.') %
                    (self.__attr['name'], property_name)
                )

        # Verify that match, min and max properties have an object.
        for property_name in self.get_mandatory_property_names():
            if property_name not in edxml_event:
                raise EDXMLEventValidationError(
                    'An event of type %s is missing an object for mandatory property %s.'
                    % (self.__attr['name'], property_name)
                )

        # Verify that properties that cannot have multiple
        # objects actually have at most one object
        for property_name in self.get_singular_property_names():
            if property_name in edxml_event:
                if len(edxml_event[property_name]) > 1:
                    raise EDXMLEventValidationError(
                        ('An event of type %s has multiple objects of property %s, '
                         'while it is a single-valued property.') %
                        (self.__attr['name'], property_name)
                    )

        return self

    def validate_event_objects(self, event, property_name=None):
        """

        Validates the object values in the event by comparing
        the values with their data types. Generates exceptions
        that are much more readable than standard XML validation
        exceptions.

        Optionally the validation can be limited to a specific
        property only by setting the property_name argument.

        Args:
          event (edxml.EDXMLEvent):
          property_name (str):

        Raises:
          EDXMLEventValidationError

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        for event_property_name, objects in event.items():
            if property_name is not None and event_property_name != property_name:
                # We are not asked to check this property.
                continue

            try:
                property_object_type = self.__properties[event_property_name].get_object_type()
            except KeyError:
                raise EDXMLEventValidationError(
                    'Event type %s has no property named "%s".' % (self.__attr['name'], event_property_name)
                )

            for object_value in objects:
                try:
                    property_object_type.validate_object_value(object_value)
                except EDXMLEventValidationError as e:
                    raise EDXMLEventValidationError(
                        'Invalid value for property %s of event type %s: %s' % (
                            event_property_name, self.__attr['name'], e)
                    )

        return self

    def validate_event_attachments(self, event):
        for attachment_name, attachment_values in event.get_attachments().items():
            if attachment_name not in self.__attachments.keys():
                raise EDXMLEventValidationError(
                    f"An event of type {self.__attr['name']} has an attachment named '{attachment_name}' "
                    f"while this event type has no such attachment."
                )
            for attachment_id, attachment_value in attachment_values.items():
                if attachment_value == '':
                    raise EDXMLEventValidationError(
                        f"An event of type {self.__attr['name']} has an attachment named '{attachment_name}' "
                        f"which is empty."
                    )

                attachment = self.__attachments[attachment_name]
                if attachment.is_base64_string():
                    try:
                        base64.decodebytes(attachment_value.encode())
                    except binascii.Error as e:
                        raise EDXMLEventValidationError(
                            f"An event of type {self.__attr['name']} has a base64 encoded attachment "
                            f"named '{attachment_name}' which is not a valid base64 string: '{e}'.\n\n"
                            f"Attachment value is:\n\n{attachment_value}"
                        )

    def normalize_event_objects(self, event, property_names):
        """

        Normalizes the object values in the event, resulting in
        valid EDXML object value strings. Raises an exception
        in case an object value cannot be normalized.

        Args:
          event (edxml.EDXMLEvent):
          property_names (List[str]):

        Raises:
          EDXMLEventValidationError

        Returns:
          edxml.ontology.EventType: The EventType instance
        """

        for property_name, objects in event.items():
            if property_name not in property_names:
                # This is not a property that we are supposed to normalize.
                continue

            try:
                property_object_type = self.__properties[property_name].get_object_type()
            except KeyError:
                raise EDXMLEventValidationError(
                    "Event type '%s' has no property '%s'." % (self.get_name(), property_name)
                )

            try:
                event[property_name] = property_object_type.get_data_type(
                ).normalize_objects(objects)
            except EDXMLEventValidationError as e:
                raise EDXMLEventValidationError(
                    'Invalid value for property %s of event type %s: %s' % (
                        property_name, self.__attr['name'], e)
                )

        return self

    def generate_relax_ng(self, ontology, namespaced=True):
        """

        Returns an ElementTree containing a RelaxNG schema for validating
        events of this event type. It requires an Ontology instance for
        obtaining the definitions of objects types referred to by the
        properties of the event type.

        By default, the schema expects the events to be namespaced. This can
        be turned off for validating events that will be added into an EDXML
        data stream that has a default namespace that events will inherit.

        Args:
          ontology (Ontology): Ontology containing the event type
          namespaced (bool): Require a namespace specification or not

        Returns:
          lxml.etree.RelaxNG: The schema
        """
        namespace = {'ns': 'http://edxml.org/edxml'} if namespaced else {}

        e = ElementMaker()

        # Define a recursive 'anything' pattern
        anything = e.zeroOrMore(
            e.choice(
                e.element(
                    e.anyName(),
                    e.ref(name='anything')
                ),
                e.attribute(
                    e.anyName()
                )
            )
        )

        # Use the 'anything' pattern to define a pattern
        # that allows any element attributes as long as they
        # have a namespace that is not the EDXML namespace.
        # We will use that pattern in the event definition.
        foreign_attribs = e.zeroOrMore(
            e.attribute(
                e.anyName(
                    getattr(e, 'except')(
                        e.nsName(ns=''),
                        e.nsName(ns='http://edxml.org/edxml')
                    )
                )
            )
        )

        properties = []

        for property_name, event_property in self.__properties.items():
            object_type = ontology.get_object_type(event_property.get_object_type_name())
            if property_name in self.get_mandatory_property_names():
                if property_name in self.get_singular_property_names():
                    # Exactly one object must be present, no need
                    # to wrap it into an element to indicate this.
                    properties.append(
                        e.element(object_type.generate_relaxng(), name=property_name))
                else:
                    # Property is mandatory and can have any
                    # number of objects.
                    properties.append(e.oneOrMore(
                        e.element(object_type.generate_relaxng(), name=property_name)))
            else:
                if property_name in self.get_singular_property_names():
                    # Property is not mandatory, but if present there
                    # cannot be multiple values.
                    properties.append(e.optional(
                        e.element(object_type.generate_relaxng(), name=property_name)))
                else:
                    # Property is not mandatory and can have any
                    # number of objects.
                    properties.append(e.zeroOrMore(
                        e.element(object_type.generate_relaxng(), name=property_name)))

        attachments = []
        for attachment_name, attachment in self.get_attachments().items():
            if attachment.is_base64_string():
                attachments.append(
                    e.zeroOrMore(
                        e.element(
                            e.attribute(
                                e.data(
                                    e.param('1', name='minLength'),
                                    e.param('40', name='maxLength'),
                                    type='string'
                                ),
                                name='id'
                            ),
                            e.data(
                                e.param('4', name='minLength'),
                                type='base64Binary'
                            ),
                            name=attachment_name
                        )
                    )
                )
            else:
                attachments.append(
                    e.zeroOrMore(
                        e.element(
                            e.attribute(
                                e.data(
                                    e.param('1', name='minLength'),
                                    e.param('40', name='maxLength'),
                                    type='string'
                                ),
                                name='id'
                            ),
                            e.data(
                                e.param('1', name='minLength'),
                                type='string'
                            ), name=attachment_name)
                    )
                )

        schema = e.element(
            e.ref(name='foreign-attributes'),
            e.attribute(
                e.data(
                    e.param('1', name='minLength'),
                    e.param('64', name='maxLength'),
                    e.param('[a-z0-9.-]*', name='pattern'),
                    type='token'
                ),
                name='event-type'
            ),
            e.attribute(
                e.data(
                    e.param('1', name='minLength'),
                    e.param('(/[a-z0-9-]+)*/', name='pattern'),
                    type='token'
                ),
                name='source-uri'
            ),
            e.optional(
                e.attribute(
                    e.data(
                        e.param(
                            '([0-9a-f]{40})(,[0-9a-f]{40})*', name='pattern'),
                        type='normalizedString'),
                    name='parents'
                )
            ),
            e.element(
                e.interleave(*properties),
                name='properties'
            ) if len(properties) > 0 else e.element(e.empty, name='properties'),
            e.optional(
                e.element(
                    e.interleave(*attachments),
                    name='attachments'
                ) if len(attachments) > 0 else e.element(e.empty, name='attachments'),
            ),
            name='event',
            **namespace
        )

        schema = e.grammar(
            e.start(
                schema
            ),
            e.define(
                anything,
                name='anything'
            ),
            e.define(
                foreign_attribs,
                name='foreign-attributes'
            ),
            xmlns='http://relaxng.org/ns/structure/1.0',
            datatypeLibrary='http://www.w3.org/2001/XMLSchema-datatypes',
        )

        # Note that, for some reason, using a programmatically built ElementTree
        # to instantiate a RelaxNG object fails with 'schema is empty'. If we
        # convert the schema to a string and parse it back gain, all is good.
        return etree.parse(BytesIO(etree.tostring(etree.ElementTree(schema))))

    def merge_events(self, events):
        """

        Merges the specified events and returns the merged event.
        The merged event is an instance of the same class as the
        first input event.

        Args:
          events (List[edxml.EDXMLEvent]): List of events

        Returns:
          edxml.EDXMLEvent: Merged event
        """

        # Below is a mapping from EDXML data types to Python types
        # used for comparing object values.
        types = {
            'datetime': str,  # Datetime objects can be ordered lexicographically.
            'sequence': int,
            'number:tinyint': int,
            'number:smallint': int,
            'number:mediumint': int,
            'number:int': int,
            'number:bigint': int,
            'number:float': float,
            'number:double': float,
            'number:decimal': Decimal
        }

        event_properties = defaultdict(list)
        parents = set()

        # First we make sure that the events are ordered correctly
        # in case event order is relevant.
        version_property = self.get_version_property_name()
        if version_property is not None:
            # Event type has a version property, which means we need
            # to check for merge conflicts.
            events = sorted(events, key=lambda e: int(e.get_any(version_property)))
            self._check_merge_conflict(events, version_property)

        # For each property we accumulate all values from all events.
        for event in events:
            parents.update(event.get_parent_hashes())
            for property_name, values in event.items():
                event_properties[property_name].extend(values)

        output_properties = {}
        for property_name, objects in event_properties.items():
            strategy = self.__properties[property_name].get_merge_strategy()
            data_type = ':'.join(self.__properties[property_name].get_data_type().get_split()[0:2])
            if strategy == 'min':
                output_properties[property_name] = [min(event_properties[property_name], key=types[data_type])]
            elif strategy == 'max':
                output_properties[property_name] = [max(event_properties[property_name], key=types[data_type])]
            elif strategy == 'add':
                output_properties[property_name] = set(event_properties[property_name])
            elif strategy == 'replace':
                # Take the value of the last event
                output_properties[property_name] = events[-1][property_name]
            elif strategy == 'set':
                # Take the first non-empty value, if available
                output_properties[property_name] = next(
                    (e[property_name] for e in events if e[property_name] != set()), set()
                )
            else:
                # Merge strategy 'any', should not matter which
                # value to pick, we pick the first one.
                output_properties[property_name] = event_properties[property_name][0]

        return events[0].copy().set_properties(output_properties).set_parents(parents)

    def _check_merge_conflict(self, events, version_property):
        # Compile all events that share a particular version, these
        # are the events that can potentially conflict.
        events_by_version = defaultdict(list)
        for event in events:
            events_by_version[event.get_any(version_property)].append(event)

        # Now check the event sets that share a single version.
        for version, version_events in events_by_version.items():
            # For each property of all events that share the same
            # version we accumulate all value sets from all events.
            property_object_sets = defaultdict(set)
            for event in version_events:
                for property_name in self.__properties.keys():
                    property_object_sets[property_name].add(tuple(sorted(event[property_name])))
            # Now we check for each property if the object sets of all
            # events that share a version are mutually consistent.
            for property_name, object_sets in property_object_sets.items():
                strategy = self.__properties[property_name].get_merge_strategy()
                if strategy in [EventProperty.MERGE_MATCH, EventProperty.MERGE_ANY]:
                    # No conflict possible because the object values are either identical (match)
                    # or any differences are insignificant (drop)
                    continue
                if len(object_sets) > 1:
                    # There is more than one unique set of object values
                    # for this property.
                    raise EDXMLMergeConflictError(version_events)
