from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils import resample

# Page setup
st.set_page_config(page_title="Model Evaluation", layout="wide")
st.title("Titanic Decision Tree: Model Evaluation")
st.caption("This app only reports numbers. It makes no decisions on its own and uses no AI model.")

# Colors for the Light and Dark modes (System uses Streamlit's own setting)
THEMES = {
    "Light": {"background": "#FFFFFF", "panel": "#F0F2F6", "text": "#31333F", "border": "#D5D8DE"},
    "Dark": {"background": "#0E1117", "panel": "#262730", "text": "#FAFAFA", "border": "#3D4048"},
}

# Theme choice: Light and Dark add CSS that recolors the page; System adds nothing
theme = st.radio("Display mode", ["System", "Light", "Dark"], horizontal=True,
                 help="System follows the ⋮ menu > Settings choice, which follows your computer by default.")
if theme in THEMES:
    c = THEMES[theme]
    st.markdown(f"""
    <style>
    .stApp, [data-testid="stHeader"] {{ background-color: {c["background"]}; }}
    .stApp, .stApp p, .stApp li, .stApp label, .stApp span, .stApp h1, .stApp h2, .stApp h3,
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], [data-baseweb="tab"] {{ color: {c["text"]}; }}
    [data-testid="stCode"] pre, [data-testid="stCode"] code {{ background-color: {c["panel"]}; }}
    [data-testid="stTable"] th, [data-testid="stTable"] td {{
        background-color: {c["background"]}; color: {c["text"]}; border-color: {c["border"]}; }}
    [data-baseweb="input"], [data-baseweb="input"] input, [data-testid="stNumberInputContainer"] button {{
        background-color: {c["panel"]}; color: {c["text"]}; }}
    [data-testid="stVerticalBlockBorderWrapper"] {{ border-color: {c["border"]}; }}
    </style>
    """, unsafe_allow_html=True)

# Read the data once and keep it in memory
DATA = Path(__file__).parent / "data" / "titanic_train_clean.csv"


@st.cache_data
def load_data():
    return pd.read_csv(DATA)


titanic = load_data()
X = titanic.drop(["PassengerId", "Survived"], axis=1)
y = titanic["Survived"]


# The same decision tree every time, so only the evaluation method changes
def make_tree(depth):
    return DecisionTreeClassifier(max_depth=depth, criterion="entropy", random_state=42)


# Bootstrap: train on a sample drawn with replacement, test on the rows not drawn
@st.cache_data
def bootstrap_scores(depth, rounds):
    rows = np.arange(len(X))
    scores = []
    oob_sizes = []
    for b in range(rounds):
        train_rows = resample(rows, replace=True, n_samples=len(X), random_state=b)
        test_rows = np.setdiff1d(rows, train_rows)
        tree = make_tree(depth).fit(X.iloc[train_rows], y.iloc[train_rows])
        scores.append(accuracy_score(y.iloc[test_rows], tree.predict(X.iloc[test_rows])))
        oob_sizes.append(len(test_rows))
    return np.array(scores), np.array(oob_sizes)


(tab,) = st.tabs(["Model Evaluation"])

with tab:
    # Settings: every control for the tab in one box
    with st.container(border=True):
        st.subheader("Settings")
        st.write(f"Data: {len(X)} passengers, {X.shape[1]} input columns, target = Survived (1 = survived).")
        depth = st.slider("max_depth (how many questions deep the tree may go)", min_value=1, max_value=15, value=3)
        method = st.radio("Validation method for Section 1",
                          ["Holdout", "K-fold cross validation", "Bootstrap"], horizontal=True)
        test_size = st.slider("Holdout test size (fraction of passengers)", min_value=0.10, max_value=0.50,
                              value=0.30, step=0.05)
        if method == "K-fold cross validation":
            k = st.slider("Number of folds (k)", min_value=3, max_value=10, value=5)
        if method == "Bootstrap":
            rounds = st.slider("Bootstrap rounds", min_value=10, max_value=200, value=100)

    # Holdout split, shared by the holdout accuracy and Sections 2 to 4
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, stratify=y, random_state=1)
    tree = make_tree(depth).fit(X_train, y_train)
    y_pred = tree.predict(X_test)
    cm = confusion_matrix(y_test, y_pred, labels=[1, 0])
    tp, fn = cm[0, 0], cm[0, 1]  # actual 1: predicted 1, predicted 0
    fp, tn = cm[1, 0], cm[1, 1]  # actual 0: predicted 1, predicted 0

    # Summary of the holdout split
    st.info(f"Holdout split ({test_size:.2%} test): {len(X_train)} passengers train the tree and "
            f"{len(X_test)} test it. Survivors: {y_train.mean():.2%} of the training part and "
            f"{y_test.mean():.2%} of the test part (stratify=y keeps these shares equal). "
            "Sections 2 to 4 always use this holdout split, whichever method you pick for Section 1.")

    # Section 1: accuracy from the chosen validation method
    st.header(f"1. Accuracy: {method}")

    # Section 1, holdout: one train/test split
    if method == "Holdout":
        st.write("**What it measures:** the share of the test passengers the tree predicts correctly. "
                 "The tree never saw these passengers while it was learning.")
        accuracy = accuracy_score(y_test, y_pred)
        st.metric("Holdout accuracy", f"{accuracy:.2%}")
        st.write("**How it was calculated**")
        st.markdown(f"- Correct predictions = TP + TN = {tp} + {tn} = {tp + tn}\n"
                    f"- Accuracy = correct / test passengers = {tp + tn} / {len(y_test)} = **{accuracy:.2%}**")
        st.write("**scikit-learn**")
        st.code(f"X_train, X_test, y_train, y_test = train_test_split(X, y, test_size={test_size:.2f}, "
                "stratify=y, random_state=1)\n"
                "accuracy_score(y_test, tree.predict(X_test))")

    # Section 1, cross validation: k folds, each tested once
    elif method == "K-fold cross validation":
        st.write(f"**What it measures:** the passengers are cut into {k} folds. Each fold takes one turn as the "
                 f"test set while the other {k - 1} train the tree, so every passenger is tested exactly once.")
        folds = StratifiedKFold(n_splits=k, shuffle=True, random_state=1)
        scores = cross_val_score(make_tree(depth), X, y, cv=folds)
        left, right = st.columns(2)
        left.metric("Mean accuracy", f"{scores.mean():.2%}")
        right.metric("Standard deviation", f"{scores.std():.2%}")
        st.write("**How it was calculated**")
        fold_sizes = [len(test_rows) for _, test_rows in folds.split(X, y)]
        fold_table = pd.DataFrame({
            "Fold": range(1, k + 1),
            "Test passengers": fold_sizes,
            "Accuracy": [f"{s:.2%}" for s in scores],
        })
        st.table(fold_table.set_index("Fold"))
        st.markdown(f"- Mean = sum of the {k} fold accuracies / {k} = **{scores.mean():.2%}**\n"
                    f"- Standard deviation = how far the fold accuracies typically sit from the mean "
                    f"= **{scores.std():.2%}** (smaller means the folds agree more)")
        st.write("**scikit-learn**")
        st.code(f"folds = StratifiedKFold(n_splits={k}, shuffle=True, random_state=1)\n"
                "scores = cross_val_score(tree, X, y, cv=folds)\n"
                "scores.mean(), scores.std()")

    # Section 1, bootstrap: many rounds, each tested on the out-of-bag passengers
    else:
        st.write(f"**What it measures:** in each of {rounds} rounds, the tree trains on {len(X)} passengers drawn "
                 "with replacement (some appear twice or more). It is then tested on the passengers that were "
                 "never drawn in that round, the out-of-bag passengers.")
        scores, oob_sizes = bootstrap_scores(depth, rounds)
        low, high = np.percentile(scores, 2.5), np.percentile(scores, 97.5)
        left, middle, right = st.columns(3)
        left.metric("Mean out-of-bag accuracy", f"{scores.mean():.2%}")
        middle.metric("Middle 95%: low (2.5th percentile)", f"{low:.2%}")
        right.metric("Middle 95%: high (97.5th percentile)", f"{high:.2%}")
        st.write("**How it was calculated**")
        st.markdown(f"- Rounds: b = 0 to {rounds - 1}, and round b draws its sample with random_state=b\n"
                    f"- Out-of-bag passengers per round: {oob_sizes.mean():.1f} on average "
                    f"({oob_sizes.mean() / len(X):.2%} of the passengers)\n"
                    f"- Mean = sum of the {rounds} round accuracies / {rounds} = **{scores.mean():.2%}**\n"
                    f"- Middle 95%: sort the {rounds} accuracies. 2.5% of them fall below **{low:.2%}** and "
                    f"2.5% fall above **{high:.2%}**.")
        st.write("**scikit-learn**")
        st.code("train_rows = resample(rows, replace=True, n_samples=len(X), random_state=b)  # b = 0, 1, 2, ...\n"
                "test_rows = np.setdiff1d(rows, train_rows)\n"
                "accuracy_score(y.iloc[test_rows], tree.predict(X.iloc[test_rows]))\n"
                "scores.mean(), np.percentile(scores, 2.5), np.percentile(scores, 97.5)")

    # Section 2: confusion matrix on the holdout split (Survived = 1 first)
    st.header("2. Confusion matrix (holdout split)")
    st.write("**What it shows:** how many test passengers fall into each combination of actual and predicted "
             "class. Rows are the actual class and columns the predicted class.")
    cm_table = pd.DataFrame(cm,
                            index=["Actual 1 (survived)", "Actual 0 (did not survive)"],
                            columns=["Predicted 1 (survived)", "Predicted 0 (did not survive)"])
    st.table(cm_table)
    st.write("**How to read it**")
    st.markdown(f"- TP (true positive), actual 1 and predicted 1: **{tp}** survivors correctly predicted\n"
                f"- FN (false negative), actual 1 and predicted 0: **{fn}** survivors the tree missed\n"
                f"- FP (false positive), actual 0 and predicted 1: **{fp}** non-survivors wrongly predicted to survive\n"
                f"- TN (true negative), actual 0 and predicted 0: **{tn}** non-survivors correctly predicted\n"
                f"- Check: {tp} + {fn} + {fp} + {tn} = {cm.sum()} test passengers")
    st.write("**scikit-learn**")
    st.code("confusion_matrix(y_test, y_pred, labels=[1, 0])")

    # Section 3: precision, recall and F1 for the positive class (Survived = 1)
    st.header("3. Precision, recall and F1 (positive class: Survived = 1)")
    st.write("**What they measure:** precision is the share of predicted survivors who really survived. "
             "Recall is the share of real survivors the tree found. F1 balances the two in one number.")
    precision = precision_score(y_test, y_pred, pos_label=1)
    recall = recall_score(y_test, y_pred, pos_label=1)
    f1 = f1_score(y_test, y_pred, pos_label=1)
    left, middle, right = st.columns(3)
    left.metric("Precision", f"{precision:.2%}")
    middle.metric("Recall", f"{recall:.2%}")
    right.metric("F1", f"{f1:.2%}")
    st.write("**How it was calculated**")
    st.markdown(f"- Precision = TP / (TP + FP) = {tp} / ({tp} + {fp}) = **{precision:.2%}**\n"
                f"- Recall = TP / (TP + FN) = {tp} / ({tp} + {fn}) = **{recall:.2%}**\n"
                f"- F1 = 2 x precision x recall / (precision + recall) "
                f"= 2 x {precision:.2%} x {recall:.2%} / ({precision:.2%} + {recall:.2%}) = **{f1:.2%}**")
    st.write("**scikit-learn**")
    st.code("precision_score(y_test, y_pred, pos_label=1)\n"
            "recall_score(y_test, y_pred, pos_label=1)\n"
            "f1_score(y_test, y_pred, pos_label=1)")

    # Section 4: total cost of the holdout predictions
    st.header("4. Total cost (holdout split)")
    st.write("**What it measures:** the cost of the tree's mistakes on the test passengers, using the cost you "
             "enter for each kind of mistake. Correct predictions (TP and TN) cost 0.")
    left, right = st.columns(2)
    fp_cost = left.number_input("Cost of one false positive", min_value=0.0, value=1.0)
    fn_cost = right.number_input("Cost of one false negative", min_value=0.0, value=1.0)
    total_cost = fp * fp_cost + fn * fn_cost
    st.metric("Total cost", f"{total_cost:,.2f}")
    st.write("**How it was calculated**")
    st.markdown(f"- Total cost = FP x FP cost + FN x FN cost\n"
                f"- = {fp} x {fp_cost:,.2f} + {fn} x {fn_cost:,.2f}\n"
                f"- = {fp * fp_cost:,.2f} + {fn * fn_cost:,.2f} = **{total_cost:,.2f}**")
    st.write("**scikit-learn** (the counts come from the confusion matrix)")
    st.code("cm = confusion_matrix(y_test, y_pred, labels=[1, 0])\n"
            "fp, fn = cm[1, 0], cm[0, 1]\n"
            "total_cost = fp * fp_cost + fn * fn_cost")
