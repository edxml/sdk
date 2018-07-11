# -*- coding: utf-8 -*-

import re
import edxml.ontology

from edxml.EDXMLBase import EDXMLValidationError
from lxml import etree


class EventProperty(object):
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

    def __init__(self, eventType, Name, ObjectType, Description=None, ConceptName=None, ConceptConfidence=0, Cnp=128,
                 Unique=False, Optional=True, Multivalued=True, Merge='drop', Similar=''):

        self._attr = {
            'name': Name,
            'object-type': ObjectType.GetName(),
            'description': Description or Name.replace('-', ' '),
            'concept': ConceptName,
            'concept-confidence': int(ConceptConfidence),
            'unique': bool(Unique),
            'optional': bool(Optional),
            'multivalued': bool(Multivalued),
            'cnp': int(Cnp),
            'merge': Merge,
            'similar': Similar
        }

        self._eventType = eventType  # type: edxml.ontology.EventType
        self._objectType = ObjectType  # type: edxml.ontology.ObjectType
        self._dataType = ObjectType.GetDataType()  # type: edxml.ontology.ObjectType

    def _setEventType(self, eventType):
        self._eventType = eventType
        return self

    def _childModifiedCallback(self):
        """Callback for change tracking"""
        self._eventType._childModifiedCallback()
        return self

    def _setAttr(self, key, value):
        if self._attr[key] != value:
            self._attr[key] = value
            self._childModifiedCallback()

    def GetName(self):
        """

        Returns the property name.

        Returns:
          str:
        """
        return self._attr['name']

    def GetDescription(self):
        """

        Returns the property description.

        Returns:
          str:
        """
        return self._attr['description']

    def GetObjectTypeName(self):
        """

        Returns the name of the associated object type.

        Returns:
          str:
        """
        return self._attr['object-type']

    def GetMergeStrategy(self):
        """

        Returns the merge strategy.

        Returns:
          str:
        """
        return self._attr['merge']

    def GetConceptConfidence(self):
        """

        Returns the concept identification confidence.

        Returns:
          int:
        """
        return self._attr['concept-confidence']

    def GetSimilarHint(self):
        """

        Get the EDXML 'similar' attribute.

        Returns:
          str:
        """
        return self._attr['similar']

    def GetObjectType(self):
        """

        Returns the ObjectType instance that is associated
        with the property.

        Returns:
          edxml.ontology.ObjectType: The ObjectType instance
        """
        return self._objectType

    def GetDataType(self):
        """

        Returns the DataType instance that is associated
        with the object type of the property.

        Returns:
          edxml.ontology.DataType: The DataType instance
        """
        return self._dataType

    def GetConceptNamingPriority(self):
        """

        Returns concept naming priority of the event property.

        Returns:
          int:
        """

        return self._attr['cnp']

    def RelateTo(self, TypePredicate, TargetPropertyName, Reason=None, Confidence=10, Directed=True):
        """

        Creates and returns a relation between this property and
        the specified target property.

        When no reason is specified, the reason is constructed by
        wrapping the type predicate with the place holders for
        the two properties.

        Args:
          TypePredicate (str): free form predicate
          TargetPropertyName (str): Name of the related property
          Reason (str): Relation description, with property placeholders
          Confidence (int): Relation confidence [00,10]
          Directed (bool): Directed relation True / False

        Returns:
          edxml.ontology.EventPropertyRelation: The EventPropertyRelation instance

        """
        return self._eventType.CreateRelation(
            self.GetName(), TargetPropertyName,
            Reason or '[[%s]] %s [[%s]]' % (
                self.GetName(), TypePredicate, TargetPropertyName),
            'other', TypePredicate, Confidence, Directed
        )

    def RelateInter(self, TypePredicate, TargetPropertyName, Reason=None, Confidence=10, Directed=True):
        """

        Creates and returns a relation between this property and
        the specified target property. The relation is an 'inter'
        relation, indicating that the related objects belong to
        different, related concept instances.

        When no reason is specified, the reason is constructed by
        wrapping the type predicate with the place holders for
        the two properties.

        Args:
          TypePredicate (str): free form predicate
          TargetPropertyName (str): Name of the related property
          Reason (str): Relation description, with property placeholders
          Confidence (int): Relation confidence [0,10]
          Directed (bool): Directed relation True / False

        Returns:
          edxml.ontology.EventPropertyRelation: The EventPropertyRelation instance

        """
        return self._eventType.CreateRelation(
            self.GetName(), TargetPropertyName,
            Reason or '[[%s]] %s [[%s]]' % (
                self.GetName(), TypePredicate, TargetPropertyName),
            'inter', TypePredicate, Confidence, Directed
        )

    def RelateIntra(self, TypePredicate, TargetPropertyName, Reason=None, Confidence=10, Directed=True):
        """

        Creates and returns a relation between this property and
        the specified target property. The relation is an 'intra'
        relation, indicating that the related objects belong to
        the same concept instance.

        When no reason is specified, the reason is constructed by
        wrapping the type predicate with the place holders for
        the two properties.

        Args:
          TargetPropertyName (str): Name of the related property
          Reason (str): Relation description, with property placeholders
          TypePredicate (str): free form predicate
          Confidence (float): Relation confidence [0,10]
          Directed (bool): Directed relation True / False

        Returns:
          edxml.ontology.EventPropertyRelation: The EventPropertyRelation instance

        """
        return self._eventType.CreateRelation(
            self.GetName(), TargetPropertyName,
            Reason or '[[%s]] %s [[%s]]' % (
                self.GetName(), TypePredicate, TargetPropertyName),
            'intra', TypePredicate, Confidence, Directed
        )

    def SetMergeStrategy(self, MergeStrategy):
        """

        Set the merge strategy of the property. This should
        be one of the MERGE_* attributes of this class.

        Automatically makes the property mandatory or single
        valued when the merge strategy requires it.

        Args:
          MergeStrategy (str): The merge strategy

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._setAttr('merge', MergeStrategy)

        if MergeStrategy == 'match':
            self._setAttr('unique', True)

        if MergeStrategy in ('match', 'min', 'max', 'replace'):
            self._setAttr('multivalued', False)

        if MergeStrategy in ('match', 'min', 'max'):
            self._setAttr('optional', False)

        return self

    def SetDescription(self, Description):
        """

        Set the description of the property. This should
        be really short, indicating which role the object
        has in the event type.

        Args:
          Description (str): The property description

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._setAttr('description', Description)
        return self

    def Unique(self):
        """

        Mark property as a unique property, which also sets
        the merge strategy to 'match' and makes the property
        both mandatory and single valued.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._setAttr('unique', True)
        self._setAttr('merge', 'match')
        self._setAttr('optional', False)
        self._setAttr('multivalued', False)
        return self

    def IsUnique(self):
        """

        Returns True if property is unique, returns False otherwise

        Returns:
          bool:
        """
        return self._attr['unique']

    def IsOptional(self):
        """

        Returns True if property is optional, returns False otherwise

        Returns:
          bool:
        """
        return self._attr['optional']

    def IsMandatory(self):
        """

        Returns True if property is mandatory, returns False otherwise

        Returns:
          bool:
        """
        return not self._attr['optional']

    def IsMultiValued(self):
        """

        Returns True if property is multi-valued, returns False otherwise

        Returns:
          bool:
        """
        return self._attr['multivalued']

    def IsSingleValued(self):
        """

        Returns True if property is single-valued, returns False otherwise

        Returns:
          bool:
        """
        return not self._attr['multivalued']

    def Identifies(self, ConceptName, Confidence):
        """

        Marks the property as an identifier for specified
        concept, with specified confidence.

        Args:
          ConceptName (str): concept name
          Confidence (int): concept identification confidence [0, 10]

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._setAttr('concept', ConceptName)
        self._setAttr('concept-confidence', int(Confidence))
        return self

    def SetConceptNamingPriority(self, Priority):
        """

        Configure the concept naming priority of
        the property. When the value is not explicitly
        specified using this method, it's value is 128.

        Args:
          Priority (int): The EDXML cnp attribute

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._setAttr('cnp', int(Priority))
        return self

    def GetConceptName(self):
        """

        Returns the name of the concept if the property is an
        identifier for a concept, returns None otherwise.

        Returns:
          str:
        """
        return self._attr['concept']

    def HintSimilar(self, Similarity):
        """

        Set the EDXML 'similar' attribute.

        Args:
          Similarity (str): similar attribute string

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self._setAttr('similar', Similarity)
        return self

    def MergeAdd(self):
        """

        Set merge strategy to 'add'.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self.SetMergeStrategy('add')
        return self

    def MergeReplace(self):
        """

        Set merge strategy to 'replace'.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self.SetMergeStrategy('replace')
        return self

    def MergeDrop(self):
        """

        Set merge strategy to 'drop', which is
        the default merge strategy.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self.SetMergeStrategy('drop')
        return self

    def MergeMin(self):
        """

        Set merge strategy to 'min'.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self.SetMergeStrategy('min')
        return self

    def MergeMax(self):
        """

        Set merge strategy to 'max'.

        Returns:
          edxml.ontology.EventProperty: The EventProperty instance
        """
        self.SetMergeStrategy('max')
        return self

    def Validate(self):
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
        if not re.match(self.EDXML_PROPERTY_NAME_PATTERN, self._attr['name']):
            raise EDXMLValidationError(
                'Invalid property name in property definition: "%s"' % self._attr['name'])

        if not re.match(edxml.ontology.ObjectType.NAME_PATTERN, self._attr['object-type']):
            raise EDXMLValidationError(
                'Invalid object type name in property definition: "%s"' % self._attr['object-type'])

        if not len(self._attr['description']) <= 128:
            raise EDXMLValidationError(
                'Property description is too long: "%s"' % self._attr['description'])

        if not len(self._attr['similar']) <= 64:
            raise EDXMLValidationError(
                'Property attribute is too long: similar="%s"' % self._attr['similar'])

        if not 0 <= int(self._attr['cnp']) < 256:
            raise EDXMLValidationError(
                'Property "%s" has an invalid concept naming priority: "%d"' % (
                    self._attr['name'], self._attr['cnp'])
            )

        if self.IsUnique():
            if self.IsOptional():
                raise EDXMLValidationError(
                    'Property "%s" is unique and optional at the same time' % self._attr['name']
                )
            if self.IsMultiValued():
                raise EDXMLValidationError(
                    'Property "%s" is unique and multivalued at the same time' % self._attr[
                        'name']
                )

        if self._attr['merge'] in ('match', 'min', 'max') and self.IsOptional():
            raise EDXMLValidationError(
                'Property "%s" cannot be optional due to its merge strategy' % self._attr[
                    'name']
            )

        if self._attr['merge'] in ('match', 'min', 'max', 'replace') and self.IsMultiValued():
            raise EDXMLValidationError(
                'Property "%s" cannot be multivalued due to its merge strategy' % self._attr[
                    'name']
            )

        if not self._attr['merge'] in ('drop', 'add', 'replace', 'min', 'max', 'match'):
            raise EDXMLValidationError(
                'Invalid property merge strategy: "%s"' % self._attr['merge'])

        if self._attr['concept-confidence'] < 0 or self._attr['concept-confidence'] > 10:
            raise EDXMLValidationError(
                'Invalid property concept confidence: "%d"' % self._attr['concept-confidence'])

        return self

    @classmethod
    def Read(cls, propertyElement, parentEventType):
        name = propertyElement.attrib['name']
        objectTypeName = propertyElement.attrib['object-type']
        objectType = parentEventType._ontology.GetObjectType(objectTypeName)

        if not objectType:
            raise EDXMLValidationError(
                'Property "%s" of event type "%s" refers to undefined object type "%s".' %
                (name, parentEventType.GetName(), objectTypeName)
            )

        return cls(
            parentEventType,
            propertyElement.attrib['name'],
            objectType,
            propertyElement.attrib['description'],
            propertyElement.get('concept'),
            propertyElement.get('concept-confidence', 0),
            int(propertyElement.get('cnp', 0)),
            propertyElement.get('unique', 'false') == 'true',
            propertyElement.get('optional') == 'true',
            propertyElement.get('multivalued') == 'true',
            propertyElement.get('merge', 'drop'),
            propertyElement.get('similar', '')
        )

    def Update(self, eventProperty):
        """

        Updates the event property to match the EventProperty
        instance passed to this method, returning the
        updated instance.

        Args:
          eventProperty (edxml.ontology.EventProperty): The new EventProperty instance

        Returns:
          edxml.ontology.EventProperty: The updated EventProperty instance

        """
        if self._attr['name'] != eventProperty.GetName():
            raise Exception('Attempt to update event property "%s" with event property "%s".' %
                            (self._attr['name'], eventProperty.GetName()))

        if self._attr['description'] != eventProperty.GetDescription():
            raise Exception('Attempt to update event property "%s", but descriptions do not match.' %
                            self._attr['name'],
                            (self._attr['description'], eventProperty.GetName()))

        if int(self._attr['cnp']) != eventProperty.GetConceptNamingPriority():
            raise Exception(
                'Attempt to update event property "%s", but Entity Naming Priorities do not match.' %
                self._attr['name'],
                (self._attr['cnp'], eventProperty.GetName()))

        if self._attr['optional'] != eventProperty.IsOptional():
            raise Exception(
                'Attempt to update event property "%s", but "optional" attributes do not match.' % self._attr[
                    'name']
            )

        if self._attr['multivalued'] != eventProperty.IsMultiValued():
            raise Exception(
                'Attempt to update event property "%s", but "multivalued" attributes do not match.' % self._attr[
                    'name']
            )

        self.Validate()

        return self

    def GenerateXml(self):
        """

        Generates an lxml etree Element representing
        the EDXML <property> tag for this event property.

        Returns:
          etree.Element: The element

        """

        attribs = dict(self._attr)

        attribs['concept-confidence'] = '%d' % self._attr['concept-confidence']
        attribs['unique'] = 'true' if self._attr['unique'] else 'false'
        attribs['optional'] = 'true' if self._attr['optional'] else 'false'
        attribs['multivalued'] = 'true' if self._attr['multivalued'] else 'false'
        attribs['cnp'] = '%d' % attribs['cnp']

        if attribs['concept'] is None:
            del attribs['concept']
            del attribs['concept-confidence']
            del attribs['cnp']

        return etree.Element('property', attribs)
