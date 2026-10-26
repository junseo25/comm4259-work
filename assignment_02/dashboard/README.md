# Data Preparation Workbench

A Streamlit app with two tabs. **Data Preparation Workbench** lets you prepare a CSV file step by step.
**EDA** lets you explore the raw or the prepared data.
The app makes no decisions on its own and uses no AI model: it only runs the steps you add.

## How to run

```
cd assignment_02/dashboard
python -m streamlit run app.py
```

## What it does

1. **Load data**: upload any CSV, or leave the uploader empty to use `data/titanic_features.csv`
   (an unchanged copy of `assignment_02/titanic_train.csv`).
2. **Profile**: rows, columns, the type of each column, and the number and share of missing values per column.
3. **Add steps** from a fixed menu:
   - Drop a column: `df = df.drop(columns=["Cabin"])`
   - Fill missing values (mean, median, most frequent, or a typed value):
     `df["Age"] = df["Age"].fillna(df["Age"].median())`
   - Flag missing values: `df["Age_missing"] = df["Age"].isna().astype(int)`
   - Dummy-code a column (Lab 05/06 style, the original column is kept; optional `dummy_na=True`):
     `Sex_dummy = pd.get_dummies(df.Sex, prefix="Sex", drop_first=True, dtype=int)` then
     `df = pd.concat([df, Sex_dummy], axis=1)`
   - Drop rows missing a value: `df = df.dropna(subset=["Embarked"])`
4. **See each step**: rows, columns and missing values before and after, plus the pandas line it equals.
5. **Download** the prepared data as `prepared_data.csv`.

Steps run in the order you add them. Uploading a different file starts a new, empty step list.

## EDA tab

Pick **Raw data** or **Prepared data**. Each part shows the pandas line it uses:

1. Summary statistics and a frequency table: `df.describe()`, `df["Sex"].value_counts()`
2. Histogram of a chosen number column: `df["Age"].value_counts(bins=10, sort=False)`
3. Survived rate for each group of a chosen column: `df.groupby("Sex")["Survived"].mean()`
   (only when the data has a Survived column)
4. Correlation table: `df.corr(numeric_only=True)`

## Recipe for my Titanic decisions

1. Flag missing values: Age (flag before filling, otherwise nothing is missing anymore)
2. Fill missing values: Age, median
3. Drop a column: Cabin
4. Flag missing values: Embarked
5. Dummy-code a column: Sex, then Embarked, then Pclass

## Files

- `app.py`: the app
- `data/titanic_features.csv`: default data
- `requirements.txt`: package versions used
- `ai_sessions/`: AI session records
- `AI_USE_LOG.md`: my AI use log
