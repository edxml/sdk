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

"""
This module offers classes for constructing graphs for concept mining.

..  autoclass:: KnowledgePullParser
    :members:
    :show-inheritance:

..  autoclass:: KnowledgePushParser
    :members:
    :show-inheritance:

..  autoclass:: KnowledgeBase
    :members:
    :show-inheritance:
"""
import json
from collections import defaultdict

import edxml
from edxml import EDXMLPullParser, EDXMLEvent, EDXMLPushParser
from edxml.miner import GraphConstructor
from edxml.miner.graph import ConceptInstanceGraph
from edxml.miner.result import ConceptInstanceCollection
from edxml.miner.result import from_json as concept_collection_from_json
from edxml.ontology import Ontology


class KnowledgeParserBase:
    def __init__(self, knowledge_base):
        """
        Args:
            knowledge_base (KnowledgeBase): Knowledge base to use
        """
        super().__init__()
        self._ontology = Ontology()
        self._graph = ConceptInstanceGraph()
        self._constructor = GraphConstructor(self._graph)
        self._knowledge_base = knowledge_base  # type: KnowledgeBase

    def _parsed_ontology(self, ontology):
        self._ontology.update(ontology)
        self._constructor.update_ontology(ontology)

    def _parsed_event(self, event):
        self._constructor.add(event)
        self._mine_universals(event)

    def _mine_universals(self, event: EDXMLEvent):
        event_type = self._ontology.get_event_type(event.get_type_name())

        universals = (
            ('name', self._knowledge_base.add_universal_name),
            ('description', self._knowledge_base.add_universal_description),
            ('container', self._knowledge_base.add_universal_container)
        )

        for relation_type, add in universals:
            for relation in event_type.get_property_relations(relation_type).values():
                source = relation.get_source()
                target = relation.get_target()
                source_object_type = event_type.get_properties()[source].get_object_type_name()
                target_object_type = event_type.get_properties()[target].get_object_type_name()
                for target_object in event[target]:
                    if event[source] != set():
                        for source_object in event[source]:
                            add(target_object_type, target_object, source_object_type, source_object)

    def mine(self, seed=None, min_confidence=0.1, max_depth=10):
        """

        Mines the events for concept instances. When a seed is specified, only
        the concept instance containing the specified seed is mined. When no
        seed is specified, an optimum set of seeds will be selected and mined,
        covering the full event data set. The algorithm will auto-select the
        strongest concept identifiers. Any previously obtained concept mining
        results will be discarded in the process.

        After mining completes, the concept collection is updated to contain
        the mined concept instances.

        Concept instances are constructed within specified confidence and
        recursion depth limits.

        Args:
            seed (EventObjectNode): Concept seed
            min_confidence (float): Confidence cutoff
            max_depth (int): Max recursion depth
        """
        self._graph.mine(seed, min_confidence, max_depth)
        self._knowledge_base.concept_collection = self._graph.extract_result_set(min_confidence)


class KnowledgePullParser(KnowledgeParserBase, EDXMLPullParser):
    """
    EDXML pull parser that feeds EDXML data into a knowledge base.
    """
    def __init__(self, knowledge_base):
        """
        Args:
            knowledge_base (KnowledgeBase): Knowledge base to use
        """
        EDXMLPullParser.__init__(self)
        KnowledgeParserBase.__init__(self, knowledge_base)


class KnowledgePushParser(KnowledgeParserBase, EDXMLPushParser):
    """
    EDXML push parser that feeds EDXML data into a knowledge base.
    """
    def __init__(self, knowledge_base):
        """
        Args:
            knowledge_base (KnowledgeBase): Knowledge base to use
        """
        EDXMLPullParser.__init__(self)
        KnowledgeParserBase.__init__(self, knowledge_base)


class KnowledgeBase:
    """
    Class that can be used to extract knowledge from EDXML events. It can
    do that both by mining concepts and by gathering universals from name
    relations, description relations, and so on.
    """
    def __init__(self):
        super().__init__()
        self._ontology = Ontology()
        self._names = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
        self._descriptions = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
        self._containers = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

        self.concept_collection = ConceptInstanceCollection()  # type: edxml.miner.result.ConceptInstanceCollection
        """
        The concept instance collection holding mined concept instances.
        """

    def __repr__(self):
        result = [repr(self.concept_collection)]
        if len(self._names) > 0:
            result.append('names')
        if len(self._descriptions) > 0:
            result.append('descriptions')
        if len(self._containers) > 0:
            result.append('containers')
        return ', '.join(result)

    def get_names_for(self, object_type_name, value):
        """

        Returns a dictionary containing any names for
        specified object type and value. The dictionary
        has the object type names of the names as keys.
        The values are sets of object values.

        Args:
            object_type_name (str): Object type name
            value (str): Object value

        Returns:
            Dict[str, Set]
        """
        return self._names[object_type_name][value]

    def get_descriptions_for(self, object_type_name, value):
        """

        Returns a dictionary containing any descriptions for
        specified object type and value. The dictionary
        has the object type names of the descriptions as keys.
        The values are sets of object values.

        Args:
            object_type_name (str): Object type name
            value (str): Object value

        Returns:
            Dict[str, Set]
        """
        return self._descriptions[object_type_name][value]

    def get_containers_for(self, object_type_name, value):
        """

        Returns a dictionary containing any containers for
        specified object type and value. As described in the
        EDXML specification, containers are classes / categories
        that a value belongs to. The dictionary has the object
        type names of the containers as keys. The values are
        sets of object values.

        Args:
            object_type_name (str): Object type name
            value (str): Object value

        Returns:
            Dict[str, Set]
        """
        return self._containers[object_type_name][value]

    def add_universal_name(self, named_object_type, value, name_object_type, name):
        """

        Adds a name universal. A name universal associates a value with a name for
        that value and is usually mined from EDXML name relations. The parameters
        are two pairs of object type / value combinations, one for the value that
        is being named and one for the name itself.

        Args:
            named_object_type (str): Object type of named object
            value (str): value of named object
            name_object_type (str): Object type of name
            name (str): Name value

        """
        self._names[named_object_type][value][name_object_type].add(name)

    def add_universal_description(self, described_object_type, value, description_object_type, description):
        """

        Adds a description universal. A description universal associates a value with
        a description for that value and is usually mined from EDXML description
        relations. The parameters are two pairs of object type / value combinations,
        one for the value that is being described and one for the description itself.

        Args:
            described_object_type (str): Object type of described object
            value (str): value of described object
            description_object_type (str): Object type of description
            description (str): Description value

        """
        self._descriptions[described_object_type][value][description_object_type].add(description)

    def add_universal_container(self, contained_object_type, value, container_object_type, container):
        """

        Adds a container universal. A container universal associates a value with
        another value that contains it and is usually mined from EDXML container
        relations. The parameters are two pairs of object type / value combinations,
        one for the value that is being contained and one for the container itself.

        Args:
            contained_object_type (str): Object type of contained object
            value (str): value of contained object
            container_object_type (str): Object type of container
            container (str): Container value

        """
        self._containers[contained_object_type][value][container_object_type].add(container)

    def filter_concept(self, concept_name):
        """

        Returns a copy of the knowledge base where the concept instances
        have been filtered down to those that may be an instance of the
        specified EDXML concept.

        The universals are kept as a reference to the original
        knowledge base.

        Args:
            concept_name (str): Name of the EDXML concept to filter on

        Returns:
            KnowledgeBase: Filtered knowledge base
        """
        filtered = KnowledgeBase()
        concepts = self.concept_collection.concepts.values()
        filtered.concept_collection = ConceptInstanceCollection(
            [concept for concept in concepts if concept_name in concept.get_concept_names()]
        )
        return filtered

    def filter_attribute(self, attribute_name):
        """

        Returns a copy of the knowledge base where the concept instances
        have been filtered down to those that have at least one value for
        the specified EDXML attribute.

        The universals are kept as a reference to the original
        knowledge base.

        Args:
            attribute_name (str): Name of the EDXML concept attribute to filter on

        Returns:
            KnowledgeBase: Filtered knowledge base
        """
        filtered = KnowledgeBase()
        concepts = self.concept_collection.concepts.values()
        filtered.concept_collection = ConceptInstanceCollection(
            [concept for concept in concepts if concept.has_attribute(attribute_name)]
        )
        return filtered

    def filter_related_concepts(self, concept_ids):
        """

        Returns a copy of the knowledge base where the concept instances
        have been filtered down to those that are related to any of the
        specified concept instances.

        The universals are kept as a reference to the original
        knowledge base.

        Args:
            concept_ids (Iterable[str]): Iterable containing concept IDs

        Returns:
            KnowledgeBase: Filtered knowledge base
        """
        concepts = []
        for concept in self.concept_collection.concepts.values():
            for related_concept_id in concept.get_related_concepts().keys():
                if related_concept_id in concept_ids:
                    concepts.append(concept)
        filtered = KnowledgeBase()
        filtered.concept_collection = ConceptInstanceCollection(concepts)
        return filtered

    def to_json(self, as_string=True, **kwargs):
        """

        Returns a JSON representation of the knowledge base. Note that this is
        a basic representation which does not include details such as the nodes associated
        with a particular concept attribute.

        Optionally a dictionary can be returned in stead of a JSON string.

        Args:
            as_string (bool): Returns a JSON string or not
            **kwargs: Keyword arguments for the json.dumps() method.

        Returns:
            Union[dict, str]: JSON string or dictionary
        """
        concepts = self.concept_collection.to_json(as_string=False, **kwargs)
        dictionary = {
            'version': '1.0',
            'universals': {
                'names': self._get_universals_dict(self._names),
                'descriptions': self._get_universals_dict(self._descriptions),
                'containers': self._get_universals_dict(self._containers)
            },
            'concepts': concepts['concepts']
        }

        if as_string:
            return json.dumps(dictionary, **kwargs)
        else:
            return dictionary

    @classmethod
    def _get_universals_dict(cls, universals):
        dictionary = dict()
        for object_type_source, values_source in universals.items():
            dictionary[object_type_source] = {}
            for value, values_target in values_source.items():
                dictionary[object_type_source][value] = \
                    {object_type: list(values) for object_type, values in values_target.items()}
        return dictionary

    @classmethod
    def from_json(cls, json_data):
        """
        Builds a KnowledgeMiner from a JSON string that was previously
        created using the to_json() method of a concept instance collection.

        Args:
            json_data (str): JSON string

        Returns:
            KnowledgeBase:
        """
        concepts_data = json.dumps(json.loads(json_data))

        knowledge = KnowledgeBase()

        knowledge.concept_collection = concept_collection_from_json(concepts_data)

        universals_types = (
            ('names', knowledge._names),
            ('descriptions', knowledge._descriptions),
            ('containers', knowledge._containers)
        )

        json_data_dict = json.loads(json_data)

        for key, universals in universals_types:
            for object_type_source, values_source in json_data_dict['universals'][key].items():
                universals[object_type_source] = {}
                for value, values_target in values_source.items():
                    universals[object_type_source][value] = \
                        {object_type: set(values) for object_type, values in values_target.items()}

        return knowledge
