# -*- coding: utf-8 -*-

from lxml import etree


from edxml.error import EDXMLValidationError
from edxml.ontology import OntologyElement, EventType, EventProperty, normalize_xml_token


class PropertyConcept(OntologyElement):
    """
    Class representing an association between a property and a concept
    """

    def __init__(self, event_type, property, name, confidence=10, naming_priority=128):

        self.__attr = {
            'name': name,
            'confidence': confidence,
            'cnp': naming_priority,
            'attr-extension': '',
            'attr-display-name-singular': '',
            'attr-display-name-plural': '',
        }

        self.__event_type = event_type  # type: EventType
        self.__property = property      # type: EventProperty

    def __repr__(self):
        return f"{self.__property.get_name()} => {self.__attr['name']}"

    def __str__(self):
        return f"{self.__property.get_name()}=>{self.__attr['name']}"

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

    def get_attribute_name(self):
        """

        Returns the full name of the concept attribute, which includes the object
        type name, a colon and its extension.

        Returns:
            str:
        """
        return self.__property.get_object_type().get_name() + ':' + self.__attr['attr-extension']

    def get_attribute_name_extension(self):
        """

        Returns the attribute name extension.

        Returns:
            str:
        """
        return self.__attr['attr-extension']

    def get_attribute_display_name_singular(self):
        """

        Returns the display name of the concept attribute (singular form).
        When the attribute does not have a custom display name, the display
        name of the object type of the associated property is used.

        Returns:
            str:
        """
        if self.__attr['attr-display-name-singular'] == '':
            # No custom display name, fall back to object type
            return self.__property.get_object_type().get_display_name_singular()
        else:
            return self.__attr['attr-display-name-singular']

    def get_attribute_display_name_plural(self):
        """

        Returns the display name of the concept attribute (plural form)
        When the attribute does not have a custom display name, the display
        name of the object type of the associated property is used.

        Returns:
            str:
        """
        if self.__attr['attr-display-name-plural'] == '':
            # No custom display name, fall back to object type
            return self.__property.get_object_type().get_display_name_plural()
        else:
            return self.__attr['attr-display-name-plural']

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

    def set_attribute(self, extension, display_name_singular='', display_name_plural=''):
        """

        Set the name extension of the concept attribute. By default, concept attributes
        are named after the object type of their associated property by taking the object
        type name, appending a colon and appending a concept name extension.

        If the plural form of the display name is omitted, it will be auto-generated by
        appending an 's' to the singular form.

        Args:
            extension (str):
            display_name_singular (str):
            display_name_plural (str):

        Returns:
            edxml.ontology.PropertyConcept: The PropertyConcept instance
        """

        if display_name_singular != '' and display_name_plural == '':
            display_name_plural = display_name_singular + 's'

        self._set_attr('attr-extension', extension)
        self._set_attr('attr-display-name-singular', display_name_singular)
        self._set_attr('attr-display-name-plural', display_name_plural)

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

        if self.get_attribute_name_extension() == '':
            if self.__attr['attr-display-name-singular'] != '' or self.__attr['attr-display-name-plural'] != '':
                raise EDXMLValidationError(
                    'The property / concept association between property %s in event type %s and concept %s has '
                    'a custom display name while it does not have a custom attribute name extension.' %
                    (self.__event_type.get_name(), self.__property.get_name(), self.__attr['name'])
                )

        if normalize_xml_token(self.__attr['attr-display-name-singular']) != self.__attr['attr-display-name-singular']:
            raise EDXMLValidationError(
                'The property / concept association between property %s in event type %s and concept %s has '
                'a custom display name which contains illegal whitespace characters: "%s"' %
                (self.__event_type.get_name(), self.__property.get_name(), self.__attr['name'],
                 self.__attr['attr-display-name-singular'])
            )

        if normalize_xml_token(self.__attr['attr-display-name-plural']) != self.__attr['attr-display-name-plural']:
            raise EDXMLValidationError(
                'The property / concept association between property %s in event type %s and concept %s has '
                'a custom display name which contains illegal whitespace characters: "%s"' %
                (self.__event_type.get_name(), self.__property.get_name(), self.__attr['name'],
                 self.__attr['attr-display-name-plural'])
            )

        return self

    @classmethod
    def create_from_xml(cls, concept_element, event_type, property):
        try:
            association = cls(
                event_type,
                property,
                concept_element.attrib['name'],
                int(concept_element.attrib['confidence']),
                int(concept_element.attrib['cnp'])
            )

            attr_extension = concept_element.attrib.get('attr-extension', '')
            attr_display_name_singular = concept_element.attrib.get('attr-display-name-singular', '')
            attr_display_name_plural = concept_element.attrib.get('attr-display-name-plural', '')

            association.set_attribute(attr_extension, attr_display_name_singular, attr_display_name_plural)

            return association

        except (ValueError, KeyError) as e:
            raise EDXMLValidationError(
                "Failed to instantiate a property-concept association from the following definition:\n" +
                etree.tostring(concept_element, pretty_print=True, encoding='unicode') +
                "\nError message: " + str(e)
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

        if old.get_attribute_name_extension() != new.get_attribute_name_extension():
            # The attribute name extensions differ, no upgrade possible.
            equal = is_valid_upgrade = False

        # Compare attributes that cannot produce illegal upgrades because they can
        # be changed freely between versions. We only need to know if they changed.

        for attr in ['confidence', 'cnp', 'attr-display-name-singular', 'attr-display-name-plural']:
            equal &= old.__attr[attr] == new.__attr[attr]

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
            "Definitions of event type {} are {} due to the following difference in property concept associations:\n"
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

            if property_concept.get_attribute_name_extension() != '':
                # Attribute has custom name extension
                self.set_attribute(
                    extension=property_concept.get_attribute_name_extension(),
                    display_name_singular=property_concept.__attr['attr-display-name-singular'],
                    display_name_plural=property_concept.__attr['attr-display-name-plural'],
                )

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

        if self.__attr['attr-extension'] == '':
            del attribs['attr-extension']
            del attribs['attr-display-name-singular']
            del attribs['attr-display-name-plural']

        return etree.Element('property-concept', attribs)
