-- This file displays the steps I took to preprocess the data,
-- then train, test, and evaluate the boosted tree classifier model in BigQuery.

-- Step 1:Create a new cleaned table from accepted_loans
CREATE OR REPLACE TABLE loan_club_dataset.accepted_loans_cleaned AS
WITH accepted AS (
    SELECT 
        -- Relevant columns
        loan_amnt, 
        funded_amnt, 
        funded_amnt_inv, 
        int_rate, 
        installment, 
        grade, 
        sub_grade, 
        emp_length, 
        home_ownership, 
        annual_inc, 
        verification_status,
        loan_status,  
        dti, 
        delinq_2yrs, 
        fico_range_low, 
        fico_range_high, 
        inq_last_6mths, 
        mths_since_last_delinq, 
        open_acc, 
        pub_rec, 
        revol_bal, 
        revol_util,
        total_acc,
        total_pymnt, 
        total_rec_prncp,
        total_rec_int,
        recoveries,
        collection_recovery_fee,
        last_pymnt_amnt,
        CASE 
            WHEN loan_status = 'Charged Off' THEN 1 
            ELSE 0 
        END AS defaulted
    FROM loan_club_dataset.accepted_loans
    WHERE loan_status IS NOT NULL
)
SELECT 
    loan_amnt, 
    funded_amnt, 
    funded_amnt_inv, 
    int_rate, 
    installment, 
    sub_grade,
    emp_length, 
    home_ownership, 
    annual_inc, 
    verification_status,
    loan_status, 
    dti, 
    delinq_2yrs, 
    fico_range_low, 
    fico_range_high, 
    inq_last_6mths, 
    mths_since_last_delinq, 
    open_acc, 
    pub_rec, 
    revol_bal, 
    revol_util,
    total_acc,
    total_pymnt, 
    total_rec_prncp,
    total_rec_int,
    recoveries,
    collection_recovery_fee,
    last_pymnt_amnt,
    defaulted
FROM accepted;



-- Step 2: Remove columns with too many missing values or irrelevant features
CREATE OR REPLACE TABLE loan_club_dataset.accepted_loans_cleaned_no_missing AS
SELECT 
    loan_amnt, 
    funded_amnt, 
    funded_amnt_inv, 
    int_rate, 
    installment, 
    sub_grade, 
    home_ownership, 
    annual_inc, 
    verification_status,
    dti, 
    delinq_2yrs, 
    fico_range_low, 
    fico_range_high, 
    inq_last_6mths, 
    mths_since_last_delinq, 
    open_acc, 
    pub_rec,   -- Correct column for public records/bankruptcies
    revol_bal, 
    revol_util,
    total_acc,
    total_pymnt, 
    total_rec_prncp,
    total_rec_int,
    recoveries,
    collection_recovery_fee,
    last_pymnt_amnt,
    defaulted
FROM loan_club_dataset.accepted_loans_cleaned
WHERE revol_util IS NOT NULL AND pub_rec IS NOT NULL; 


-- Step 3: Convert categorical variables such as sub_grade, home_ownership, verification_status, and zip_code into dummy variables.
CREATE OR REPLACE TABLE loan_club_dataset.accepted_loans_final AS
SELECT 
    loan_amnt, 
    funded_amnt, 
    funded_amnt_inv, 
    int_rate, 
    installment, 
    -- Drop the 'grade' column and use 'sub_grade' dummies instead
    sub_grade, 
    home_ownership,
    annual_inc, 
    verification_status,
    dti, 
    delinq_2yrs, 
    fico_range_low, 
    fico_range_high, 
    inq_last_6mths, 
    mths_since_last_delinq, 
    open_acc, 
    pub_rec, 
    revol_bal, 
    revol_util,
    total_acc,
    total_pymnt, 
    total_rec_prncp,
    total_rec_int,
    recoveries,
    collection_recovery_fee,
    last_pymnt_amnt,
    defaulted
FROM loan_club_dataset.accepted_loans_cleaned_no_missing;



-- Step 4: Remove the address column and any other features that don't provide value to the model (like issue_d or emp_title).
-- Drop the 'address' and 'issue_d' columns (irrelevant)
CREATE OR REPLACE TABLE loan_club_dataset.accepted_loans_final_cleaned AS
SELECT 
    loan_amnt, 
    funded_amnt, 
    funded_amnt_inv, 
    int_rate, 
    installment, 
    sub_grade, 
    home_ownership, 
    annual_inc, 
    verification_status,
    dti, 
    delinq_2yrs, 
    fico_range_low, 
    fico_range_high, 
    inq_last_6mths, 
    mths_since_last_delinq, 
    open_acc, 
    pub_rec, 
    revol_bal, 
    revol_util,
    total_acc,
    total_pymnt, 
    total_rec_prncp,
    total_rec_int,
    recoveries,
    collection_recovery_fee,
    last_pymnt_amnt,
    defaulted
FROM loan_club_dataset.accepted_loans_final;



-- Confirm distribution of defaulted loans (ie. make sure the classifier accuracy is higher than highest distribution. IE. ensure it isn't just outputting 0 or 1)
SELECT 
  defaulted, 
  COUNT(*) AS count,
  ROUND(COUNT(*) * 100 / SUM(COUNT(*)) OVER(), 2) AS percentage
FROM `loan_club_dataset.accepted_loans_final_cleaned`
GROUP BY defaulted
ORDER BY defaulted;



--------------------------------- Model Training ---------------------------------

-- Split the data into training and test sets
CREATE OR REPLACE TABLE `loan_club_dataset.train_data` AS
WITH stratified_data AS (
  SELECT *, RAND() AS random_value
  FROM `loan_club_dataset.accepted_loans_final_cleaned`
)

SELECT *
FROM stratified_data
WHERE random_value <= 0.8;  -- 80% for training


CREATE OR REPLACE TABLE `loan_club_dataset.test_data` AS
WITH stratified_data AS (
  SELECT *, RAND() AS random_value
  FROM `loan_club_dataset.accepted_loans_final_cleaned`
)

SELECT *
FROM stratified_data
WHERE random_value > 0.8;  -- 20% for testing



-- Train the model, tweaked with parameters and this was the best I got
CREATE OR REPLACE MODEL `loan_club_dataset.boosted_tree_model`
OPTIONS(
  model_type='BOOSTED_TREE_CLASSIFIER',
  input_label_cols=['defaulted'],
  max_iterations=100,      
  max_tree_depth=20,
  colsample_bytree=1,   -- Uses x% of features per tree (prevents feature dominance)
  l1_reg=0.1            -- higher value encourance sparsity (if overfitting, increase this), lower values mean more complex model, defaults 0.0
  -- subsample=0.7    -- defaults 1, decrease down to 0.8 to introduce randomness
) AS
SELECT * FROM `loan_club_dataset.train_data`;



-------------------------- Model Testing and Evaluation ------------------------------

-- Test the model on the test set
SELECT predicted_defaulted, predicted_defaulted_probs
FROM
  ML.PREDICT(MODEL `loan_club_dataset.boosted_tree_model`,
             (SELECT * FROM `loan_club_dataset.test_data`));


-- Evaluate the model
SELECT *
FROM
  ML.EVALUATE(MODEL `loan_club_dataset.boosted_tree_model`, 
              (SELECT * FROM `loan_club_dataset.test_data`));

