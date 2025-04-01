import pandas as pd
import os

def merge_dataframes(df1, df2, key_column, columns_to_copy):
    """
    Merge specific columns from df2 into df1 based on a matching key column.
    
    :param df1: First DataFrame (destination)
    :param df2: Second DataFrame (source)
    :param key_column: Column used for matching rows
    :param columns_to_copy: List of columns to copy from df2 to df1
    :return: Updated df1 with copied values
    """
    # Ensure columns exist in both DataFrames
    for col in columns_to_copy:
        if col not in df2.columns:
            raise ValueError(f"Column '{col}' not found in second DataFrame")
    
    # Merge using key_column
    df1.update(df2.set_index(key_column)[columns_to_copy], overwrite=True)
    
    return df1

def process_csv_files(folder_path, source_csv, key_column, columns_to_copy):
    """
    Process all CSV files in a folder, updating them with values from the source CSV.
    
    :param folder_path: Path to the folder containing target CSV files
    :param source_csv: Path to the source CSV file
    :param key_column: Column used for matching rows
    :param columns_to_copy: List of columns to copy from the source CSV to the target CSVs
    """
    df_source = pd.read_csv(source_csv)
    
    for file in os.listdir(folder_path):
        if file.endswith(".csv"):
            file_path = os.path.join(folder_path, file)
            df_target = pd.read_csv(file_path)
            
            updated_df = merge_dataframes(df_target, df_source, key_column, columns_to_copy)
            
            updated_df.to_csv(file_path, index=False)
            print(f"Updated {file}")

# Example usage
folder_path = "./Analysis results"  
source_csv = "path/to/source.csv"  
process_csv_files(folder_path, source_csv, key_column='KG id', columns_to_copy=['Author (query)','Contributor','Publisher','Verifiability score'])
