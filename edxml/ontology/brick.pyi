# -*- coding: utf-8 -*-

from edxml.ontology import Ontology, ObjectType, Concept
from typing import List


class Brick(object):

    @classmethod
    def generate_object_types(cls, target_ontology: Ontology) -> List[ObjectType]: ...

    @classmethod
    def generate_concepts(cls, target_ontology: Ontology) -> List[Concept]: ...

    @classmethod
    def test(cls): ...

    @classmethod
    def as_xml(cls) -> bytes: ...
