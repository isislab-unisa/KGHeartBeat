"""Run Human Accessibility metrics for datasets listed in the LOD Cloud catalogue.

Run from the repository root with:
    python src/test/human_accessibility_lodcloud.py

Catalogue metadata is read only through LODCloudAPI. The metric checks may
contact the dataset's advertised website, VoID document, resources, and SPARQL
endpoint; no other dataset catalogue is used to select or enrich datasets.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import pandas as pd
import requests

SRC_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_DIR))

import VoIDAnalyses
import query
import utils
from API import LODCloudAPI
from QualityDimensions.Accessibility4All import Accessibility4All
from QualityDimensions.Accessibility4VisuallyImpaired import Accessibility4VisuallyImpaired
from QualityDimensions.DeafHearingAccessibility import DeafHearingAccessibility


def _metadata_description(metadata):
    description = metadata.get("description", "absent")
    if isinstance(description, dict):
        return description.get("en", "absent")
    return description if isinstance(description, str) else "absent"


def _readability_without_nltk(text):
    """LIX fallback for installations missing NLTK's punkt_tab data."""
    words = re.findall(r"\b\w+\b", text, flags=re.UNICODE)
    if not words:
        return 0
    sentences = [part for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part]
    long_words = sum(len(word) > 6 for word in words)
    return len(words) / max(len(sentences), 1) + long_words / len(words)


def _description_readability(accessibility, endpoint, void_url, metadata):
    description = _metadata_description(metadata)
    source = "LOD Cloud metadata"
    if description in ("", "absent") and utils.is_url(endpoint):
        descriptions = query.getDescription(endpoint)
        if isinstance(descriptions, list) and descriptions:
            description = descriptions[0]
            source = "SPARQL metadata"
    if description in ("", "absent") and utils.is_url(void_url):
        void_data = VoIDAnalyses.parseVoID(void_url)
        descriptions = VoIDAnalyses.getDescription(void_data) if void_data is not False else False
        if isinstance(descriptions, list) and descriptions:
            description = descriptions[0]
            source = "VoID file"
    if not isinstance(description, str) or not description:
        return accessibility.description_readability(endpoint, void_url, description)

    try:
        return accessibility.description_readability(endpoint, void_url, description)
    except LookupError as error:
        if "punkt" not in str(error):
            raise
        lix = _readability_without_nltk(description)
        score = min(1, max(0, (55 - lix) / 30))
        return score, f"Description from {source} (local tokenizer fallback): {description}"


def _metric_score(result, name):
    value = result.get(name, (0, "Not available"))
    return value[0] if isinstance(value, (tuple, list)) and value else 0


def _evaluator_scores(result):
    """Apply the aggregate formulas used by EvaluateHumanCenteredAcc.evaluate_all."""
    perceivable = sum(_metric_score(result, key) for key in (
        "image_metadata", "image", "audio_meta", "audio", "video_meta", "video"
    )) / 6
    understandable = sum(_metric_score(result, key) for key in (
        "metadata_lang", "data_lang", "human_redeable_labels", "example",
        "description_readability",
    )) / 5
    operable = sum(_metric_score(result, key) for key in (
        "contact_point", "dump_size", "sparql_availability_evaluator",
        "common_format_availability", "open_license", "alternative_access_point",
    )) / 6
    robust = sum(_metric_score(result, key) for key in (
        "version", "webpage_status", "metadata_broken_links_rate", "canonical_citation",
    )) / 4
    visually_impaired = (
        _metric_score(result, "alt_image") + _metric_score(result, "audio_description_ratio")
    ) / 2
    deaf_hearing = sum(_metric_score(result, key) for key in (
        "video_description_ratio", "video_sign_language_ratio",
        "audio_sign_language_ratio", "video_subtitle_ratio",
        "audio_subtitle_ratio", "video_description_ratio",
        "audio_description_ratio",
    )) / 7
    if not _metric_score(result, "sparql_availability_evaluator"):
        deaf_hearing = 0
    return {
        "perceivable_score": perceivable,
        "operable_score": operable,
        "understandable_score": understandable,
        "robust_score": robust,
        "accessibility_for_visually_impaired_score": visually_impaired,
        "accessibility_for_deaf_hearing_score": deaf_hearing,
        "overall_score_no_special": perceivable + operable + understandable + robust,
        "overall_score_with_special": perceivable + operable + understandable + robust + visually_impaired + deaf_hearing,
        "overall_score_only_special": visually_impaired + deaf_hearing,
    }


def _lod_resources(metadata):
    """Normalize LOD Cloud resources without asking Aggregator for other sources."""
    resources = []
    for kind, resource_type in (("full_download", "full_download"),
                                ("example", "example"),
                                ("other_download", "other_download")):
        items = metadata.get(kind) or []
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            url = item.get("download_url") or item.get("access_url") or item.get("url")
            resources.append({
                "path": url,
                "format": item.get("media_type") or item.get("format"),
                "type": resource_type,
                "title": item.get("title") or item.get("label"),
                "description": item.get("description"),
            })
    return resources


def analyze_dataset(dataset_id, metadata):
    endpoint = LODCloudAPI.getSPARQLEndpoint(metadata) or False
    website = metadata.get("website") or False
    resources = _lod_resources(metadata)
    resource_objects = utils.toObjectResources(resources)
    void_url = utils.getUrlVoID(resource_objects)
    if not utils.is_url(void_url) and utils.is_url(website):
        candidate = website.rstrip("/") + "/.well-known/void"
        try:
            response = requests.get(candidate, timeout=10)
            if response.status_code == 200 and VoIDAnalyses.parseVoID(candidate) is not False:
                void_url = candidate
            else:
                void_url = False
        except Exception:
            void_url = False

    # Only LOD Cloud metadata is used for these metadata-derived inputs.
    license_value = LODCloudAPI.getLicense(metadata) or False
    if not license_value and utils.is_url(endpoint):
        licenses = query.checkLicenseMR(endpoint)
        if isinstance(licenses, list) and licenses:
            license_value = licenses
    if not license_value and utils.is_url(void_url):
        void_data = VoIDAnalyses.parseVoID(void_url)
        license_value = VoIDAnalyses.getLicense(void_data) if void_data is not False else False

    accessibility = Accessibility4All()
    deaf_hearing = DeafHearingAccessibility()
    visual = Accessibility4VisuallyImpaired()
    total_resources = False
    if utils.is_url(endpoint):
        total_resources = utils.run_with_timeout(query.fetch_subjects, args=(endpoint,), timeout=1800)
        if not isinstance(total_resources, int):
            total_resources = utils.run_with_timeout(query.count_res, args=(endpoint,), timeout=600)
    metadata_language = accessibility.metadata_lang(endpoint, void_url)
    if utils.is_url(endpoint):
        dataset_languages = query.getLangugeSupported(endpoint)
        data_language = (1, f"Languages available: {dataset_languages}") if isinstance(dataset_languages, list) and dataset_languages else (0, "No language specified")
    else:
        data_language = (0, "No SPARQL endpoint available")
    sparql_available = bool(query.check_if_up(endpoint)) if utils.is_url(endpoint) else False
    evaluator_sparql_status = (
        1 if sparql_available else 0,
        "SPARQL endpoint status: " + ("Available" if sparql_available else "Unavailable"),
    )

    # The shared implementation falls back to Aggregator (which merges several
    # catalogues) when the endpoint and VoID file have no link metadata. Keep
    # that fallback scoped to this LOD Cloud record instead.
    broken_links = []
    if not utils.is_url(endpoint) and not utils.is_url(void_url):
        candidate_links = [website] + [resource.get("path") for resource in resources]
        checked_links = [link for link in candidate_links if utils.is_url(link)]
        alive = 0
        for link in checked_links:
            try:
                response = requests.head(link, timeout=5, allow_redirects=True)
                alive += int(response.status_code == 200)
                if response.status_code != 200:
                    broken_links.append(link)
            except requests.RequestException:
                broken_links.append(link)
        metadata_link_rate = (alive / len(checked_links)) if checked_links else 0
        broken_links_result = (metadata_link_rate, f"Links from LOD Cloud metadata: {checked_links}")
    else:
        broken_links_result = accessibility.metadata_broken_links_rate(
            metadata, endpoint, void_url, dataset_id
        )

    result = {
        "title": LODCloudAPI.getNameKG(metadata),
        "domain": metadata.get("domain"),
        "sparql_endpoint": endpoint,
        "void_file": void_url,
        "open_license": accessibility.open_license(license_value, metadata.get("license_id")),
        "webpage_status": accessibility.webpage_status(metadata, endpoint, void_url),
        "check_authentication": accessibility.check_authentication(endpoint),
        "sparql_availability_evaluator": evaluator_sparql_status,
        "metadata_broken_links_rate": broken_links_result,
        "version": accessibility.version(void_url, endpoint),
        "assistive_technologies": accessibility.assistive_technologies(endpoint, void_url),
        "canonical_citation": accessibility.canonical_citation(void_url, endpoint, metadata),
        "contact_point": accessibility.contact_point(metadata, endpoint, void_url),
        "metadata_lang": metadata_language,
        "data_lang": data_language,
        "image": accessibility.image(endpoint, total_resources),
        "human_redeable_labels": accessibility.human_redeable_labels(endpoint),
        "robots_txt": accessibility.robots_txt(resource_objects, endpoint, website),
        "example": accessibility.examples(void_url, endpoint, metadata),
        "description_readability": _description_readability(
            accessibility, endpoint, void_url, metadata
        ),
        "image_metadata": deaf_hearing.image_metadata(endpoint, void_url, resource_objects),
        "video_meta": deaf_hearing.video_meta(endpoint, void_url, resource_objects),
        "video": deaf_hearing.video(endpoint, total_resources),
        "alt_image": visual.alt_image(endpoint),
        "audio_meta": visual.audio_meta(endpoint, void_url, resource_objects),
        "audio": visual.audio(endpoint, total_resources),
    }

    video_accessibility = deaf_hearing.check_video_description_subtitles(endpoint)
    for key, value in video_accessibility.items():
        result[f"video_{key}"] = value
    audio_accessibility = deaf_hearing.check_audio_description_subtitles(endpoint)
    for key, value in audio_accessibility.items():
        result[f"audio_{key}"] = value

    # These three checks normally query Aggregator for resources. Calculate
    # their LOD Cloud equivalents here so the run never silently mixes catalogs.
    full_downloads = [r for r in resources if r["type"] == "full_download"]
    known_formats = [r["format"] for r in full_downloads if r["format"]]
    supported_formats = [fmt for fmt in known_formats if utils.check_common_acceppted_format(fmt)]
    common_format_score = 1 if supported_formats else 0.5 if full_downloads else 0
    result["common_format_availability"] = (common_format_score, known_formats)
    available_download = any(
        utils.check_common_acceppted_format(r.get("format"))
        or utils.check_if_zipped_dump(r.get("format"))
        or utils.url_points_to_graph_file(r.get("path"))
        for r in full_downloads
    )
    result["alternative_access_point"] = (
        int(available_download and sparql_available),
        {"download": available_download, "sparql_endpoint": sparql_available, "api": False},
    )
    # dump_size estimates sizes of advertised LOD Cloud full downloads and VoID dumps.
    dump_links = [r.get("path") for r in full_downloads if utils.is_url(r.get("path"))]
    size_scores = []
    for link in dump_links:
        try:
            size = utils.estimate_file_size_gb(link)
            if isinstance(size, float):
                size_scores.append(1 if size < 0.5 else 0.5 if size < 4 else 0)
        except Exception:
            pass
    if utils.is_url(void_url):
        void_data = VoIDAnalyses.parseVoID(void_url)
        void_dump = VoIDAnalyses.getDataDump(void_data) if void_data is not False else False
        if utils.is_url(void_dump):
            dump_links.append(void_dump)
            try:
                size = utils.estimate_file_size_gb(void_dump)
                if isinstance(size, float):
                    size_scores.append(1 if size < 0.5 else 0.5 if size < 4 else 0)
            except Exception:
                pass
    result["dump_size"] = (max(size_scores) if size_scores else 0,
                           dump_links if dump_links else "No data dumps found")
    result.update(_evaluator_scores(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="Analyze at most this many LOD Cloud datasets")
    parser.add_argument("--dataset", help="Analyze a single LOD Cloud dataset ID")
    parser.add_argument("--output-dir", default=".", help="Directory for JSON and CSV outputs")
    args = parser.parse_args()

    # getJSONMetadata refreshes/downloads the LOD Cloud snapshot once; loading
    # the catalogue through that API keeps the dataset selection LOD-only.
    catalogue = LODCloudAPI._load_catalogue(os.path.join(LODCloudAPI.abs_path, "lodcloud.json"))
    if args.dataset:
        metadata = LODCloudAPI.getJSONMetadata(args.dataset)
        if not isinstance(metadata, dict):
            parser.error(f"Dataset {args.dataset!r} is not present in the LOD Cloud catalogue")
        datasets = [(args.dataset, metadata)]
    else:
        datasets = list(catalogue.items())

    os.makedirs(args.output_dir, exist_ok=True)
    results_path = os.path.join(args.output_dir, "HumanAccessibility_LODCloud_results.json")
    if os.path.exists(results_path):
        try:
            with open(results_path, "r", encoding="utf-8") as existing_file:
                results = json.load(existing_file)
            if not isinstance(results, dict):
                parser.error(f"Existing results file is not a JSON object: {results_path}")
        except (OSError, json.JSONDecodeError) as error:
            parser.error(f"Could not read existing results file {results_path}: {error}")
    else:
        results = {}

    analyzed_this_run = 0
    for dataset_id, metadata in datasets:
        if not isinstance(metadata, dict):
            continue
        existing_result = results.get(dataset_id)
        if isinstance(existing_result, dict) and "error" not in existing_result:
            print(f"Skipping {dataset_id}: already analyzed")
            continue
        if args.limit is not None and analyzed_this_run >= max(0, args.limit):
            break
        print(f"Analyzing LOD Cloud dataset {dataset_id}: {LODCloudAPI.getNameKG(metadata)}")
        try:
            results[dataset_id] = analyze_dataset(dataset_id, metadata)
        except Exception as error:
            results[dataset_id] = {"error": str(error)}
        analyzed_this_run += 1
        with open(results_path, "w", encoding="utf-8") as output:
            json.dump(results, output, ensure_ascii=False, indent=2, default=str)

    rows = [{"KG_ID": dataset_id, **metrics} for dataset_id, metrics in results.items()]
    pd.DataFrame(rows).to_csv(
        os.path.join(args.output_dir, "HumanAccessibility_LODCloud_results.csv"), index=False
    )
    print(
        f"Finished this run: analyzed {analyzed_this_run} dataset(s); "
        f"{len(results)} dataset result(s) are saved in {args.output_dir}."
    )


if __name__ == "__main__":
    main()
