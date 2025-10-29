import requests
import pandas as pd

# ---- CONFIG ----
json_url = "https://lod-cloud.net/versions/2025-09-02/lod-data.json"     # URL of JSON file
csv_input_path = "HumanAccessibility_results_verbose.tsv"                   # Path to the CSV to filter
csv_output_path = "HumanAccessibility_results_verbose-filtered.csv"               # Output path


def filter_csv_using_json_keys(json_url, csv_input_path, csv_output_path):
    # 1. Fetch JSON from URL
    response = requests.get(json_url)
    response.raise_for_status()  # raises error if request failed
    data = response.json()

    # 2. Extract keys (assuming JSON is an object/dict)
    json_keys = list(data.keys())

    # 3. Load CSV
    df = pd.read_csv(csv_input_path, sep="\t")

    # 4. Filter rows where 'KG ID' exists in JSON keys
    filtered_df = df[df["KG_ID"].isin(json_keys)]

    # 5. Save result
    filtered_df.to_csv(csv_output_path, index=False)
    print(f"✅ Filtered CSV saved to: {csv_output_path}")


if __name__ == "__main__":
    filter_csv_using_json_keys(json_url, csv_input_path, csv_output_path)
