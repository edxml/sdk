# -*- coding: utf-8 -*-

from lxml import etree

import edxml
from edxml.error import EDXMLValidationError
from edxml.ontology import OntologyElement


class PropertyConcept(OntologyElement):
    """
    Class representing an association between a property and a concept
    """

    def __init__(self, event_type, property, name, confidence=10, naming_priority=128):

        self.__attr = {
            'name': name,
            'confidence': confidence,
            'cnp': naming_priority
        }

        self.__event_type = event_type  # type: edxml.ontology.EventType
        self.__property = property  # type: edxml.ontology.EventProperty

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self.__property._child_modified_callback()
        return self

    def _set_attr(self, key, value):
        if self.__attr[key] != value:
            self.__attr[key] = value
            self._child_modified_callback()

    def get_concept_name(self):
        """

        Returns the name of the associated concept.

        Returns:
          str:
        """
        return self.__attr['name']

    def get_property_name(self):
        """

        Returns the name of the event property.

        Returns:
          str:
        """
        return self.__property.get_name()

    def get_confidence(self):
        """

        Returns the concept confidence of the association,
        indicating how strong the property values are as
        identifiers of instances of the associated concept.

        Returns:
          int:
        """
        return self.__attr['confidence']

    def get_concept_naming_priority(self):
        """

        Returns the concept naming priority.

        Returns:
          int:
        """
        return self.__attr['cnp']

    def set_confidence(self, confidence):
        """

        Configure the concept confidence of the association,
        indicating how strong the property values are as
        identifiers of instances of the associated concept.

        Args:
         confidence (int): Confidence [1,10]

        Returns:
          edxml.ontology.PropertyConcept: The PropertyConcept instance
        """

        self._set_attr('confidence', int(confidence))
        return self

    def set_concept_naming_priority(self, priority):
        """

        Configure the concept naming priority.

        Args:
         priority (int): Naming priority [1,10]

        Returns:
          edxml.ontology.PropertyConcept: The PropertyConcept instance
        """

        self._set_attr('cnp', int(priority))
        return self

    def validate(self):
        """

        Checks if the concept association is valid. It only looks
        at the attributes of the association itself. Since it does
        not have access to the full ontology, the context of
        the association is not considered. For example, it does not
        check if the concept actually exist.

        Raises:
          EDXMLValidationError
        Returns:
          edxml.ontology.PropertyConcept: The PropertyConcept instance

        """

        if self.__attr['confidence'] < 0 or self.__attr['confidence'] > 10:
            raise EDXMLValidationError(
                'The property / concept association between property %s in event type %s and concept %s has '
                'an invalid confidence: "%d"' %
                (self.__event_type.get_name(), self.__property.get_name(),
                 self.__attr['name'], self.__attr['confidence'])
            )

        if not 0 <= int(self.__attr['cnp']) < 256:
            raise EDXMLValidationError(
                'The property / concept association between property %s in event type %s and concept %s has '
                'an invalid concept naming priority: "%d"' %
                (self.__event_type.get_name(), self.__property.get_name(), self.__attr['name'], self.__attr['cnp'])
            )

        return self

    @classmethod
    def create_from_xml(cls, concept_element, event_type, property):
        return cls(
            event_type,
            property,
            concept_element.attrib['name'],
            int(concept_element.attrib['confidence']),
            int(concept_element.attrib['cnp'])
        )

    def __cmp__(self, other):

        if not isinstance(other, type(self)):
            raise TypeError("Cannot compare different types of ontology elements.")

        # Note that property concepts are part of event type definitions,
        # so we look at the version of the event type for which this association is defined.
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
            raise EDXMLValidationError(
                "Attempt to compare property / concept associations from two different event types"
            )

        if old.get_concept_name() != new.get_concept_name():
            raise ValueError("Associations to different concepts are not comparable.")

        # Check for illegal upgrade paths:

        if old.__event_type[old.get_property_name()].get_name() != new.__event_type[new.get_property_name()].get_name():
            # The properties in the associations are different, no upgrade possible.
            equal = is_valid_upgrade = False

        # Compare attributes that cannot produce illegal upgrades because they can
        # be changed freely between versions. We only need to know if they changed.

        equal &= old.get_confidence() == new.get_confidence()
        equal &= old.get_concept_naming_priority() == new.get_concept_naming_priority()

        if equal:
            return 0

        if is_valid_upgrade and versions_differ:
            return -1 if other_is_newer else 1

        raise EDXMLValidationError(
            "Definitions of event type {} are neither equal nor valid upgrades / downgrades of one another "
            "due to the following difference in property concept associations:\n"
            "Old version:\n{}\nNew version:\n{}".format(
                self.__event_type.get_name(),
                etree.tostring(old.generate_xml(), pretty_print=True, encoding='unicode'),
                etree.tostring(new.generate_xml(), pretty_print=True, encoding='unicode')
            )
        )

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def update(self, property_concept):
        """

        Updates the concept association to match the PropertyConcept
        instance passed to this method, returning the
        updated instance.

        Args:
          property_concept (edxml.ontology.PropertyConcept): The new PropertyConcept instance

        Returns:
          edxml.ontology.PropertyConcept: The updated PropertyConcept instance

        """
        if property_concept > self:
            # The new definition is indeed newer. Update self.
            self.set_confidence(property_concept.get_confidence())
            self.set_concept_naming_priority(property_concept.get_concept_naming_priority())
            self.__event_type = property_concept.__event_type

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <property-concept> tag for this
        property concept association

        Returns:
          etree.Element: The element

        """

        attribs = dict(self.__attr)

        attribs['name'] = self.__attr['name']
        attribs['confidence'] = '%d' % self.__attr['confidence']
        attribs['cnp'] = '%d' % self.__attr['cnp']

        return etree.Element('property-concept', attribs)
