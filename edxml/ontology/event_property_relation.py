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

    def get_persistent_id(self):
        """
        Generates and returns a unique, persistent identifier for
        the property relation.

        Returns:
            str:
        """
        return '{}:{}:{},{}'.format(
            self.__event_type.get_name(), self.get_type_class(), self.get_source(), self.get_target()
        )

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

    def set_description(self, description):
        """

        Sets the relation description to specified string,
        which should contain placeholders for the values
        of both related properties.

        Args:
          description (str): Relation description

        Returns:
          edxml.ontology.PropertyRelation: The PropertyRelation instance

        """
        return self.because(description)

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

    def __cmp__(self, other):

        if not isinstance(other, type(self)):
            raise TypeError("Cannot compare different types of ontology elements.")

        # Note that property relations are part of event type definitions,
        # so we look at the version of the event type for which this relation is defined.
        other_is_newer = other.__event_type.get_version() > self.__event_type.get_version()
        versions_differ = other.__event_type.get_version() != self.__event_type.get_version()

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

        if old.__event_type.get_name() != new.__event_type.get_name():
            raise EDXMLValidationError("Attempt to compare property relations from two different event types")

        # Check for illegal upgrade paths:

        if old.__event_type[old.get_source()].get_name() != new.__event_type[new.get_source()].get_name():
            # The properties in the relations are different, no upgrade possible.
            equal = is_valid_upgrade = False

        if old.__event_type[old.get_target()].get_name() != new.__event_type[new.get_target()].get_name():
            # The properties in the relations are different, no upgrade possible.
            equal = is_valid_upgrade = False

        if old.is_directed() != new.is_directed():
            # The relation directedness is different, no upgrade possible.
            equal = is_valid_upgrade = False

        if old.get_type() != new.get_type():
            # The relation types are different, no upgrade possible.
            equal = is_valid_upgrade = False

        # Compare attributes that cannot produce illegal upgrades because they can
        # be changed freely between versions. We only need to know if they changed.

        equal &= old.get_description() == new.get_description()
        equal &= old.get_confidence() == new.get_confidence()

        if equal:
            return 0

        if is_valid_upgrade and versions_differ:
            return -1 if other_is_newer else 1

        raise EDXMLValidationError(
            "Definitions of event type {} are neither equal nor valid upgrades / downgrades of one another "
            "due to the following difference in a property relation:\nOld version:\n{}\nNew version:\n{}".format(
                self.__event_type.get_name(),
                etree.tostring(old.generate_xml(), pretty_print=True),
                etree.tostring(new.generate_xml(), pretty_print=True)
            )
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
        if property_relation > self:
            # The new definition is indeed newer. Update self.
            self.set_description(property_relation.get_description())
            self.set_confidence(property_relation.get_confidence())

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
