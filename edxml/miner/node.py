from functools import reduce
from operator import mul
from typing import Dict, Set, Optional, MutableMapping
from collections import defaultdict, UserDict

from edxml.miner.inference import Inference
from edxml.ontology import Concept

import edxml.miner.inference


def is_intra_edge(edge):
    return isinstance(edge, edxml.miner.inference.RelationInference) and edge.relation.get_type() != 'inter'


def check_node_concept_in_scope(seed, node):
    """

    This function guards the concept mining process from generating
    inconsistent concept instances by combining information about unrelated
    concepts.

    While the seed has a single concept type associated with it, intra-concept
    relations may indicate that the concept instance is also an instance of
    other concepts. These concepts are accumulated in the seed during the
    mining process. In this method, we use that information to check if the
    specified node could belong to the concept instance that is associated
    with the specified seed.

    Args:
        seed (Node): Seed node of the concept instance
        node (EventObjectNode): Node to be considered
    Returns:
        float: Confidence of being in scope
    """
    node_concept = node.concept_association.get_concept_name()

    confidences = []
    for concept_name, node_confidences in seed.concept_name_equivalents.items():
        if Concept.concept_names_share_branch(concept_name, node_concept):
            confidences.extend(node_confidences.values())

    if confidences:
        return 1.0 - reduce(mul, (1.0 - c for c in confidences))

    return 0.0


class Node(object):

    def __init__(self, object_type_name, value, confidence):
        self.concept_name_equivalents = defaultdict(dict)
        self.object_type_name = object_type_name
        """
        The name of the object type associated with the node
        """
        self.id = value
        self.value = value
        """
        The object value that is represented by the node
        """
        self.confidence = 0.1 * confidence
        """
        Confidence of the node
        """

        self._edges = set()                  # type: Set[Inference]
        self._edges_inward = defaultdict()   # type: Dict[str, Inference]
        self._edges_outward = defaultdict()  # type: Dict[str, Inference]

        self.seed_confidences = dict()
        self.taint = 0.0
        self.depth = 0
        self.visited = False

        self.reason = None  # type: Optional[Inference]
        """
        The reason of a node is a reference to one of the edges which
        was used during reasoning to arrive at this node.
        """

        self.conclusions = set()  # type: Set[Inference]
        """
        The conclusions of a node are references to zero or more of
        its edges which were used during reasoning to infer other nodes.
        """

    def __repr__(self):
        return self.value

    def add_inward(self, edge):
        """

        Adds specified edge as an inward edge.

        Args:
            edge (Inference):

        """
        # TODO: We can auto-detect if the edge in inward or outward.
        self._edges_inward[edge.source.id] = edge
        self._edges.add(edge)

    def add_outward(self, edge):
        """

        Adds specified edge as an outward edge.

        Args:
            edge (Inference):

        """
        self._edges_outward[edge.target.id] = edge
        self._edges.add(edge)

    def get_inferences(self):
        """

        Returns:
            Iterable[Inference]:
        """
        return self._edges_outward.values()

    def get_inter_concept_inferences(self):
        """

        Returns:
            List[Inference]:
        """
        return [
            c for c in self._edges_outward.values() if
            isinstance(c, edxml.miner.inference.RelationInference) and c.relation.get_type() == 'inter'
        ]

    def get_intra_concept_inferences(self):
        """

        Returns:
            List[Inference]:
        """
        return [
            c for c in self._edges_outward.values() if
            isinstance(c, edxml.miner.inference.RelationInference) and c.relation.get_type() == 'intra'
        ]

    def _inference_same_concept(self, inference, seed, min_confidence):
        if not isinstance(inference.target, edxml.miner.node.EventObjectNode):
            # Target node is a hub. Jumping to a hub does not make us get to
            # a different concept, so this is always safe to do.
            return True

        if isinstance(inference, edxml.miner.inference.SameObjectInference):
            in_scope_confidence = check_node_concept_in_scope(seed, inference.target) * self.seed_confidences[seed.id]
            return in_scope_confidence > min_confidence

        if is_intra_edge(inference):
            return True

        return False

    def get_same_concept_inferences(self, seed, min_confidence):
        """

        Args:
            seed (Node): Concept seed
            min_confidence (float): Minimum confidence

        Returns:
            List[Inference]:
        """
        return [
            c for c in self._edges_outward.values() if self._inference_same_concept(c, seed, min_confidence)
        ]

    def clear_edge_roles(self):
        """

        Clears the roles that the edges play as either a reason
        or an argument. These roles are specific to the perspective
        of a particular seed.

        """
        self.reason = None
        self.conclusions = set()

    def reset(self):
        """

        Resets the state of the node to its initial state, clearing the edge roles,
        marking the node as unvisited, and so on.

        """
        self.conclusions = set()
        self.visited = False
        self.depth = 0
        self.reason = None
        self.seed_confidences = {}
        self.concept_name_equivalents = defaultdict(dict)
        self.taint = 0.0

        for edge in list(self._edges_inward.values()):
            if isinstance(edge.source, EventObjectHub) or isinstance(edge.target, EventObjectHub):
                del self._edges_inward[edge.source.id]
                self._edges.discard(edge)
            edge.seeds = set()

        for edge in list(self._edges_outward.values()):
            if isinstance(edge.source, EventObjectHub) or isinstance(edge.target, EventObjectHub):
                del self._edges_outward[edge.target.id]
                self._edges.discard(edge)
            edge.seeds = set()


class EventObjectNode(Node):
    """
    Node representing a single instance of an object value.
    """
    def __init__(self, event_id, concept_association, object_type_name, value, confidence):
        super().__init__(object_type_name, value, confidence)
        self.event_id = event_id
        self.attribute_name = concept_association.get_attribute_name()
        self.concept_association = concept_association  # type: edxml.ontology.PropertyConcept
        self.concept_name = concept_association.get_concept_name()
        self.id = f"obj:{event_id}:{concept_association.get_property_name()}:{self.concept_name}:{value}"

    def __repr__(self):
        return f"{self.attribute_name} = {self.value}"

    def link_relation(self, node, relation):
        """

        Args:
            relation (edxml.ontology.PropertyRelation):
            node (EventObjectNode):

        """
        if node is self:
            return

        # Note that we create edges for inference in both directions. We want to do this
        # because inference can start from any node in the graph, which means the
        # inference can go in any direction.

        edge_outgoing = edxml.miner.inference.RelationInference(self, node, relation)
        self.add_outward(edge_outgoing)
        node.add_inward(edge_outgoing)

        edge_incoming = edxml.miner.inference.RelationInference(node, self, relation.reversed())
        self.add_inward(edge_incoming)
        node.add_outward(edge_incoming)


class EventObjectHub(Node):
    """
    An event object hub represents the reasoning result that if one
    event has reasons for an object value to be part of the concept,
    then all references to this same object in other events may also
    be part of the concept.
    By connecting all instances of an object value, from all events
    that refer to it, to a single hub a star geometry results. This
    geometry allows the reasoning process to reach the other object
    instances using a small number of edges.
    """

    def __init__(self, object_type_name, value, object_nodes):
        super().__init__(object_type_name, value, confidence=10)

        self.id = f"hub:{self.object_type_name}:{self.value}"

        for node in object_nodes:
            # The confidence indicates how strong of an identifier the object is for
            # the concept within the context of the event from which the object
            # instance originated.
            ident_confidence = 0.1 * node.concept_association.get_confidence()

            # Create edges in two directions, connecting the object nodes with the hub.
            # Note that the inward edge has no associated confidence loss, only the
            # outward edge has.
            edge_inward = edxml.miner.inference.SameObjectInference(node, self, 1.0)
            edge_outward = edxml.miner.inference.SameObjectInference(self, node, ident_confidence)

            # Add edges to self and to the event object node. Note that
            # the direction of the edge depends on the perspective.
            self.add_inward(edge_inward)
            self.add_outward(edge_outward)
            node.add_outward(edge_inward)
            node.add_inward(edge_outward)


class NodeCollection(UserDict, MutableMapping[str, Node]):
    """--
    A dictionary containing a set of Node instances indexed by their ID.
    """
    def compute_net_confidence(self, seed_id):
        """

        Computes the net confidence of the nodes as viewed from
        the perspective of specified seed. The net confidence is
        the likelihood that none of the nodes belongs to the concept.

        Args:
            seed_id (str): Seed ID

        Returns:
            float: Confidence
        """
        try:
            return 1.0 - reduce(mul, [1.0 - node.seed_confidences.get(seed_id, 0) for node in self.values()])
        except TypeError:
            raise ValueError("None of the nodes in the collection is part of specified seed.")
