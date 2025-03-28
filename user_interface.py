import streamlit as st
from google.cloud import bigquery
import json
import os

# Access service account JSON from Streamlit Secrets
service_account_json = st.secrets["google"]["service_account_json"]

# Load the service account JSON as a dictionary
credentials_info = json.loads(service_account_json)

# Set the environment variable for Google Cloud authentication
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_info

# Initialize BigQuery client
client = bigquery.Client()

# Now you can make BigQuery queries using this client

# Define the BigQuery SQL query for making predictions
def predict_loan(defaulted, loan_amnt, funded_amnt, funded_amnt_inv, int_rate, installment, sub_grade,
                 home_ownership, annual_inc, verification_status, dti, delinq_2yrs, fico_range_low, fico_range_high,
                 inq_last_6mths, mths_since_last_delinq, open_acc, pub_rec, revol_bal, revol_util, total_acc,
                 total_pymnt, total_rec_prncp, total_rec_int, recoveries, collection_recovery_fee, last_pymnt_amnt):
    query = f"""
    SELECT
        predicted_defaulted
    FROM
        ML.PREDICT(MODEL `loan_club_dataset.boosted_tree_model`,
            (SELECT
                {loan_amnt} AS loan_amnt,
                {funded_amnt} AS funded_amnt,
                {funded_amnt_inv} AS funded_amnt_inv,
                {int_rate} AS int_rate,
                {installment} AS installment,
                '{sub_grade}' AS sub_grade,
                '{home_ownership}' AS home_ownership,
                {annual_inc} AS annual_inc,
                '{verification_status}' AS verification_status,
                {dti} AS dti,
                {delinq_2yrs} AS delinq_2yrs,
                {fico_range_low} AS fico_range_low,
                {fico_range_high} AS fico_range_high,
                {inq_last_6mths} AS inq_last_6mths,
                {mths_since_last_delinq} AS mths_since_last_delinq,
                {open_acc} AS open_acc,
                {pub_rec} AS pub_rec,
                {revol_bal} AS revol_bal,
                {revol_util} AS revol_util,
                {total_acc} AS total_acc,
                {total_pymnt} AS total_pymnt,
                {total_rec_prncp} AS total_rec_prncp,
                {total_rec_int} AS total_rec_int,
                {recoveries} AS recoveries,
                {collection_recovery_fee} AS collection_recovery_fee,
                {last_pymnt_amnt} AS last_pymnt_amnt))
    """
    # Execute the query and get the prediction
    result = client.query(query).result()
    
    # Extract prediction from result
    for row in result:
        return row.predicted_defaulted

# Define the Streamlit UI for user input
def main():
    st.title("Loan Default Prediction")
    st.write("Enter the details below to predict loan default probability.")

    # Input fields for the user to fill out
    loan_amnt = st.number_input("Loan Amount", min_value=0.0)
    funded_amnt = st.number_input("Funded Amount", min_value=0.0)
    funded_amnt_inv = st.number_input("Funded Amount Investment", min_value=0.0)
    int_rate = st.number_input("Interest Rate (%)", min_value=0.0)
    installment = st.number_input("Installment Amount", min_value=0.0)
    sub_grade = st.selectbox("Sub Grade", ['A', 'B', 'C', 'D', 'E', 'F', 'G'])
    home_ownership = st.selectbox("Home Ownership", ['OWN', 'MORTGAGE', 'RENT'])
    annual_inc = st.number_input("Annual Income", min_value=0.0)
    verification_status = st.selectbox("Verification Status", ['Verified', 'Not Verified'])
    dti = st.number_input("Debt-to-Income Ratio", min_value=0.0)
    delinq_2yrs = st.number_input("Delinquencies in the last 2 years", min_value=0)
    fico_range_low = st.number_input("FICO Range Low", min_value=0)
    fico_range_high = st.number_input("FICO Range High", min_value=0)
    inq_last_6mths = st.number_input("Inquiries in the last 6 months", min_value=0)
    mths_since_last_delinq = st.number_input("Months since last delinquency", min_value=0)
    open_acc = st.number_input("Open Accounts", min_value=0)
    pub_rec = st.number_input("Public Records", min_value=0)
    revol_bal = st.number_input("Revolving Balance", min_value=0.0)
    revol_util = st.number_input("Revolving Utilization Rate (%)", min_value=0.0)
    total_acc = st.number_input("Total Accounts", min_value=0)
    total_pymnt = st.number_input("Total Payment", min_value=0.0)
    total_rec_prncp = st.number_input("Total Principal Repaid", min_value=0.0)
    total_rec_int = st.number_input("Total Interest Repaid", min_value=0.0)
    recoveries = st.number_input("Recoveries", min_value=0.0)
    collection_recovery_fee = st.number_input("Collection Recovery Fee", min_value=0.0)
    last_pymnt_amnt = st.number_input("Last Payment Amount", min_value=0.0)

    # Button to trigger prediction
    if st.button('Predict Loan Default'):
        # Get the prediction from BigQuery model
        prediction = predict_loan(
            loan_amnt, funded_amnt, funded_amnt_inv, int_rate, installment, sub_grade,
            home_ownership, annual_inc, verification_status, dti, delinq_2yrs, fico_range_low,
            fico_range_high, inq_last_6mths, mths_since_last_delinq, open_acc, pub_rec, revol_bal,
            revol_util, total_acc, total_pymnt, total_rec_prncp, total_rec_int, recoveries,
            collection_recovery_fee, last_pymnt_amnt
        )
        if prediction == 1:
            st.write("The loan is likely to **default**.")
        else:
            st.write("The loan is **unlikely to default**.")

if __name__ == '__main__':
    main()
