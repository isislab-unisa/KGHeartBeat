"""Evaluate quality signals that can be derived directly from an RDF/Turtle graph.

The script is intentionally a small stdin/stdout bridge for the Node web API.
It receives Turtle on stdin and prints exactly one JSON document on stdout.
"""

import json
import math
import statistics
import sys
from collections import Counter

from rdflib import BNode, Graph, Literal, RDF, RDFS, URIRef
from rdflib.namespace import DC, DCTERMS, OWL, SKOS


LABEL_PREDICATES = {RDFS.label, RDFS.comment, SKOS.prefLabel, SKOS.altLabel, DC.title, DCTERMS.title}
DECLARATION_TYPES = {RDFS.Class, OWL.Class, RDF.Property, OWL.ObjectProperty,
                     OWL.DatatypeProperty, OWL.AnnotationProperty}
RDF_STRUCTURE_TYPES = {RDF.List, RDF.Seq, RDF.Bag, RDF.Alt, RDF.Statement}
DEPRECATED_TYPES = {OWL.DeprecatedClass, OWL.DeprecatedProperty}
LICENSE_PREDICATES = {DCTERMS.license, DC.rights}


def ratio(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def uri_stats(values):
    lengths = [len(str(value)) for value in values if isinstance(value, URIRef)]
    if not lengths:
        return {"count": 0, "average": 0.0, "standard_deviation": 0.0,
                "minimum": 0, "maximum": 0}
    return {
        "count": len(lengths),
        "average": statistics.fmean(lengths),
        "standard_deviation": statistics.pstdev(lengths),
        "minimum": min(lengths),
        "maximum": max(lengths),
    }


def evaluate(turtle):
    graph = Graph()
    graph.parse(data=turtle, format="turtle")
    triples = list(graph)
    triple_count = len(triples)
    subjects = {s for s, _, _ in triples}
    predicates = {p for _, p, _ in triples}
    objects = {o for _, _, o in triples}
    resources = {term for term in subjects | objects if isinstance(term, (URIRef, BNode))}

    labeled_resources = {s for s, p, _ in triples if p in LABEL_PREDICATES}
    blank_nodes = {term for term in subjects | objects if isinstance(term, BNode)}
    rdf_structures = sum(1 for _, _, obj in graph.triples((None, RDF.type, None))
                         if obj in RDF_STRUCTURE_TYPES)

    empty_annotations = 0
    whitespace_annotations = 0
    malformed_datatypes = 0
    languages = set()
    for _, predicate, obj in triples:
        if isinstance(obj, Literal):
            if obj.language:
                languages.add(obj.language)
            if predicate in LABEL_PREDICATES:
                text = str(obj)
                empty_annotations += int(not text.strip())
                whitespace_annotations += int(bool(text) and text != text.strip())
            if obj.datatype:
                try:
                    obj.toPython()
                except (ValueError, TypeError, OverflowError):
                    malformed_datatypes += 1

    declared = {s for s, _, obj in graph.triples((None, RDF.type, None)) if obj in DECLARATION_TYPES}
    used_classes = {obj for _, _, obj in graph.triples((None, RDF.type, None)) if isinstance(obj, URIRef)}
    builtin_namespaces = (str(RDF), str(RDFS), str(OWL))
    undefined_classes = {item for item in used_classes if item not in declared and
                         not str(item).startswith(builtin_namespaces)}
    undefined_properties = {item for item in predicates if item not in declared and
                            not str(item).startswith(builtin_namespaces)}
    deprecated = {s for s, _, obj in graph.triples((None, RDF.type, None)) if obj in DEPRECATED_TYPES}

    duplicate_count = sum(count - 1 for count in Counter(triples).values() if count > 1)
    same_as_count = sum(1 for _ in graph.triples((None, OWL.sameAs, None)))
    external_links = sum(1 for _, p, obj in triples if p in {OWL.sameAs, RDFS.seeAlso} and
                         isinstance(obj, URIRef))
    licenses = sorted({str(obj) for p in LICENSE_PREDICATES for obj in graph.objects(None, p)})

    # Only locally observable dimensions participate in the score. Each component is
    # bounded to [0, 1], and the response reports what was excluded.
    dimension_scores = {
        "accuracy": 1.0 - ratio(empty_annotations + whitespace_annotations + malformed_datatypes,
                                 max(triple_count, 1)),
        "consistency": 1.0 - ratio(len(undefined_classes) + len(undefined_properties),
                                    max(len(used_classes) + len(predicates), 1)),
        "conciseness": 1.0 - ratio(duplicate_count, max(triple_count, 1)),
        "understandability": ratio(len(labeled_resources), len(resources)),
        "interpretability": 1.0 - ratio(len(blank_nodes), max(len(resources), 1)),
        "interlinking": min(1.0, ratio(same_as_count + external_links, max(len(resources), 1))),
        "licensing": 1.0 if licenses else 0.0,
    }
    dimension_scores = {key: max(0.0, min(1.0, value)) for key, value in dimension_scores.items()}
    normalized_score = statistics.fmean(dimension_scores.values()) if dimension_scores else 0.0

    return {
        "score": round(normalized_score * 100, 3),
        "normalized_score": round(normalized_score, 6),
        "score_scale": "0-100",
        "dimension_scores": {key: round(value, 6) for key, value in dimension_scores.items()},
        "metrics": {
            "number_of_triples": triple_count,
            "number_of_entities": len(resources),
            "number_of_properties": len(predicates),
            "number_of_blank_nodes": len(blank_nodes),
            "number_of_labels_or_comments": len(labeled_resources),
            "percentage_of_resources_with_labels": round(ratio(len(labeled_resources), len(resources)) * 100, 3),
            "languages": sorted(languages),
            "rdf_structures": rdf_structures,
            "same_as_links": same_as_count,
            "external_links": external_links,
            "licenses": licenses,
            "empty_annotations": empty_annotations,
            "annotations_with_surrounding_whitespace": whitespace_annotations,
            "malformed_datatype_literals": malformed_datatypes,
            "deprecated_terms": len(deprecated),
            "undefined_classes": len(undefined_classes),
            "undefined_properties": len(undefined_properties),
            "duplicate_triples": duplicate_count,
            "subject_uri_length": uri_stats(subjects),
            "predicate_uri_length": uri_stats(predicates),
            "object_uri_length": uri_stats(objects),
        },
        "not_evaluated": [
            "availability", "performance", "security", "reputation", "currency",
            "volatility", "completeness", "believability", "verifiability"
        ],
    }


def main():
    try:
        payload = sys.stdin.read()
        if not payload.strip():
            raise ValueError("The RDF/Turtle payload is empty")
        print(json.dumps(evaluate(payload), ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
