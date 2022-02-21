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

from edxml import EDXMLEvent
from edxml.miner.graph.construct import GraphConstructor
from edxml.miner.graph import ConceptInstanceGraph
from edxml.miner.knowledge import KnowledgeBase
from edxml.ontology import Ontology


class Miner:
    """
    Class combining an ontology, concept graph and a knowledge
    base to mine concepts and universals.
    """
    def __init__(self, knowledge_base):
        """
        Args:
            knowledge_base (edxml.miner.knowledge.KnowledgeBase): Knowledge base to use
        """
        super().__init__()
        self._ontology = Ontology()
        self._graph = ConceptInstanceGraph()
        self._constructor = GraphConstructor(self._graph)
        self._knowledge_base = knowledge_base  # type: KnowledgeBase

    def add_ontology(self, ontology):
        self._ontology.update(ontology)
        self._constructor.update_ontology(ontology)

    def add_event(self, event):
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
