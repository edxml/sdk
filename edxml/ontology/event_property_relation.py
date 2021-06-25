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
from copy import copy

import edxml.template
import edxml.ontology

from lxml import etree

from edxml import template
from edxml.error import EDXMLOntologyValidationError
from edxml.ontology import OntologyElement, normalize_xml_token
from edxml.ontology.ontology_element import event_type_element_upgrade_error


class PropertyRelation(OntologyElement):
    """
    Class representing a relation between two EDXML properties
    """

    def __init__(self, event_type, source, target, source_concept, target_concept, description,
                 type_class, type_predicate, confidence=10):

        self._type = type_class
        self._is_reversed = False

        self.__attr = {
            'source': source.get_name(),
            'target': target.get_name(),
            'source-concept': source_concept.get_name() if source_concept else None,
            'target-concept': target_concept.get_name() if target_concept else None,
            'description': description,
            'predicate': type_predicate,
            'confidence': int(confidence) if confidence is not None else None,
        }

        self.__event_type = event_type  # type: edxml.ontology.EventType

    def __repr__(self):
        return f"{self.__attr['source']} {self.get_predicate()} {self.__attr['target']}"

    def __str__(self):
        return f"{self.__attr['source']}=>{self.__attr['target']}"

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self.__event_type._child_modified_callback()
        return self

    def _set_attr(self, key, value):
        if self.__attr[key] != value:
            self.__attr[key] = value
            self._child_modified_callback()

    def is_reversed(self):
        """
        Returns True when the direction of the relation has been reversed
        compared to how it is originally defined. Returns False otherwise.

        Returns:
            bool:
        """
        return self._is_reversed

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
        return self.__attr['source']

    def get_target(self):
        """

        Returns the target property.

        Returns:
          str:
        """
        return self.__attr['target']

    def get_source_concept(self):
        """

        Returns the source concept.

        Returns:
          str:
        """
        return self.__attr['source-concept']

    def get_target_concept(self):
        """

        Returns the target concept.

        Returns:
          str:
        """
        return self.__attr['target-concept']

    def get_description(self):
        """

        Returns the relation description.

        Returns:
          str:
        """
        return self.__attr['description'] or f"[[{self.__attr['source']}]] is described as [[{self.__attr['target']}]]"

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
        return self.__attr['predicate'] or 'is described as'

    def get_confidence(self):
        """

        Returns the relation confidence.

        Returns:
          int:
        """
        return self.__attr['confidence'] or 10

    def evaluate_description(self, event_properties, capitalize=True, colorize=False, ignore_value_errors=False):
        """

        Evaluates the description template of the relation using specified
        event properties, returning the result.

        Optionally, the output can be colorized. At his time this means that,
        when printed on the terminal, the objects in the evaluated string will
        be displayed using bold white characters.

        When rendering of object values fails because the value is not valid for
        its object type an exception is raised unless ignore_value_errors is enabled.

        Args:
          event_properties (Dict[str, Set]): the event properties to use
          capitalize (bool): Capitalize evaluated template yes or no
          colorize (bool): Colorize output or not
          ignore_value_errors (bool): Ignore object value errors yes or no

        Returns:
          str:
        """
        return template.Template(self.get_description()).evaluate(
            self.__event_type, event_properties=event_properties, event_attachments={},
            capitalize=capitalize, colorize=colorize, ignore_value_errors=ignore_value_errors
        )

    def because(self, reason):
        """

        Sets the relation description to specified string,
        which should contain placeholders for the values
        of both related properties.

        Args:
          reason (Optional[str]): Relation description

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
          description (Optional[str]): Relation description

        Returns:
          edxml.ontology.PropertyRelation: The PropertyRelation instance

        """
        return self.because(description)

    def set_predicate(self, predicate):
        """

        Sets the relation predicate to specified string.

        Args:
          predicate (Optional[str]): Relation predicate

        Returns:
          edxml.ontology.PropertyRelation: The PropertyRelation instance

        """
        self._set_attr('predicate', predicate)
        return self

    def set_confidence(self, confidence):
        """

        Configure the relation confidence

        Args:
         confidence (Optional[int]): Relation confidence [1,10]

        Returns:
          edxml.ontology.PropertyRelation: The PropertyRelation instance
        """

        self._set_attr('confidence', int(confidence) if confidence is not None else None)
        return self

    def validate(self):
        """

        Checks if the property relation is valid. It only looks
        at the attributes of the relation itself. Since it does
        not have access to the full ontology, the context of
        the relation is not considered. For example, it does not
        check if the properties in the relation actually exist.

        Raises:
          EDXMLOntologyValidationError
        Returns:
          edxml.ontology.PropertyRelation: The PropertyRelation instance

        """
        if not re.match(edxml.ontology.EventProperty.EDXML_PROPERTY_NAME_PATTERN, self.__attr['source']):
            raise EDXMLOntologyValidationError(
                'Invalid property name in property relation: "%s"' % self.__attr['source'])

        if not re.match(edxml.ontology.EventProperty.EDXML_PROPERTY_NAME_PATTERN, self.__attr['target']):
            raise EDXMLOntologyValidationError(
                'Invalid property name in property relation: "%s"' % self.__attr['target'])

        if self.__attr['description'] is not None:
            if not len(self.__attr['description']) <= 255:
                raise EDXMLOntologyValidationError(
                    'Property relation description is too long: "%s"' % self.__attr['description']
                )

            if normalize_xml_token(self.__attr['description']) != self.__attr['description']:
                raise EDXMLOntologyValidationError(
                    'Property relation description contains illegal whitespace characters: "%s"' %
                    self.__attr['description']
                )

            try:
                edxml.Template(self.__attr['description']).validate(self.__event_type)
            except EDXMLOntologyValidationError as e:
                raise EDXMLOntologyValidationError(
                    'Relation between properties %s and %s has an invalid description: "%s" The validator said: %s' % (
                        self.__attr['source'], self.__attr['target'],
                        self.__attr['description'], str(e)
                    )
                )

        if self.__attr['predicate'] is not None:
            if not len(self.__attr['predicate']) <= 32:
                raise EDXMLOntologyValidationError(
                    'Property relation predicate is too long: "%s"' % self.__attr['predicate']
                )

            if normalize_xml_token(self.__attr['predicate']) != self.__attr['predicate']:
                raise EDXMLOntologyValidationError(
                    'Property relation predicate contains illegal whitespace characters: "%s"' % (
                        self.__attr['predicate']
                    )
                )

        if self._type not in ['inter', 'intra', 'name', 'description', 'container', 'original', 'other']:
            raise EDXMLOntologyValidationError('Invalid property relation type: "%s"' % self._type)

        if self.__attr['confidence'] is not None:
            if self.__attr['confidence'] < 1 or self.__attr['confidence'] > 10:
                raise EDXMLOntologyValidationError(
                    'Invalid property relation confidence: "%d"' % self.__attr['confidence']
                )

        if self.get_type() in ('inter', 'intra'):
            if self.__attr.get('source-concept') is None or self.__attr.get('target-concept') is None:
                raise EDXMLOntologyValidationError(
                    'The %s-concept relation between properties %s and %s does not specify both related concepts.' %
                    (self.get_type(), self.__attr['source'], self.__attr['target'])
                )
        else:
            if self.__attr.get('source-concept') is not None or self.__attr.get('target-concept') is not None:
                raise EDXMLOntologyValidationError(
                    'The "%s" relation between properties %s and %s must not specify any concepts.' %
                    (self.get_type(), self.__attr['source'], self.__attr['target'])
                )

        if self.get_type() in ['name', 'description', 'container', 'original']:
            if self.__attr['description'] is not None:
                raise EDXMLOntologyValidationError(
                    'The %s relation between properties %s and %s in event type %s '
                    'must not have a relation description.' %
                    (self.get_type(), self.get_source(), self.get_target(), self.__event_type.get_name())
                )
            if self.__attr['predicate'] is not None:
                raise EDXMLOntologyValidationError(
                    'The %s relation between properties %s and %s in event type %s '
                    'must not have a relation predicate.' %
                    (self.get_type(), self.get_source(), self.get_target(), self.__event_type.get_name())
                )
            if self.__attr['confidence'] is not None:
                raise EDXMLOntologyValidationError(
                    'The %s relation between properties %s and %s in event type %s '
                    'must not have a relation confidence.' %
                    (self.get_type(), self.get_source(), self.get_target(), self.__event_type.get_name())
                )
            if self.__event_type.get_properties()[self.get_source()].is_multi_valued():
                raise EDXMLOntologyValidationError(
                    'The %s relation between properties %s and %s in event type %s '
                    'must not have a multi-valued source property.' %
                    (self.get_type(), self.get_source(), self.get_target(), self.__event_type.get_name())
                )
            if self.get_type() in ['original']:
                if self.__event_type.get_properties()[self.get_target()].is_multi_valued():
                    raise EDXMLOntologyValidationError(
                        'The %s relation between properties %s and %s in event type %s '
                        'must not have a multi-valued target property.' %
                        (self.get_type(), self.get_source(), self.get_target(), self.__event_type.get_name())
                    )

        # Verify that inter / intra relations are defined between
        # properties that refer to concepts, in the right way
        if self.get_type() in ('inter', 'intra'):
            source_concepts = self.__event_type[self.get_source()].get_concept_associations()
            target_concepts = self.__event_type[self.get_target()].get_concept_associations()

            if len(source_concepts) == 0 or len(target_concepts) == 0:
                raise EDXMLOntologyValidationError(
                    'Both properties %s and %s in the inter/intra-concept relation in event type %s must '
                    'refer to a concept.' % (self.get_source(), self.get_target(), self.__event_type.get_name())
                )

            if self.get_source_concept() not in source_concepts:
                raise EDXMLOntologyValidationError(
                    'The %s-concept relation between properties %s and %s refers to source concept %s. '
                    'However, property %s is not associated with that concept.' %
                    (self.get_type(), self.__attr['source'], self.__attr['target'],
                     self.__attr['source-concept'], self.__attr['source'])
                )

            if self.get_target_concept() not in target_concepts:
                raise EDXMLOntologyValidationError(
                    'The %s-concept relation between properties %s and %s refers to target concept %s. '
                    'However, property %s is not associated with that concept.' %
                    (self.get_type(), self.__attr['source'], self.__attr['target'],
                     self.__attr['target-concept'], self.__attr['target'])
                )

        return self

    @classmethod
    def create_from_xml(cls, relation_element, event_type, ontology):
        try:
            source = relation_element.attrib['source']
        except KeyError:
            raise EDXMLOntologyValidationError(
                'Failed to parse definition of event type "%s": '
                'It is missing the source property attribute (source)' % event_type.get_name()
            )
        try:
            target = relation_element.attrib['target']
        except KeyError:
            raise EDXMLOntologyValidationError(
                'Failed to parse definition of event type "%s": '
                'It is missing the target property attribute (target)' % event_type.get_name()
            )

        for property_name in (source, target):
            if property_name not in event_type:
                raise EDXMLOntologyValidationError(
                    'Event type "%s" contains a property relation referring to property "%s", which is not defined.' %
                    (event_type.get_name(), property_name))

        source_concept_name = relation_element.attrib.get('source-concept')
        target_concept_name = relation_element.attrib.get('target-concept')

        source_concept = ontology.get_concept(source_concept_name)
        target_concept = ontology.get_concept(target_concept_name)

        if source_concept_name is not None and source_concept is None:
            raise EDXMLOntologyValidationError(
                'Failed to instantiate a property relation, source concept "%s" does not exist.' % source_concept_name
            )
        if target_concept_name is not None and target_concept is None:
            raise EDXMLOntologyValidationError(
                'Failed to instantiate a property relation, target concept "%s" does not exist.' % target_concept_name
            )

        try:
            return cls(
                event_type,
                event_type[source],
                event_type[target],
                source_concept,
                target_concept,
                relation_element.attrib.get('description'),
                relation_element.tag[24:],
                relation_element.attrib.get('predicate'),
                relation_element.attrib.get('confidence')
            )
        except (ValueError, KeyError) as e:
            raise EDXMLOntologyValidationError(
                "Failed to instantiate a property relation from the following definition:\n" +
                etree.tostring(relation_element, pretty_print=True, encoding='unicode') +
                "\nMissing attribute or illegal value: " + str(e)
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
            raise EDXMLOntologyValidationError("Attempt to compare property relations from two different event types")

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

        if old.get_type() != new.get_type():
            # The relation types are different, no upgrade possible.
            equal = is_valid_upgrade = False

        # Compare attributes that cannot produce illegal upgrades because they can
        # be changed freely between versions. We only need to know if they changed.

        for attr in ['description', 'predicate', 'confidence']:
            equal &= old.__attr[attr] == new.__attr[attr]

        if equal:
            return 0

        if is_valid_upgrade and versions_differ:
            return -1 if other_is_newer else 1

        event_type_element_upgrade_error('property relation', old, new, old.__event_type, new.__event_type)

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
            if self._type not in ['name', 'description', 'container', 'original']:
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

        attribs['confidence'] = '%d' % self.get_confidence()

        if self._type not in ['inter', 'intra']:
            del attribs['source-concept']
            del attribs['target-concept']

        if self._type in ['name', 'description', 'container', 'original']:
            del attribs['description']
            del attribs['confidence']
            del attribs['predicate']

        return etree.Element(self._type, attribs)

    def reversed(self):
        reversed = copy(self)
        reversed.__attr = dict(reversed.__attr)

        source_concept = reversed.__attr['source-concept']
        target_concept = reversed.__attr['target-concept']
        source = reversed.__attr['source']
        target = reversed.__attr['target']

        reversed.__attr['source-concept'] = target_concept
        reversed.__attr['target-concept'] = source_concept
        reversed.__attr['source'] = target
        reversed.__attr['target'] = source

        reversed._is_reversed = not reversed._is_reversed

        return reversed
