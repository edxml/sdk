# -*- coding: utf-8 -*-

import re
import edxml.ontology

from edxml.EDXMLBase import EDXMLValidationError
from lxml import etree

from edxml.ontology import OntologyElement


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
    MERGE_REPLACE = 'replace'
    """Merge strategy 'replace'"""
    MERGE_MIN = 'min'
    """Merge strategy 'min'"""
    MERGE_MAX = 'max'
    """Merge strategy 'max'"""

    def __init__(self, event_type, name, object_type, description=None, concept_name=None, concept_confidence=0,
                 cnp=128, unique=False, optional=True, multivalued=True, merge='drop', similar=''):

        self.__attr = {
            'name': name,
            'object-type': object_type.get_name(),
            'description': description or name.replace('-', ' '),
            'concept': concept_name,
            'concept-confidence': int(concept_confidence),
            'unique': bool(unique),
            'optional': bool(optional),
            'multivalued': bool(multivalued),
            'cnp': int(cnp),
            'merge': merge,
            'similar': similar
        }

        self.__event_type = event_type  # type: edxml.ontology.EventType
        self.__object_type = object_type  # type: edxml.ontology.ObjectType
        self.__data_type = object_type.get_data_type()  # type: edxml.ontology.ObjectType

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

    def get_concept_confidence(self):
        """

        Returns the concept identification confidence.

        Returns:
          int:
        """
        return self.__attr['concept-confidence']

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

    def get_concept_naming_priority(self):
        """

        Returns concept naming priority of the event property.

        Returns:
          int:
        """

        return self.__attr['cnp']

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
            self.get_name(), type_predicate, target_property_name), 'other', type_predicate, confidence, directed)

    def relate_inter(self, type_predicate, target_property_name, reason=None, confidence=10, directed=True):
        """

        Creates and returns a relation between this property and
        the specified target property. The relation is an 'inter'
        relation, indicating that the related objects belong to
        different, related concept instances.

        When no reason is specified, the reason is constructed by
        wrapping the type predicate with the place holders for
        the two properties.

        Args:
          type_predicate (str): free form predicate
          target_property_name (str): Name of the related property
          reason (str): Relation description, with property placeholders
          confidence (int): Relation confidence [0,10]
          directed (bool): Directed relation True / False

        Returns:
          edxml.ontology.EventPropertyRelation: The EventPropertyRelation instance

        """
        return self.__event_type.create_relation(self.get_name(), target_property_name, reason or '[[%s]] %s [[%s]]' % (
            self.get_name(), type_predicate, target_property_name), 'inter', type_predicate, confidence, directed)

    def relate_intra(self, type_predicate, target_property_name, reason=None, confidence=10, directed=True):
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
            self.get_name(), type_predicate, target_property_name), 'intra', type_predicate, confidence, directed)

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

        if merge_strategy in ('match', 'min', 'max', 'replace'):
            self._set_attr('multivalued', False)

        if merge_strategy in ('match', 'min', 'max'):
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

    def unique(self):
        """

        Mark property as a unique property, which also sets
        the merge strategy to 'match' and makes the property
        both mandatory and single valued.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._set_attr('unique', True)
        self._set_attr('merge', 'match')
        self._set_attr('optional', False)
        self._set_attr('multivalued', False)
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

    def identifies(self, concept_name, confidence):
        """

        Marks the property as an identifier for specified
        concept, with specified confidence.

        Args:
          concept_name (str): concept name
          confidence (int): concept identification confidence [0, 10]

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._set_attr('concept', concept_name)
        self._set_attr('concept-confidence', int(confidence))
        return self

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

    def set_concept_naming_priority(self, priority):
        """

        Configure the concept naming priority of
        the property. When the value is not explicitly
        specified using this method, it's value is 128.

        Args:
          priority (int): The EDXML cnp attribute

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._set_attr('cnp', int(priority))
        return self

    def get_concept_name(self):
        """

        Returns the name of the concept if the property is an
        identifier for a concept, returns None otherwise.

        Returns:
          str:
        """
        return self.__attr['concept']

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
        if not re.match(self.EDXML_PROPERTY_NAME_PATTERN, self.__attr['name']):
            raise EDXMLValidationError(
                'Invalid property name in property definition: "%s"' % self.__attr['name'])

        if not re.match(edxml.ontology.ObjectType.NAME_PATTERN, self.__attr['object-type']):
            raise EDXMLValidationError(
                'Invalid object type name in property definition: "%s"' % self.__attr['object-type'])

        if not len(self.__attr['description']) <= 128:
            raise EDXMLValidationError(
                'Property description is too long: "%s"' % self.__attr['description'])

        if not len(self.__attr['similar']) <= 64:
            raise EDXMLValidationError(
                'Property attribute is too long: similar="%s"' % self.__attr['similar'])

        if not 0 <= int(self.__attr['cnp']) < 256:
            raise EDXMLValidationError(
                'Property "%s" has an invalid concept naming priority: "%d"' % (
                    self.__attr['name'], self.__attr['cnp'])
            )

        if self.is_unique():
            if self.is_optional():
                raise EDXMLValidationError(
                    'Property "%s" is unique and optional at the same time' % self.__attr['name']
                )
            if self.is_multi_valued():
                raise EDXMLValidationError(
                    'Property "%s" is unique and multivalued at the same time' % self.__attr[
                        'name']
                )

        if self.__attr['merge'] in ('match', 'min', 'max') and self.is_optional():
            raise EDXMLValidationError(
                'Property "%s" cannot be optional due to its merge strategy' % self.__attr[
                    'name']
            )

        if self.__attr['merge'] in ('match', 'min', 'max', 'replace') and self.is_multi_valued():
            raise EDXMLValidationError(
                'Property "%s" cannot be multivalued due to its merge strategy' % self.__attr[
                    'name']
            )

        if not self.__attr['merge'] in ('drop', 'add', 'replace', 'min', 'max', 'match'):
            raise EDXMLValidationError(
                'Invalid property merge strategy: "%s"' % self.__attr['merge'])

        if self.__attr['concept-confidence'] < 0 or self.__attr['concept-confidence'] > 10:
            raise EDXMLValidationError(
                'Invalid property concept confidence: "%d"' % self.__attr['concept-confidence'])

        return self

    @classmethod
    def create_from_xml(cls, property_element, ontology, parent_event_type):
        name = property_element.attrib['name']
        object_type_name = property_element.attrib['object-type']
        object_type = ontology.get_object_type(object_type_name)

        if not object_type:
            raise EDXMLValidationError(
                'Property "%s" of event type "%s" refers to undefined object type "%s".' %
                (name, parent_event_type.get_name(), object_type_name)
            )

        return cls(
            parent_event_type,
            property_element.attrib['name'],
            object_type,
            property_element.attrib['description'],
            property_element.get('concept'),
            property_element.get('concept-confidence', 0),
            int(property_element.get('cnp', 0)),
            property_element.get('unique', 'false') == 'true',
            property_element.get('optional') == 'true',
            property_element.get('multivalued') == 'true',
            property_element.get('merge', 'drop'),
            property_element.get('similar', '')
        )

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
        if self.__attr['name'] != event_property.get_name():
            raise Exception('Attempt to update event property "%s" with event property "%s".' %
                            (self.__attr['name'], event_property.get_name()))

        if self.__attr['description'] != event_property.get_description():
            raise Exception('Attempt to update event property "%s", but descriptions do not match.' %
                            self.__attr['name'],
                            (self.__attr['description'], event_property.get_name()))

        if int(self.__attr['cnp']) != event_property.get_concept_naming_priority():
            raise Exception(
                'Attempt to update event property "%s", but Entity Naming Priorities do not match.' %
                self.__attr['name'],
                (self.__attr['cnp'], event_property.get_name()))

        if self.__attr['optional'] != event_property.is_optional():
            raise Exception(
                'Attempt to update event property "%s", but "optional" attributes do not match.' % self.__attr[
                    'name']
            )

        if self.__attr['multivalued'] != event_property.is_multi_valued():
            raise Exception(
                'Attempt to update event property "%s", but "multivalued" attributes do not match.' % self.__attr[
                    'name']
            )

        self.validate()

        return self

    def generate_xml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <property> tag for this event property.

        Returns:
          etree.Element: The element

        """

        attribs = dict(self.__attr)

        attribs['concept-confidence'] = '%d' % self.__attr['concept-confidence']
        attribs['unique'] = 'true' if self.__attr['unique'] else 'false'
        attribs['optional'] = 'true' if self.__attr['optional'] else 'false'
        attribs['multivalued'] = 'true' if self.__attr['multivalued'] else 'false'
        attribs['cnp'] = '%d' % attribs['cnp']

        if attribs['concept'] is None:
            del attribs['concept']
            del attribs['concept-confidence']
            del attribs['cnp']

        return etree.Element('property', attribs)
