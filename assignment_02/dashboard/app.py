from pathlib import Path

import pandas as pd
import streamlit as st

# Where the default data file lives
DATA_DIR = Path(__file__).parent / "data"
DEFAULT_FILE = DATA_DIR / "titanic_features.csv"

ACTIONS = [
    "Drop a column",
    "Fill missing values",
    "Flag missing values",
    "Dummy-code a column",
    "Drop rows missing a value",
]
FILL_METHODS = ["mean", "median", "most frequent", "a value I type"]


# Write a column the way Lab 05/06 does: df.Sex, or df["My Col"] if the name has spaces
def col_ref(column):
    if column.isidentifier():
        return f"df.{column}"
    return f'df["{column}"]'


# Build a table with the type and missing values of each column
def profile_table(df):
    return pd.DataFrame({
        "column": df.columns,
        "type": [str(t) for t in df.dtypes],
        "missing": df.isna().sum().values,
        "missing share (%)": (df.isna().mean().values * 100).round(1),
    })


# Show rows, columns and the profile table
def show_profile(df):
    left, right = st.columns(2)
    left.metric("Rows", df.shape[0])
    right.metric("Columns", df.shape[1])
    st.dataframe(profile_table(df), hide_index=True)


# Carry out one step and return the new data plus the pandas code it equals
def apply_step(df, step):
    column = step["column"]
    action = step["action"]

    if action == "Drop a column":
        df = df.drop(columns=[column])
        code = f'df = df.drop(columns=["{column}"])'

    elif action == "Fill missing values":
        method = step["method"]
        if method == "mean":
            fill_value = df[column].mean()
            code_value = f'df["{column}"].mean()'
        elif method == "median":
            fill_value = df[column].median()
            code_value = f'df["{column}"].median()'
        elif method == "most frequent":
            fill_value = df[column].mode()[0]
            code_value = f'df["{column}"].mode()[0]'
        else:
            fill_value = step["value"]
            if isinstance(fill_value, str):
                code_value = f'"{fill_value}"'
            else:
                code_value = str(fill_value)
        df[column] = df[column].fillna(fill_value)
        code = f'df["{column}"] = df["{column}"].fillna({code_value})'

    elif action == "Flag missing values":
        flag_name = f"{column}_missing"
        df[flag_name] = df[column].isna().astype(int)
        code = f'df["{flag_name}"] = df["{column}"].isna().astype(int)'

    elif action == "Dummy-code a column":
        dummies = pd.get_dummies(df[column], prefix=column, drop_first=True,
                                 dtype=int, dummy_na=step["dummy_na"])
        df = pd.concat([df, dummies], axis=1)
        dummy_name = f"{column}_dummy" if column.isidentifier() else "dummy"
        na_part = ", dummy_na=True" if step["dummy_na"] else ""
        code = (f'{dummy_name} = pd.get_dummies({col_ref(column)}, prefix="{column}", '
                f'drop_first=True, dtype=int{na_part})\n'
                f'df = pd.concat([df, {dummy_name}], axis=1)')

    else:  # Drop rows missing a value
        df = df.dropna(subset=[column])
        code = f'df = df.dropna(subset=["{column}"])'

    return df, code


# Page setup and the two tabs
st.set_page_config(page_title="Data Preparation Workbench", layout="wide")
st.title("Data Preparation Workbench")
workbench_tab, eda_tab = st.tabs(["Data Preparation Workbench", "EDA"])

with workbench_tab:
    # 1. Load the uploaded CSV, or the default Titanic file
    uploaded = st.file_uploader("Upload a CSV (leave empty to use data/titanic_features.csv)", type="csv")
    if uploaded is not None:
        raw = pd.read_csv(uploaded)
        source_name = uploaded.name
    else:
        raw = pd.read_csv(DEFAULT_FILE)
        source_name = DEFAULT_FILE.name
    st.caption(f"Using: {source_name}")

    # Start a fresh step list when the file changes (old steps point to old columns)
    if st.session_state.get("source_name") != source_name:
        st.session_state["source_name"] = source_name
        st.session_state["steps"] = []

    st.header("1. Profile of the original data")
    show_profile(raw)

    # 2. Replay every saved step in order and record before/after numbers
    df = raw.copy()
    reports = []
    for number, step in enumerate(st.session_state["steps"], start=1):
        if step["column"] not in df.columns:
            reports.append({"number": number, "step": step, "skipped": True})
            continue
        before = (df.shape[0], df.shape[1], int(df.isna().sum().sum()))
        df, code = apply_step(df, step)
        after = (df.shape[0], df.shape[1], int(df.isna().sum().sum()))
        reports.append({"number": number, "step": step, "skipped": False,
                        "before": before, "after": after, "code": code})

    # 3. Menu for adding a new step (works on the data as it is after the saved steps)
    st.header("2. Add a step")
    action = st.selectbox("Action", ACTIONS)
    column = st.selectbox("Column", list(df.columns))
    new_step = {"action": action, "column": column, "method": None, "value": None, "dummy_na": False}

    if action == "Fill missing values" and column is not None:
        is_numeric = pd.api.types.is_numeric_dtype(df[column])
        methods = FILL_METHODS if is_numeric else ["most frequent", "a value I type"]
        new_step["method"] = st.radio("Fill with", methods, horizontal=True)
        if new_step["method"] == "a value I type":
            if is_numeric:
                new_step["value"] = st.number_input("Value")
            else:
                new_step["value"] = st.text_input("Value")

    if action == "Dummy-code a column":
        new_step["dummy_na"] = st.checkbox("Add a column for missing values (dummy_na=True)")

    if st.button("Add step", disabled=column is None):
        if action == "Fill missing values" and new_step["method"] == "most frequent" and df[column].isna().all():
            st.error(f"{column} has no values, so there is no most frequent value.")
        else:
            st.session_state["steps"].append(new_step)
            st.rerun()

    # 4. Report for each step: before/after numbers and the pandas line
    st.header("3. Steps")
    if not reports:
        st.info("No steps yet. Add one above.")
    for report in reports:
        step = report["step"]
        title = f'Step {report["number"]}: {step["action"]} - {step["column"]}'
        with st.expander(title, expanded=True):
            if report["skipped"]:
                st.warning(f'Skipped: column "{step["column"]}" no longer exists at this point.')
                continue
            table = pd.DataFrame(
                [report["before"], report["after"]],
                index=["before", "after"],
                columns=["rows", "columns", "missing values"],
            )
            st.dataframe(table)
            st.code(report["code"], language="python")

    # 5. Profile of the prepared data and download button
    st.header("4. Prepared data")
    show_profile(df)
    st.dataframe(df.head(20))
    st.download_button(
        "Download prepared data (CSV)",
        data=df.to_csv(index=False),
        file_name="prepared_data.csv",
        mime="text/csv",
    )

with eda_tab:
    # Choose which data to explore: the original file or the result of the steps
    st.header("Exploratory data analysis")
    choice = st.radio("Data to explore", ["Raw data", "Prepared data"], horizontal=True)
    eda = raw if choice == "Raw data" else df
    numeric_columns = list(eda.select_dtypes("number").columns)

    # 1. Summary statistics and a frequency table
    with st.container(border=True):
        st.subheader("1. Summary statistics and frequency table")
        st.code("df.describe()", language="python")
        st.dataframe(eda.describe())
        freq_column = st.selectbox("Column for the frequency table", list(eda.columns), key="freq_column")
        st.code(f'df["{freq_column}"].value_counts()', language="python")
        st.dataframe(eda[freq_column].value_counts())

    # 2. Histogram of a chosen number column
    with st.container(border=True):
        st.subheader("2. Histogram")
        if not numeric_columns:
            st.info("This data has no number columns.")
        else:
            hist_column = st.selectbox("Number column", numeric_columns, key="hist_column")
            bins = st.slider("Number of bins", 5, 50, 10)
            st.code(f'df["{hist_column}"].value_counts(bins={bins}, sort=False)', language="python")
            counts = eda[hist_column].value_counts(bins=bins, sort=False)
            counts.index = counts.index.astype(str)
            st.bar_chart(counts, sort=False, x_label=hist_column, y_label="count")

    # 3. Survival rate for each group of a chosen column
    with st.container(border=True):
        st.subheader("3. Survived rate by group")
        if "Survived" not in eda.columns:
            st.info("This data has no Survived column.")
        else:
            other_columns = [c for c in eda.columns if c != "Survived"]
            group_column = st.selectbox("Group by", other_columns, key="group_column")
            st.code(f'df.groupby("{group_column}")["Survived"].mean()', language="python")
            st.dataframe(eda.groupby(group_column)["Survived"].mean())

    # 4. Correlation table of the number columns
    with st.container(border=True):
        st.subheader("4. Correlation table")
        st.code("df.corr(numeric_only=True)", language="python")
        st.dataframe(eda.corr(numeric_only=True).round(2))
