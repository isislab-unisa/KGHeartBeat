"""Export batch CSVs and upsert their assessments into the web catalogue."""
import importlib.util
import json
import os
from pathlib import Path

from pymongo import MongoClient
from result_paths import results_dir


def main():
    exporter_path = Path(__file__).with_name("csv_to_json.py")
    spec = importlib.util.spec_from_file_location("csv_to_json", exporter_path)
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    directory = results_dir()
    exporter.splitted_csv(directory)
    exporter.full_csv(directory)
    count = 0
    with MongoClient(os.environ["MONGO_URI"], serverSelectionTimeoutMS=30000) as client:
        collection = client[os.environ.get("DB_NAME", "KGHeartbeatDB")]["quality_analysis_data"]
        for path in sorted((directory / "json_files").glob("*.json")):
            document = json.loads(path.read_text(encoding="utf-8"))
            key = {field: document[field] for field in ("kg_id", "analysis_date")}
            collection.replace_one(key, document, upsert=True)
            count += 1
    print(f"Imported {count} assessments.")


if __name__ == "__main__":
    main()
