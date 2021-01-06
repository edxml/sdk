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

from edxml.ontology import Concept
from edxml.util import truncate_string


def generate_graph_property_concepts(ontology, graph):
    """
    Appends nodes and edges to specified Digraph that show possible concept
    mining reasoning paths.

    Args:
        ontology (edxml.ontology.Ontology):
        graph (graphviz.Digraph):
    """

    confidence_colors = [
        'red2',
        'red2',
        'orange2',
        'orange2',
        'orange2',
        'gold3',
        'gold3',
        'gold3',
        'forestgreen',
        'forestgreen',
        'forestgreen',
    ]

    graph.node(
        "title",
        "<Concept Mining<br/><font point-size='32'>Inference Pathways</font>>",
        fontsize='64',
        shape='none'
    )

    type_property_concepts = dict()
    for event_type_name, event_type in ontology.get_event_types().items():
        type_property_concepts[event_type_name] = {}
        for property_name, event_property in event_type.get_properties().items():
            type_property_concepts[event_type_name][property_name] = set()
            for concept_name, concept in event_property.get_concept_associations().items():
                type_property_concepts[event_type_name][property_name].add(concept_name)

    for event_type_name, properties in type_property_concepts.items():
        event_type = ontology.get_event_type(event_type_name)
        for property_name, concepts in properties.items():
            event_property = event_type.get_properties()[property_name]
            for concept_name in concepts:
                concept = ontology.get_concept(concept_name)
                concept_association = event_property.get_concept_associations()[concept_name]

                # Color nodes by their confidence
                node_color = confidence_colors[concept_association.get_confidence()]

                fields = [
                    '<TD BGCOLOR="%s"></TD>' % node_color,
                    _get_property_node_title(
                        concept_association.get_attribute_display_name_singular(),
                        concept.get_display_name_singular(),
                        f"{event_type.get_display_name_singular()}",
                    ),
                ]
                title = '<<TABLE STYLE="ROUNDED" BORDER="0" COLOR="#eeeeee" BGCOLOR="#eeeeee" CELLBORDER="0" ' \
                        'CELLSPACING="6"><TR>' + ''.join(fields) + '</TR></TABLE>>'

                graph.node(
                    f"property_{event_type_name}_{property_name}_{concept_name}",
                    title,
                    color='transparent'
                )
                _add_shared_object_edges(
                    ontology,
                    graph,
                    event_type_name,
                    property_name,
                    concept_name,
                    type_property_concepts
                )

        for relation in ontology.get_event_type(event_type_name).get_property_relations(relation_type='intra').values():
            source = f"property_{event_type_name}_{relation.get_source()}_{relation.get_source_concept()}"
            target = f"property_{event_type_name}_{relation.get_target()}_{relation.get_target_concept()}"
            label = f"label_{source}_{target}"
            graph.node(label, relation.get_predicate(), shape='none', fontsize='8', margin='0.005')
            graph.edge(
                source,
                label,
                arrowhead='none',
                weight=str(relation.get_confidence())
            )
            graph.edge(
                label,
                target,
                weight=str(relation.get_confidence())
            )

        for relation in ontology.get_event_type(event_type_name).get_property_relations(relation_type='inter').values():
            source = f"property_{event_type_name}_{relation.get_source()}_{relation.get_source_concept()}"
            target = f"property_{event_type_name}_{relation.get_target()}_{relation.get_target_concept()}"
            label = f"label_{source}_{target}"
            graph.node(label, relation.get_predicate(), shape='none', fontsize='8', margin='0.005')
            graph.edge(
                source,
                label,
                arrowhead='none',
                weight='0',
                style='dashed'
            )
            graph.edge(
                label,
                target,
                weight='0',
                style='dashed'
            )


def _get_property_node_title(title, subtitle, subsubtitle):
    node_subtitle = truncate_string(subtitle, 32)
    node_subsubtitle = truncate_string(subsubtitle, 32)

    node_title = truncate_string(title, 24)
    node_title += f"<br/><font point-size='11'>{node_subtitle}</font>"
    node_title += f"<br/><font point-size='10'>{node_subsubtitle}</font>"
    return f"<TD>{node_title}</TD>"


def _add_shared_object_edges(ontology, graph, event_type_name, property_name, concept_name, type_property_concepts):
    object_type_name = ontology.get_event_type(event_type_name).get_properties()[property_name].get_object_type_name()

    for other_event_type_name, other_properties in type_property_concepts.items():
        if other_event_type_name == event_type_name:
            continue
        other_event_type = ontology.get_event_type(other_event_type_name)

        for other_property_name, other_concepts in other_properties.items():
            if other_event_type.get_properties()[other_property_name].get_object_type_name() != object_type_name:
                # The properties of the two event types do not
                # share a common object type, so they can never
                # have shared object values.
                continue
            for other_concept_name in other_concepts:
                if not Concept.concept_names_share_branch(concept_name, other_concept_name):
                    # The properties of the two event types are not
                    # associated with a common concept.
                    continue

                object_type_node_id = f"object_type_{object_type_name}"

                # TODO: We create one node for each object type, irrespective of concept. We should split
                #       this up in nodes that represent mutually compatible concepts.
                graph.node(
                    object_type_node_id,
                    ontology.get_object_type(object_type_name).get_display_name_singular(),
                    shape='circle',
                    color='royalblue3',
                    penwidth='4'
                )

                graph.edge(
                    f"property_{event_type_name}_{property_name}_{concept_name}",
                    object_type_node_id,
                    arrowshape='odot'
                )
                graph.edge(
                    f"property_{other_event_type_name}_{other_property_name}_{other_concept_name}",
                    object_type_node_id,
                    arrowhead='odot'
                )


def parent_child_hierarchy(ontology, graph):
    """
    Appends nodes and edges to specified Digraph that show parent-child
    relations between all event types in the ontology.

    Args:
        ontology (edxml.ontology.Ontology):
        graph (graphviz.Digraph):
    """
    for event_type in ontology.get_event_types().values():
        if event_type.get_parent() is None:
            continue
        parent = event_type.get_parent()
        _gv_generate_parent_child(graph, ontology.get_event_type(parent.get_event_type_name()), event_type)


def _gv_generate_parent_child(graph, parent, child):
    parent.get_display_name_singular()
    graph.node(parent.get_name(), parent.get_display_name_singular())
    graph.node(child.get_name(), child.get_display_name_singular())
    graph.node(child.get_name() + '.siblings', 'more\n' + child.get_display_name_plural())
    graph.edge(parent.get_name(), child.get_name(), label=child.get_parent().get_parent_description())
    graph.edge(child.get_name(), child.get_name() + '.siblings', label='')
    graph.node(parent.get_name() + '.second', parent.get_display_name_singular())
    graph.edge(child.get_name() + '.siblings', parent.get_name() + '.second',
               label=child.get_parent().get_siblings_description())
