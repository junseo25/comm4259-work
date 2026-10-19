# Customer Churn Dashboard (Lab 7)

A Streamlit dashboard for `data/Customer.csv`. The **Data Preparation** tab shows:

- rows and columns before and after preparation
- missing values in each column before and after preparation
- a chart of the average `AgeAtJoin` for churned (`Churn = 1`) and returning (`Churn = 0`) customers

## Data-preparation decisions

1. **HasReview**: 1 if the customer left a review, else 0.
2. **Drop Reviews and Feedback_Call**: keep only columns with less than 80% missing.
3. **ZipCode**: keep the first five digits.
4. **BirthYear**: fill missing values with the median.
5. **AgeAtJoin**: year of `JoinDate` minus `BirthYear`.

## How to run

From this folder (`lab_07/agent_demo/`):

```
streamlit run app.py
```

The app reads the data relative to its own file, so you can also run it from anywhere with
`streamlit run path/to/agent_demo/app.py`.
