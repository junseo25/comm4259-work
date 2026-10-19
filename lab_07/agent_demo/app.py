from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Customer Churn Dashboard", layout="wide")
st.title("Customer churn dashboard")

# Load the raw data from the data/ folder next to this file
DATA_PATH = Path(__file__).parent / "data" / "Customer.csv"
raw = pd.read_csv(DATA_PATH)


# Apply my data-preparation decisions, in order
def prepare(df):
    df = df.copy()

    # HasReview: 1 if the customer left a review, else 0 (made before dropping Reviews)
    df["HasReview"] = df["Reviews"].notna().astype(int)

    # Keep only columns with less than 80% missing (drops Reviews and Feedback_Call)
    missing_share = df.isna().mean()
    df = df.loc[:, missing_share < 0.80]

    # ZipCode: keep the first five digits
    df["ZipCode"] = df["ZipCode"].astype(str).str[:5]

    # BirthYear: fill missing values with the median
    df["BirthYear"] = df["BirthYear"].fillna(df["BirthYear"].median())

    # AgeAtJoin: year of JoinDate minus BirthYear
    df["AgeAtJoin"] = pd.to_datetime(df["JoinDate"]).dt.year - df["BirthYear"]

    return df


prepared = prepare(raw)

# Create the dashboard tabs
(prep_tab,) = st.tabs(["Data Preparation"])

with prep_tab:
    # Show rows and columns before and after
    st.subheader("Rows and columns")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows before", raw.shape[0])
    c2.metric("Rows after", prepared.shape[0], delta=prepared.shape[0] - raw.shape[0])
    c3.metric("Columns before", raw.shape[1])
    c4.metric("Columns after", prepared.shape[1], delta=prepared.shape[1] - raw.shape[1])

    # Show missing values in each column before and after
    st.subheader("Missing values by column")
    missing = pd.DataFrame({
        "Missing before": raw.isna().sum(),
        "% before": (raw.isna().mean() * 100).round(1),
        "Missing after": prepared.isna().sum(),
        "% after": (prepared.isna().mean() * 100).round(1),
    })
    # Columns that only exist on one side show as blank; label them so it's clear why
    missing["Note"] = ""
    missing.loc[~missing.index.isin(prepared.columns), "Note"] = "Dropped"
    missing.loc[~missing.index.isin(raw.columns), "Note"] = "New column"
    missing = missing.reindex(list(raw.columns) + [c for c in prepared.columns if c not in raw.columns])
    st.dataframe(missing, width="stretch")

    # Chart the average AgeAtJoin for churned vs. returning customers
    st.subheader("Average age at join: churned vs. returning customers")
    avg_age = (
        prepared.assign(Group=prepared["Churn"].map({1: "Churned", 0: "Returning"}))
        .groupby("Group")["AgeAtJoin"]
        .mean()
        .round(1)
    )
    st.bar_chart(avg_age, y_label="Average AgeAtJoin (years)")
    st.dataframe(avg_age.rename("Average AgeAtJoin"))
