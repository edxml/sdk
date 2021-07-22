#!/usr/bin/env python3

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

import argparse
import logging
import sys
from collections import defaultdict

from edxml.cli import configure_logger
from edxml.miner.graph.visualize import graphviz_nodes, graphviz_concepts
from edxml.miner.inference import RelationInference
from edxml.miner.knowledge import KnowledgePullParser, KnowledgeBase


def parse_args():
    parser = argparse.ArgumentParser(
        description="This utility performs concept mining on EDXML data received on standard input or from a file."
    )

    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='By default, input is read from standard input. This option can be used to read from a '
             'file in stead.'
    )

    parser.add_argument(
        '--min-confidence', type=float, default=0.1, help='Confidence threshold in range [0,1] for the mining process.'
    )

    parser.add_argument(
        '--max-depth', type=int, default=10, help='Maximum number of reasoning iterations for the mining process.'
    )

    parser.add_argument(
        '--verbose', '-v', action='count', help='Increments the output verbosity of logging messages on standard error.'
    )

    parser.add_argument(
        '--quiet', '-q', action='store_true', help='Suppresses all logging messages except for errors.'
    )

    parser.add_argument(
        '--tell', action='store_true', help='Prints descriptions of findings while mining.'
    )

    parser.add_argument(
        '--with-reasons', action='store_true', help='When used with --tell, prints the reasons for the findings.'
    )

    parser.add_argument(
        '--dump-json', action='store_true', help='Prints a JSON representation of the mined knowledge.'
    )

    parser.add_argument(
        '--dump-concept-graph', type=str, help='Dumps a PNG image of the concept graph to specified output file.'
    )

    parser.add_argument(
        '--dump-mining-graph', type=str,
        help='Dumps a PNG image of the full concept mining graph to specified output file.'
    )

    return parser.parse_args()


def main():

    args = parse_args()
    configure_logger(args)

    min_confidence = min(1.0, max(0.0, args.min_confidence))
    max_depth = max(0, args.max_depth)

    logging.info("Constructing graph...")
    input = open(args.file, 'rb') if args.file else sys.stdin.buffer

    knowledge_base = KnowledgeBase()
    parser = KnowledgePullParser(knowledge_base).parse(input)
    logging.info("Graph complete.")

    ontology = parser._ontology

    found_concepts = set()
    instance_concepts = defaultdict(set)

    while True:
        seed = parser._graph.find_optimal_seed()

        if seed is None:
            # When the best seed we can find
            # is tainted, all nodes have been
            # used and we are done.
            break

        seed_dn = seed.concept_association.get_attribute_display_name_singular()
        logging.info(f"Selected seed: {seed_dn} = {seed.value}")

        parser.mine(seed, min_confidence=min_confidence, max_depth=max_depth)
        results = knowledge_base.concept_collection
        # Find the ID of the newly created concept and report it.
        concept_id = next(iter(set(results.concepts.keys()) - found_concepts))
        concept = results.concepts[concept_id]
        if args.tell:
            instance_concepts[seed.id] = {(seed.concept_association.get_concept_name())}
            instance_concepts = report_new_concept(ontology, seed.id, concept, instance_concepts, args.with_reasons)
        found_concepts.add(concept_id)

    if args.dump_json:
        print(knowledge_base.to_json(indent=True))
    if args.dump_concept_graph:
        logging.info(f"Dumped concept graph into {args.dump_concept_graph}.png")
        graphviz_concepts(knowledge_base.concept_collection).render(filename=args.dump_concept_graph, format='png')
    if args.dump_mining_graph:
        logging.info(f"Dumped mining graph into {args.dump_mining_graph}.png")
        graphviz_nodes(knowledge_base.concept_collection).render(filename=args.dump_mining_graph, format='png')


def report_new_concept(ontology, seed_id, concept_instance, instance_concepts, with_reasons):
    concept = ontology.get_concept(concept_instance.get_best_concept_name())
    concept_dn = concept.get_display_name_singular()

    print(f"\nFound a {concept.get_display_name_singular()}: '{concept_instance.get_instance_title()}'")

    for attr in concept_instance.attributes:
        for attr_concept in attr.concept_names.keys():
            if attr_concept not in instance_concepts[seed_id]:
                instance_concepts[seed_id].add(attr_concept)
                alternative_concept_dn = ontology.get_concept(attr_concept).get_display_name_singular()
                print(f"Discovery: this {concept_dn} is a {alternative_concept_dn}.")
        descriptions = defaultdict(set)
        for node in attr.nodes.values():
            if not isinstance(node.reason, RelationInference):
                continue
            relation = node.reason.relation
            source_value = node.reason.source.value
            target_value = node.reason.target.value
            source_dn = node.reason.source.concept_association.get_attribute_display_name_singular()
            target_dn = node.reason.target.concept_association.get_attribute_display_name_singular()
            if relation.is_reversed():
                # The node relation is reversed, which means that the source and target values come
                # out in the wrong order when joining them together using the relation predicate.
                source_dn, target_dn = target_dn, source_dn
                source_value, target_value = target_value, source_value

            description = "Found attribute: "
            description += f"'{source_value}' ({source_dn}) {relation.get_predicate()} '{target_value}' ({target_dn})"
            descriptions[description].add('')
            if with_reasons:
                reason = "\n                 Reason: "
                reason += relation.evaluate_description(
                    event_properties={
                        relation.get_source(): {source_value},
                        relation.get_target(): {target_value}
                    }
                )
                descriptions[description].add(reason)

        print(',\n'.join([description + ''.join(reasons) for description, reasons in descriptions.items()]))

    return instance_concepts


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
