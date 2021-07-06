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

import json

from collections import defaultdict
from functools import reduce
from operator import mul
from typing import List, Dict, Optional
from dateutil.parser import parse

from edxml.miner.node import NodeCollection


class ConceptAttribute:
    """
    The ConceptAttribute class represents a single attribute of
    a concept instance, viewed from the perspective of a
    specific seed. It holds the collection of inferred nodes
    that confirm the existence of the attribute.
    """
    def __init__(self, name, value, confidence=1.0, confidence_timeline=(), concept_naming_priority=128,
                 concept_names=None):
        """

        Args:
            name (str): Attribute name
            value (str): Attribute value
            confidence (float): Attribute Confidence
            confidence_timeline (List[Tuple[datetime.datetime,datetime.datetime,float]]): Time line of confidences
            concept_naming_priority (int): Concept naming priority
            concept_names (Dict[str, float]): Concept names and confidences

        Returns:
            ConceptAttribute:
        """
        self.name = name
        self.value = value

        self._cnp = concept_naming_priority
        self._confidence = confidence
        self._confidence_timeline = list(confidence_timeline)
        self._concept_names = concept_names or dict()  # type: Optional[Dict[str, float]]

    def __repr__(self):
        return f"{self.name} = {self.value}"

    @property
    def object_type_name(self):
        """
        The name of the EDXML object type of the attribute.

        Returns:
            str:
        """
        return self.name.split(':')[0]

    @property
    def confidence(self):
        """

        The confidence is the likelihood that the attribute belongs
        to the concept.

        Returns:
            float: Confidence
        """
        return self._confidence

    @property
    def confidence_timeline(self):
        """

        The confidence timeline shows how the likelihood that the attribute
        belongs to the concept changes over time.

        Returns:
            List[List[datetime.datetime,datetime.datetime, float]]: Confidence timeline
        """
        return self._confidence_timeline

    @property
    def concept_naming_priority(self):
        """

        Returns the concept naming priority of the attribute, which
        determines how suitable the attribute is for naming a
        concept instance.

        Returns:
            int:
        """
        return self._cnp

    @property
    def concept_names(self):
        """

        Returns a dictionary containing the names of all concepts that refer to this attribute
        as keys and their confidences as values.

        Returns:
            Dict[str, float]
        """
        return self._concept_names


class MinedConceptAttribute(ConceptAttribute):
    """
    The ConceptAttribute class represents a single attribute of
    a concept instance, viewed from the perspective of a
    specific seed. It holds the collection of inferred nodes
    that confirm the existence of the attribute.
    """
    def __init__(self, seed_id, name, value, nodes=None):
        """

        Args:
            seed_id (str): Seed ID
            name (str): Attribute name
            value (str): Attribute value
            nodes (NodeCollection): The nodes associated with the attribute

        Returns:
            MinedConceptAttribute:
        """
        super().__init__(name, value)
        self.seed_id = seed_id
        self.name = name
        self.value = value
        self.nodes = nodes or NodeCollection()  # type: NodeCollection

    @property
    def confidence(self):
        # Compute the net confidence of the attribute by combining
        # the confidences of all nodes that confirm its existence.
        return self.nodes.compute_net_confidence(self.seed_id)

    @property
    def confidence_timeline(self):
        # Compute a timeline showing how the confidence of the attribute
        # varies over time.
        return self.nodes.compute_confidence_timeline(self.seed_id)

    @property
    def concept_names(self):
        return self.nodes.compute_concept_name_confidences(self.seed_id)

    @property
    def concept_naming_priority(self):
        # Pick the highest concept naming priority from all property / concept
        # associations from the nodes.
        return max([node.concept_association.get_concept_naming_priority() for node in self.nodes.values()])


class ConceptInstance:
    def __init__(self, identifier):
        self._id = identifier
        self._related_concepts = {}
        self.attributes = []  # type: List[ConceptAttribute]
        """
        List of concept attributes.
        """

    def __repr__(self):
        concept_name = self.get_best_concept_name()
        if len(concept_name.split('.')) > 3:
            concept_name = '...' + '.'.join(concept_name.split('.')[-3:])
        return f"{concept_name}: {self.get_instance_title()}"

    @property
    def id(self):
        """

        An opaque identifier of the concept instance within the
        collection that it is part of.

        Returns:
            Any:
        """
        return self._id

    def add_attribute(self, attribute):
        """
        Adds an attribute to the instance.

        Args:
            attribute (ConceptAttribute): Attribute

        """
        self.attributes.append(attribute)

    def add_related_concept(self, concept_id, confidence):
        """

        Adds another related concept instance from the same concepts collection.

        Args:
            concept_id (str): Concept identifier
            confidence (float): Relation confidence

        """
        self._related_concepts[concept_id] = confidence

    def has_attribute(self, attribute_name):
        return [attribute for attribute in self.attributes if attribute.name == attribute_name] != []

    def get_concept_names(self):
        """
        Compiles the names of all possible concepts that this concept may be an instance of.
        Returns a dictionary containing the concept names as keys and their confidences as values.
        Confidences are given as a floating point number in range [0,1]

        Returns:
            dict:
        """
        concepts = defaultdict(list)
        for attribute in self.attributes:
            for concept_name, confidence in attribute.concept_names.items():
                concepts[concept_name].append(confidence)

        return {name: 1.0 - reduce(mul, [1.0 - conf for conf in confidences]) for name, confidences in concepts.items()}

    def get_best_concept_name(self):
        """

        Returns the name of the most likely EDXML concept that this
        is an instance of.

        Returns:
            str:
        """
        try:
            return next(iter(sorted(self.get_concept_names().items(), key=lambda concept: concept[1], reverse=True)))[0]
        except StopIteration:
            return 'empty concept'

    def get_instance_title(self):
        """
        Finds and returns the attribute value that is most suitable for use
        as a title for the concept instance.

        Returns:
            str:
        """
        concept_titles = []
        for attribute in self.attributes:
            # Add to the list values that are potential titles for this concept instance.
            concept_titles.append(
                {
                    'cnp': attribute.concept_naming_priority,
                    'confidence': attribute.confidence,
                    'value': attribute.value,
                }
            )

        # Find the most suitable title for the concept by sorting on
        # the concept naming priorities and confidences of its attributes.
        concept_titles = sorted(concept_titles, key=lambda c: c['cnp'] * c['confidence'], reverse=True)

        try:
            return concept_titles[0]['value']
        except IndexError:
            return 'empty concept'

    def get_related_concepts(self):
        """

        Get information about other concept instances from the same collection that
        may be related. Returns a dictionary containing the identifiers of related
        concept instances as keys and the confidence of the relation as values.

        Returns:
            Dict[str, float]: Related concepts
        """
        return self._related_concepts

    def get_attributes(self, name):
        """

        Returns the list of all attributes that have specified name.

        Args:
            name (str): Attribute name

        Returns:
            List[ConceptAttribute]:
        """
        return [attribute for attribute in self.attributes if attribute.name == name]


class MinedConceptInstance(ConceptInstance):
    """
    Class representing a single mined concept instance
    and its attributes.
    """
    def __init__(self, seed_id):
        super().__init__(seed_id)
        self._seed_id = seed_id
        self.attributes = []  # type: List[MinedConceptAttribute]

    def get_nodes(self):
        """

        Returns a NodeCollection containing all nodes which are part of the concept.

        Returns:
            NodeCollection:
        """
        return NodeCollection(
            {node_id: node for attribute in self.attributes for node_id, node in attribute.nodes.items()}
        )

    def get_seed(self):
        """

        Returns the seed node

        Returns:
            Node:
        """
        try:
            return next(attr.nodes[self._seed_id] for attr in self.attributes if self._seed_id in attr.nodes)
        except StopIteration:
            raise Exception('Seed node missing in concept instance.')

    def get_related_concepts(self):
        confidences = defaultdict(list)
        for node in self.get_nodes().values():
            # Process all inter-concept inferences that lead to other concept instances.
            for inference in node.get_inter_concept_inferences():
                source_confidence = inference.source.seed_confidences.get(self._seed_id, 0)
                for related_seed_id, target_confidence in inference.target.seed_confidences.items():
                    # Compute the confidence of concept instance being related. Note that three
                    # factors are involved. First, the source node has a certain confidence of being
                    # part of this concept. Second, the source node has a certain confidence of being
                    # related to the target node. And third, the target has a certain confidence of
                    # being part of the related concept instance. The confidence of the concept
                    # instance actually being related is computed by multiplication.
                    confidence = source_confidence * inference.confidence * target_confidence
                    confidences[related_seed_id].append(confidence)

        total_confidences = {}
        for seed_id, confidences in confidences.items():
            total_confidences[seed_id] = 1.0 - reduce(mul, [1.0 - confidence for confidence in confidences])
        return total_confidences


class ConceptInstanceCollection:
    """
    A collection of concept instances.
    """
    def __init__(self, concepts=None):
        self.concepts = {concept.id: concept for concept in concepts or []}  # type: Dict[str, ConceptInstance]
        """
        Dictionary of concept instances. Keys are unique concept identifiers.
        """

    def __repr__(self):
        return f"{len(self.concepts)} concepts"

    def append(self, concept):
        self.concepts[concept.id] = concept

    def to_json(self, as_string=True, **kwargs):
        """

        Returns a JSON representation of the concept instance collection. Note that this is
        a basic representation which does not include details such as the nodes associated
        with a particular concept attribute.

        Optionally a dictionary can be returned in stead of a JSON string.

        Args:
            as_string (bool): Returns a JSON string or not
            **kwargs: Keyword arguments for the json.dumps() method.

        Returns:
            Union[dict, str]: JSON string or dictionary
        """
        dicts = []
        for seed_id, concept in self.concepts.items():
            attr_dicts = []
            for attribute in concept.attributes:
                # Add the concept attribute
                timeline = attribute.confidence_timeline
                attr_dicts.append({
                    'name': attribute.name,
                    'value': attribute.value,
                    'confidence': attribute.confidence,
                    'confidence_timeline': [
                        {
                            'start': item[0].isoformat() if item[0] else None,
                            'end': item[1].isoformat() if item[1] else None,
                            'confidence': item[2]
                        } for item in timeline
                    ],
                    'concept_names': attribute.concept_names,
                })

            related_concepts = []
            for related_seed_id, confidence in concept.get_related_concepts().items():
                if related_seed_id in self.concepts:
                    related_concept = self.concepts[related_seed_id]
                    related_concepts.append(
                        {
                            'id': related_concept.id,
                            'confidence': confidence,
                        }
                    )

            dicts.append(
                {
                    'id': concept.id,
                    'title': concept.get_instance_title(),
                    'names': concept.get_concept_names(),
                    'attributes': attr_dicts,
                    'related': related_concepts,
                }
            )

        if as_string:
            return json.dumps({'concepts': dicts}, **kwargs)
        else:
            return {'concepts': dicts}


class MinedConceptInstanceCollection(ConceptInstanceCollection):

    def __init__(self):
        super().__init__()
        self.concepts = {}  # type: Dict[str, MinedConceptInstance]

    def get_seeds(self):
        """

        Get the seeds from all concepts in the result set

        Returns:
            List[Node]:
        """
        return [concept.get_seed() for concept in self.concepts.values()]


def from_json(json_data):
    """
    Builds a ConceptInstanceCollection from a JSON string that was previously
    created using the to_json() method of a concept instance collection.

    Args:
        json_data (str): JSON string

    Returns:
        ConceptInstanceCollection:
    """
    collection = ConceptInstanceCollection()
    for concept_data in json.loads(json_data)['concepts']:
        concept = ConceptInstance(identifier=concept_data['id'])
        for attribute_data in concept_data['attributes']:
            attribute_data['confidence_timeline'] = [
                (parse(item['start']) if item['start'] else None,
                 parse(item['end']) if item['end'] else None,
                 item['confidence']) for item in attribute_data['confidence_timeline']
            ]
            attribute = ConceptAttribute(**attribute_data)
            concept.add_attribute(attribute)
        for related_concept in concept_data['related']:
            concept.add_related_concept(related_concept['id'], related_concept['confidence'])
        collection.concepts[concept.id] = concept
    return collection
