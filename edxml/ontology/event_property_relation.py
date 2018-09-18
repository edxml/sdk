# -*- coding: utf-8 -*-

import re
import edxml.ontology

from lxml import etree
from edxml.EDXMLBase import EDXMLValidationError
from edxml.ontology import EventProperty, OntologyElement


class PropertyRelation(OntologyElement):
    """
    Class representing a relation between two EDXML properties
    """

    def __init__(self, event_type, source, target, description, type_class, type_predicate,
                 confidence=10, directed=True):

        self.__attr = {
            'property1': source.get_name(),
            'property2': target.get_name(),
            'description': description,
            'type': '%s:%s' % (type_class, type_predicate),
            'confidence': int(confidence),
            'directed': bool(directed),
        }

        self.__event_type = event_type  # type: edxml.ontology.EventType

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self.__event_type._child_modified_callback()
        return self

    def _set_attr(self, key, value):
        if self.__attr[key] != value:
            self.__attr[key] = value
            self._child_modified_callback()

    def get_source(self):
        """

        Returns the source property.

        Returns:
          str:
        """
        return self.__attr['property1']

    def get_target(self):
        """

        Returns the target property.

        Returns:
          str:
        """
        return self.__attr['property2']

    def get_description(self):
        """

        Returns the relation description.

        Returns:
          str:
        """
        return self.__attr['description']

    def get_type(self):
        """

        Returns the relation type.

        Returns:
          str:
        """
        return self.__attr['type']

    def get_type_class(self):
        """

        Returns the class part of the relation type.

        Returns:
          str:
        """
        return self.__attr['type'].split(':')[0]

    def get_type_predicate(self):
        """

        Returns the predicate part of the relation type.

        Returns:
          str:
        """
        return self.__attr['type'].split(':')[1]

    def get_confidence(self):
        """

        Returns the relation confidence.

        Returns:
          int:
        """
        return self.__attr['confidence']

    def is_directed(self):
        """

        Returns True when the relation is directed,
        returns False otherwise.

        Returns:
          bool:
        """
        return self.__attr['directed']

    def because(self, reason):
        """

        Sets the relation description to specified string,
        which should contain placeholders for the values
        of both related properties.

        Args:
          reason (str): Relation description

        Returns:
          edxml.ontology.PropertyRelation: The PropertyRelation instance

        """
        self._set_attr('description', reason)
        return self

    def set_confidence(self, confidence):
        """

        Configure the relation confidence

        Args:
         confidence (int): Relation confidence [1,10]

        Returns:
          edxml.ontology.PropertyRelation: The PropertyRelation instance
        """

        self._set_attr('confidence', int(confidence))
        return self

    def directed(self):
        """

        Marks the property relation as directed

        Returns:
          edxml.ontology.PropertyRelation: The PropertyRelation instance
        """
        self._set_attr('directed', True)
        return self

    def undirected(self):
        """

        Marks the property relation as undirected

        Returns:
          edxml.ontology.PropertyRelation: The PropertyRelation instance
        """
        self._set_attr('directed', False)
        return self

    def validate(self):
        """

        Checks if the property relation is valid. It only looks
        at the attributes of the relation itself. Since it does
        not have access to the full ontology, the context of
        the relation is not considered. For example, it does not
        check if the properties in the relation actually exist.

        Raises:
          EDXMLValidationError
        Returns:
          edxml.ontology.PropertyRelation: The PropertyRelation instance

        """
        if not re.match(EventProperty.EDXML_PROPERTY_NAME_PATTERN, self.__attr['property1']):
            raise EDXMLValidationError(
                'Invalid property name in property relation: "%s"' % self.__attr['property1'])

        if not re.match(EventProperty.EDXML_PROPERTY_NAME_PATTERN, self.__attr['property2']):
            raise EDXMLValidationError(
                'Invalid property name in property relation: "%s"' % self.__attr['property2'])

        if not len(self.__attr['description']) <= 255:
            raise EDXMLValidationError(
                'Property relation description is too long: "%s"' % self.__attr['description'])

        if not re.match('^(intra|inter|other):.+', self.__attr['type']):
            raise EDXMLValidationError(
                'Invalid property relation type: "%s"' % self.__attr['type'])

        if self.__attr['confidence'] < 1 or self.__attr['confidence'] > 10:
            raise EDXMLValidationError(
                'Invalid property relation confidence: "%d"' % self.__attr['confidence'])

        placeholders = re.findall(
            edxml.ontology.EventType.TEMPLATE_PATTERN, self.__attr['description'])

        if not self.__attr['property1'] in placeholders:
            raise EDXMLValidationError(
                'Relation between properties %s and %s has a description that does not refer to property %s: "%s"' %
                (self.__attr['property1'], self.__attr['property2'],
                 self.__attr['property1'], self.__attr['description'])
            )

        if not self.__attr['property2'] in placeholders:
            raise EDXMLValidationError(
                'Relation between properties %s and %s has a description that does not refer to property %s: "%s"' %
                (self.__attr['property1'], self.__attr['property2'],
                 self.__attr['property2'], self.__attr['description'])
            )

        for propertyName in placeholders:
            if propertyName not in (self.__attr['property1'], self.__attr['property2']):
                raise EDXMLValidationError(
                    'Relation between properties %s and %s has a description that refers to other properties: "%s"' %
                    (self.__attr['property1'], self.__attr['property2'],
                     self.__attr['description'])
                )

        return self

    @classmethod
    def create_from_xml(cls, relation_element, event_type):
        source = relation_element.attrib['property1']
        target = relation_element.attrib['property2']

        for propertyName in (source, target):
            if propertyName not in event_type:
                raise EDXMLValidationError(
                    'Event type "%s" contains a property relation referring to property "%s", which is not defined.' %
                    (event_type.get_name(), propertyName))

        return cls(
            event_type,
            event_type[relation_element.attrib['property1']],
            event_type[relation_element.attrib['property2']],
            relation_element.attrib['description'],
            relation_element.attrib['type'].split(':')[0],
            relation_element.attrib['type'].split(':')[1],
            relation_element.attrib['confidence'],
            relation_element.get('directed', 'true') == 'true'
        )

    def update(self, property_relation):
        """

        Updates the property relation to match the PropertyRelation
        instance passed to this method, returning the
        updated instance.

        Args:
          property_relation (edxml.ontology.PropertyRelation): The new PropertyRelation instance

        Returns:
          edxml.ontology.PropertyRelation: The updated PropertyRelation instance

        """
        property1 = self.__attr['property1'] != property_relation.get_source()
        property2 = self.__attr['property2'] != property_relation.get_target()
        if property1 or property2:
            raise Exception('Attempt to property relation between %s -> %s with relation between %s -> %s.' %
                            (self.__attr['property1'], self.__attr['property2'],
                             property_relation.get_source(), property_relation.get_target()))

        self.validate()

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <relation> tag for this event property.

        Returns:
          etree.Element: The element

        """

        attribs = dict(self.__attr)

        attribs['confidence'] = '%d' % self.__attr['confidence']
        attribs['directed'] = 'true' if self.__attr['directed'] else 'false'

        return etree.Element('relation', attribs)
