"""Example project dashboard for COMM 4259 (Assignment 4, Section B).

Run it from the assignment_04 folder (VS Code terminal):
    cd assignment_04
    python -m streamlit run dashboard/app.py

Five tabs, in CRISP-DM order:
  1. Data                 upload a CSV file (or use the wine quality data), pick the target
  2. EDA                  target distribution; pick x and y axes to see a feature by class
  3. Data Preparation     your decisions: duplicates, missing values, outliers, columns to drop; Apply button
  4. Model Playground     pick a model and its parameters, optionally tune with GridSearchCV
  5. Cost-Benefit         a cost matrix, the expected cost of each model you trained, and your recommendation

Every number is computed by this code from the data. The app contains no AI model and makes
no decisions by itself: the choices in each tab are yours.
"""
import base64
import inspect
import io
import json
import os
import time

import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from sklearn.ensemble import (AdaBoostClassifier, BaggingClassifier, RandomForestClassifier,
                              StackingClassifier, VotingClassifier)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix, f1_score,
                             precision_score, recall_score)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
# ADAPT 1: your project data file (put it in dashboard/data/)
DEFAULT_FILE = os.path.join(HERE, "data", "WineQuality.csv")
OUT_DIR = os.path.join(HERE, "outputs")    # saved runs and decision record, committed with the code
MAX_CLASSES = 20          # a classification target has a few classes, not hundreds


@st.cache_data
def read_csv(source):
    """Read a CSV file; sep=None detects commas or semicolons."""
    return pd.read_csv(source, sep=None, engine="python")


# Plot style: one palette, quiet axes, small figures
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID, AXIS, OTHER = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#c3c2b7"
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "font.family": ["Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 10,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlesize": 10, "axes.titleweight": "bold",
    "axes.titlecolor": INK, "axes.titlelocation": "left", "axes.titlepad": 10,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "legend.fontsize": 9, "legend.title_fontsize": 9,
})


def show(fig, share):
    """Show a figure across `share` of the page width (0 to 1). It is saved at high resolution and
    the browser scales it down, so it stays sharp on any screen."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    png = buf.getvalue()
    pixels = int.from_bytes(png[16:20], "big")             # image width, from the PNG header
    data = base64.b64encode(png).decode()
    st.markdown(f'<img src="data:image/png;base64,{data}" '
                f'style="width:{share:.0%}; max-width:min(100%, {pixels // 2}px)">', unsafe_allow_html=True)


def class_colors(values, positive):
    """The positive class is always blue; the other classes take the next colors in a fixed order."""
    others = sorted({str(v) for v in values} - {str(positive)})
    order = [str(positive)] + others
    return order, {c: SERIES[i % len(SERIES)] for i, c in enumerate(order)}


st.set_page_config(page_title="Project Dashboard", layout="wide")
# ADAPT 2: your project title and one sentence on the business question
st.title("Project Dashboard")
st.caption("Example on the wine quality data. Your team's dashboard follows the same tabs.")

tab_data, tab_eda, tab_prep, tab_model, tab_value = st.tabs(
    ["Tab 1: Data", "Tab 2: EDA", "Tab 3: Data Preparation", "Tab 4: Model Playground",
     "Tab 5: Cost-Benefit and Recommendation"])

# ---------------------------------------------------------------- 1. Data
def fit(n_rows):
    """Table height in pixels that shows every row (a header plus n rows) without scrolling."""
    return 35 * (n_rows + 1) + 3


def valid_classes(frame, column):
    """The classes of a column, or None if it cannot be a classification target."""
    values = sorted(frame[column].dropna().unique().tolist(), key=str)
    return values if 2 <= len(values) <= MAX_CLASSES else None


def default_positive(frame, column, values):
    """Prefer Good / 1 / Yes / True; otherwise the smallest class."""
    def same(c, want):                            # 1, 1.0 and "1" all count as 1; True stays True
        if isinstance(c, (int, float)) and not isinstance(c, bool) and isinstance(want, int) \
                and not isinstance(want, bool):
            return c == want
        return str(c) == str(want)
    preferred = ["Good", 1, "1", "Yes", "yes", "Y", "True", "true"]
    found = next((i for want in preferred for i, c in enumerate(values) if same(c, want)), None)
    return found if found is not None else values.index(frame[column].value_counts().idxmin())


with tab_data:
    st.subheader("What data do we have?")
    upload = st.file_uploader("Upload a CSV file, or leave empty to use the wine quality data", type="csv")
    raw = read_csv(upload) if upload is not None else read_csv(DEFAULT_FILE)
    source_name = upload.name if upload is not None else "WineQuality.csv"
    st.write(f"**First 10 rows of {source_name}**")
    st.dataframe(raw.head(10))
    cols = list(raw.columns)

    # Step 1. Describe the dataset
    st.write("**Step 1. Describe the dataset**")
    if st.session_state.get("described") not in (None, source_name):
        st.session_state.described = None                      # new data: describe it again
    if st.button("Describe the dataset", type="primary"):
        bar = st.progress(0.0, text="Counting rows, columns, missing values and duplicates...")
        time.sleep(0.15)
        bar.progress(0.5, text="Summarizing each column...")
        time.sleep(0.15)
        bar.progress(1.0, text="Done")
        st.session_state.described = source_name
    if st.session_state.get("described") == source_name:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Rows", f"{len(raw):,}")
        c2.metric("Columns", raw.shape[1])
        c3.metric("Missing values", int(raw.isna().sum().sum()))
        c4.metric("Duplicate rows", int(raw.duplicated().sum()))
        st.write("Column types, missing values, and number of different values")
        st.dataframe(pd.DataFrame({"type": raw.dtypes.astype(str), "missing": raw.isna().sum(),
                                   "different values": raw.nunique()}), height=fit(raw.shape[1]))
        numeric_cols = raw.select_dtypes("number")
        if not numeric_cols.empty:
            st.write("Summary statistics of the numeric columns")
            st.dataframe(numeric_cols.describe().T.round(3), height=fit(numeric_cols.shape[1]))
    else:
        st.caption("Click **Describe the dataset** to see its size, column types, missing values, "
                   "duplicates, and summary statistics.")

    # Step 2. Set the target variable and the positive class
    # ADAPT 3: your target column and positive class are picked here; set the defaults to yours
    st.write("**Step 2. Set the target variable and the positive class**")
    default_target = cols[-1]
    default_classes = valid_classes(raw, default_target)
    if st.session_state.get("target_set", (None,))[0] != source_name:     # new data: start from defaults
        st.session_state.target_set = (
            (source_name, default_target, default_classes[default_positive(raw, default_target, default_classes)])
            if default_classes else (source_name, None, None))

    pick_target = st.selectbox("Target column (the column the model predicts)", cols, index=len(cols) - 1)
    pick_classes = valid_classes(raw, pick_target)
    pick_positive = None
    if pick_classes is None:
        st.error(f"'{pick_target}' has {raw[pick_target].nunique()} different values. A classification "
                 f"target needs between 2 and {MAX_CLASSES} classes. Pick another target column, or "
                 "prepare the target first (for example, turn a number into Good / Poor).")
    else:
        pick_positive = st.selectbox("Positive class (the class the business wants to catch)", pick_classes,
                                     index=default_positive(raw, pick_target, pick_classes))
        n_pos = int((raw[pick_target] == pick_positive).sum())
        if n_pos < 2 or raw[pick_target].notna().sum() - n_pos < 2:
            st.error("The positive class and the other classes each need at least 2 rows.")
            pick_positive = None
    if st.button("Set target and positive class", type="primary", disabled=pick_positive is None):
        bar = st.progress(0.5, text="Setting the target and the positive class...")
        st.session_state.target_set = (source_name, pick_target, pick_positive)
        bar.progress(1.0, text="Done")
        st.success(f"Target set: **{pick_target}**, positive class **{pick_positive}** (= 1). "
                   "The other tabs now use it.")

    _, target, positive = st.session_state.target_set
    if target is None:
        st.warning("Pick a target column with 2 to 20 classes and click **Set target and positive class**.")
        st.stop()
    if (pick_target, pick_positive) != (target, positive):
        st.info(f"Not set yet: the other tabs still use target **{target}** with positive class "
                f"**{positive}**. Click **Set target and positive class** to use your new choice.")
    st.caption(f"In use: target **{target}**, positive class **{positive}** (= 1). Precision, recall, F1, "
               "and the TP and FN cells all refer to the positive class.")
    classes = valid_classes(raw, target)
    others = [c for c in classes if c != positive]
    negative = str(others[0]) if len(others) == 1 else "other"     # the name of class 0 in labels

# ---------------------------------------------------------------- 2. EDA
with tab_eda:
    st.subheader("What does the data look like?")
    numeric = [c for c in raw.select_dtypes("number").columns if c != target]
    order, colors = class_colors(raw[target].dropna(), positive)
    labels = raw[target].astype(str)

    # Top row: the target distribution
    counts = labels.value_counts().reindex(order).fillna(0).astype(int)
    fig, ax = plt.subplots(figsize=(6, 3.2))
    bars = ax.bar(counts.index, counts.values, width=0.55,
                  color=[colors[c] for c in counts.index], edgecolor="white", linewidth=2)
    for b, n in zip(bars, counts.values):
        ax.text(b.get_x() + b.get_width() / 2, n, f"{n:,} ({n / counts.sum():.0%})",
                ha="center", va="bottom", fontsize=9, color=INK2)
    ax.set_title(f"Target distribution: {target} (all {len(raw):,} rows in the file, before preparation)")
    ax.set_ylabel("rows")
    ax.set_ylim(0, counts.max() * 1.18)
    show(fig, 0.5)

    # Bottom row: one plot the user picks
    # ADAPT 4: add the EDA plots your team needs (e.g., a boxplot of a key feature, a bar chart of a category)
    st.write("**Explore one feature, or two features together**")
    if numeric:
        COUNT = "Count (distribution of the x-axis feature by class)"
        c1, c2 = st.columns(2)
        x_col = c1.selectbox("X axis", numeric, key="eda_x")
        y_col = c2.selectbox("Y axis", [COUNT] + [c for c in numeric if c != x_col], key="eda_y")
        eda_key = (source_name, target)
        if st.session_state.get("eda_key") != eda_key:          # new data or target: clear the old plot
            st.session_state.eda_key, st.session_state.eda_plot = eda_key, None
        if st.button("Show plot", type="primary"):
            bar = st.progress(0.2, text="Preparing the plot...")
            st.session_state.eda_plot = (x_col, y_col)
            bar.progress(1.0, text="Done")
        shown = st.session_state.get("eda_plot")
        if shown and shown != (x_col, y_col):
            st.info("You changed the axes. Click **Show plot** to update the plot.")
        if shown and shown[0] in raw.columns and (shown[1] == COUNT or shown[1] in raw.columns):
            x_show, y_show = shown
            fig, ax = plt.subplots(figsize=(9, 4))
            if y_show == COUNT:
                sns.histplot(data=raw, x=x_show, hue=labels, hue_order=order, palette=colors, bins=30,
                             element="step", fill=False, alpha=0.55, linewidth=1, kde=True,
                             line_kws={"linewidth": 2}, ax=ax)
                ax.set_title(f"Distribution of {x_show} by {target}")
                ax.set_ylabel("rows")
            else:
                ax.grid(True, axis="both")
                sns.scatterplot(data=raw, x=x_show, y=y_show, hue=labels, hue_order=order, palette=colors,
                                s=16, alpha=0.65, edgecolor="white", linewidth=0.4, ax=ax)
                ax.set_title(f"{y_show} against {x_show}, by {target}")
            legend = ax.get_legend()
            if legend:
                legend.set_title(target)
                legend.set_loc("upper right")
            show(fig, 0.75)
        elif not shown:
            st.caption("Pick the axes and click **Show plot**. With Y axis set to Count, the plot shows "
                       "how one feature is distributed in each class.")

# ---------------------------------------------------------------- 3. Data Preparation
OUTLIER_RULES = ["Keep outliers",
                 "Cap outliers at the 1.5 x IQR limits",
                 "Remove rows with outliers"]
MISSING_RULES = ["Drop rows with missing values",
                 "Fill numbers with the median and text with the most frequent value"]


def iqr_limits(frame):
    q1, q3 = frame.quantile(0.25), frame.quantile(0.75)
    return q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)


def prepare(raw, target, positive, choice):
    """Apply the preparation choices; return X, y, and a log of what was done."""
    df, log = raw.copy(), []
    if choice["drop_dups"]:
        n = int(df.duplicated().sum())
        df = df.drop_duplicates().reset_index(drop=True)
        log.append(("Duplicate rows", f"removed {n}"))
    else:
        log.append(("Duplicate rows", "kept"))

    n_no_target = int(df[target].isna().sum())
    if n_no_target:
        df = df.dropna(subset=[target]).reset_index(drop=True)
        log.append(("Missing target", f"dropped {n_no_target} rows with no {target} value"))
    n_missing = int(df.drop(columns=target).isna().sum().sum())
    if n_missing == 0:
        log.append(("Missing values", "none found, no action needed"))
    elif choice["missing_rule"] == MISSING_RULES[0]:
        n = len(df)
        df = df.dropna().reset_index(drop=True)
        log.append(("Missing values", f"dropped {n - len(df)} rows"))
    else:
        for c in df.columns.drop(target):
            if df[c].isna().any():
                fill = df[c].median() if pd.api.types.is_numeric_dtype(df[c]) else df[c].mode()[0]
                df[c] = df[c].fillna(fill)
        log.append(("Missing values", f"filled {n_missing} values with median / most frequent"))

    num = [c for c in df.select_dtypes("number").columns if c != target and c not in choice["drop_cols"]]
    if num and choice["outlier_rule"] != OUTLIER_RULES[0]:
        low, high = iqr_limits(df[num])
        outside = (df[num] < low) | (df[num] > high)
        if choice["outlier_rule"] == OUTLIER_RULES[1]:
            df[num] = df[num].clip(lower=low, upper=high, axis=1)
            log.append(("Outliers", f"capped {int(outside.sum().sum())} values at the 1.5 x IQR limits"))
        else:
            n = len(df)
            df = df[~outside.any(axis=1)].reset_index(drop=True)
            log.append(("Outliers", f"removed {n - len(df)} rows"))
    else:
        log.append(("Outliers", "kept"))

    if choice["drop_cols"]:
        df = df.drop(columns=choice["drop_cols"])
        log.append(("Dropped columns", ", ".join(choice["drop_cols"])))
    else:
        log.append(("Dropped columns", "none"))

    y = (df[target] == positive).astype(int)
    X = df.drop(columns=[target])
    text_cols = X.select_dtypes(exclude="number").columns.tolist()
    if text_cols:
        X = pd.get_dummies(X, columns=text_cols, dtype=int)
        log.append(("Text columns", f"one-hot encoded: {', '.join(text_cols)}"))
    log.append(("Target", f"{positive} = 1, everything else = 0"))
    return X, y, log


with tab_prep:
    st.subheader("What did we do to the data, and why?")
    st.write("Each choice below is a data preparation decision. Look at the data quality checks, make "
             "your choices, and click **Apply preparation**. Write the reason for each choice in your "
             "decision table, including the choices where no action is needed.")

    # Data quality checks on the raw data
    numeric_raw = [c for c in raw.select_dtypes("number").columns if c != target]
    st.write("**Data quality checks (before preparation; outliers counted after removing duplicates)**")
    dedup = raw.drop_duplicates()
    checks = pd.DataFrame({"missing values": raw.drop(columns=target).isna().sum()})
    n_out_rows = 0
    if numeric_raw:
        low, high = iqr_limits(dedup[numeric_raw])
        outside_raw = (dedup[numeric_raw] < low) | (dedup[numeric_raw] > high)
        checks["outliers (1.5 x IQR)"] = outside_raw.sum()
        n_out_rows = int(outside_raw.any(axis=1).sum())
    st.dataframe(checks.fillna(0).astype(int), height=fit(len(checks)))
    st.caption(f"Duplicate rows: {int(raw.duplicated().sum())}. Rows with at least one outlier, after removing "
               f"duplicates: {n_out_rows} of {len(dedup)}. A value is an outlier here if it is more than 1.5 "
               "times the interquartile range below the first quartile or above the third quartile.")

    id_like = [c for c in cols if c != target and raw[c].nunique() == len(raw)
               and not pd.api.types.is_float_dtype(raw[c])]
    if id_like:
        st.warning(f"These columns have a different value in every row and look like IDs: "
                   f"{', '.join(id_like)}. IDs do not help a model generalize; consider dropping them.")

    # ADAPT 5: one step per row of your decision table; add steps here and in prepare() for your project
    st.write("**Your decisions, one step at a time.** Every step is a row of your decision table. "
             "\"No action\" is a decision too: record it with its evidence.")
    n_dup = int(raw.duplicated().sum())
    n_miss = int(raw.drop(columns=target).isna().sum().sum())

    st.markdown("**Step 1. Duplicate rows**")
    st.caption(f"Found {n_dup:,} duplicate rows.")
    drop_dups = st.checkbox("Remove duplicate rows", value=True)

    st.markdown("**Step 2. Missing values**")
    if n_miss == 0:
        st.caption("No missing values in the input columns, so this choice has no effect on this data. "
                   "Record \"no action needed\" and the count (0) in your decision table.")
    else:
        st.caption(f"Found {n_miss:,} missing values in the input columns; see the checks table above.")
    missing_rule = st.radio("What to do with missing values", MISSING_RULES)

    st.markdown("**Step 3. Outliers**")
    st.caption(f"{n_out_rows:,} of {len(dedup):,} rows (after removing duplicates) have at least one value "
               "outside the 1.5 x IQR limits.")
    outlier_rule = st.radio("What to do with outliers", OUTLIER_RULES)

    st.markdown("**Step 4. Columns to drop**")
    st.caption("Drop columns that would not be available when the prediction is made, or that only "
               "identify a row (IDs).")
    drop_cols = st.multiselect("Columns to drop", [c for c in cols if c != target])

    choice = {"drop_dups": drop_dups, "missing_rule": missing_rule, "outlier_rule": outlier_rule,
              "drop_cols": drop_cols}
    default_choice = {"drop_dups": True, "missing_rule": MISSING_RULES[0], "outlier_rule": OUTLIER_RULES[0],
                      "drop_cols": []}
    data_key = (source_name, target, str(positive))
    if st.session_state.get("prep_data_key") != data_key:          # new data or target: start from defaults
        st.session_state.prep_data_key = data_key
        st.session_state.applied = default_choice
    if st.button("Apply preparation", type="primary"):
        bar = st.progress(0.0, text="Applying your choices...")
        steps = ["duplicate rows", "missing values", "outliers", "columns to drop", "target"]
        for k, step in enumerate(steps, 1):
            time.sleep(0.12)
            bar.progress(k / (len(steps) + 1), text=f"Applying: {step}")
        bar.progress(1.0, text="Done")
        st.session_state.applied = choice
        st.session_state.just_applied = time.strftime("%H:%M:%S")
    applied = st.session_state.applied
    if choice != applied:
        st.info("Your choices above are not applied yet. Click **Apply preparation** to use them; "
                "until then, the tables below and the Model Playground use the last applied choices.")

    X, y, log = prepare(raw, target, positive, applied)
    if st.session_state.pop("just_applied", None):
        st.success(f"Preparation applied: {len(X):,} rows and {X.shape[1]} input columns. The tables below "
                   "and the Model Playground now use these choices.")

    st.write("**Before and after (applied choices)**")
    st.dataframe(pd.DataFrame({
        "before": [len(raw), raw.shape[1] - 1, int(raw.isna().sum().sum()), int(raw.duplicated().sum())],
        "after": [len(X), X.shape[1], int(X.isna().sum().sum()),
                  int(pd.concat([X, y], axis=1).duplicated().sum())],
    }, index=["rows", "input columns", "missing values", "duplicate rows"]))
    st.caption("Capping changes values, not rows, so the counts above stay the same; the steps below "
               "show how many values were capped.")
    st.write("**Steps applied**")
    st.dataframe(pd.DataFrame(log, columns=["step", "what was done"]), hide_index=True)

    if y.sum() < 2 or len(y) - y.sum() < 2:
        st.error("After these steps, the positive class or the other class has fewer than 2 rows.")
        st.stop()

    st.info(f"**The Model Playground (tab 4) trains on this prepared data:** {len(X):,} rows and "
            f"{X.shape[1]} input columns, with the applied choices above. To change it, change your "
            "choices and click **Apply preparation** again.")
    prepared = X.copy()
    prepared[f"{target} (1 = {positive})"] = y.values
    st.download_button("Download the prepared data as CSV", prepared.to_csv(index=False),
                       file_name="prepared_data.csv", mime="text/csv")

# ---------------------------------------------------------------- 4. Model Playground
# Version note: this app was tested with scikit-learn 1.5.1 and 1.9.1, and Streamlit 1.37.1 and 1.67.0.
# The one exception is AdaBoost: scikit-learn 1.5 and earlier default to "SAMME.R", while 1.6 and later
# use "SAMME" and drop the "algorithm" argument. Asking for SAMME only where the argument still exists
# gives every student the same algorithm, whatever version they have.
ADABOOST_SAMME = ({"algorithm": "SAMME"}
                  if "algorithm" in inspect.signature(AdaBoostClassifier.__init__).parameters else {})

# ADAPT 6: the models and parameters your team compares, and the GridSearchCV values to try
# Each model: (estimator builder, needs scaling, {parameter: (type, default, minimum, values for GridSearchCV)})
SPECS = {
    "Decision tree": (lambda p: DecisionTreeClassifier(random_state=1, **p), False,
                      {"max_depth": (int, 5, 1, "3, 5, 10"), "min_samples_leaf": (int, 1, 1, "1, 5, 20")}),
    "K-nearest neighbor": (lambda p: KNeighborsClassifier(**p), True,
                           {"n_neighbors": (int, 5, 1, "3, 5, 11")}),
    "Logistic regression": (lambda p: LogisticRegression(max_iter=1000, **p), True,
                            {"C": (float, 1.0, 0.0001, "0.1, 1, 10")}),
    "Support vector machine": (lambda p: SVC(random_state=1, **p), True,
                               {"C": (float, 1.0, 0.0001, "0.1, 1, 10")}),
    "Neural network (MLP)": (lambda p: MLPClassifier(hidden_layer_sizes=(100,), max_iter=1000,
                                                     random_state=1, **p), True,
                             {"alpha": (float, 0.0001, 0.0, "0.0001, 0.01")}),
    "Random forest": (lambda p: RandomForestClassifier(random_state=1, **p), False,
                      {"n_estimators": (int, 200, 1, "100, 200"), "max_depth": (int, 10, 1, "5, 10, 20")}),
    "Bagging": (lambda p: BaggingClassifier(random_state=1, **p), False,
                {"n_estimators": (int, 50, 1, "10, 50, 100")}),
    "AdaBoost": (lambda p: AdaBoostClassifier(random_state=1, **ADABOOST_SAMME, **p), False,
                 {"n_estimators": (int, 100, 1, "50, 100, 200"),
                  "learning_rate": (float, 1.0, 0.0001, "0.1, 0.5, 1")}),
    "Hard voting (tree, KNN, logistic regression)": (lambda p: VotingClassifier([
        ("dt", DecisionTreeClassifier(max_depth=5, random_state=1)),
        ("knn", KNeighborsClassifier(n_neighbors=5)),
        ("lr", LogisticRegression(max_iter=1000))], voting="hard"), True, {}),
    "Stacking (tree, KNN; logistic regression on top)": (lambda p: StackingClassifier([
        ("dt", DecisionTreeClassifier(max_depth=5, random_state=1)),
        ("knn", KNeighborsClassifier(n_neighbors=5))],
        final_estimator=LogisticRegression(max_iter=1000)), True, {}),
}
SLOW = {"Neural network (MLP)", "Support vector machine", "Stacking (tree, KNN; logistic regression on top)"}


def make_pipeline(name, params):
    build, scale, _ = SPECS[name]
    steps = [("scaler", StandardScaler())] if scale else []
    return Pipeline(steps + [("model", build(params))])


def parse_values(text, typ, minimum):
    """'3, 5, 10' -> [3, 5, 10]; raises ValueError with a message a student can act on."""
    parts = [v.strip() for v in text.split(",") if v.strip()]
    if not parts:
        raise ValueError("enter at least one value")
    values = []
    for v in parts:
        try:
            x = typ(v)
        except ValueError:
            kind = "whole numbers" if typ is int else "numbers"
            raise ValueError(f"'{v}' is not valid; enter {kind} separated by commas, for example 3, 5, 10")
        if x < minimum or (typ is float and minimum > 0 and x <= 0):
            raise ValueError(f"{v} is too small; values must be at least {minimum}")
        values.append(x)
    return values


def save_runs():
    """Write every run to dashboard/outputs/model_runs.csv, with the analysis id; return the path."""
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "model_runs.csv")
    out = pd.DataFrame(st.session_state.runs)
    out.insert(0, "analysis_id", st.session_state.analysis_id)
    out.to_csv(path, index=False)
    return path


with tab_model:
    st.subheader("How well does each model work?")
    choices_text = "; ".join(f"{step}: {done}" for step, done in log if step != "Target")
    st.info(f"**Data used here: the prepared data from tab 3** ({len(X):,} rows, {X.shape[1]} input "
            f"columns; target {positive} = 1). Applied choices: {choices_text}. To train on different "
            "data, go to tab 3, change the choices, and click **Apply preparation**.")
    with st.expander("How to use the Model Playground", expanded=True):
        st.markdown(
            "0. Every model here trains on the **prepared data** from tab 3 (the last applied choices).\n"
            "1. Leave the testing share at 0.3 unless you have a reason to change it.\n"
            "2. Pick a **Model**, then set its parameters in the boxes below it.\n"
            "3. To tune instead, check **Tune with GridSearchCV** and type the values to try for each "
            "parameter, separated by commas (for example `3, 5, 10`). GridSearchCV picks the best "
            "combination with cross-validation on the training data.\n"
            "4. Click **Train and evaluate**. The results of that run appear below: accuracy, precision, "
            "recall, F1, the confusion matrix, and the classification report.\n"
            "5. Each click **adds one run** to the table at the bottom. Repeat steps 2 to 4 for every model "
            "you want to compare.\n"
            "6. Click **Save the runs to the project folder** to save every run so far in "
            "`dashboard/outputs/model_runs.csv`. Runs are cleared if you "
            "refresh the page, click **Clear all runs**, or change the data, the preparation choices, "
            "or the testing share.\n"
            "7. Switching to another model resets that model's boxes to their defaults. The neural network "
            "may print a `ConvergenceWarning` in the terminal; the run is still valid.")
    test_size = st.slider("Share of the data held out for testing", 0.2, 0.4, 0.3, 0.05)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=1, stratify=y)
    st.caption(f"Training rows: {len(X_train):,}  |  Testing rows: {len(X_test):,}  |  random_state = 1")

    # Runs are only comparable on the same data, preparation, and test set: clear them if any of these change.
    signature = (source_name, target, str(positive), str(sorted(applied.items())), test_size)
    if "runs" not in st.session_state:
        st.session_state.runs = []
    if st.session_state.get("signature") not in (None, signature) and st.session_state.runs:
        st.session_state.runs = []
        st.warning("The data, the applied preparation, or the testing share changed, so the earlier runs "
                   "were cleared: runs are only comparable on the same testing data.")
    if st.session_state.get("signature") != signature:            # a new analysis: new id
        st.session_state.analysis_id = time.strftime("%Y%m%d-%H%M%S")
    st.session_state.signature = signature

    name = st.selectbox("Model", list(SPECS))
    _, _, pspec = SPECS[name]
    use_grid = bool(pspec) and st.checkbox("Tune with GridSearchCV", value=False, key=f"grid_{name}")
    if not pspec:
        st.caption("This model has fixed settings, so there is nothing to tune with GridSearchCV.")

    params, grid_text = {}, {}
    for p, (typ, default, minimum, grid_default) in pspec.items():
        if use_grid:
            grid_text[p] = st.text_input(f"{p}: values to try, separated by commas", grid_default, key=f"{name}_{p}_grid")
        elif typ is int:
            params[p] = int(st.number_input(p, value=default, step=1, min_value=minimum, key=f"{name}_{p}"))
        else:
            params[p] = float(st.number_input(p, value=default, min_value=minimum, format="%g", key=f"{name}_{p}"))
    folds = st.number_input("Cross-validation folds", 3, 10, 5) if use_grid else None
    if name in SLOW:
        st.caption("This model is slower; with GridSearchCV it can take more than a minute.")

    failed = False
    if st.button("Train and evaluate", type="primary"):
        bar = st.progress(0.1, text="Step 1 of 3: checking the settings")
        try:
            with st.spinner("Training..."):
                if use_grid:
                    grid = {f"model__{p}": parse_values(grid_text[p], pspec[p][0], pspec[p][2]) for p in pspec}
                    n_fits = int(folds) * int(np.prod([len(v) for v in grid.values()]))
                    bar.progress(0.3, text=f"Step 2 of 3: GridSearchCV is training {n_fits} models "
                                           f"({int(folds)} folds x each combination)")
                    search = GridSearchCV(make_pipeline(name, {}), grid, cv=int(folds), scoring="accuracy")
                    search.fit(X_train, y_train)
                    model = search.best_estimator_
                    setting = {k.replace("model__", ""): v for k, v in search.best_params_.items()}
                    setting_text = f"GridSearchCV best: {setting}"
                else:
                    bar.progress(0.3, text=f"Step 2 of 3: training the {name.lower()}")
                    model = make_pipeline(name, params).fit(X_train, y_train)
                    setting_text = str(params) if params else "fixed settings"
        except ValueError as err:
            bar.empty()
            failed = True
            st.error(f"Could not train the model: {err}. No run was added.")
        else:
            bar.progress(0.8, text="Step 3 of 3: evaluating on the testing data")
            pred = model.predict(X_test)
            tn, fp, fn, tp = confusion_matrix(y_test, pred, labels=[0, 1]).ravel()
            st.session_state.runs.append({
                "run": len(st.session_state.runs) + 1, "model": name, "setting": setting_text,
                "accuracy": accuracy_score(y_test, pred),
                "precision": precision_score(y_test, pred, zero_division=0),
                "recall": recall_score(y_test, pred, zero_division=0),
                "f1": f1_score(y_test, pred, zero_division=0),
                "TP": int(tp), "FP": int(fp), "FN": int(fn), "TN": int(tn)})
            st.session_state.last_report = classification_report(
                y_test, pred, labels=[0, 1], target_names=[f"{negative} (0)", f"{positive} (1)"], zero_division=0)
            bar.progress(1.0, text="Done")
            st.success(f"Run {len(st.session_state.runs)} added: {name}. Its results are below, and the "
                       "runs table at the bottom now has this run.")

    if st.session_state.runs:
        last = st.session_state.runs[-1]
        heading = "Last successful run (the run above failed)" if failed else "Latest run"
        st.write(f"**{heading}. Run {last['run']}: {last['model']}** ({last['setting']})")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Accuracy", f"{last['accuracy']:.3f}")
        c2.metric(f"Precision ({positive})", f"{last['precision']:.3f}")
        c3.metric(f"Recall ({positive})", f"{last['recall']:.3f}")
        c4.metric(f"F1 ({positive})", f"{last['f1']:.3f}")
        st.write("Confusion matrix on the testing data (TP in the top left, as in the cost matrix on tab 5)")
        st.table(pd.DataFrame([[last["TP"], last["FN"]], [last["FP"], last["TN"]]],
                              index=[f"Actual {positive} (1)", f"Actual {negative} (0)"],
                              columns=[f"Predicted {positive} (1)", f"Predicted {negative} (0)"]))
        st.code(st.session_state.last_report, language=None)

        st.write(f"All runs so far (precision, recall, and F1 are for the positive class, {positive})")
        runs = pd.DataFrame(st.session_state.runs)
        st.dataframe(runs.round(4), hide_index=True)
        if st.button("Save the runs to the project folder", type="primary"):
            path = save_runs()
            st.success(f"Saved {len(runs)} run{'s' if len(runs) != 1 else ''} to `{os.path.relpath(path, os.path.dirname(HERE))}`.")
        st.download_button("Or download the runs as CSV", runs.to_csv(index=False), "model_runs.csv", "text/csv")
        st.caption("Runs are kept only while this browser tab is open. Save them before you refresh "
                   "or close the page.")
        if st.button("Clear all runs"):
            st.session_state.runs = []
            st.rerun()

# ---------------------------------------------------------------- 5. Cost-Benefit and Recommendation
def money(x, digits=0):
    return f"-${abs(x):,.{digits}f}" if x < 0 else f"${x:,.{digits}f}"


KIND = {"TP": "Benefit", "TN": "Benefit", "FP": "Cost", "FN": "Cost"}   # fixed by the cell
# ADAPT 7: starting amounts for the wine shop (dollars per wine); students can change them in the app
DEFAULT_AMOUNTS = {"TP": "-12", "FN": "0", "FP": "20", "TN": "0"}


def cost_cell(column, cell, label):
    """One cell of the cost matrix. TP and TN are benefits (0 or negative); FP and FN are costs (0 or positive)."""
    kind = KIND[cell]
    hint = "0 or a negative number, e.g. -12" if kind == "Benefit" else "0 or a positive number, e.g. 20"
    with column:
        st.markdown(f"**{cell} ({kind.lower()})**: {label}")
        text = st.text_input(f"{cell} amount in dollars per case ({hint})", key=f"amount_{cell}",
                             value=DEFAULT_AMOUNTS[cell], placeholder=hint)
    if not text.strip():
        return None, f"{cell}: enter an amount."
    try:
        x = float(text.replace("$", "").replace(",", ""))
    except ValueError:
        return None, f"{cell}: '{text}' is not a number."
    if kind == "Cost" and x < 0:
        return None, f"{cell} is a cost, so its amount must be 0 or positive (you entered {text})."
    if kind == "Benefit" and x > 0:
        return None, f"{cell} is a benefit, so its amount must be 0 or negative (you entered {text})."
    return x, None


with tab_value:
    # ADAPT 7: describe your business case in the text below, and set DEFAULT_AMOUNTS above to your cost matrix
    st.subheader("What does each model cost?")
    st.write("Each cell of the cost matrix holds the dollar amount of one case. The cells start with the "
             "wine shop's amounts; change any of them to try another business case. **TP and TN are "
             "benefits: enter 0 or a negative number. FP and FN are costs: enter 0 or a positive number.** "
             "The best option has the **lowest** expected cost.")

    st.write("**Step 1. The models you trained in the Model Playground (testing data)**")
    if not st.session_state.runs:
        st.info("No runs yet. Train at least one model on tab 4; its confusion matrix appears here, "
                "and the cost matrix below is applied to it.")
    else:
        st.caption("Each confusion matrix counts the testing cases. The expected cost multiplies each "
                   "count by the dollar amount in the same cell of the cost matrix below, and adds the four.")
        per_row = 3
        runs = st.session_state.runs
        for start in range(0, len(runs), per_row):
            cols_cm = st.columns(per_row)
            for col, r in zip(cols_cm, runs[start:start + per_row]):
                with col:
                    st.markdown(f"**Run {r['run']}: {r['model']}**  \n{r['setting']}")
                    st.dataframe(pd.DataFrame(
                        [[r["TP"], r["FN"]], [r["FP"], r["TN"]]],
                        index=[f"Actual {positive} (1)", f"Actual {negative} (0)"],
                        columns=[f"Predicted {positive} (1)", f"Predicted {negative} (0)"]))

    st.write("**Step 2. The cost matrix: dollars per case**")
    head = st.columns([1, 2, 2])
    head[1].markdown(f"**Predicted {positive} (1)**")
    head[2].markdown(f"**Predicted {negative} (0)**")
    row1 = st.columns([1, 2, 2])
    row1[0].markdown(f"**Actual {positive} (1)**")
    v_tp, p_tp = cost_cell(row1[1], "TP", f"predicted {positive}, actually {positive}")
    v_fn, p_fn = cost_cell(row1[2], "FN", f"predicted {negative}, actually {positive}")
    row0 = st.columns([1, 2, 2])
    row0[0].markdown(f"**Actual {negative} (0)**")
    v_fp, p_fp = cost_cell(row0[1], "FP", f"predicted {positive}, actually {negative}")
    v_tn, p_tn = cost_cell(row0[2], "TN", f"predicted {negative}, actually {negative}")

    problems = [p for p in (p_tp, p_fn, p_fp, p_tn) if p]          # in reading order of the matrix
    for p in problems:
        if not p.endswith("enter an amount."):
            st.warning(p)

    entered = {"TN": v_tn, "FP": v_fp, "FN": v_fn, "TP": v_tp}
    st.write("**Step 3. Calculate the expected cost of every run, and compare with two baselines**")
    if st.button("Calculate expected cost", type="primary", disabled=bool(problems)):
        bar = st.progress(0.0, text="Calculating...")
        n_options = len(st.session_state.runs) + 2
        for k in range(1, n_options + 1):
            time.sleep(0.1)
            bar.progress(k / n_options, text=f"Calculating the expected cost: {k} of {n_options} options "
                                             "(the runs and the two baselines)")
        st.session_state.cost_matrix = entered
        st.session_state.amounts_changed = False
        st.success(f"Expected cost calculated for {n_options} options. The results are below.")
    if problems:
        st.caption("Fill in all four cells with valid amounts to calculate the expected cost.")
    if st.session_state.get("cost_matrix") not in (None, entered):
        st.session_state.cost_matrix = None          # amounts changed since the last calculation
        st.session_state.amounts_changed = True
    if st.session_state.get("amounts_changed") and not st.session_state.get("cost_matrix") and not problems:
        st.info("The amounts changed. Click **Calculate expected cost** again.")

    cm = st.session_state.get("cost_matrix")
    if cm:
        n_pos, n_neg = int(y_test.sum()), int(len(y_test) - y_test.sum())
        rows = [{"option": "Baseline: predict positive for everyone", "TP": n_pos, "FP": n_neg, "FN": 0, "TN": 0},
                {"option": "Baseline: predict negative for everyone", "TP": 0, "FP": 0, "FN": n_pos, "TN": n_neg}]
        rows += [{"option": f"Run {r['run']}: {r['model']} ({r['setting']})",
                  "TP": r["TP"], "FP": r["FP"], "FN": r["FN"], "TN": r["TN"]}
                 for r in st.session_state.runs]
        table = pd.DataFrame(rows)
        table["expected cost ($)"] = (table.TP * cm["TP"] + table.FP * cm["FP"]
                                      + table.FN * cm["FN"] + table.TN * cm["TN"])
        table["cost per case ($)"] = table["expected cost ($)"] / len(y_test)
        table = table.sort_values("expected cost ($)")

        if not st.session_state.runs:
            st.info("Train at least one model in the Model Playground to compare it with the baselines.")
        st.dataframe(table, hide_index=True, column_config={
            "expected cost ($)": st.column_config.NumberColumn(format="%.0f"),
            "cost per case ($)": st.column_config.NumberColumn(format="%.2f")})
        st.caption("Expected cost is the total over the testing data; cost per case divides it by the "
                   f"{len(y_test)} testing cases.")
        chart_df = table.assign(
            label=[o.split(" (")[0] if o.startswith("Run") else o for o in table.option],
            kind=["Baseline" if o.startswith("Baseline") else "Model run" for o in table.option],
            amount=[money(v) for v in table["expected cost ($)"]],
            per_case=[money(v, 2) for v in table["cost per case ($)"]])
        best_i = chart_df.index[chart_df.kind == "Model run"][:1]
        chart_df.loc[best_i, "kind"] = "Lowest-cost run"
        order_y = chart_df.label.tolist()                              # lowest cost at the top
        base = alt.Chart(chart_df).encode(
            y=alt.Y("label:N", sort=order_y, title=None, axis=alt.Axis(labelLimit=260, labelColor=INK2, labelPadding=10)),
            x=alt.X("expected cost ($):Q", title="expected cost on the testing data ($)",
                    scale=alt.Scale(nice=True, padding=10),
                    axis=alt.Axis(format="$,.0f", tickCount=6, gridColor=GRID, labelColor=INK2,
                                  titleColor=INK2, labelPadding=6)),
            tooltip=[alt.Tooltip("option:N", title="option"), alt.Tooltip("amount:N", title="expected cost"),
                     alt.Tooltip("per_case:N", title="per case"), "TP:Q", "FP:Q", "FN:Q", "TN:Q"])
        bars = base.mark_bar(height=22, cornerRadiusEnd=4).encode(color=alt.Color(
            "kind:N", title=None, legend=alt.Legend(orient="top"),
            scale=alt.Scale(domain=["Lowest-cost run", "Model run", "Baseline"],
                            range=["#184f95", SERIES[0], OTHER])))
        pos = base.transform_filter("datum['expected cost ($)'] >= 0").mark_text(
            align="left", dx=6, color=INK2, fontSize=12).encode(text="amount:N")
        neg = base.transform_filter("datum['expected cost ($)'] < 0").mark_text(
            align="left", dx=8, color="white", fontSize=12, fontWeight="bold").encode(text="amount:N")
        zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=AXIS).encode(x="x:Q")
        st.altair_chart((bars + pos + neg + zero).properties(width=700, height=alt.Step(44))
                        .configure_view(stroke=None).configure_axis(domain=False, tickColor=GRID))

        best = table.iloc[0]
        best_text = (f"{money(best['expected cost ($)'])} "
                     f"({money(best['cost per case ($)'], 2)} per case)").replace("$", "\\$")
        st.write(f"Lowest expected cost on the testing data: **{best['option']}**, {best_text}. "
                 "A negative expected cost is a net benefit.")

    st.subheader("Recommendation, saved as a decision record")
    run_labels = [f"Run {r['run']}: {r['model']} ({r['setting']})" for r in st.session_state.runs]
    can_save = bool(run_labels) and bool(st.session_state.get("cost_matrix"))
    if not can_save:
        st.caption("To save: train at least one run and click **Calculate expected cost**, then pick the "
                   "recommended run and write the recommendation.")
    with st.form("decision_record"):
        chosen = st.selectbox("Recommended run", run_labels or ["(no runs yet)"])
        rec_text = st.text_area("Your recommendation, in your own words (the same text as Task B5): which "
                                "model, what it costs or saves compared with the baselines, and one limitation",
                                height=150)
        submitted = st.form_submit_button("Save the decision record to the project folder", type="primary")
    if submitted and not can_save:
        st.error("Nothing saved: train at least one run and click **Calculate expected cost** first.")
    elif submitted and not rec_text.strip():
        st.error("Nothing saved: write the recommendation first.")
    elif submitted:
        bar = st.progress(0.3, text="Saving the model runs...")
        runs_path = save_runs()
        bar.progress(0.7, text="Saving the decision record...")
        record = {
            "analysis_id": st.session_state.analysis_id,
            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "data_file": source_name, "rows_in_file": len(raw),
            "target": target, "positive_class": str(positive),
            "preparation_choices": {k: v for k, v in applied.items()},
            "preparation_steps_applied": {step: done for step, done in log},
            "prepared_rows": len(X), "input_columns": int(X.shape[1]),
            "testing_share": test_size, "random_state": 1, "testing_rows": len(y_test),
            "cost_matrix": st.session_state.cost_matrix,
            "expected_cost_by_option": {o: float(c) for o, c in zip(table.option, table["expected cost ($)"])},
            "lowest_cost_option": str(table.iloc[0]["option"]),
            "recommended_run": chosen,
            "recommendation": rec_text.strip(),
            "model_runs_file": "model_runs.csv",
        }
        rec_path = os.path.join(OUT_DIR, "decision_record.json")
        with open(rec_path, "w") as f:
            json.dump(record, f, indent=2, default=str)
        bar.progress(1.0, text="Done")
        st.success("Saved to `dashboard/outputs/`: `model_runs.csv` (one row per run) and "
                   "`decision_record.json` (one record for this analysis). Commit both with your code.")
    st.caption("Good practice: one file per level of detail (runs and the decision), linked by the "
               f"analysis id ({st.session_state.get('analysis_id', '')}); the decision record lists the data, "
               "preparation, testing split, and cost matrix behind the recommendation, so it can be reproduced.")
