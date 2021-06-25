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

import re

import edxml.ontology

from lxml import etree
from edxml.error import EDXMLOntologyValidationError
from edxml.ontology import OntologyElement, normalize_xml_token
from edxml.ontology.ontology_element import event_type_element_upgrade_error


class EventTypeParent(OntologyElement):
    """
    Class representing an EDXML event type parent
    """

    PROPERTY_MAP_PATTERN = re.compile(
        "^[a-z0-9-]{1,64}:[a-z0-9-]{1,64}(,[a-z0-9-]{1,64}:[a-z0-9-]{1,64})*$")

    def __init__(self, child_event_type, parent_event_type_name, property_map, parent_description='belonging to',
                 siblings_description='sharing'):

        self._attr = {
            'event-type': parent_event_type_name,
            'property-map': property_map,
            'parent-description': parent_description,
            'siblings-description': siblings_description
        }

        self._child_event_type = child_event_type

    def __repr__(self):
        return f"({self._child_event_type.get_name()} has parent {self._attr['event-type']})"

    def __str__(self):
        return f"{self._child_event_type.get_name()}=>{self._attr['event-type']}"

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self._child_event_type._child_modified_callback()
        return self

    def _set_attr(self, key, value):
        if self._attr[key] != value:
            self._attr[key] = value
            self._child_modified_callback()

    @classmethod
    def create(cls, child_event_type, parent_event_type_name, property_map, parent_description='belonging to',
               siblings_description='sharing'):
        """

        Creates a new event type parent. The PropertyMap argument is a dictionary
        mapping property names of the child event type to property names of the
        parent event type.

        Note:
           All hashed properties of the parent event type must appear in
           the property map.

        Note:
           The parent event type must be defined in the same EDXML stream
           as the child.

        Args:
          child_event_type (EventType): The child event type
          parent_event_type_name (str): Name of the parent event type
          property_map (Dict[str, str]): Property map
          parent_description (Optional[str]): The EDXML parent-description attribute
          siblings_description (Optional[str]): The EDXML siblings-description attribute

        Returns:
          edxml.ontology.EventTypeParent: The EventTypeParent instance
        """
        return cls(
            child_event_type,
            parent_event_type_name,
            ','.join(['%s:%s' % (child, parent) for child, parent in property_map.items()]),
            parent_description,
            siblings_description
        )

    def set_parent_description(self, description):
        """
        Sets the EDXML parent-description attribute

        Args:
          description (str): The EDXML parent-description attribute

        Returns:
          edxml.ontology.EventTypeParent: The EventTypeParent instance
        """
        self._set_attr('parent-description', description)

        return self

    def set_siblings_description(self, description):
        """

        Sets the EDXML siblings-description attribute

        Args:
          description (str): The EDXML siblings-description attribute

        Returns:
          edxml.ontology.EventTypeParent: The EventTypeParent instance
        """
        self._set_attr('siblings-description', description)

        return self

    def map(self, child_property_name, parent_property_name=None):
        """

        Add a property mapping, mapping a property in the child
        event type to the corresponding property in the parent.
        When the parent property name is omitted, it is assumed
        that the parent and child properties are named identically.

        Args:
          child_property_name (str):  Child property
          parent_property_name (str): Parent property

        Returns:
          edxml.ontology.EventTypeParent: The EventTypeParent instance
        """
        parent_property_name = child_property_name if parent_property_name is None else parent_property_name

        try:
            current = dict(mapping.split(':')
                           for mapping in self._attr['property-map'].split(','))
        except ValueError:
            current = {}

        current[child_property_name] = parent_property_name
        self._set_attr('property-map', ','.join(
            ['%s:%s' % (child, parent) for child, parent in current.items()]))
        return self

    def get_event_type_name(self):
        """

        Returns the name of the parent event type.

        Returns:
          str:
        """
        return self._attr['event-type']

    def get_property_map(self):
        """

        Returns the property map as a dictionary mapping
        property names of the child event type to property
        names of the parent.

        Returns:
          Dict[str,str]:
        """
        return dict(mapping.split(':') for mapping in self._attr['property-map'].split(','))

    def get_parent_description(self):
        """

        Returns the EDXML 'parent-description' attribute.

        Returns:
          str:
        """
        return self._attr['parent-description']

    def get_siblings_description(self):
        """

        Returns the EDXML 'siblings-description' attribute.

        Returns:
          str:
        """
        return self._attr['siblings-description']

    def validate(self):
        """

        Checks if the event type parent is valid. It only looks
        at the attributes of the definition itself. Since it does
        not have access to the full ontology, the context of
        the parent is not considered. For example, it does not
        check if the parent definition refers to an event type that
        actually exists.

        Raises:
          EDXMLOntologyValidationError
        Returns:
          edxml.ontology.EventTypeParent: The EventTypeParent instance

        """
        if not len(self._attr['event-type']) <= 64:
            raise EDXMLOntologyValidationError(
                'An implicit parent definition refers to a parent event type using an invalid event type name: "%s"' %
                self._attr['event-type']
            )
        if not re.match(edxml.ontology.EventType.NAME_PATTERN, self._attr['event-type']):
            raise EDXMLOntologyValidationError(
                'An implicit parent definition refers to a parent event type using an invalid event type name: "%s"' %
                self._attr['event-type']
            )

        if not re.match(self.PROPERTY_MAP_PATTERN, self._attr['property-map']):
            raise EDXMLOntologyValidationError(
                'An implicit parent definition contains an invalid property map: "%s"' % self._attr['property-map']
            )

        if not 1 <= len(self._attr['parent-description']) <= 128:
            raise EDXMLOntologyValidationError(
                'An implicit parent definition contains an parent-description '
                'attribute that is either empty or too long: "%s"'
                % self._attr['parent-description']
            )

        if normalize_xml_token(self._attr['parent-description']) != self._attr['parent-description']:
            raise EDXMLOntologyValidationError(
                'The parent-description attribute in the implicit parent definition of event type "%s" '
                'contains illegal whitespace characters: "%s"' % (
                    self._child_event_type.get_name(), self._attr['parent-description'])
            )

        if not 1 <= len(self._attr['siblings-description']) <= 128:
            raise EDXMLOntologyValidationError(
                'An implicit parent definition contains an siblings-description '
                'attribute that is either empty or too long: "%s"'
                % self._attr['siblings-description']
            )

        if normalize_xml_token(self._attr['siblings-description']) != self._attr['siblings-description']:
            raise EDXMLOntologyValidationError(
                'The siblings-description attribute in the implicit parent definition of event type "%s" '
                'contains illegal whitespace characters: "%s"' % (
                    self._child_event_type.get_name(), self._attr['siblings-description'])
            )

        return self

    @classmethod
    def create_from_xml(cls, parent_element, child_event_type):
        try:
            return cls(
                child_event_type,
                parent_element.attrib['event-type'],
                parent_element.attrib['property-map'],
                parent_element.attrib['parent-description'],
                parent_element.attrib['siblings-description']
            )
        except KeyError as e:
            raise EDXMLOntologyValidationError(
                "Failed to instantiate an event type parent from the following definition:\n" +
                etree.tostring(parent_element, pretty_print=True, encoding='unicode') +
                "\nMissing attribute: " + str(e)
            )

    def __cmp__(self, other):

        if not isinstance(other, type(self)):
            raise TypeError("Cannot compare different types of ontology elements.")

        # Note that parent definitions are part of event type definitions,
        # so we look at the version of the event type for which this property is defined.
        other_is_newer = other._child_event_type.get_version() > self._child_event_type.get_version()
        versions_differ = other._child_event_type.get_version() != self._child_event_type.get_version()

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

        if old._child_event_type.get_name() != new._child_event_type.get_name():
            raise EDXMLOntologyValidationError(
                "Attempt to compare event type parent definitions from two different child event types"
            )

        # Check for illegal upgrade paths:

        if old.get_event_type_name() != new.get_event_type_name():
            # The parent event types are different, no upgrade possible.
            equal = is_valid_upgrade = False

        if old.get_property_map() != new.get_property_map():
            # The property maps are different, no upgrade possible.
            equal = is_valid_upgrade = False

        # Compare attributes that cannot produce illegal upgrades because they can
        # be changed freely between versions. We only need to know if they changed.

        for attr in ['parent-description', 'siblings-description']:
            equal &= old._attr[attr] == new._attr[attr]

        if equal:
            return 0

        if is_valid_upgrade and versions_differ:
            return -1 if other_is_newer else 1

        event_type_element_upgrade_error(
            'child/parent association', old, new, old._child_event_type, new._child_event_type
        )

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def update(self, parent):
        """

        Updates the event type parent to match the EventTypeParent
        instance passed to this method, returning the
        updated instance.

        Args:
          parent (edxml.ontology.EventTypeParent): The new EventTypeParent instance

        Returns:
          edxml.ontology.EventTypeParent: The updated EventTypeParent instance

        """
        if parent > self:
            # The new definition is indeed newer. Update self.
            self.set_parent_description(parent.get_parent_description())
            self.set_siblings_description(parent.get_siblings_description())
            self._child_event_type = parent._child_event_type

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <parent> tag for this event type parent.

        Returns:
          etree.Element: The element

        """

        return etree.Element('parent', self._attr)
