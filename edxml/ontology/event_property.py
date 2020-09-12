# -*- coding: utf-8 -*-

import re
import edxml.ontology

from edxml.error import EDXMLValidationError
from lxml import etree
from typing import Dict
from edxml.ontology import OntologyElement, normalize_xml_token


class EventProperty(OntologyElement):
    """
    Class representing an EDXML event property
    """

    EDXML_PROPERTY_NAME_PATTERN = re.compile('^[a-z0-9-]{1,64}$')

    MERGE_MATCH = 'match'
    """Merge strategy 'match'"""
    MERGE_DROP = 'drop'
    """Merge strategy 'drop'"""
    MERGE_ADD = 'add'
    """Merge strategy 'add'"""
    MERGE_SET = 'set'
    """Merge strategy 'set'"""
    MERGE_REPLACE = 'replace'
    """Merge strategy 'replace'"""
    MERGE_MIN = 'min'
    """Merge strategy 'min'"""
    MERGE_MAX = 'max'
    """Merge strategy 'max'"""

    def __init__(self, event_type, name, object_type, description=None, unique=False, optional=False, multivalued=False,
                 merge='drop', similar=''):

        self.__attr = {
            'name': name,
            'object-type': object_type.get_name(),
            'description': description or name.replace('-', ' '),
            'unique': bool(unique),
            'optional': bool(optional),
            'multivalued': bool(multivalued),
            'merge': merge,
            'similar': similar
        }

        self.__event_type = event_type  # type: edxml.ontology.EventType
        self.__object_type = object_type  # type: edxml.ontology.ObjectType
        self.__data_type = object_type.get_data_type()  # type: edxml.ontology.DataType
        self.__concepts = {}      # type: Dict[str, edxml.ontology.PropertyConcept]

    def __repr__(self):
        return f"{self.__event_type.get_name()}::{self.__attr['name']} (object type {self.__attr['object-type']})"

    def __str__(self):
        return self.__attr['name']

    def _set_event_type(self, event_type):
        self.__event_type = event_type
        return self

    def _child_modified_callback(self):
        """Callback for change tracking"""
        self.__event_type._child_modified_callback()
        return self

    def _set_attr(self, key, value):
        if self.__attr[key] != value:
            self.__attr[key] = value
            self._child_modified_callback()

    def __getattr__(self, relation_type_predicate):
        """

        Magic method allowing to define property relations in
        a way that looks like::

          sender.communicates_with('recipient').because(...)

        The return value is a lambda that wraps the relate_to()
        method. The call parameters are identical to those of
        relate_to() except for the predicate parameter, which
        is skipped. The relation predicate is derived from the
        method name by replacing underscores with spaces. So
        in the above example, the relation predicate would
        become "communicates with".

        Args:
            relation_type_predicate (str):

        Returns:
          Callable[[str, Optional[str], Optional[int], Optional[bool]], edxml.ontology.PropertyRelation]
        """
        if relation_type_predicate.startswith('__'):
            # We do not want to make callers think we have
            # any magic methods that we actually do not have.
            raise AttributeError
        return lambda *args, **kwargs: self.relate_to(relation_type_predicate.replace('_', ' '), *args, **kwargs)

    def get_name(self):
        """

        Returns the property name.

        Returns:
          str:
        """
        return self.__attr['name']

    def get_description(self):
        """

        Returns the property description.

        Returns:
          str:
        """
        return self.__attr['description']

    def get_object_type_name(self):
        """

        Returns the name of the associated object type.

        Returns:
          str:
        """
        return self.__attr['object-type']

    def get_merge_strategy(self):
        """

        Returns the merge strategy.

        Returns:
          str:
        """
        return self.__attr['merge']

    def get_similar_hint(self):
        """

        Get the EDXML 'similar' attribute.

        Returns:
          str:
        """
        return self.__attr['similar']

    def get_object_type(self):
        """

        Returns the ObjectType instance that is associated
        with the property.

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        return self.__object_type

    def get_data_type(self):
        """

        Returns the DataType instance that is associated
        with the object type of the property.

        Returns:
          edxml.ontology.DataType: The DataType instance
        """
        return self.__data_type

    def get_concept_associations(self):
        """

        Returns a dictionary containing the names of all associated
        concepts as keys and the PropertyConcept instances as values.

        Returns:
          Dict[str,edxml.ontology.PropertyConcept]:
        """
        return self.__concepts

    def relate_to(self, type_predicate, target_property_name, reason=None, confidence=10, directed=True):
        """

        Creates and returns a relation between this property and
        the specified target property.

        When no reason is specified, the reason is constructed by
        wrapping the type predicate with the place holders for
        the two properties.

        Args:
          type_predicate (str): free form predicate
          target_property_name (str): Name of the related property
          reason (str): Relation description, with property placeholders
          confidence (int): Relation confidence [00,10]
          directed (bool): Directed relation True / False

        Returns:
          edxml.ontology.EventPropertyRelation: The EventPropertyRelation instance

        """
        return self.__event_type.create_relation(self.get_name(), target_property_name, reason or '[[%s]] %s [[%s]]' % (
            self.get_name(), type_predicate, target_property_name), 'other', type_predicate, confidence=confidence,
                                                 directed=directed)

    def relate_inter(self, type_predicate, target_property_name, source_concept_name=None, target_concept_name=None,
                     reason=None, confidence=10, directed=True):
        """

        Creates and returns a relation between this property and
        the specified target property. The relation is an 'inter'
        relation, indicating that the related objects belong to
        different, related concept instances.

        When any of the related properties is associated with more
        than one concept, you are required to specify which of the
        associated concepts is involved in the relation.

        When no reason is specified, the reason is constructed by
        wrapping the type predicate with the place holders for
        the two properties.

        Args:
          type_predicate (str): free form predicate
          target_property_name (str): Name of the related property
          source_concept_name (str): Name of the source concept
          target_concept_name (str): Name of the target concept
          reason (str): Relation description, with property placeholders
          confidence (int): Relation confidence [0,10]
          directed (bool): Directed relation True / False

        Returns:
          edxml.ontology.EventPropertyRelation: The EventPropertyRelation instance

        """
        return self.__event_type.create_relation(self.get_name(), target_property_name, reason or '[[%s]] %s [[%s]]' % (
            self.get_name(), type_predicate, target_property_name), 'inter',
            type_predicate, source_concept_name, target_concept_name, confidence, directed
        )

    def relate_intra(self, type_predicate, target_property_name, source_concept_name=None, target_concept_name=None,
                     reason=None, confidence=10, directed=True):
        """

        Creates and returns a relation between this property and
        the specified target property. The relation is an 'intra'
        relation, indicating that the related objects belong to
        the same concept instance.

        When no reason is specified, the reason is constructed by
        wrapping the type predicate with the place holders for
        the two properties.

        Args:
          target_property_name (str): Name of the related property
          reason (str): Relation description, with property placeholders
          type_predicate (str): free form predicate
          confidence (float): Relation confidence [0,10]
          directed (bool): Directed relation True / False

        Returns:
          edxml.ontology.EventPropertyRelation: The EventPropertyRelation instance

        """
        return self.__event_type.create_relation(self.get_name(), target_property_name, reason or '[[%s]] %s [[%s]]' % (
            self.get_name(), type_predicate, target_property_name), 'intra', type_predicate, source_concept_name,
                                                 target_concept_name, confidence, directed)

    def add_associated_concept(self, concept_association):
        """
        Add the specified concept association.

        Args:
          concept_association (edxml.ontology.PropertyConcept): Property concept association
        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self.__concepts[concept_association.get_concept_name()] = concept_association
        return self

    def set_merge_strategy(self, merge_strategy):
        """

        Set the merge strategy of the property. This should
        be one of the MERGE_* attributes of this class.

        Automatically makes the property mandatory or single
        valued when the merge strategy requires it.

        Args:
          merge_strategy (str): The merge strategy

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._set_attr('merge', merge_strategy)

        if merge_strategy == 'match':
            self._set_attr('unique', True)

        if merge_strategy in ('min', 'max', 'replace'):
            self._set_attr('multivalued', False)

        if merge_strategy in ('min', 'max'):
            self._set_attr('optional', False)

        return self

    def set_description(self, description):
        """

        Set the description of the property. This should
        be really short, indicating which role the object
        has in the event type.

        Args:
          description (str): The property description

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._set_attr('description', description)
        return self

    def make_optional(self):
        """
        Make the property optional.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._set_attr('optional', True)
        return self

    def make_mandatory(self):
        """
        Make the property mandatory.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._set_attr('optional', False)
        return self

    def set_optional(self, is_optional):
        """
        Set the optional flag for the property to True (property is optional)
        or False (property is mandatory).

        Args:
            is_optional (bool):

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._set_attr('optional', is_optional)
        return self

    def make_multivalued(self):
        """
        Make the property multi-valued.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._set_attr('multivalued', True)
        return self

    def unique(self):
        """

        Mark property as a unique property, which also sets
        the merge strategy to 'match' and marks it as mandatory.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._set_attr('unique', True)
        self._set_attr('merge', 'match')
        self._set_attr('optional', False)
        return self

    def is_unique(self):
        """

        Returns True if property is unique, returns False otherwise

        Returns:
          bool:
        """
        return self.__attr['unique']

    def is_optional(self):
        """

        Returns True if property is optional, returns False otherwise

        Returns:
          bool:
        """
        return self.__attr['optional']

    def is_mandatory(self):
        """

        Returns True if property is mandatory, returns False otherwise

        Returns:
          bool:
        """
        return not self.__attr['optional']

    def is_multi_valued(self):
        """

        Returns True if property is multi-valued, returns False otherwise

        Returns:
          bool:
        """
        return self.__attr['multivalued']

    def is_single_valued(self):
        """

        Returns True if property is single-valued, returns False otherwise

        Returns:
          bool:
        """
        return not self.__attr['multivalued']

    def identifies(self, concept_name, confidence=10, cnp=128):
        """

        Marks the property as an identifier for specified
        concept, with specified confidence.

        Args:
          concept_name (str): concept name
          confidence (int): concept identification confidence [0, 10]
          cnp (int): concept naming priority [0,255]

        Returns:
          edxml.ontology.PropertyConcept: The PropertyConcept association
        """
        self.__concepts[concept_name] = edxml.ontology.PropertyConcept(
            self.__event_type, self, concept_name, confidence=confidence, naming_priority=cnp
        )
        return self.__concepts[concept_name]

    def set_multi_valued(self, is_multivalued):
        """
        Configures the property as multi-valued or single-valued

        Args:
            is_multivalued (bool):

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance

        """
        self._set_attr('multivalued', is_multivalued)
        return self

    def hint_similar(self, similarity):
        """

        Set the EDXML 'similar' attribute.

        Args:
          similarity (str): similar attribute string

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._set_attr('similar', similarity)
        return self

    def merge_add(self):
        """

        Set merge strategy to 'add'.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self.set_merge_strategy('add')
        return self

    def merge_replace(self):
        """

        Set merge strategy to 'replace'.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self.set_merge_strategy('replace')
        return self

    def merge_set(self):
        """

        Set merge strategy to 'set'.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self.set_merge_strategy('set')
        return self

    def merge_drop(self):
        """

        Set merge strategy to 'drop', which is
        the default merge strategy.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self.set_merge_strategy('drop')
        return self

    def merge_min(self):
        """

        Set merge strategy to 'min'.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self.set_merge_strategy('min')
        return self

    def merge_max(self):
        """

        Set merge strategy to 'max'.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self.set_merge_strategy('max')
        return self

    def _validate_attributes(self):

        if not re.match(self.EDXML_PROPERTY_NAME_PATTERN, self.__attr['name']):
            raise EDXMLValidationError(
                'Invalid property name in property definition: "%s"' % self.__attr['name'])

        if not re.match(edxml.ontology.ObjectType.NAME_PATTERN, self.__attr['object-type']):
            raise EDXMLValidationError(
                'Invalid object type name in property definition: "%s"' % self.__attr['object-type'])

        if not len(self.__attr['description']) <= 128:
            raise EDXMLValidationError(
                'Property description is too long: "%s"' % self.__attr['description'])

        if normalize_xml_token(self.__attr['description']) != self.__attr['description']:
            raise EDXMLValidationError(
                'The description of property "%s" of event type "%s" contains illegal whitespace characters: "%s"' % (
                    self.__event_type.get_name(), self.__attr['name'], self.__attr['description'])
            )

        if not len(self.__attr['similar']) <= 64:
            raise EDXMLValidationError(
                'Property attribute is too long: similar="%s"' % self.__attr['similar'])

        if normalize_xml_token(self.__attr['similar']) != self.__attr['similar']:
            raise EDXMLValidationError(
                'The similar attribute of property "%s" of event type "%s" contains illegal whitespace '
                'characters: "%s"' % (
                    self.__event_type.get_name(), self.__attr['name'], self.__attr['description'])
            )

    def validate(self):
        """

        Checks if the property definition is valid. It only looks
        at the attributes of the property itself. Since it does
        not have access to the full ontology, the context of
        the property is not considered. For example, it does not
        check if the object type in the property actually exist.

        Raises:
          EDXMLValidationError
        Returns:
          edxml.ontology.EventProperty: The EventProperty instance

        """
        self._validate_attributes()

        if self.__attr['merge'] in ('min', 'max') and self.is_optional():
            raise EDXMLValidationError(
                'Property "%s" cannot be optional due to its merge strategy' % self.__attr[
                    'name']
            )

        if self.__attr['merge'] in ('min', 'max', 'replace') and self.is_multi_valued():
            raise EDXMLValidationError(
                'Property "%s" cannot be multivalued due to its merge strategy' % self.__attr[
                    'name']
            )

        if not self.__attr['merge'] in ('drop', 'add', 'replace', 'set', 'min', 'max', 'match'):
            raise EDXMLValidationError('Invalid property merge strategy: "%s"' % self.__attr['merge'])

        # Check if merge strategies make sense for the
        # configured property merge strategies
        if self.get_merge_strategy() in ('min', 'max'):
            if not self.get_data_type().is_numerical():
                if not self.get_data_type().is_datetime():
                    if self.get_data_type().get_family() != 'sequence':
                        raise EDXMLValidationError(
                            'Property "%s" of event type "%s" has data type %s, which '
                            'cannot be used with merge strategy %s.' % (
                                self.get_name(), self.__event_type.get_name(), self.get_data_type(),
                                self.get_merge_strategy()
                            )
                        )

        if self.is_unique():
            if self.get_merge_strategy() != 'match':
                raise EDXMLValidationError(
                    'Unique property "%s" of event type "%s" does not have its merge strategy set to "match".' %
                    (self.get_name(), self.__event_type.get_name())
                )
        else:
            if self.get_merge_strategy() == 'match':
                raise EDXMLValidationError(
                    'Property "%s" of event type "%s" is not unique but it does '
                    'have its merge strategy set to "match".' %
                    (self.get_name(), self.__event_type.get_name())
                )

        for concept_association in self.__concepts.values():
            concept_association.validate()

        return self

    @classmethod
    def create_from_xml(cls, property_element, ontology, parent_event_type):
        try:
            name = property_element.attrib['name']
            object_type_name = property_element.attrib['object-type']
            object_type = ontology.get_object_type(object_type_name)

            if not object_type:
                raise EDXMLValidationError(
                    'Property "%s" of event type "%s" refers to undefined object type "%s".' %
                    (name, parent_event_type.get_name(), object_type_name)
                )

            property = cls(
                parent_event_type,
                property_element.attrib['name'],
                object_type,
                property_element.attrib['description'],
                property_element.get('unique', 'false') == 'true',
                property_element.get('optional') == 'true',
                property_element.get('multivalued') == 'true',
                property_element.get('merge', 'drop'),
                property_element.get('similar', '')
            )
        except KeyError as e:
            raise EDXMLValidationError(
                "Failed to instantiate an event property from the following definition:\n" +
                etree.tostring(property_element, pretty_print=True, encoding='unicode') +
                "\nError message: " + str(e)
            )

        concept_names = []
        for element in property_element:
            if element.tag == '{http://edxml.org/edxml}property-concept':
                property_concept = edxml.ontology.PropertyConcept.create_from_xml(element, parent_event_type, property)
                if property_concept.get_concept_name() in concept_names:
                    raise EDXMLValidationError(
                        'EDXML <property-concept> element contains duplicate definition of "%s"' %
                        property_concept.get_concept_name()
                    )
                property.add_associated_concept(property_concept)
                concept_names.append(property_concept.get_concept_name())

        return property

    def __cmp__(self, other):

        if not isinstance(other, type(self)):
            raise TypeError("Cannot compare different types of ontology elements.")

        # Note that property definitions are part of event type definitions,
        # so we look at the version of the event type for which this property is defined.
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
            raise EDXMLValidationError("Attempt to compare property definitions from two different event types")

        if old.get_name() != new.get_name():
            raise ValueError("Properties with different names are not comparable.")

        # Check for illegal upgrade paths:

        if old.__object_type.get_name() != new.__object_type.get_name():
            # The object types differ, no upgrade possible.
            equal = is_valid_upgrade = False

        if old.get_merge_strategy() != new.get_merge_strategy():
            # The merge strategies differ, no upgrade possible.
            equal = is_valid_upgrade = False

        if old.is_unique() != new.is_unique():
            # Property uniqueness differs, no upgrade possible.
            equal = is_valid_upgrade = False

        if old.is_multi_valued() != new.is_multi_valued():
            # Single-valued properties can become multi-valued, while a multi-valued
            # property cannot become single-valued.
            equal = False
            is_valid_upgrade &= new.is_multi_valued()

        if old.is_optional() != new.is_optional():
            # Mandatory properties can become optional, while an optional property
            # cannot become mandatory.
            equal = False
            is_valid_upgrade &= new.is_optional()

        if old.get_concept_associations().keys() != new.get_concept_associations().keys():
            # Adding a concept association is possible, removing one is not.
            equal = False
            missing_concept_names = set(old.get_concept_associations().keys()) - \
                set(new.get_concept_associations().keys())
            is_valid_upgrade &= versions_differ and len(missing_concept_names) == 0

        for concept_name, associations in new.get_concept_associations().items():
            if concept_name in old.get_concept_associations():
                if old.get_concept_associations()[concept_name] != new.get_concept_associations()[concept_name]:
                    # Association definitions differ, check that new definition is
                    # a valid upgrade of the old definition.
                    equal = False
                    is_valid_upgrade &= new.get_concept_associations()[concept_name] > \
                        old.get_concept_associations()[concept_name]

        # Compare attributes that cannot produce illegal upgrades because they can
        # be changed freely between versions. We only need to know if they changed.

        for attr in ['description', 'similar']:
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
            "Definitions of event type {} are {} due to the following difference in property definitions:\n"
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

    def update(self, event_property):
        """

        Updates the event property to match the EventProperty
        instance passed to this method, returning the
        updated instance.

        Args:
          event_property (edxml.ontology.EventProperty): The new EventProperty instance

        Returns:
          edxml.ontology.EventProperty: The updated EventProperty instance

        """
        if event_property > self:
            # The new definition is indeed newer. Update self.
            self.set_description(event_property.get_description())
            self.hint_similar(event_property.get_similar_hint())
            self.set_optional(event_property.is_optional())
            self.set_multi_valued(event_property.is_multi_valued())

            for concept_name, association in self.__concepts.items():
                association.update(event_property.get_concept_associations()[concept_name])

            new_concept_names = \
                set(event_property.get_concept_associations().keys()) - \
                set(self.get_concept_associations().keys())

            for concept_name in new_concept_names:
                self.add_associated_concept(event_property.get_concept_associations()[concept_name])

            self.__event_type = event_property.__event_type

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <property> tag for this event property.

        Returns:
          etree.Element: The element

        """

        attribs = dict(self.__attr)

        attribs['unique'] = 'true' if self.__attr['unique'] else 'false'
        attribs['optional'] = 'true' if self.__attr['optional'] else 'false'
        attribs['multivalued'] = 'true' if self.__attr['multivalued'] else 'false'

        if attribs['similar'] == '':
            del attribs['similar']

        prop = etree.Element('property', attribs)

        for concept_name in sorted(self.__concepts.keys()):
            prop.append(self.__concepts[concept_name].generate_xml())

        return prop
