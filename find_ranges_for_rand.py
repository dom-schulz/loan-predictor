from google.cloud import bigquery
import json
from google.oauth2 import service_account

# Read service account credentials
with open('streamlit_service_key.json', 'r') as f:
    credentials_info = json.load(f)

credentials = service_account.Credentials.from_service_account_info(credentials_info)
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

# Query for numerical columns min/max
numerical_query = """
SELECT
    MIN(loan_amnt) as loan_amnt_min,
    MAX(loan_amnt) as loan_amnt_max,
    MIN(funded_amnt) as funded_amnt_min,
    MAX(funded_amnt) as funded_amnt_max,
    MIN(funded_amnt_inv) as funded_amnt_inv_min,
    MAX(funded_amnt_inv) as funded_amnt_inv_max,
    MIN(int_rate) as int_rate_min,
    MAX(int_rate) as int_rate_max,
    MIN(installment) as installment_min,
    MAX(installment) as installment_max,
    MIN(annual_inc) as annual_inc_min,
    MAX(annual_inc) as annual_inc_max,
    MIN(dti) as dti_min,
    MAX(dti) as dti_max,
    MIN(delinq_2yrs) as delinq_2yrs_min,
    MAX(delinq_2yrs) as delinq_2yrs_max,
    MIN(fico_range_low) as fico_range_low_min,
    MAX(fico_range_low) as fico_range_low_max,
    MIN(fico_range_high) as fico_range_high_min,
    MAX(fico_range_high) as fico_range_high_max,
    MIN(inq_last_6mths) as inq_last_6mths_min,
    MAX(inq_last_6mths) as inq_last_6mths_max,
    MIN(mths_since_last_delinq) as mths_since_last_delinq_min,
    MAX(mths_since_last_delinq) as mths_since_last_delinq_max,
    MIN(open_acc) as open_acc_min,
    MAX(open_acc) as open_acc_max,
    MIN(pub_rec) as pub_rec_min,
    MAX(pub_rec) as pub_rec_max,
    MIN(revol_bal) as revol_bal_min,
    MAX(revol_bal) as revol_bal_max,
    MIN(revol_util) as revol_util_min,
    MAX(revol_util) as revol_util_max,
    MIN(total_acc) as total_acc_min,
    MAX(total_acc) as total_acc_max,
    MIN(total_pymnt) as total_pymnt_min,
    MAX(total_pymnt) as total_pymnt_max,
    MIN(total_rec_prncp) as total_rec_prncp_min,
    MAX(total_rec_prncp) as total_rec_prncp_max,
    MIN(total_rec_int) as total_rec_int_min,
    MAX(total_rec_int) as total_rec_int_max,
    MIN(recoveries) as recoveries_min,
    MAX(recoveries) as recoveries_max,
    MIN(collection_recovery_fee) as collection_recovery_fee_min,
    MAX(collection_recovery_fee) as collection_recovery_fee_max,
    MIN(last_pymnt_amnt) as last_pymnt_amnt_min,
    MAX(last_pymnt_amnt) as last_pymnt_amnt_max
FROM `loan_club_dataset.train_data`
"""

# Query for distinct string values
string_query = """
SELECT
    STRING_AGG(DISTINCT sub_grade, ', ' ORDER BY sub_grade) as sub_grades,
    STRING_AGG(DISTINCT home_ownership, ', ' ORDER BY home_ownership) as home_ownerships,
    STRING_AGG(DISTINCT verification_status, ', ' ORDER BY verification_status) as verification_statuses
FROM `loan_club_dataset.train_data`
"""

# Execute queries
numerical_results = client.query(numerical_query).result()
string_results = client.query(string_query).result()

# Print results
print("\nNumerical Ranges:")
print("-----------------")
for row in numerical_results:
    for field in row.keys():
        print(f"{field}: {row[field]}")

print("\nDistinct String Values:")
print("----------------------")
for row in string_results:
    for field in row.keys():
        print(f"{field}: {row[field]}")
