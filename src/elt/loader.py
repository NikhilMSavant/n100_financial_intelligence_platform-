from pathlib import Path

import pandas as pd


RAW_DATA_PATH = Path("data/raw")

def load_excel_file(file_name):

    file_path = RAW_DATA_PATH / file_name

    special_files = {

        "analysis.xlsx",
        "balancesheet.xlsx",
        "cashflow.xlsx",
        "companies.xlsx",
        "documents.xlsx",
        "profitandloss.xlsx",
        "prosandcons.xlsx"

    }

    if file_name in special_files:

        df = pd.read_excel(file_path, header=1)

    else:

        df = pd.read_excel(file_path)

    print("\n" + "=" * 50)

    print(f"Loaded: {file_name}")

    print(f"Rows: {df.shape[0]}")

    print("Columns:")

    for column in df.columns:

        print(f" - {column}")

    return df


if __name__ == "__main__":

    excel_files = list(RAW_DATA_PATH.glob("*.xlsx"))

    print(f"\nFound {len(excel_files)} files\n")

    for file in excel_files:
        load_excel_file(file.name)

def load_all_data():

    datasets = {}

    excel_files = list(RAW_DATA_PATH.glob("*.xlsx"))

    for file in excel_files:

        datasets[file.stem] = load_excel_file(file.name)

    return datasets