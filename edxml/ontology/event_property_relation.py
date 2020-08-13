# -*- coding: utf-8 -*-

import re
import edxml.ontology

from lxml import etree
from edxml.error import EDXMLValidationError
from edxml.ontology import EventProperty, OntologyElement, normalize_xml_token


class PropertyRelation(OntologyElement):
    """
    Class representing a relation between two EDXML properties
    """

    def __init__(self, event_type, source, target, source_concept, target_concept, description,
                 type_class, type_predicate, confidence=10, directed=True):

        self._type = type_class

        self.__attr = {
            'property1': source.get_name(),
            'property2': target.get_name(),
            'concept1': source_concept.get_name() if source_concept else None,
            'concept2': target_concept.get_name() if target_concept else None,
            'description': description,
            'predicate': type_predicate,
            'confidence': int(confidence),
            'directed': bool(directed),
        }

        self.__event_type = event_type  # type: edxml.ontology.EventType

    def __repr__(self):
        return f"{self.__attr['property1']} {self.__attr['predicate']} {self.__attr['property2']}"

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
            self.__event_type.get_name(), self.get_type(), self.get_source(), self.get_target()
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

    def get_source_concept(self):
        """

        Returns the source concept.

        Returns:
          str:
        """
        return self.__attr['concept1']

    def get_target_concept(self):
        """

        Returns the target concept.

        Returns:
          str:
        """
        return self.__attr['concept2']

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
        return self._type

    def get_predicate(self):
        """

        Returns the relation predicate.

        Returns:
          str:
        """
        return self.__attr['predicate']

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

    def set_predicate(self, predicate):
        """

        Sets the relation predicate to specified string.

        Args:
          predicate (str): Relation predicate

        Returns:
          edxml.ontology.PropertyRelation: The PropertyRelation instance

        """
        self._set_attr('predicate', predicate)
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

        if normalize_xml_token(self.__attr['description']) != self.__attr['description']:
            raise EDXMLValidationError(
                'Property relation description contains illegal whitespace characters: "%s"' % (
                    self.__attr['description'])
            )

        if not len(self.__attr['predicate']) <= 32:
            raise EDXMLValidationError(
                'Property relation predicate is too long: "%s"' % self.__attr['predicate'])

        if normalize_xml_token(self.__attr['predicate']) != self.__attr['predicate']:
            raise EDXMLValidationError(
                'Property relation predicate contains illegal whitespace characters: "%s"' % (
                    self.__attr['predicate'])
            )

        if self._type not in ['inter', 'intra', 'other']:
            raise EDXMLValidationError(
                'Invalid property relation type: "%s"' % self._type)

        if self.__attr['confidence'] < 1 or self.__attr['confidence'] > 10:
            raise EDXMLValidationError(
                'Invalid property relation confidence: "%d"' % self.__attr['confidence'])

        try:
            edxml.Template(self.__attr['description']).validate(self.__event_type)
        except EDXMLValidationError as e:
            raise EDXMLValidationError(
                'Relation between properties %s and %s has an invalid description: "%s" The validator said: %s' % (
                    self.__attr['property1'], self.__attr['property2'],
                    self.__attr['description'], str(e)
                 )
            )

        if self.get_type() in ('inter', 'intra'):
            if self.__attr.get('concept1') is None or self.__attr.get('concept2') is None:
                raise EDXMLValidationError(
                    'The %s-concept relation between properties %s and %s does not specify both related concepts.' %
                    (self.get_type(), self.__attr['property1'], self.__attr['property2'])
                )

        return self

    @classmethod
    def create_from_xml(cls, relation_element, event_type, ontology):
        try:
            source = relation_element.attrib['property1']
        except KeyError:
            raise EDXMLValidationError(
                'Failed to parse definition of event type "%s": '
                'It is missing the source property attribute (property1)' % event_type.get_name()
            )
        try:
            target = relation_element.attrib['property2']
        except KeyError:
            raise EDXMLValidationError(
                'Failed to parse definition of event type "%s": '
                'It is missing the target property attribute (property2)' % event_type.get_name()
            )

        for propertyName in (source, target):
            if propertyName not in event_type:
                raise EDXMLValidationError(
                    'Event type "%s" contains a property relation referring to property "%s", which is not defined.' %
                    (event_type.get_name(), propertyName))

        concept1_name = relation_element.attrib.get('concept1')
        concept2_name = relation_element.attrib.get('concept2')

        concept1 = ontology.get_concept(concept1_name)
        concept2 = ontology.get_concept(concept2_name)

        if concept1_name is not None and concept1 is None:
            raise EDXMLValidationError(
                'Failed to instantiate a property relation, source concept "%s" does not exist.' % concept1_name
            )
        if concept2_name is not None and concept2 is None:
            raise EDXMLValidationError(
                'Failed to instantiate a property relation, target concept "%s" does not exist.' % concept2_name
            )

        try:
            return cls(
                event_type,
                event_type[source],
                event_type[target],
                concept1,
                concept2,
                relation_element.attrib['description'],
                relation_element.tag[24:],
                relation_element.attrib['predicate'],
                relation_element.attrib['confidence'],
                relation_element.get('directed', 'true') == 'true'
            )
        except (ValueError, KeyError) as e:
            raise EDXMLValidationError(
                "Failed to instantiate a property relation from the following definition:\n" +
                etree.tostring(relation_element, pretty_print=True, encoding='unicode') +
                "\nError message: " + str(e)
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

        if old.get_source_concept() != new.get_source_concept():
            # The concepts in the relations are different, no upgrade possible.
            equal = is_valid_upgrade = False

        if old.get_target_concept() != new.get_target_concept():
            # The concepts in the relations are different, no upgrade possible.
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
        equal &= old.get_predicate() == new.get_predicate()
        equal &= old.get_confidence() == new.get_confidence()

        if equal:
            return 0

        if is_valid_upgrade and versions_differ:
            return -1 if other_is_newer else 1

        problem = 'invalid upgrades / downgrades of one another' if versions_differ else 'in conflict'

        old_version = str(old.__event_type.get_version())
        new_version = str(new.__event_type.get_version())

        if not versions_differ:
            new_version += ' (conflicting definition)'

        raise EDXMLValidationError(
            "Definitions of event type {} are {} due to the following difference in a property relation:\n"
            "Version {}:\n{}\nVersion {}:\n{}".format(
                self.__event_type.get_name(),
                problem,
                old_version,
                etree.tostring(old.generate_xml(), pretty_print=True, encoding='unicode'),
                new_version,
                etree.tostring(new.generate_xml(), pretty_print=True, encoding='unicode')
            )
        )

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

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
            self.set_predicate(property_relation.get_predicate())
            self.set_confidence(property_relation.get_confidence())
            self.__event_type = property_relation.__event_type

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

        if self._type not in ['inter', 'intra']:
            del attribs['concept1']
            del attribs['concept2']

        return etree.Element(self._type, attribs)
