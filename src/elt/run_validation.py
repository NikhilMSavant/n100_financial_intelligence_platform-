from validator import (
    check_primary_key,
    check_foreign_key,
    check_positive_sales,
    check_company_year_uniqueness,
    check_foreign_key_integrity,
    save_validation_failure
)
from loader import load_all_data
from validator import (
    check_primary_key,
    check_foreign_key,
    check_positive_sales
)

datasets = load_all_data()

companies = datasets["companies"]

profitandloss = datasets["profitandloss"]


duplicates = check_primary_key(
    companies,
    "id"
)

print("\nDQ-01 PRIMARY KEY CHECK")

print(duplicates)


invalid_sales = check_positive_sales(
    profitandloss
)
save_validation_failure(
    rule_id="DQ-06",
    severity="WARNING",
    dataframe=invalid_sales
)
print("\nDQ-06 POSITIVE SALES CHECK")

print(invalid_sales)

# DQ-02

duplicates = check_company_year_uniqueness(
    profitandloss
)

print("\nDQ-02 COMPANY + YEAR UNIQUENESS CHECK")

print(duplicates)


save_validation_failure(
    rule_id="DQ-02",
    severity="CRITICAL",
    dataframe=duplicates
)


# DQ-03

invalid_fk = check_foreign_key_integrity(

    profitandloss,

    companies,

    fk_column="company_id"

)

print("\nDQ-03 FOREIGN KEY CHECK")

print(invalid_fk)


save_validation_failure(

    rule_id="DQ-03",

    severity="CRITICAL",

    dataframe=invalid_fk

)

print(companies["id"].head(20))

print(
    profitandloss["company_id"]
    .isin(companies["id"])
    .value_counts()
)


missing_ids = set(
    profitandloss["company_id"]
) - set(
    companies["id"]
)

print(missing_ids)