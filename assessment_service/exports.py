"""Produce the same dated CSV and DQV Turtle files as the batch manager."""
from pathlib import Path


def export_assessment(kg, analysis_date, directory):
    from OutputCSV import OutputCSV
    from fromCSV_to_KG import convert_to_kg_code_from_llm

    # The worker sets KGH_RESULTS_DIR before importing the analysis modules.
    # These are the original exporters, including the default CSV column names.
    output = OutputCSV(kg, [kg.extra.KGid])
    for dimensions in (False, True):
        OutputCSV.writeHeader(analysis_date, include_dimensions=dimensions)
        output.writeRow(analysis_date, include_dimensions=dimensions)
    # This function is a deterministic DQV converter; it makes no LLM calls.
    convert_to_kg_code_from_llm(analysis_date + '_with_dimensions')
    directory = Path(directory)
    return {'schema_version': 2, 'analysis_date': analysis_date,
            'files': {extension: (directory / f'{analysis_date}.{extension}').read_bytes().decode('utf-8')
                      for extension in ('csv', 'ttl')}}
