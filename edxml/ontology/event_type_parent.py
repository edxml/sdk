# -*- coding: utf-8 -*-

import re
import edxml

from lxml import etree
from edxml.EDXMLBase import EDXMLValidationError


class EventTypeParent(object):
    """
    Class representing an EDXML event type parent
    """

    PROPERTY_MAP_PATTERN = re.compile(
        "^[a-z0-9-]{1,64}:[a-z0-9-]{1,64}(,[a-z0-9-]{1,64}:[a-z0-9-]{1,64})*$")

    def __init__(self, ChildEventType, ParentEventTypeName, PropertyMap, ParentDescription=None,
                 SiblingsDescription=None):

        self._attr = {
            'eventtype': ParentEventTypeName,
            'propertymap': PropertyMap,
            'parent-description': ParentDescription or 'belonging to',
            'siblings-description': SiblingsDescription or 'sharing'
        }

        self._childEventType = ChildEventType

    def _childModifiedCallback(self):
        """Callback for change tracking"""
        self._childEventType._childModifiedCallback()
        return self

    def _setAttr(self, key, value):
        if self._attr[key] != value:
            self._attr[key] = value
            self._childModifiedCallback()

    @classmethod
    def Create(cls, ChildEventType, ParentEventTypeName, PropertyMap, ParentDescription=None, SiblingsDescription=None):
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
          ChildEventType (EventType): The child event type
          ParentEventTypeName (str): Name of the parent event type
          PropertyMap (Dict[str, str]): Property map
          ParentDescription (Optional[str]): The EDXML parent-description attribute
          SiblingsDescription (Optional[str]): The EDXML siblings-description attribute

        Returns:
          edxml.ontology.EventTypeParent: The EventTypeParent instance
        """
        return cls(
            ChildEventType,
            ParentEventTypeName,
            ','.join(['%s:%s' % (Child, Parent)
                      for Child, Parent in PropertyMap.items()]),
            ParentDescription,
            SiblingsDescription
        )

    def SetParentDescription(self, Description):
        """
        Sets the EDXML parent-description attribute

        Args:
          Description (str): The EDXML parent-description attribute

        Returns:
          edxml.ontology.EventTypeParent: The EventTypeParent instance
        """
        self._setAttr('parent-description', Description)

        return self

    def SetSiblingsDescription(self, Description):
        """

        Sets the EDXML siblings-description attribute

        Args:
          Description (str): The EDXML siblings-description attribute

        Returns:
          edxml.ontology.EventTypeParent: The EventTypeParent instance
        """
        self._setAttr('siblings-description', Description)

        return self

    def Map(self, ChildPropertyName, ParentPropertyName=None):
        """

        Add a property mapping, mapping a property in the child
        event type to the corresponding property in the parent.
        When the parent property name is omitted, it is assumed
        that the parent and child properties are named identically.

        Args:
          ChildPropertyName (str):  Child property
          ParentPropertyName (str): Parent property

        Returns:
          edxml.ontology.EventTypeParent: The EventTypeParent instance
        """
        ParentPropertyName = ChildPropertyName if ParentPropertyName is None else ParentPropertyName

        try:
            current = dict(Mapping.split(':')
                           for Mapping in self._attr['propertymap'].split(','))
        except ValueError:
            current = {}

        current[ChildPropertyName] = ParentPropertyName
        self._setAttr('propertymap', ','.join(
            ['%s:%s' % (Child, Parent) for Child, Parent in current.items()]))
        return self

    def GetEventType(self):
        """

        Returns the name of the parent event type.

        Returns:
          str:
        """
        return self._attr['eventtype']

    def GetPropertyMap(self):
        """

        Returns the property map as a dictionary mapping
        property names of the child event type to property
        names of the parent.

        Returns:
          Dict[str,str]:
        """
        return dict(Mapping.split(':') for Mapping in self._attr['propertymap'].split(','))

    def GetParentDescription(self):
        """

        Returns the EDXML 'parent-description' attribute.

        Returns:
          str:
        """
        return self._attr['eventtype']

    def GetSiblingsDescription(self):
        """

        Returns the EDXML 'siblings-description' attribute.

        Returns:
          str:
        """
        return self._attr['eventtype']

    def Validate(self):
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
    def Read(cls, parentElement, childEventType):
        return cls(
            childEventType,
            parentElement.attrib['eventtype'],
            parentElement.attrib['propertymap'],
            parentElement.attrib['parent-description'],
            parentElement.attrib['siblings-description']
        )

    def Update(self, parent):
        """

        Updates the event type parent to match the EventTypeParent
        instance passed to this method, returning the
        updated instance.

        Args:
          parent (edxml.ontology.EventTypeParent): The new EventTypeParent instance

        Returns:
          edxml.ontology.EventTypeParent: The updated EventTypeParent instance

        """
        if self._attr['eventtype'] != parent.GetEventType():
            raise Exception('Attempt to update parent of event type "%s" with parent of event type "%s".' %
                            (self._attr['eventtype'], parent.GetEventType()))

        self.Validate()

        return self

    def GenerateXml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <parent> tag for this event type parent.

        Returns:
          etree.Element: The element

        """

        return etree.Element('parent', self._attr)
