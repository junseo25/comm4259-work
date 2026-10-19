from pathlib import Path
import pandas as pd
import streamlit as st

st.title("Customer churn: a first look")

customer = pd.read_csv(Path(__file__).parent / "Customer.csv")   # the data file next to this app

st.metric("Customers", len(customer))
st.metric("Churn rate", f"{customer['Churn'].mean():.1%}")

column = st.selectbox("Show the churn rate by", ["Gender", "Education", "Children"])
st.bar_chart(customer.groupby(column)["Churn"].mean())

st.dataframe(customer.head(10))
