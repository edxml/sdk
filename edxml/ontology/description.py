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

from edxml.ontology import Ontology, Concept


def describe_producer_rst(ontology, producer_name, input_description):
    """
    Returns a reStructuredText description for a producer of an
    ontology, such as a transcoder or a processor.

    Args:
        ontology (edxml.ontology.Ontology): The ontology
        producer_name (str): Name of the ontology producer
        input_description (str): Short description of the data used as input by producer

    Returns:
        str: reStructuredText description
    """

    description = f"\n\nThis is a {producer_name} that reads {input_description} and produces " \
                  f"`EDXML <http://edxml.org/>`_ containing {_describe_event_types(ontology)}.\n"

    relates_inter = _describe_inter_concept_relations(ontology)
    relates_intra = _describe_intra_concept_relations(ontology)
    concept_combinations = _describe_concept_universals(
        ontology,
        '- {concept_source} as {concept_target}'
    )
    concept_combinations.update(_describe_concept_specializations(
            ontology,
            '- {concept_source} as {concept_target} (using {event_type})'
        )
    )

    if relates_inter:
        description += f"\nThe {producer_name} enables automatic correlation of:\n"
        for source_concept_name, target_concept_names in relates_inter.items():
            for target_concept_name, event_type_names in target_concept_names.items():
                source_concept_dn = ontology.get_concept(source_concept_name).get_display_name_plural()
                target_concept_dn = ontology.get_concept(target_concept_name).get_display_name_plural()
                if source_concept_name == target_concept_name:
                    description += f"\n- Multiple {source_concept_dn} to discover interconnected networks (using "
                else:
                    description += f"\n- {source_concept_dn.capitalize()} to {target_concept_dn} (using "
                event_type_dn = []
                for event_type_name in event_type_names:
                    event_type_dn.append(ontology.get_event_type(event_type_name).get_display_name_plural())
                description += _list_strings(event_type_dn) + ')'

    if relates_intra:
        description += f"\n\nThe {producer_name} enhances `concept mining <http://edxml.org/concept-mining>`_ " \
                       "by expanding knowledge about:\n"

    expansions = defaultdict(set)
    for concept_name, attribute_names in relates_intra.items():
        concept_dn = ontology.get_concept(concept_name).get_display_name_plural()
        expansions[concept_dn].update(attribute_names)

    for concept_dn, object_types in expansions.items():
        description += f"\n:{concept_dn.capitalize()}: Discovering new " + _list_strings(object_types)

    if concept_combinations:
        description += f"\n\nThe {producer_name} identifies:\n" + '\n'.join(set(concept_combinations.values()))

    value_names = set()
    value_descriptions = set()
    value_containers = set()
    for event_type in ontology.get_event_types().values():
        for relation in event_type.get_property_relations(relation_type='name').values():
            value_names.add(
                event_type.get_properties()[relation.get_target()].get_object_type().get_display_name_plural()
            )
        for relation in event_type.get_property_relations(relation_type='description').values():
            value_descriptions.add(
                event_type.get_properties()[relation.get_target()].get_object_type().get_display_name_plural()
            )
        for relation in event_type.get_property_relations(relation_type='container').values():
            value_containers.add(
                event_type.get_properties()[relation.get_target()].get_object_type().get_display_name_plural() +
                ' as being part of a ' +
                event_type.get_properties()[relation.get_source()].get_object_type().get_display_name_singular()
            )

    if value_names:
        description += f"\n\nThe {producer_name} provides names for " + _list_strings(value_names) + '.'
    if value_descriptions:
        description += f"\n\nThe {producer_name} provides descriptions for " + _list_strings(value_descriptions) + '.'
    if value_containers:
        description += f"\n\nThe {producer_name} identifies " + _list_strings(value_containers) + '.'

    concepts = _describe_concepts(ontology)
    object_types = _describe_object_types(ontology)

    description += f"\n\nThe output can be auto-correlated with third party data sources that share any of the " \
                   f"concepts and object types generated by this {producer_name}. These are listed below."

    if concepts:
        description += '\n\n'
        description += 'Concepts\n'
        description += '--------\n'
        for concept in sorted(concepts):
            description += f"\n- {concept}"

    if object_types:
        description += '\n\n'
        description += 'Object Types\n'
        description += '------------\n'
        for object_type in sorted(object_types):
            description += f"\n- {object_type}"

    return description


def _describe_concepts(ontology: Ontology):
    concept_names = []
    for concept in ontology.get_concepts().values():
        concept_names.append(f"{concept.get_name()} ({concept.get_display_name_singular()})")
    return concept_names


def _describe_object_types(ontology: Ontology):
    object_type_names = []
    for object_type in ontology.get_object_types().values():
        object_type_names.append(f"{object_type.get_name()} ({object_type.get_display_name_singular()})")
    return object_type_names


def _describe_event_types(ontology: Ontology):
    type_names = []
    for event_type_name in ontology.get_event_type_names():
        type_names.append(ontology.get_event_type(event_type_name).get_display_name_plural())
    return _list_strings(type_names)


def _describe_inter_concept_relations(ontology: Ontology):
    relations = defaultdict(lambda: defaultdict(set))
    for event_type_name in ontology.get_event_type_names():
        event_type = ontology.get_event_type(event_type_name)
        for relation in event_type.relations:
            if relation.get_type() != 'inter':
                continue
            relations[relation.get_source_concept()][relation.get_target_concept()].add(event_type_name)
    return relations


def _describe_intra_concept_relations(ontology: Ontology):
    relations = defaultdict(set)
    for event_type_name in ontology.get_event_type_names():
        event_type = ontology.get_event_type(event_type_name)
        for relation in event_type.relations:
            if relation.get_type() != 'intra':
                continue
            relations[relation.get_source_concept()].add(
                event_type[relation.get_source()].get_concept_associations()[relation.get_source_concept()]
                .get_attribute_display_name_plural(),
            )
            relations[relation.get_target_concept()].add(
                event_type[relation.get_target()].get_concept_associations()[relation.get_target_concept()]
                .get_attribute_display_name_plural(),
            )
    return relations


def _describe_concept_specializations(ontology: Ontology, item_template):
    descriptions = {}
    for event_type_name in ontology.get_event_type_names():
        event_type = ontology.get_event_type(event_type_name)
        for relation in event_type.relations:
            if relation.get_type() != 'intra':
                continue
            source_concept = ontology.get_concept(relation.get_source_concept())
            target_concept = ontology.get_concept(relation.get_target_concept())
            if source_concept.get_name() == target_concept.get_name():
                continue
            descriptions[(source_concept.get_name(), target_concept.get_name())] = item_template.format(**{
                'concept_source': source_concept.get_display_name_plural(),
                'concept_target': target_concept.get_display_name_plural(),
                'event_type': event_type.get_display_name_plural()
            })

    return descriptions


def _describe_concept_universals(ontology: Ontology, item_template):
    descriptions = {}
    for concept_name in ontology.get_concept_names():
        # Search for a base concept by traversing all specializations until
        # we find one that exists.
        for parent in Concept.generate_specializations(concept_name):
            # Note that we do not want to import any concepts here, as that
            # may pull in concepts that are not actually used in the ontology.
            source_concept = ontology.get_concept(parent, import_brick=False)
            if source_concept is None:
                continue

            # Search for specializations of the parent name to generate pairs of
            # concepts that are a generalization and a specialization of the base concept.
            # So, given a parent concept of a.b we try to pair it with a.b.c.
            for specialization in Concept.generate_specializations(concept_name, parent):
                # Note that we do not want to import any concepts here, as that
                # may pull in concepts that are not actually used in the ontology.
                target_concept = ontology.get_concept(specialization, import_brick=False)
                if target_concept is None:
                    continue

                descriptions[(source_concept.get_name(), target_concept.get_name())] = item_template.format(**{
                    'concept_source': source_concept.get_display_name_plural(),
                    'concept_target': target_concept.get_display_name_plural()
                })

    return descriptions


def _list_strings(strings):
    if len(strings) > 1:
        last = strings.pop()
        return ', '.join(strings) + ' and ' + last
    else:
        return ' and '.join(strings)
