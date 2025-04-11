query = """
    SELECT predicted_defaulted
    FROM ML.PREDICT(MODEL `loan_club_dataset.boosted_tree_model`,
        (SELECT
            @loan_amnt AS loan_amnt,
            ...
            @sub_grade AS sub_grade,
            ...
            RAND() AS random_value))
"""

job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("loan_amnt", "FLOAT64", loan_amnt),
        bigquery.ScalarQueryParameter("sub_grade", "STRING", sub_grade),
        # ...and so on for all parameters
    ]
)

result = client.query(query, job_config=job_config).result()
