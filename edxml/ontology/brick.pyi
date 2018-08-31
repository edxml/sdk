# -*- coding: utf-8 -*-

import edxml
from typing import List


class Brick(object):

    @classmethod
    def generate_object_types(cls, target_ontology: edxml.ontology.Ontology) -> List[edxml.ontology.ObjectType]: ...

    @classmethod
    def generate_concepts(cls, target_ontology: edxml.ontology.Ontology) -> List[edxml.ontology.Concept]: ...
