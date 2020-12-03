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

import edxml.miner


class Inference(object):
    """

    An edge in a concept instance graph representing the
    inference of a relation between two nodes.

    """

    def __init__(self, source_node, target_node, confidence):
        """

        Args:
            source_node (edxml.miner.Node):
            target_node (edxml.miner.Node):
        """

        self.source = source_node  # type: edxml.miner.Node
        self.target = target_node  # type: edxml.miner.Node
        self.confidence = confidence
        self.seeds = set()

    def __repr__(self):
        return f"{self.source.id} => {self.target.id}"

    def reason(self, seed, confidence):
        """
        Performs a reasoning step by using this inference to
        go from the source node to the target node. When the
        target node was previously reasoned to from any other
        source node, that source node will be detached from
        the target node first.

        Args:
            seed (edxml.miner.Node): Seed of the concept instance
            confidence: New confidence of target node

        """
        self.target.seed_confidences[seed.id] = confidence

        # Remove the current edge to target.
        if self.target.reason is not None:
            self._unlink_reason(seed)

        # Add newly found conclusion
        self.seeds.add(seed.id)
        self.source.conclusions.add(self)
        self.target.reason = self.target._edges_inward[self.source.id]

    def _unlink_reason(self, seed):
        prev_source = self.target.reason.source
        self.target.reason.seeds.remove(seed.id)
        prev_source.conclusions.difference_update([c for c in prev_source.conclusions if c.target is self.target])

    def compute_dijkstra_confidence(self, seed):
        """

        Returns the confidence of the target node for use as edge length when
        using Dijkstra's algorithm for finding the shortest path to a given node.

        Args:
            seed (edxml.miner.Node): Concept seed

        Returns:
            float:
        """

        # We compute confidence by combining three factors:
        # 1. Confidence of the edge
        # 2. Confidence of the target node with respect to the source
        # 3. Taint of the target node. Taint is the confidence of the target
        #    node being part of a concept instance defined by a previously
        #    used concept seed. This has the effect of making paths that enter
        #    the territory of another concept instance longer. As a special
        #    case, the confidence of a node that was previously selected as
        #    a concept seed becomes zero and will never be considered for
        #    inclusion in any other concept instance.
        return self.source.seed_confidences[seed.id] * self.confidence * (1.0 - self.target.taint) * \
            self.target.confidence


class SameObjectInference(Inference):
    """
    An edge in a concept instance graph formed by connecting
    identical object values shared between two different events.
    It represents inferring that two nodes represent the same object
    value.
    The confidence of the edge is determined by the property-concept
    association of the target property that contains the value.
    """
    ...


class RelationInference(Inference):
    """
    An edge in a concept instance graph formed by connecting
    object values related by means of a property relation within
    a single event. It represents inferring that two nodes either
    belong to the same concept instance or to a pair of related
    concept instances. The confidence of the edge is
    determined by the confidence of the property relation.
    """

    def __init__(self, source_node, target_node, relation):
        """

        Args:
            source_node (edxml.miner.node.EventObjectNode):
            target_node (edxml.miner.node.EventObjectNode):
            relation (edxml.ontology.PropertyRelation):
        """
        self.relation = relation
        self.source = ...  # type: edxml.miner.node.EventObjectNode
        self.target = ...  # type: edxml.miner.node.EventObjectNode

        # Note that relation confidence is in range [1,10]
        super().__init__(source_node, target_node, 0.1 * relation.get_confidence())

    def reason(self, seed, confidence):
        super().reason(seed, confidence)
        if self.relation.get_type() == 'intra':
            # Intra-concept relations can identify multiple concepts that
            # each describe the concept instance that is being constructed.
            # We accumulate these in the seed while reasoning, allowing
            # shared object inference to use these to determine which kinds
            # of event type properties it can safely add to the concept
            # instance.
            seed.concept_name_equivalents[self.target.concept_name][self.target.id] = confidence
