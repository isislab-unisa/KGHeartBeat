"""KGSum's VoID/DCAT serializer, separated from its ML imports.

Copied without function changes from GabrieleT0/KGSum src/generate_profile.py,
commit fc6ed7f44beb0cae2d82e78af5272976c2415daf (MIT).
See kgsum-LICENSE.txt. Extraction still runs from the configured KGSum checkout.
"""
import ast
import urllib.parse
from typing import Any

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, FOAF, OWL, RDF, XSD
from src.lov_data_preparation import IS_URI
from src.void_linksets import aggregate_same_as_links


def profile_to_rdf(
        profile: dict[str, Any],
        base_iri: str = "https://www.isislab.it/resource/",
        rdf_format: str = "xml"
) -> str:
    """Serialize a generated profile as RDF using the same VoID/DCAT mapping used for storage."""
    raw_id_str = _extract_first_valid_uri(profile.get('id'))
    if not raw_id_str:
        raise ValueError("Cannot serialize profile as RDF without a valid id.")

    if IS_URI.match(raw_id_str):
        iri = raw_id_str
    else:
        iri = base_iri + urllib.parse.quote(raw_id_str, safe="")

    dataset = URIRef(iri)
    graph = Graph()

    DCAT = Namespace("http://www.w3.org/ns/dcat#")
    VOID = Namespace("http://rdfs.org/ns/void#")

    graph.bind("dcat", DCAT)
    graph.bind("dcterms", DCTERMS)
    graph.bind("foaf", FOAF)
    graph.bind("owl", OWL)
    graph.bind("rdf", RDF)
    graph.bind("void", VOID)
    graph.bind("xsd", XSD)

    graph.add((dataset, RDF.type, VOID.Dataset))

    literal_fields = (
        ("title", DCTERMS.title),
        ("language", DCTERMS.language),
        ("dsc", DCTERMS.description),
        ("creator", DCTERMS.creator),
        ("contributor", DCTERMS.contributor),
        ("publisher", DCTERMS.publisher),
        ("source", DCTERMS.source),
        ("identifier", DCTERMS.identifier),
        ("date", DCTERMS.date),
        ("created", DCTERMS.created),
        ("issued", DCTERMS.issued),
        ("modified", DCTERMS.modified),
        ("license", DCTERMS.license),
    )
    for field_name, predicate in literal_fields:
        for value in _flatten_and_stringify(profile.get(field_name)):
            if value and not (field_name == "language" and value in {"UNKNOWN", "xx", "ND"}):
                graph.add((dataset, predicate, Literal(value)))

    for sparql in _flatten_and_stringify(profile.get("sparql")):
        if sparql and IS_URI.match(sparql):
            graph.add((dataset, VOID.sparqlEndpoint, URIRef(sparql)))

    for homepage in _flatten_and_stringify(profile.get("homepage")):
        if homepage and IS_URI.match(homepage):
            graph.add((dataset, FOAF.homepage, URIRef(homepage)))

    for uri_regex_pattern in _flatten_and_stringify(profile.get("uri_regex_pattern")):
        if uri_regex_pattern:
            graph.add((dataset, VOID.uriRegexPattern, Literal(uri_regex_pattern)))

    for feature in _flatten_and_stringify(profile.get("feature")):
        if feature and IS_URI.match(feature):
            graph.add((dataset, VOID.feature, URIRef(feature)))

    for example_resource in _flatten_and_stringify(profile.get("example_resource")):
        if example_resource and IS_URI.match(example_resource):
            graph.add((dataset, VOID.exampleResource, URIRef(example_resource)))

    for uri_space in _flatten_and_stringify(profile.get("uri_space")):
        if uri_space:
            graph.add((dataset, VOID.uriSpace, Literal(uri_space)))

    graph.add((dataset, DCTERMS.identifier, Literal(raw_id_str)))

    category = profile.get("category")
    if category:
        graph.add((dataset, DCTERMS.subject, Literal(str(category))))

    statistics = _extract_statistics(profile.get("statistics"))
    triple_count = _coerce_positive_int(statistics.get("triples"))
    entity_count = _coerce_positive_int(statistics.get("entities"))
    distinct_subject_count = _coerce_positive_int(statistics.get("distinctSubjects"))
    distinct_object_count = _coerce_positive_int(statistics.get("distinctObjects"))
    class_count = _coerce_positive_int(statistics.get("classes"))
    property_count = _coerce_positive_int(statistics.get("properties"))
    if triple_count:
        graph.add((dataset, VOID.triples, Literal(triple_count, datatype=XSD.integer)))
    if entity_count:
        graph.add((dataset, VOID.entities, Literal(entity_count, datatype=XSD.integer)))
    if distinct_subject_count:
        graph.add((dataset, VOID.distinctSubjects, Literal(distinct_subject_count, datatype=XSD.integer)))
    if distinct_object_count:
        graph.add((dataset, VOID.distinctObjects, Literal(distinct_object_count, datatype=XSD.integer)))
    if class_count:
        graph.add((dataset, VOID.classes, Literal(class_count, datatype=XSD.integer)))
    if property_count:
        graph.add((dataset, VOID.properties, Literal(property_count, datatype=XSD.integer)))

    for partition in _normalize_partition_list(profile.get("class_partitions"), "class", "entities"):
        node = BNode()
        graph.add((dataset, VOID.classPartition, node))
        graph.add((node, VOID["class"], URIRef(partition["class"])))
        if partition["entities"]:
            graph.add((node, VOID.entities, Literal(partition["entities"], datatype=XSD.integer)))

    for partition in _normalize_partition_list(profile.get("property_partitions"), "property", "triples"):
        node = BNode()
        graph.add((dataset, VOID.propertyPartition, node))
        graph.add((node, VOID.property, URIRef(partition["property"])))
        if partition["triples"]:
            graph.add((node, VOID.triples, Literal(partition["triples"], datatype=XSD.integer)))

    for voc in _flatten_and_stringify(profile.get("voc")):
        if voc and IS_URI.match(voc):
            graph.add((dataset, VOID.vocabulary, URIRef(voc)))

    for tag in _flatten_and_stringify(profile.get("tags")):
        if tag:
            graph.add((dataset, DCAT.keyword, Literal(tag)))

    for subject in _flatten_and_stringify(profile.get("sbj")):
        if subject and IS_URI.match(subject):
            graph.add((dataset, DCTERMS.subject, URIRef(subject)))

    for download in _flatten_and_stringify(profile.get("download")):
        if download and IS_URI.match(download):
            graph.add((dataset, VOID.dataDump, URIRef(download)))

    for link in aggregate_same_as_links(profile.get("same_as_links") or profile.get("con")):
        target_dataset = link.get("dataset")
        predicate = str(link.get("predicate") or OWL.sameAs)
        count = _coerce_positive_int(link.get("count"))
        if not target_dataset or not IS_URI.match(str(target_dataset)) or not IS_URI.match(predicate) or not count:
            continue

        target = URIRef(str(target_dataset))
        encoded_target = urllib.parse.quote(f"{target_dataset}|{predicate}", safe="")
        linkset = URIRef(f"{iri.rstrip('/#')}/linkset/{encoded_target}")
        graph.add((linkset, RDF.type, VOID.Linkset))
        graph.add((linkset, VOID.target, dataset))
        graph.add((linkset, VOID.target, target))
        graph.add((linkset, VOID.subjectsTarget, dataset))
        graph.add((linkset, VOID.objectsTarget, target))
        graph.add((linkset, VOID.linkPredicate, URIRef(predicate)))
        graph.add((linkset, VOID.triples, Literal(count, datatype=XSD.integer)))
        graph.add((linkset, VOID.subset, dataset))
        graph.add((target, RDF.type, VOID.Dataset))
        graph.add((target, FOAF.homepage, target))

    return graph.serialize(format=rdf_format)


def _flatten_and_stringify(val: Any) -> list[str]:
    """
    Flatten nested lists and convert all items to strings.
    This fixes the 'expected string or bytes-like object, got list' error.
    """
    if val is None:
        return []

    def _flatten_recursive(item: Any) -> list[str]:
        if isinstance(item, list):
            result = []
            for subitem in item:
                result.extend(_flatten_recursive(subitem))
            return result
        else:
            # Convert to string and filter out empty values
            item_str = str(item).strip() if item is not None else ""
            return [item_str] if item_str else []

    if isinstance(val, list):
        return _flatten_recursive(val)
    else:
        val_str = str(val).strip() if val is not None else ""
        return [val_str] if val_str else []


def _extract_first_valid_uri(val: Any) -> str:
    """
    Extract the first valid URI from a value that might be a list, string, or other type.
    Returns empty string if no valid URI is found.
    """
    if val is None:
        return ""

    # If it's a list, try to find the first valid URI
    if isinstance(val, list):
        for item in val:
            if item is not None:
                item_str = str(item).strip()
                if item_str and IS_URI.match(item_str):
                    return item_str
        # If no valid URI found in list, return the first non-empty item as string
        for item in val:
            if item is not None:
                item_str = str(item).strip()
                if item_str:
                    return item_str
        return ""
    else:
        # Single value - convert to string
        val_str = str(val).strip()
        return val_str if val_str else ""


def _coerce_positive_int(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return number if number > 0 else 0


def _parse_statistics_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text or text == "[]":
            return {}
        try:
            parsed = ast.literal_eval(text)
        except (SyntaxError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _extract_statistics(value: Any) -> dict[str, int]:
    if isinstance(value, list):
        totals: dict[str, int] = {}
        for item in value:
            for key, val in _parse_statistics_mapping(item).items():
                totals[str(key)] = totals.get(str(key), 0) + _coerce_positive_int(val)
        return totals
    return {str(key): _coerce_positive_int(val) for key, val in _parse_statistics_mapping(value).items()}


def _normalize_partition_list(value: Any, uri_key: str, count_key: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list):
        return []

    partitions = []
    for item in value:
        if isinstance(item, list):
            partitions.extend(_normalize_partition_list(item, uri_key, count_key))
            continue
        if not isinstance(item, dict):
            continue
        uri = item.get(uri_key)
        count = _coerce_positive_int(item.get(count_key))
        if uri and IS_URI.match(str(uri)):
            partitions.append({uri_key: str(uri), count_key: count})
    return partitions
