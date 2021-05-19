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

..  autoclass:: GraphConstructor
    :members:
    :show-inheritance:
"""
from dateutil.parser import parse

from edxml.miner.node import EventObjectNode
from edxml.ontology import Ontology


class GraphConstructor(object):
    """
    Constructs graph from EDXML events. Used in conjunction with
    the EventCollector class.
    """

    def __init__(self, graph, ontology=None):
        """

        Args:
            ontology (edxml.ontology.Ontology)
            graph (edxml.miner.graph.ConceptInstanceGraph):
        """
        self._ontology = ontology if ontology is not None else Ontology()
        self._graph = graph
        self._next_event_id = 0

    def add(self, event):
        """

        Expands the graph using information from specified EDXML event.

        Args:
            event (edxml.EDXMLEvent):

        """
        event_type = self._ontology.get_event_type(event.get_type_name())
        time_span = self._extract_time_span(event, event_type)
        nodes = {}
        for relation in event_type.relations:
            if relation.get_type() in ['inter', 'intra']:
                nodes = self._add_relation_nodes(event_type, relation, event, nodes, time_span)

        # Properties that are not part of a concept relation may still be associated
        # with a concept. Below, we check the remaining properties and process the
        # ones that have concept associations.
        relation_properties = set()
        for relation in event_type.relations:
            if relation.get_type() in ['inter', 'intra']:
                relation_properties.add(relation.get_source())
                relation_properties.add(relation.get_target())

        for property_name, event_property in event_type.get_properties().items():
            if property_name in relation_properties:
                # Property objects have already been added.
                continue
            for concept_name, concept_association in event_property.get_concept_associations().items():
                # This property is not part of any concept relation, but it is associated
                # with one or more concepts.
                for value in event[property_name]:
                    node = EventObjectNode(
                        self._next_event_id,
                        concept_association,
                        event_property.get_object_type_name(),
                        value,
                        event_property.get_confidence(),
                        time_span
                    )
                    if node.id in nodes:
                        node = nodes[node.id]
                    else:
                        nodes[node.id] = node
                    self._graph.add(node)

        self._next_event_id += 1

    def _add_relation_nodes(self, event_type, relation, event, nodes, time_span):
        source_property = event_type[relation.get_source()]
        target_property = event_type[relation.get_target()]
        concept_association_source = source_property.get_concept_associations()[relation.get_source_concept()]
        concept_association_target = target_property.get_concept_associations()[relation.get_target_concept()]

        source_nodes = []
        target_nodes = []
        for value in event[relation.get_source()]:
            node = EventObjectNode(
                self._next_event_id,
                concept_association_source,
                source_property.get_object_type_name(),
                value,
                source_property.get_confidence(),
                time_span
            )
            if node.id in nodes:
                node = nodes[node.id]
            else:
                nodes[node.id] = node
            source_nodes.append(node)
        for value in event[relation.get_target()]:
            node = EventObjectNode(
                self._next_event_id,
                concept_association_target,
                target_property.get_object_type_name(),
                value,
                target_property.get_confidence(),
                time_span
            )
            if node.id in nodes:
                node = nodes[node.id]
            else:
                nodes[node.id] = node
            target_nodes.append(node)
        for source_node in source_nodes:
            self._graph.add(source_node)
            for target_node in target_nodes:
                self._graph.add(target_node)
                source_node.link_relation(target_node, relation)
        return nodes

    def _extract_time_span(self, event, event_type):
        if event_type.is_timeless():
            return None

        timespan_prop_start = event_type.get_timespan_property_name_start()
        timespan_prop_end = event_type.get_timespan_property_name_end()

        event_timestamps = []
        if timespan_prop_start is None or timespan_prop_end is None:
            for property_name, prop in event_type.get_properties().items():
                if prop.get_object_type().get_data_type().is_datetime():
                    event_timestamps.extend(event.properties[property_name])

        if timespan_prop_start is None:
            if event_timestamps:
                timespan_start = min(event_timestamps)
            else:
                timespan_start = None
        else:
            timespan_start = event.get_any(timespan_prop_start)

        if timespan_prop_end is None:
            if event_timestamps:
                timespan_end = max(event_timestamps)
            else:
                timespan_end = None
        else:
            timespan_end = event.get_any(timespan_prop_end)

        if isinstance(timespan_start, str):
            timespan_start = parse(timespan_start)
        if isinstance(timespan_end, str):
            timespan_end = parse(timespan_end)

        return timespan_start, timespan_end

    def update_ontology(self, ontology):
        """

        Updates the ontology that describes the events that have been
        added to the graph.

        Args:
            ontology (edxml.ontology.Ontology):

        """
        self._ontology.update(ontology)
        self._graph.update_ontology(ontology)
