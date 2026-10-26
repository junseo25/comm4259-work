"""Evaluate a decision tree on the wine quality data, with new costs (Lab 08).

Run from comm4259-work:  python lab_08/skill_demo/new_costs/evaluate.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # save the plot to a file without opening a window
import matplotlib.pyplot as plt

from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             confusion_matrix, ConfusionMatrixDisplay)

# Settings: file locations, target, positive class, dropped columns and cost matrix
OUT_DIR = Path(__file__).resolve().parent                 # lab_08/skill_demo/new_costs/
DATA_FILE = OUT_DIR.parent.parent / "WineQuality.csv"     # lab_08/WineQuality.csv
TARGET = "quality"
POSITIVE = "Good"
DROP_COLUMNS = []                                         # none besides the target
LABELS = ["Good", "Poor"]                                 # positive class first
COST = np.array([[0, 10],                                 # rows actual, columns predicted
                 [2, 0]])


# The model being evaluated (a fresh copy each time it is called)
def make_model():
    return DecisionTreeClassifier(max_depth=5, random_state=1)


# Read the data and separate the input features from the class label
data = pd.read_csv(DATA_FILE)
X = data.drop(columns=[TARGET] + DROP_COLUMNS)
y = data[TARGET]

# Holdout: stratified 70/30 split, train on 70%, predict the 30%
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=1)
y_pred = make_model().fit(X_train, y_train).predict(X_test)

# Holdout metrics, with Good as the positive class
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, pos_label=POSITIVE)
recall = recall_score(y_test, y_pred, pos_label=POSITIVE)
f1 = f1_score(y_test, y_pred, pos_label=POSITIVE)

# Confusion matrix in the order Good, Poor; save it as a PNG
cm = confusion_matrix(y_test, y_pred, labels=LABELS)
ConfusionMatrixDisplay(cm, display_labels=LABELS).plot()
plt.title("Confusion matrix (holdout test set)")
png_path = OUT_DIR / "confusion_matrix.png"
plt.savefig(png_path, dpi=150, bbox_inches="tight")
plt.close()

# Total cost: multiply each confusion-matrix cell by its cost, then add
total_cost = (cm * COST).sum()

# Cross validation: 5 stratified folds, accuracy in each fold
folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=1)
cv_scores = cross_val_score(make_model(), X, y, cv=folds, scoring="accuracy")

# Print the confusion matrix
print("Confusion matrix (rows actual, columns predicted):")
print(pd.DataFrame(cm, index=[f"Actual {l}" for l in LABELS],
                   columns=[f"Predicted {l}" for l in LABELS]).to_string())
print()

# Print the results table
rows = [
    ("Holdout accuracy", f"{accuracy:.2%}"),
    ("Precision (Good)", f"{precision:.2%}"),
    ("Recall (Good)", f"{recall:.2%}"),
    ("F1 (Good)", f"{f1:.2%}"),
    ("Total cost", f"${total_cost}"),
    ("5-fold CV accuracy", f"{cv_scores.mean():.2%} +/- {cv_scores.std():.2%}"),
]
print(f"{'Metric':<20}{'Result':>20}")
print("-" * 40)
for name, value in rows:
    print(f"{name:<20}{value:>20}")
print()
print(f"Confusion matrix saved to {png_path}")
