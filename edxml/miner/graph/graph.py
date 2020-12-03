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

from collections import defaultdict
from functools import reduce
from typing import Dict, Set, Iterable

from edxml.ontology import Ontology
from edxml.miner.node import Node, EventObjectHub, EventObjectNode
from edxml.miner.result import MinedConceptAttribute, MinedConceptInstance, MinedConceptInstanceCollection


class ConceptInstanceGraph(object):
    """
    Class representing a graph of concept nodes. The graph
    can contain information about a single concept instance
    or about multiple concepts. Depending on the graph topology
    these instances may or may not be related.
    """

    def __init__(self, ontology=None):
        self._ontology = ontology if ontology is not None else Ontology()
        self._nodes = {}  # type: Dict[str, Node]
        self._object_type_value_nodes = defaultdict(lambda: defaultdict(set))  # type: Dict[str, Dict[str, Set[Node]]]
        self._hubs_by_object_type_value = defaultdict(dict)  # type: Dict[str, Dict]
        self._seed = None

    def add(self, node):
        """

        Args:
            node (Node):

        """
        if node.id in self._nodes:
            if node is not self._nodes[node.id]:
                # We have two distinct node instances with the
                # same ID. This indicates a problem in the logic
                # of the caller that generates the nodes.
                raise ValueError(f"Attempt to add multiple instances of node {node.id}.")
            return

        self._nodes[node.id] = node
        # Add object value to index. We use the index to efficiently
        # construct concept graphs.
        self._object_type_value_nodes[node.object_type_name][node.value].add(node)
        # Also add children to index
        for edge in node.get_inferences():
            if not isinstance(edge.target, EventObjectHub):
                self.add(edge.target)

    def mine(self, seed=None, min_confidence=0.1, max_depth=10):
        """

        Mines the graph for concept instances. When a seed is specified, only
        the concept instance containing the specified seed is mined. When no
        seed is specified, an optimum set of seeds will be selected and mined,
        covering the entire graph. The algorithm will auto-select the strongest
        concept identifiers spread across the graph as seeds. Any previously
        obtained concept mining results will be discarded in the process.

        Concept instances are constructed within specified confidence and
        recursion depth limits.

        Args:
            seed (EventObjectNode): Concept seed
            min_confidence (float): Confidence cutoff
            max_depth (int): Max recursion depth
        """
        if seed is None:
            self._auto_mine(min_confidence=min_confidence, max_depth=max_depth)
        else:
            self._set_seed(seed, min_confidence=min_confidence, max_depth=max_depth)

    def _auto_mine(self, min_confidence=0.1, max_depth=10):
        """

        Returns a collection of concept instances selected from the strongest
        concept identifiers in the graph. Concept instances are constructed
        within specified confidence and recursion depth limits.

        Args:
            min_confidence (float): Confidence cutoff
            max_depth (int): Max recursion depth

        """

        # For producing a concept instance we must pick one of its nodes as
        # the seed and find other associated nodes that probably belong to
        # the same concept instance. This means we could generate one concept
        # instance for each node in the graph. This would likely produce many
        # duplicate instances.
        # Below we will try and find the smallest set of concept instances
        # that covers the entire graph by selecting seeds that are spread evenly
        # across the extent of the graph and which are strong identifiers of the
        # concept they represent.
        # How strong of an identifier a particular node is, is determined by
        # the confidence of the property-concept associations of event
        # properties. These associations are stored in the nodes.

        self.reset()

        while True:
            seed = self.find_optimal_seed()

            if seed is None:
                # When the best seed we can find
                # is tainted, all nodes have been
                # used and we are done.
                break

            self.mine(seed, min_confidence=min_confidence, max_depth=max_depth)

    def find_optimal_seed(self, max_taint=0):
        """

        Finds and returns the optimal seed for constructing a new concept instance or None in
        case all nodes are badly tainted. The taint of a node is the confidence of the node
        being part of any previously mined concepts. A seed is considered optimal if it is a
        strong identifier of a concept.

        Args:
            max_taint (float): Node taint limit

        Returns:
            Optional[EventObjectNode]:

        """
        # We sort the nodes by taint (ascending) and confidence (descending) and pick
        # the first one as optimal concept seed. This selection method ensures that we pick
        # a seed that is not close to any previously selected seeds and is a strong identifier
        # for a new concept.
        seeds = sorted(
            (node for node in self._nodes.values() if isinstance(node, EventObjectNode) and node.taint <= max_taint),
            key=lambda node: (1.0 - node.taint, node.concept_association.get_confidence()),
            reverse=True
        )

        if not seeds:
            return None

        return seeds[0]

    def extract_result_set(self, min_confidence=0.1):
        """

        Extracts the concept mining results from the graph, skipping any results
        that have confidence below specified threshold.

        Args:
            min_confidence (float): Confidence threshold

        Returns:
            MinedConceptInstanceCollection:

        """
        concept_value_nodes = defaultdict(lambda: defaultdict(dict))

        for node in self._nodes.values():
            if not isinstance(node, EventObjectNode):
                # We only want to include event object nodes,
                # as these represent event object data. Other
                # types of nodes, like shared object hubs are
                # just guidance to the inference and do not
                # directly represent event data.
                continue
            for seed_id, confidence in node.seed_confidences.items():
                if confidence < min_confidence:
                    continue
                if node.value not in concept_value_nodes[seed_id][node.attribute_name]:
                    concept_value_nodes[seed_id][node.attribute_name][node.value] = MinedConceptAttribute(
                        seed_id, node.attribute_name, node.value
                    )
                concept_value_nodes[seed_id][node.attribute_name][node.value].nodes[node.id] = node

        results = MinedConceptInstanceCollection()
        for seed_id, attribute_nodes in concept_value_nodes.items():
            results.concepts[seed_id] = MinedConceptInstance(seed_id)
            for attribute_name, value_nodes in attribute_nodes.items():
                for value, attribute in value_nodes.items():
                    results.concepts[seed_id].add_attribute(attribute)

        return results

    def _ensure_hubs(self, seed, origin, confidence=1.0, depth=1, min_confidence=0.1, max_depth=10):
        """

        Performs reasoning starting from the specified seed and continuing until the confidence
        becomes too low or until the depth limit is reached.
        While reasoning, any missing shared object hubs are created as needed.

        Args:
            seed (Node): Concept seed
            origin (Node): Starting node
            confidence (float): Current Recursion confidence
            depth (int): Current recursion depth
            max_depth (int): Recursion depth cutoff
            min_confidence (float): Recursion cutoff

        """

        if confidence < min_confidence or depth > max_depth:
            # This method is called recursively and we use both
            # a depth and confidence cutoff to determine where to stop.
            return

        origin.visited = True

        shared_value_nodes = self._object_type_value_nodes[origin.object_type_name][origin.value]

        if origin.object_type_name not in self._hubs_by_object_type_value or \
                origin.value not in self._hubs_by_object_type_value[origin.object_type_name]:
            # Hub does not exist yet, create it. Note that this will automatically
            # create edges between the nodes and the hub.
            hub = EventObjectHub(origin.object_type_name, origin.value, shared_value_nodes)
            self._hubs_by_object_type_value[origin.object_type_name][origin.value] = hub
            self._nodes[hub.id] = hub

        # For each of the nodes connected to the hub we fetch its intra-concept
        # edges. The, we recurse to create the hubs for the target nodes of these edges.
        for node in shared_value_nodes:
            edges = node.get_intra_concept_inferences()
            for edge in edges:
                if edge.target.visited:
                    continue
                self._ensure_hubs(
                    seed,
                    edge.target,
                    confidence=confidence * edge.confidence,
                    depth=depth + 1,
                    min_confidence=min_confidence,
                    max_depth=max_depth
                )

    def _set_seed(self, seed, min_confidence=0.1, max_depth=10):
        """

        Sets the specified seed of the concept graph. The seed is the node that is
        known to belong to the concept. When set, the confidences of all
        other nodes relative to the seed are computed up to the specified
        accuracy.

        Args:
            seed (EventObjectNode): The seed node
            min_confidence (float): Confidence cutoff
            max_depth (int): Max recursion depth

        """

        self._clear_visited_status()
        self._clear_edge_roles()
        self._ensure_hubs(seed, seed, min_confidence=min_confidence, max_depth=max_depth)
        self._reason_from(seed, min_confidence=min_confidence, max_depth=max_depth)
        self._update_seed_taints()
        seed.taint = 1.0
        self._seed = seed

    def _reason_from(self, seed, min_confidence=0.1, max_depth=10):
        """

        Finds the best reasoning paths for the nodes in the graph from the
        perspective of given node within that graph: the seed. The seed is
        the initial premise that defines the concept instance. By definition
        it has confidence = 1. We use a variant of Dijkstra's algorithm to
        find the shortest paths from the seed to other nodes, which also sets
        the confidences of these nodes.

        Args:
            seed (EventObjectNode): Concept instance seed
            min_confidence (float): Confidence cutoff
            max_depth (int): Max recursion depth

        """

        for node in self._get_nodes():
            node.depth = 0
            node.visited = False

        seed.visited = True
        seed.seed_confidences[seed.id] = 1.0
        seed.concept_name_equivalents = defaultdict(dict)
        seed.concept_name_equivalents[seed.concept_name] = {seed.id: 1.0}

        node = seed
        nodes_unvisited_touched = set()

        # TODO: While reasoning we may discover other concepts that the concept instance
        #       might be an instance of. These are accumulated in the seed. This means we
        #       could ignore a possible inference step and later discover the inter-concept
        #       inference that would have allowed us to use it. We need a second pass to
        #       improve reasoning paths based on these new inference opportunities.

        while node is not None and node.seed_confidences[seed.id] >= min_confidence and node.depth < max_depth:

            # Find all edges to unvisited nodes, for as far as these edges
            # do not jump to another concept instance.
            edges = node.get_same_concept_inferences(seed, min_confidence)

            # Use the edges to check all neighbors.
            for edge in edges:
                if edge.target.visited:
                    continue
                confidence = edge.compute_dijkstra_confidence(seed)
                if confidence > min_confidence and confidence > edge.target.seed_confidences.get(seed.id, 0):
                    # We found a shorter path to the target node of this edge. We
                    # will configure the edge as the reason for including the target
                    # node in the concept instance, replacing any previously used edge.
                    edge.reason(seed, confidence)
                    edge.target.depth = edge.source.depth + 1
                    if not edge.target.visited:
                        nodes_unvisited_touched.add(edge.target)

            node.visited = True
            try:
                nodes_unvisited_touched.remove(node)
            except KeyError:
                pass

            # In order to find the closest unvisited node to process next, we sort the set of
            # unvisited, touched nodes by their confidence. Considering only the touched nodes
            # is an optimization. Nodes are considered untouched as long as we have not assigned it
            # a confidence yet, which implies that their confidence is zero. Below, we ignore these
            # nodes assuming that a single concept instance will be small compared to the full graph,
            # allowing us to ignore a large part of the graph.
            sorted_nodes = sorted(nodes_unvisited_touched, key=lambda n: n.seed_confidences[seed.id], reverse=True)

            if sorted_nodes:
                node = sorted_nodes[0]
            else:
                node = None

    def _update_seed_taints(self):
        for node in self._nodes.values():
            if not isinstance(node, EventObjectNode):
                # We only want event objects to get
                # tainted, not shared object hubs.
                continue
            confidences = node.seed_confidences.values()
            num_confidences = len(confidences)
            if num_confidences == 0:
                new_taint = 0.0
            elif num_confidences == 1:
                new_taint = list(confidences)[0]
            else:
                new_taint = 1.0 - reduce(lambda x, y: (1.0 - x) * (1.0 - y), confidences)
            node.taint = max(node.taint, new_taint)

    def reset(self):
        """
        Clears artifacts of previous concept mining from the graph
        """
        self._seed = None
        self._hubs_by_object_type_value = defaultdict(dict)

        for node in list(self._nodes.values()):
            if isinstance(node, EventObjectHub):
                del self._nodes[node.id]
                continue
            node.reset()

    def _get_nodes(self) -> Iterable[Node]:
        return self._nodes.values()

    def _clear_visited_status(self):
        for node in self._nodes.values():
            node.visited = False

    def _clear_edge_roles(self):
        for node in self._nodes.values():
            node.clear_edge_roles()

    def update_ontology(self, ontology):
        self._ontology.update(ontology)
