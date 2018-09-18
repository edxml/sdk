# -*- coding: utf-8 -*-

import re
import edxml

from lxml import etree
from edxml.EDXMLBase import EDXMLValidationError
from edxml.ontology import OntologyElement


class EventTypeParent(OntologyElement):
    """
    Class representing an EDXML event type parent
    """

    PROPERTY_MAP_PATTERN = re.compile(
        "^[a-z0-9-]{1,64}:[a-z0-9-]{1,64}(,[a-z0-9-]{1,64}:[a-z0-9-]{1,64})*$")

    def __init__(self, child_event_type, parent_event_type_name, property_map, parent_description=None,
                 siblings_description=None):

        self._attr = {
            'eventtype': parent_event_type_name,
            'propertymap': property_map,
            'parent-description': parent_description or 'belonging to',
            'siblings-description': siblings_description or 'sharing'
        }

        self._childEventType = child_event_type

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self._childEventType._child_modified_callback()
        return self

    def _set_attr(self, key, value):
        if self._attr[key] != value:
            self._attr[key] = value
            self._child_modified_callback()

    @classmethod
    def create(cls, child_event_type, parent_event_type_name, property_map, parent_description=None,
               siblings_description=None):
        """

        Creates a new event type parent. The PropertyMap argument is a dictionary
        mapping property names of the child event type to property names of the
        parent event type.

        If no ParentDescription is specified, it will be set to 'belonging to'.
        If no SiblingsDescription is specified, it will be set to 'sharing'.

        Note:
           All unique properties of the parent event type must appear in
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
            ','.join(['%s:%s' % (Child, Parent)
                      for Child, Parent in property_map.items()]),
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
            current = dict(Mapping.split(':')
                           for Mapping in self._attr['propertymap'].split(','))
        except ValueError:
            current = {}

        current[child_property_name] = parent_property_name
        self._set_attr('propertymap', ','.join(
            ['%s:%s' % (Child, Parent) for Child, Parent in current.items()]))
        return self

    def get_event_type(self):
        """

        Returns the name of the parent event type.

        Returns:
          str:
        """
        return self._attr['eventtype']

    def get_property_map(self):
        """

        Returns the property map as a dictionary mapping
        property names of the child event type to property
        names of the parent.

        Returns:
          Dict[str,str]:
        """
        return dict(Mapping.split(':') for Mapping in self._attr['propertymap'].split(','))

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
          EDXMLValidationError
        Returns:
          edxml.ontology.EventTypeParent: The EventTypeParent instance

        """
        if not len(self._attr['eventtype']) <= 64:
            raise EDXMLValidationError(
                'An implicit parent definition refers to a parent event type using an invalid event type name: "%s"' %
                self._attr['eventtype']
            )
        if not re.match(edxml.ontology.EventType.NAME_PATTERN, self._attr['eventtype']):
            raise EDXMLValidationError(
                'An implicit parent definition refers to a parent event type using an invalid event type name: "%s"' %
                self._attr['eventtype']
            )

        if not re.match(self.PROPERTY_MAP_PATTERN, self._attr['propertymap']):
            raise EDXMLValidationError(
                'An implicit parent definition contains an invalid property map: "%s"' % self._attr[
                    'propertymap']
            )

        if not 1 <= len(self._attr['parent-description']) <= 128:
            raise EDXMLValidationError(
                'An implicit parent definition contains an parent-description '
                'attribute that is either empty or too long: "%s"'
                % self._attr['parent-description']
            )

        if not 1 <= len(self._attr['siblings-description']) <= 128:
            raise EDXMLValidationError(
                'An implicit parent definition contains an siblings-description '
                'attribute that is either empty or too long: "%s"'
                % self._attr['siblings-description']
            )

        return self

    @classmethod
    def create_from_xml(cls, parent_element, child_event_type):
        return cls(
            child_event_type,
            parent_element.attrib['eventtype'],
            parent_element.attrib['propertymap'],
            parent_element.attrib['parent-description'],
            parent_element.attrib['siblings-description']
        )

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
        if self._attr['eventtype'] != parent.get_event_type():
            raise Exception('Attempt to update parent of event type "%s" with parent of event type "%s".' %
                            (self._attr['eventtype'], parent.get_event_type()))

        self.validate()

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <parent> tag for this event type parent.

        Returns:
          etree.Element: The element

        """

        return etree.Element('parent', self._attr)
