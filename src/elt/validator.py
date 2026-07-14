import pandas as pd


def check_primary_key(df, column_name):

    duplicates = df[df[column_name].duplicated()]

    return duplicates


def check_foreign_key(child_df, parent_df, fk_column, pk_column):

    invalid = child_df[
        ~child_df[fk_column].isin(parent_df[pk_column])
    ]

    return invalid


def check_positive_sales(df):

    invalid = df[df["sales"] <= 0]

    return invalid
def save_validation_failure(
    rule_id,
    severity,
    dataframe,
    output_file="output/validation_failures.csv"
):

    if dataframe.empty:
        return

    dataframe = dataframe.copy()

    dataframe["rule_id"] = rule_id
    dataframe["severity"] = severity

    dataframe.to_csv(
        output_file,
        mode="a",
        header=not pd.io.common.file_exists(output_file),
        index=False
    )

def check_company_year_uniqueness(df):

    duplicates = df[
        df.duplicated(
            subset=["company_id", "year"],
            keep=False
        )
    ]

    return duplicates


def check_foreign_key_integrity(
    child_df,
    parent_df,
    fk_column,
    pk_column="id"
):

    invalid = child_df[
        ~child_df[fk_column].isin(
            parent_df[pk_column]
        )
    ]

    return invalid