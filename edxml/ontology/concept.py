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

import copy
import re

from lxml import etree

import edxml.ontology

from edxml.error import EDXMLOntologyValidationError
from edxml.ontology import VersionedOntologyElement, normalize_xml_token
from edxml.ontology.ontology_element import ontology_element_upgrade_error


class Concept(VersionedOntologyElement):
    """
    Class representing an EDXML concept
    """

    NAME_PATTERN = re.compile('^[a-z0-9.-]{1,255}$')

    def __init__(self, ontology, name, display_name_singular=None, display_name_plural=None, description=None):

        display_name_singular = display_name_singular or name.replace('.', ' ')
        display_name_plural = display_name_plural or display_name_singular + 's'

        self._attr = {
            'name': name,
            'display-name-singular': display_name_singular,
            'display-name-plural': display_name_plural,
            'description': description or name,
            'version': 1
        }

        self._ontology = ontology  # type: edxml.ontology.Ontology

        self.__versions = {1: copy.copy(self)}

    def __repr__(self):
        return f"{self._attr['name']} ({self._attr['display-name-singular']})"

    def __str__(self):
        return self._attr['name']

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self._ontology._child_modified_callback()
        return self

    def _set_attr(self, key, value):
        if self._attr[key] != value:
            self._attr[key] = value
            self._child_modified_callback()

    @classmethod
    def concept_names_share_branch(cls, a, b):
        """
        Returns True when concept name a is a specialization of
        b or the other way around. This is true when both share the same
        branch in the concept name hierarchy. For example concept
        names a.b and a.b.c share the same branch while a.b and a.c
        do not.

        Args:
            a (str):
            b (str):

        Returns:
            bool:

        """

        # Make sure that b is longer than a
        if len(a) > len(b):
            tmp = a
            a = b
            b = tmp

        # Truncate b to the length of a
        if len(b) > len(a):
            b = b[0:len(a)]

        return a == b

    @classmethod
    def concept_name_is_specialization(cls, concept_name, specialization_concept_name):
        """
        Returns True when the one concept name a is a specialization of
        the other. This is true when the specialization extends the
        concept name by appending to it.

        Args:
            concept_name (str):
            specialization_concept_name (str):

        Returns:
            bool:

        """

        # Make sure that b is longer than a
        if len(specialization_concept_name) <= len(concept_name):
            return False

        return specialization_concept_name[:len(concept_name)] == concept_name

    def get_name(self):
        """

        Returns the name of the concept.

        Returns:
          str: The concept name
        """

        return self._attr['name']

    def get_display_name_singular(self):
        """

        Returns the display name of the concept, in singular form.

        Returns:
          str:
        """

        return self._attr['display-name-singular']

    def get_display_name_plural(self):
        """

        Returns the display name of the concept, in plural form.

        Returns:
          str:
        """

        return self._attr['display-name-plural']

    def get_description(self):
        """

        Returns the description of the concept.

        Returns:
          str:
        """

        return self._attr['description']

    def get_version(self):
        """

        Returns the version of the concept definition.

        Returns:
          int:
        """

        return self._attr['version']

    def set_description(self, description):
        """

        Sets the concept description

        Args:
          description (str): Description

        Returns:
          edxml.ontology.Concept: The Concept instance
        """

        self._set_attr('description', str(description))
        return self

    def set_display_name(self, singular, plural=None):
        """

        Configure the display name. If the plural form
        is omitted, it will be auto-generated by
        appending an 's' to the singular form.

        Args:
          singular (str): display name (singular form)
          plural (str): display name (plural form)

        Returns:
          edxml.ontology.Concept: The Concept instance
        """

        self._set_attr('display-name-singular', singular)
        self._set_attr('display-name-plural', plural or (singular + 's'))

        return self

    def set_version(self, version):
        """

        Sets the concept version

        Args:
          version (int): Version

        Returns:
          edxml.ontology.Concept: The Concept instance
        """

        self.__versions[self._attr['version']] = copy.copy(self)
        self._set_attr('version', int(version))
        return self

    def upgrade(self):
        """
        Verifies if the current instance is a valid upgrade of the instance as it
        was when the version was last changed. When successful the version number is
        incremented.

        This method is used for fluent upgrading of ontology bricks, allowing
        definitions of concepts to be changed in a single call chain while
        making sure that no backward incompatible changes are made.

        Returns:
          edxml.ontology.Concept: The Concept instance
        """
        new_version = copy.deepcopy(self).set_version(self._attr['version'] + 1)
        if new_version > self.__versions[self._attr['version']]:
            self.set_version(self._attr['version'] + 1)
        else:
            raise Exception('Cannot upgrade when current version is not greater than previous version.')

        return self

    def validate(self):
        """

        Checks if the concept is valid. It only looks
        at the attributes of the definition itself. Since it does
        not have access to the full ontology, the context of
        the ontology is not considered. For example, it does not
        check if other, conflicting concept definitions exist.

        Raises:
          EDXMLOntologyValidationError

        Returns:
          edxml.ontology.Concept: The Concept instance

        """
        if not len(self._attr['name']) <= 255:
            raise EDXMLOntologyValidationError(
                'The name of concept "%s" is too long.' % self._attr['name'])
        if not re.match(self.NAME_PATTERN, self._attr['name']):
            raise EDXMLOntologyValidationError(
                'Concept "%s" has an invalid name.' % self._attr['name'])

        if not len(self._attr['display-name-singular']) <= 32:
            raise EDXMLOntologyValidationError(
                'The singular display name of concept "%s" is too long: "%s".' % (
                    self._attr['name'], self._attr['display-name-singular'])
            )

        if not len(self._attr['display-name-plural']) <= 32:
            raise EDXMLOntologyValidationError(
                'The plural display name of concept "%s" is too long: "%s".' % (
                    self._attr['name'], self._attr['display-name-plural'])
            )

        if normalize_xml_token(self._attr['display-name-singular']) != self._attr['display-name-singular']:
            raise EDXMLOntologyValidationError(
                'Singular display name of concept "%s" contains illegal whitespace characters: "%s"' % (
                    self._attr['name'], self._attr['display-name-singular'])
            )

        if normalize_xml_token(self._attr['display-name-plural']) != self._attr['display-name-plural']:
            raise EDXMLOntologyValidationError(
                'Plural display name of concept "%s" contains illegal whitespace characters: "%s"' % (
                    self._attr['name'], self._attr['display-name-plural'])
            )

        if normalize_xml_token(self._attr['description']) != self._attr['description']:
            raise EDXMLOntologyValidationError(
                'The description of concept "%s" contains illegal whitespace characters: "%s"' % (
                    self._attr['name'], self._attr['description'])
            )

        if not len(self._attr['description']) <= 128:
            raise EDXMLOntologyValidationError(
                'The description of concept "%s" is too long: "%s"' % (
                    self._attr['name'], self._attr['description'])
            )

        return self

    @classmethod
    def create_from_xml(cls, type_element, ontology):
        try:
            return cls(
                ontology,
                type_element.attrib['name'],
                type_element.attrib['display-name-singular'],
                type_element.attrib['display-name-plural'],
                type_element.attrib['description'],
            ).set_version(type_element.attrib['version'])
        except KeyError as e:
            raise EDXMLOntologyValidationError(
                "Failed to instantiate a concept from the following definition:\n" +
                etree.tostring(type_element, pretty_print=True, encoding='unicode') +
                "\nMissing attribute: " + str(e)
            )

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

        if old.get_name() != new.get_name():
            raise ValueError("Concepts with different names are not comparable.")

        # Compare attributes that cannot produce illegal upgrades because they can
        # be changed freely between versions. We only need to know if they changed.

        equal &= old.get_display_name_singular() == new.get_display_name_singular()
        equal &= old.get_display_name_plural() == new.get_display_name_plural()
        equal &= old.get_description() == new.get_description()

        if equal:
            return 0

        if versions_differ:
            return -1 if other_is_newer else 1

        ontology_element_upgrade_error('concept', old, new)

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __lt__(self, other):
        return self.__cmp__(other) < 0

    def update(self, concept):
        """
        Update the concept using information from the provided
        concept and validate the result.

        Args:
          concept (edxml.ontology.Concept): The new Concept instance

        Returns:
          edxml.ontology.Concept: The updated Concept instance

        """
        if concept > self:
            # The new definition is indeed newer. Update self.
            self.set_display_name(concept.get_display_name_singular(), concept.get_display_name_plural())
            self.set_description(concept.get_description())
            self.set_version(concept.get_version())

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <concept> tag for this concept.

        Returns:
          etree.Element: The element

        """
        attribs = dict(self._attr)
        attribs['version'] = str(attribs['version'])

        return etree.Element('concept', attribs)

    @classmethod
    def generate_specializations(cls, concept_name, parent_concept_name=None):
        """
        Generator yielding specializations of a given concept. For example, when
        given a concept name 'a.b.c' it will generate concept names 'a', 'a.b'
        and 'a.b.c'.

        Optionally a parent concept can be specified. In that case the specializations
        will be generated starting at the parent concept.

        Args:
            concept_name (str): Concept for which to generate specializations
            parent_concept_name (Optional[str]): First yielded concept name

        Yields:
            str
        """
        components = concept_name.split('.')
        if not components:
            return
        parent_components = parent_concept_name.split('.') if parent_concept_name else []
        current_concept_name = []
        while components and current_concept_name != parent_components:
            current_concept_name.append(components.pop(0))
        while len(components) > 0:
            current_concept_name.append(components.pop(0))
            yield '.'.join(current_concept_name)

    @classmethod
    def generate_generalizations(cls, concept_name):
        """
        Generator yielding generalizations of a given concept. For example, when
        given a concept name 'a.b.c' it will generate concept names 'a.b' and 'a'.

        Args:
            concept_name (str): Concept for which to generate generalizations

        Yields:
            str
        """
        components = concept_name.split('.')
        while len(components) > 1:
            components.pop()
            yield '.'.join(components)
