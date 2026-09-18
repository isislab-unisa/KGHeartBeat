from contextlib import ExitStack, contextmanager
from concurrent.futures import ThreadPoolExecutor

from KnowledgeGraph import KnowledgeGraph
from kg_profile import create_profile

import QualityDimensions.AmountOfData as AmountOfData
import utils
from API import Aggregator
from QualityDimensions.Accuracy import Accuracy, calculate as calculate_accuracy
from QualityDimensions.Availability import Availability, rdf_dump_from_endpoint, uri_dereferenceability
from QualityDimensions.Believability import Believability, description_from_metadata, reliable_provider, trust_value
from QualityDimensions.Completeness import build as build_completeness, external_links_info
from QualityDimensions.Conciseness import Conciseness, calculate as calculate_conciseness
from QualityDimensions.Consistency import Consistency, build as build_consistency, collect_metrics as collect_consistency_metrics
from QualityDimensions.Currency import Currency, build as build_currency, build_void as build_void_currency, endpoint_dates
from QualityDimensions.Interlinking import Interlinking, graph_metrics, same_as_chains, skos_mapping
from QualityDimensions.Interpretability import Interpretability, blank_nodes
from QualityDimensions.Licensing import Licensing, human_readable_from_endpoint, machine_readable_from_endpoint
from QualityDimensions.Performance import Performance
from QualityDimensions.RepresentationalConciseness import (
    RepresentationalConciseness,
    calculate as calculate_representational_conciseness,
    rdf_structures,
)
from QualityDimensions.RepresentationalConsistency import RepresentationalConsistency, new_terms, new_vocabularies
from QualityDimensions.Reputation import Reputation, page_rank
from QualityDimensions.Security import Security, https_available
from QualityDimensions.Understendability import Understendability, build as build_understendability
from QualityDimensions.Understendability import labels_count, uri_regexes, vocabularies_from_endpoint
from QualityDimensions.Verifiability import Verifiability, authors_from_endpoint, contributors_from_endpoint
from QualityDimensions.Verifiability import publishers_from_endpoint, signed_kg
from QualityDimensions.Versatility import Versatility, dcat_download_links, languages_from_endpoint
from QualityDimensions.Versatility import serialization_formats_from_endpoint
from QualityDimensions.Volatility import Volatility, frequency_from_endpoint
from QualityDimensions.base import AnalysisContext, MISSING_VALUE
from analysis_support import (
    build_extra_available,
    build_extra_unavailable,
    check_endpoint,
    check_void,
    common_formats_availability,
    configure_logger,
    endpoint_limited,
    endpoint_unavailable_message,
    has_example,
    inactive_links,
    load_graph,
    load_resources,
    load_sources,
    metadata_language,
    metadata_triples,
    parse_void_fallback,
    recover_triples,
    resolve_target,
    resolve_query_target,
    type_objects,
    triple_retrieval_info,
)


def analyses(analysis_date, idKG=None, nameKG=None, sparql_endpoint=None, rdf_dump=None, triple_limit=10000):
    with analysis_session(analysis_date, idKG, nameKG, sparql_endpoint, rdf_dump, triple_limit) as kg:
        return kg


@contextmanager
def analysis_session(analysis_date, idKG=None, nameKG=None, sparql_endpoint=None, rdf_dump=None, triple_limit=10000, include_profile=False):
    """Keep local queries alive; optionally profile in parallel and wait on exit."""
    if triple_limit is not None and (type(triple_limit) is not int or triple_limit <= 0):
        raise ValueError('triple_limit must be a positive integer or None for full retrieval')
    with ExitStack() as stack:
        profile_worker = stack.enter_context(ThreadPoolExecutor(max_workers=1)) if include_profile else None
        kg = _analyses(analysis_date, idKG, nameKG, sparql_endpoint, rdf_dump, stack, triple_limit, profile_worker)
        try:
            yield kg
        finally:
            kg.extra.queryEndpointUrl = kg.extra.endpointUrl


def _analyses(analysis_date, idKG, nameKG, sparql_endpoint, rdf_dump, stack, triple_limit=10000, profile_worker=None):
    utils.skipCheckSSL()

    target = resolve_target(idKG, nameKG, sparql_endpoint, rdf_dump)
    logger, kg_info = configure_logger(analysis_date, target.kg_id, target.name)
    logger.info('Analysis started...', extra=kg_info)
    logger.info(f"SPARQL endpoint link: {target.access_url}", extra=kg_info)

    context = AnalysisContext(target.access_url, target.name, analysis_date, logger, kg_info, triple_limit)
    sources, sources_obj = load_sources(target.metadata, target.access_url)
    endpoint_check = check_endpoint(target.access_url, context, sources_obj)

    access_url = endpoint_check.access_url
    context = AnalysisContext(access_url, target.name, analysis_date, logger, kg_info, triple_limit)
    logger.info(f"SPARQL endpoint availability: {endpoint_check.available}", extra=kg_info)

    triples_metadata = metadata_triples(target.metadata)
    resource_info = load_resources(target.kg_id, resources=target.resources)
    void_info = check_void(context, resource_info.objects, sources_obj)

    public_access_url = access_url
    query_target = resolve_query_target(target, endpoint_check, context, stack)
    if profile_worker is not None:
        # Explicit input wins; catalog targets use the resolved public source.
        profile_dump = rdf_dump
        if not profile_dump and not sparql_endpoint:
            profile_dump = query_target.rdf_dump_source
        profile_endpoint = None if profile_dump else sparql_endpoint or public_access_url
        profile_worker.submit(create_profile, target.kg_id, analysis_date, profile_endpoint, profile_dump)
    access_url = query_target.access_url
    endpoint_check = query_target.endpoint_check
    context = AnalysisContext(access_url, target.name, analysis_date, logger, kg_info, triple_limit)

    metadata_license = Aggregator.getLicense(target.metadata)
    author_metadata = Aggregator.getAuthor(target.metadata)
    inactive_link = inactive_links(resource_info.objects)
    example = has_example(resource_info.objects)
    external_links, linked_triples = external_links_info(context, target.kg_id)
    page_rank_value, degree, centrality, clustering = _graph_values(context, target.kg_id, sparql_endpoint)
    description = description_from_metadata(target.metadata)
    language_metadata = metadata_language(context, target.kg_id)
    believable = reliable_provider(context, target.kg_id)

    error_message = MISSING_VALUE
    if not endpoint_check.available:
        error_message, access_override = endpoint_unavailable_message(
            context,
            endpoint_check.restricted,
            False,
            endpoint_check.absent,
        )
        if access_override is not None:
            access_url = access_override
            context = AnalysisContext(access_url, target.name, analysis_date, logger, kg_info, triple_limit)

    values = _endpoint_values(
        context,
        triples_metadata,
        resource_info.download_urls,
        resource_info.offline_dumps,
        local_dump=query_target.is_local,
    ) if endpoint_check.available else None
    void_available, void_values = (False, None)
    if not endpoint_check.available:
        void_available, void_values = parse_void_fallback(void_info)

    if void_available and void_values is not None:
        values = _void_values(error_message, void_values)
        values["new_vocab"] = new_vocabularies(context, values["vocabularies"], 'Check the re-using of existing vocabs')
    elif not endpoint_check.available:
        values = _unavailable_values(error_message)

    normalized_id = '' if target.kg_id is False else target.kg_id
    reported_access_url = public_access_url if query_target.is_local else access_url
    normalized_access_url = reported_access_url or ''
    normalized_name = '' if target.name is False else target.name

    trust = trust_value(context, normalized_name, description, sources_obj.web, believable)
    common_formats = common_formats_availability(
        resource_info.available_download,
        values["available_dump"],
        resource_info.metadata_media_type,
    )
    download_urls = list(dict.fromkeys(resource_info.download_urls))

    dimensions = _build_dimensions(
        context=context,
        endpoint_check=endpoint_check,
        void_available=void_available,
        values=values,
        endpoint=endpoint_check.endpoint,
        available_download=resource_info.available_download,
        inactive_link=inactive_link,
        metadata_license=metadata_license,
        author_metadata=author_metadata,
        sources=sources_obj,
        language_metadata=language_metadata,
        external_links=external_links,
        linked_triples=linked_triples,
        page_rank_value=page_rank_value,
        degree=degree,
        centrality=centrality,
        clustering=clustering,
        triples_metadata=triples_metadata,
        example=example,
        name=normalized_name,
        description=description,
        believable=believable,
        trust=trust,
        error_message=error_message,
    )

    extra = _build_extra(
        context=context,
        endpoint_check=endpoint_check,
        normalized_id=normalized_id,
        normalized_access_url=normalized_access_url,
        download_urls=download_urls,
        values=values,
        resource_info=resource_info,
        void_info=void_info,
        common_formats=common_formats,
        error_message=error_message,
    )

    extra.analysisSource = "rdf_dump" if query_target.is_local else "sparql" if endpoint_check.available else "metadata"
    extra.datasetSource = target.dataset_source
    extra.rdfDumpSource = query_target.rdf_dump_source
    extra.queryEndpointUrl = access_url
    extra.tripleRetrieval = values.get('triple_retrieval', {
        'basis': 'unavailable', 'limit': triple_limit, 'retrieved': 0,
        'checked_at': analysis_date,
    })

    return KnowledgeGraph(
        dimensions["availability"],
        dimensions["currency"],
        dimensions["versatility"],
        dimensions["security"],
        dimensions["representational_conciseness"],
        dimensions["licensing"],
        dimensions["performance"],
        dimensions["amount"],
        dimensions["volatility"],
        dimensions["interlinking"],
        dimensions["consistency"],
        dimensions["reputation"],
        dimensions["believability"],
        dimensions["verifiability"],
        dimensions["completeness"],
        dimensions["representational_consistency"],
        dimensions["understendability"],
        dimensions["interpretability"],
        dimensions["conciseness"],
        dimensions["accuracy"],
        extra,
    )


def _endpoint_values(context, triples_metadata, download_urls, offline_dumps, local_dump=False):
    all_triples = recover_triples(context)
    if local_dump:
        from QualityDimensions.Performance import unavailable
        performance = unavailable()
        throughput_no_offset = dict.fromkeys(("min", "average", "max", "standard_deviation"), MISSING_VALUE)
    else:
        performance, throughput_no_offset = Performance.calculate(context)
    triples_query = AmountOfData.count_triples(context)
    limited = endpoint_limited(context, all_triples, triples_query)
    triples_o = type_objects(context)
    rdf_structure_value = rdf_structures(context)
    representational_conciseness, all_uri, uri_list_o, uri_list_p = calculate_representational_conciseness(
        context,
        all_triples,
        rdf_structure_value,
    )
    vocabularies = vocabularies_from_endpoint(context)
    regex = uri_regexes(context)
    num_entities, entities_regex = AmountOfData.count_entities(context, regex, all_triples)
    consistency_metrics = collect_consistency_metrics(context, all_triples)

    values = {
        "all_triples": all_triples,
        "performance": performance,
        "throughput_no_offset": throughput_no_offset,
        "triples_query": triples_query,
        "limited": limited,
        "triples_o": triples_o,
        "new_terms": new_terms(context, triples_o),
        "languages": languages_from_endpoint(context),
        "num_blank_nodes": blank_nodes(context),
        "is_secure": MISSING_VALUE if local_dump else https_available(context),
        "rdf_structures": rdf_structure_value,
        "formats": serialization_formats_from_endpoint(context),
        "dcat_links": dcat_download_links(context),
        "available_dump": True if local_dump else rdf_dump_from_endpoint(context, download_urls, offline_dumps),
        "license_mr": machine_readable_from_endpoint(context),
        "license_hr": human_readable_from_endpoint(context),
        "num_property": AmountOfData.count_properties(context),
        "num_label": labels_count(context),
        "regex": regex,
        "vocabularies": vocabularies,
        "author_query": authors_from_endpoint(context),
        "publisher": publishers_from_endpoint(context),
        "num_entities": num_entities,
        "entities_regex": entities_regex,
        "contributors": contributors_from_endpoint(context),
        "same_as": same_as_chains(context),
        "skos_mapping": skos_mapping(context),
        "frequency": frequency_from_endpoint(context),
        "dates": endpoint_dates(context),
        "representational_conciseness": representational_conciseness,
        "all_uri": all_uri,
        "uri_list_o": uri_list_o,
        "uri_list_p": uri_list_p,
        "new_vocab": new_vocabularies(context, vocabularies),
        "consistency_metrics": consistency_metrics,
        "accuracy": calculate_accuracy(context, all_triples, triples_query),
        "conciseness": calculate_conciseness(context, all_triples),
        "signed_kg": signed_kg(context),
        "def_value": uri_dereferenceability(context, all_triples),
    }
    values['triple_retrieval'] = triple_retrieval_info(context, all_triples, triples_query)
    return values


def _void_values(error_message, void_values):
    return {
        "available_dump": void_values.available_dump,
        "num_entities": void_values.num_entities,
        "frequency": void_values.frequency,
        "vocabularies": void_values.vocabularies,
        "regex": void_values.regex,
        "formats": void_values.formats,
        "languages": void_values.languages,
        "license_mr": void_values.license_mr,
        "dates": (void_values.creation_date, void_values.modification_date, error_message, error_message),
        "new_vocab": [],
    }


def _unavailable_values(error_message):
    return {
        "available_dump": error_message,
        "num_entities": error_message,
        "frequency": error_message,
        "vocabularies": error_message,
        "regex": error_message,
        "formats": error_message,
        "languages": error_message,
        "license_mr": error_message,
        "dates": (error_message, error_message, error_message, error_message),
        "new_vocab": error_message,
    }


def _build_dimensions(
    context,
    endpoint_check,
    void_available,
    values,
    endpoint,
    available_download,
    inactive_link,
    metadata_license,
    author_metadata,
    sources,
    language_metadata,
    external_links,
    linked_triples,
    page_rank_value,
    degree,
    centrality,
    clustering,
    triples_metadata,
    example,
    name,
    description,
    believable,
    trust,
    error_message,
):
    if endpoint_check.available:
        creation_date, modification_date, historical_updates, updated_triples = values["dates"]
        return {
            "availability": Availability(endpoint, available_download, values["available_dump"], inactive_link, values["def_value"]),
            "currency": build_currency(context, creation_date, modification_date, updated_triples, values["triples_query"], triples_metadata, historical_updates),
            "versatility": Versatility(values["languages"], language_metadata, values["formats"], endpoint, values["available_dump"], available_download),
            "security": Security(values["is_secure"], MISSING_VALUE if endpoint_check.absent else endpoint_check.restricted),
            "representational_conciseness": values["representational_conciseness"],
            "licensing": Licensing(metadata_license, values["license_mr"], values["license_hr"]),
            "performance": values["performance"],
            "amount": AmountOfData.AmountOfData(triples_metadata, values["triples_query"], values["num_entities"], values["num_property"], values["entities_regex"]),
            "volatility": Volatility(values["frequency"]),
            "interlinking": Interlinking(degree, clustering, centrality, values["same_as"], external_links, values["skos_mapping"]),
            "consistency": build_consistency(context, values["consistency_metrics"], values["triples_query"], values["num_entities"], values["entities_regex"]),
            "reputation": Reputation(external_links, page_rank_value),
            "believability": Believability(name, description, sources.web, believable, trust),
            "verifiability": Verifiability(values["vocabularies"], values["author_query"], author_metadata, values["contributors"], values["publisher"], sources, values["signed_kg"]),
            "completeness": build_completeness(values["triples_query"], triples_metadata, linked_triples),
            "representational_consistency": RepresentationalConsistency(values["new_vocab"], values["new_terms"]),
            "understendability": build_understendability(values["num_label"], values["triples_query"], triples_metadata, values["regex"], values["vocabularies"], example, name, description, sources.web),
            "interpretability": Interpretability(values["num_blank_nodes"], values["rdf_structures"]),
            "conciseness": values["conciseness"],
            "accuracy": values["accuracy"],
        }

    if void_available:
        creation_date, modification_date, _, _ = values["dates"]
        return _fallback_dimensions(
            error_message,
            endpoint,
            available_download,
            inactive_link,
            values,
            metadata_license,
            author_metadata,
            sources,
            language_metadata,
            external_links,
            linked_triples,
            page_rank_value,
            degree,
            centrality,
            clustering,
            triples_metadata,
            example,
            name,
            description,
            believable,
            trust,
            currency=build_void_currency(context, creation_date, modification_date),
            completeness=build_completeness(error_message, triples_metadata, linked_triples),
        )

    return _fallback_dimensions(
        error_message,
        endpoint,
        available_download,
        inactive_link,
        values,
        metadata_license,
        author_metadata,
        sources,
        language_metadata,
        external_links,
        linked_triples,
        page_rank_value,
        degree,
        centrality,
        clustering,
        triples_metadata,
        example,
        name,
        description,
        believable,
        trust,
        currency=Currency(error_message, error_message, MISSING_VALUE, MISSING_VALUE, MISSING_VALUE),
        completeness=build_completeness(error_message, triples_metadata, linked_triples),
    )


def _fallback_dimensions(
    error_message,
    endpoint,
    available_download,
    inactive_link,
    values,
    metadata_license,
    author_metadata,
    sources,
    language_metadata,
    external_links,
    linked_triples,
    page_rank_value,
    degree,
    centrality,
    clustering,
    triples_metadata,
    example,
    name,
    description,
    believable,
    trust,
    currency,
    completeness,
):
    return {
        "availability": Availability(endpoint, available_download, values["available_dump"], inactive_link, error_message),
        "currency": currency,
        "versatility": Versatility(error_message, language_metadata, values["formats"], error_message, values["available_dump"], available_download),
        "security": Security(error_message, error_message),
        "representational_conciseness": RepresentationalConciseness(*([error_message] * 22)),
        "licensing": Licensing(metadata_license, values["license_mr"], error_message),
        "performance": Performance(*([error_message] * 14)),
        "amount": AmountOfData.AmountOfData(triples_metadata, error_message, values["num_entities"], error_message, error_message),
        "volatility": Volatility(values["frequency"]),
        "interlinking": Interlinking(degree, clustering, centrality, error_message, external_links, error_message),
        "consistency": Consistency(*([error_message] * 7)),
        "reputation": Reputation(external_links, page_rank_value),
        "believability": Believability(name, description, sources.web, believable, trust),
        "verifiability": Verifiability(values["vocabularies"], error_message, author_metadata, error_message, error_message, sources, error_message),
        "completeness": completeness,
        "representational_consistency": RepresentationalConsistency(values["new_vocab"], error_message),
        "understendability": Understendability(error_message, MISSING_VALUE, values["regex"], error_message, example, name, description, sources.web),
        "interpretability": Interpretability(error_message, error_message),
        "conciseness": Conciseness(error_message, error_message),
        "accuracy": Accuracy(error_message, error_message, error_message, error_message, error_message),
    }


def _build_extra(context, endpoint_check, normalized_id, normalized_access_url, download_urls, values, resource_info, void_info, common_formats, error_message):
    if endpoint_check.available:
        metrics = values["consistency_metrics"]
        creation_date, modification_date, historical_updates, updated_triples = values["dates"]
        return build_extra_available(
            context,
            normalized_id,
            normalized_access_url,
            download_urls,
            values["dcat_links"],
            updated_triples,
            metrics["classes"],
            metrics["properties"],
            values["all_uri"],
            values["triples_o"],
            values["all_triples"],
            metrics["undefined_properties"],
            metrics["undefined_classes"],
            metrics["misplaced_class"],
            metrics["misplaced_property"],
            metrics["deprecated"],
            values["limited"],
            resource_info.offline_dumps,
            void_info,
            values["throughput_no_offset"],
            resource_info.metadata_media_type,
            common_formats,
            resource_info.objects,
        )

    return build_extra_unavailable(
        context,
        normalized_id,
        normalized_access_url,
        download_urls,
        error_message,
        resource_info.offline_dumps,
        void_info,
        resource_info.metadata_media_type,
        common_formats,
        resource_info.objects,
    )


def _graph_values(context, kg_id, sparql_endpoint):
    if sparql_endpoint is not None:
        return MISSING_VALUE, MISSING_VALUE, MISSING_VALUE, MISSING_VALUE
    graph = load_graph()
    rank = page_rank(context, graph, kg_id)
    degree, centrality, clustering = graph_metrics(context, graph, kg_id)
    return rank, degree, centrality, clustering
