import streamlit as st
from google.cloud import bigquery
import json
import os
from google.oauth2 import service_account
import random

# Set page config
st.set_page_config(
    page_title="Loan Default Prediction",
    page_icon="💰",
    layout="wide"
)

# Function to generate random values within pre-defined ranges in the "find_ranges_for_rand.py" file
# These values are manually coded, so the application does not have to query for the ranges every time
def get_random_defaults():
    ranges = {
        'loan_amnt': (800.0, 40000.0),
        'funded_amnt': (800.0, 40000.0),
        'funded_amnt_inv': (0.0, 40000.0),
        'int_rate': (5.31, 30.99),
        'installment': (24.84, 1618.24),
        'annual_inc': (0.0, 9225000.0),
        'dti': (0.0, 999.0),
        'delinq_2yrs': (0.0, 35.0),
        'fico_range_low': (625.0, 845.0),
        'fico_range_high': (629.0, 850.0),
        'inq_last_6mths': (0.0, 17.0),
        'mths_since_last_delinq': (0.0, 152.0),
        'open_acc': (1.0, 66.0),
        'pub_rec': (0.0, 61.0),
        'revol_bal': (0.0, 689335.0),
        'revol_util': (0.0, 137.2),
        'total_acc': (1.0, 122.0),
        'total_pymnt': (0.0, 40981.43),
        'total_rec_prncp': (0.0, 40000.0),  # predetermined loan max
        'total_rec_int': (0.0, 40000.0),    # predetermined loan max
        'recoveries': (0.0, 40000.0),       # predetermined loan max
        'collection_recovery_fee': (0.0, 1000.0),  # predetermined max
        'last_pymnt_amnt': (0.0, 40981.43)
    }
    
    # String values from query results
    string_values = {
        'sub_grade': ['A1', 'A2', 'A3', 'A4', 'A5', 'B1', 'B2', 'B3', 'B4', 'B5', 
                     'C1', 'C2', 'C3', 'C4', 'C5', 'D1', 'D2', 'D3', 'D4', 'D5', 
                     'E1', 'E2', 'E3', 'E4', 'E5', 'F1', 'F2', 'F3', 'F4', 'F5', 
                     'G1', 'G2', 'G3', 'G4', 'G5'],
        'home_ownership': ['ANY', 'MORTGAGE', 'OTHER', 'OWN', 'RENT'],
        'verification_status': ['Not Verified', 'Source Verified', 'Verified']
    }
    
    # Actually generate random values
    random_values = {}
    for field, (min_val, max_val) in ranges.items():
        if field in ['delinq_2yrs', 'inq_last_6mths', 'open_acc', 'pub_rec', 'total_acc']:
            # Integer values
            random_values[field] = random.randint(int(min_val), int(max_val))
        else:
            # Float values, rounded to 2 decimal places
            random_values[field] = round(random.uniform(min_val, max_val), 2)
    
    # Generate random string values
    for field, values in string_values.items():
        random_values[field] = random.choice(values)
    
    return random_values

try:
    # Retrieve service account credentials from Streamlit secrets
    credentials_info = {
        "type": st.secrets["google"]["type"],
        "project_id": st.secrets["google"]["project_id"],
        "private_key_id": st.secrets["google"]["private_key_id"],
        "private_key": st.secrets["google"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["google"]["client_email"],
        "client_id": st.secrets["google"]["client_id"],
        "auth_uri": st.secrets["google"]["auth_uri"],
        "token_uri": st.secrets["google"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["google"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["google"]["client_x509_cert_url"],
        "universe_domain": st.secrets["google"]["universe_domain"]
    }

    # Use the credentials to authenticate the BigQuery client
    credentials = service_account.Credentials.from_service_account_info(credentials_info)
    client = bigquery.Client(credentials=credentials, project=credentials_info["project_id"])

except Exception as e:
    st.error(f"Error initializing BigQuery client: {str(e)}")
    st.stop()


# Define the BigQuery SQL query for making predictions
def predict_loan(defaulted, loan_amnt, funded_amnt, funded_amnt_inv, int_rate, installment, sub_grade,
                 home_ownership, annual_inc, verification_status, dti, delinq_2yrs, fico_range_low, fico_range_high,
                 inq_last_6mths, mths_since_last_delinq, open_acc, pub_rec, revol_bal, revol_util, total_acc,
                 total_pymnt, total_rec_prncp, total_rec_int, recoveries, collection_recovery_fee, last_pymnt_amnt):
    try:
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
                    {last_pymnt_amnt} AS last_pymnt_amnt,
                    RAND() AS random_value))
        """
        # Execute the query and get the prediction
        result = client.query(query).result()
        
        # Extract prediction from result
        for row in result:
            return row.predicted_defaulted
    except Exception as e:
        st.error(f"Error making prediction: {str(e)}")
        return None

# Streamlit UI for user input
st.title("Loan Default Prediction")

# Initialize session state for defaults if not exists
if 'defaults' not in st.session_state:
    st.session_state.defaults = get_random_defaults()

st.write("Enter the details below to predict loan default probability.")

# Input fields for the user to fill out with random default values
loan_amnt = st.number_input("Loan Amount", min_value=800.0, max_value=40000.0, value=float(st.session_state.defaults['loan_amnt']))
funded_amnt = st.number_input("Funded Amount", min_value=800.0, max_value=40000.0, value=float(st.session_state.defaults['funded_amnt']))
funded_amnt_inv = st.number_input("Funded Amount Investment", min_value=0.0, max_value=40000.0, value=float(st.session_state.defaults['funded_amnt_inv']))
int_rate = st.number_input("Interest Rate (%)", min_value=5.31, max_value=30.99, value=float(st.session_state.defaults['int_rate']))
installment = st.number_input("Installment Amount", min_value=24.84, max_value=1618.24, value=float(st.session_state.defaults['installment']))

# Define sub_grade options
sub_grade_options = ['A1', 'A2', 'A3', 'A4', 'A5', 'B1', 'B2', 'B3', 'B4', 'B5', 
                    'C1', 'C2', 'C3', 'C4', 'C5', 'D1', 'D2', 'D3', 'D4', 'D5', 
                    'E1', 'E2', 'E3', 'E4', 'E5', 'F1', 'F2', 'F3', 'F4', 'F5', 
                    'G1', 'G2', 'G3', 'G4', 'G5']

# Create boxes and dropdowns for the user to fill out or generate random values
sub_grade = st.selectbox("Sub Grade", sub_grade_options, 
                        index=sub_grade_options.index(st.session_state.defaults['sub_grade']))
home_ownership = st.selectbox("Home Ownership", ['ANY', 'MORTGAGE', 'OTHER', 'OWN', 'RENT'],
                            index=['ANY', 'MORTGAGE', 'OTHER', 'OWN', 'RENT'].index(st.session_state.defaults['home_ownership']))
annual_inc = st.number_input("Annual Income", min_value=0.0, max_value=9225000.0, value=float(st.session_state.defaults['annual_inc']))
verification_status = st.selectbox("Verification Status", ['Not Verified', 'Source Verified', 'Verified'],
                                    index=['Not Verified', 'Source Verified', 'Verified'].index(st.session_state.defaults['verification_status']))
dti = st.number_input("Debt-to-Income Ratio", min_value=0.0, max_value=999.0, value=float(st.session_state.defaults['dti']))
delinq_2yrs = st.number_input("Delinquencies in the last 2 years", min_value=0.0, max_value=35.0, value=float(st.session_state.defaults['delinq_2yrs']))
fico_range_low = st.number_input("FICO Range Low", min_value=625.0, max_value=845.0, value=float(st.session_state.defaults['fico_range_low']))
fico_range_high = st.number_input("FICO Range High", min_value=629.0, max_value=850.0, value=float(st.session_state.defaults['fico_range_high']))
inq_last_6mths = st.number_input("Inquiries in the last 6 months", min_value=0.0, max_value=17.0, value=float(st.session_state.defaults['inq_last_6mths']))
mths_since_last_delinq = st.number_input("Months since last delinquency", min_value=0.0, max_value=152.0, value=float(st.session_state.defaults['mths_since_last_delinq']))
open_acc = st.number_input("Open Accounts", min_value=1.0, max_value=66.0, value=float(st.session_state.defaults['open_acc']))
pub_rec = st.number_input("Public Records", min_value=0.0, max_value=61.0, value=float(st.session_state.defaults['pub_rec']))
revol_bal = st.number_input("Revolving Balance", min_value=0.0, max_value=689335.0, value=float(st.session_state.defaults['revol_bal']))
revol_util = st.number_input("Revolving Utilization Rate (%)", min_value=0.0, max_value=137.2, value=float(st.session_state.defaults['revol_util']))
total_acc = st.number_input("Total Accounts", min_value=1.0, max_value=122.0, value=float(st.session_state.defaults['total_acc']))
total_pymnt = st.number_input("Total Payment", min_value=0.0, max_value=40981.43, value=float(st.session_state.defaults['total_pymnt']))
total_rec_prncp = st.number_input("Total Principal Repaid", min_value=0.0, max_value=40000.0, value=float(st.session_state.defaults['total_rec_prncp']))
total_rec_int = st.number_input("Total Interest Repaid", min_value=0.0, max_value=40000.0, value=float(st.session_state.defaults['total_rec_int']))
recoveries = st.number_input("Recoveries", min_value=0.0, max_value=40000.0, value=float(st.session_state.defaults['recoveries']))
collection_recovery_fee = st.number_input("Collection Recovery Fee", min_value=0.0, max_value=1000.0, value=float(st.session_state.defaults['collection_recovery_fee']))
last_pymnt_amnt = st.number_input("Last Payment Amount", min_value=0.0, max_value=40981.43, value=float(st.session_state.defaults['last_pymnt_amnt']))

# Button to generate new random values
if st.button('Generate New Random Values', key='generate_random'):
    st.session_state.defaults = get_random_defaults()
    st.rerun()

# Button to trigger prediction
if st.button('Predict Loan Default', type="primary"):
    with st.spinner('Making prediction...'):
        # Get the prediction from BigQuery model
        prediction = predict_loan(
            0,  # defaulted parameter (not used in prediction but required by function)
            loan_amnt, funded_amnt, funded_amnt_inv, int_rate, installment, sub_grade,
            home_ownership, annual_inc, verification_status, dti, delinq_2yrs, fico_range_low,
            fico_range_high, inq_last_6mths, mths_since_last_delinq, open_acc, pub_rec, revol_bal,
            revol_util, total_acc, total_pymnt, total_rec_prncp, total_rec_int, recoveries,
            collection_recovery_fee, last_pymnt_amnt
        )
        if prediction is not None:
            if prediction == 1:
                st.error("The loan is **predicted to default**.")
            else:
                st.success("The loan is **predicted not to default**.")
