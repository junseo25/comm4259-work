---
name: evaluate-classifier
description: Use when I ask to evaluate a classification model on a CSV file. It writes and runs a Python script that reports holdout accuracy, precision, recall, F1, the confusion matrix, the total cost from a cost matrix, and cross-validation accuracy.
---

# Evaluate a classifier on a CSV file

## Step 1: Ask before writing any code
Ask me for each item below that my prompt has not already given. Do not guess any of them. Repeat them back to me in a short list before you write code.

1. **The CSV file**, as a path from `comm4259-work` (for example `lab_08/WineQuality.csv`).
2. **The target column**, i.e. the class label.
3. **The positive class**, i.e. which value of the target counts as "positive" for precision, recall and F1.
4. **Columns to drop** before training (for example ID columns), or "none". The target is always dropped from the inputs.
5. **The model and its settings** (for example `DecisionTreeClassifier(max_depth=5, random_state=1)`).
6. **The cost matrix**: rows actual, columns predicted, and the class order (positive class first).
7. **The output folder**, where the script and its PNG go.

Use these defaults unless I say otherwise, and tell me you are using them:
- Holdout: stratified 70/30 split (`stratify=y`), `random_state=1`.
- Cross validation: `StratifiedKFold(n_splits=5, shuffle=True, random_state=1)`, scoring accuracy, on the whole data set.

If the target has more than two classes, or the cost matrix does not match the number of classes, stop and ask me.

## Step 2: Write the script
Write `evaluate.py` in the output folder. Create and edit files only in that folder. If the folder does not exist, create it.

- Put a short comment above each block of code that says what it does.
- Put all my answers from Step 1 in one settings block at the top of the script.
- Find files relative to the script (`Path(__file__)`), so it runs from `comm4259-work`.
- Make a fresh copy of the model for each method (a `make_model()` function), so that holdout and cross validation do not share a fitted model.
- Pass the positive class as `pos_label` to `precision_score`, `recall_score` and `f1_score`.
- Build the confusion matrix with `labels=[positive, negative]`, so rows and columns are in the same order as the cost matrix.
- Total cost = `(confusion_matrix * cost_matrix).sum()`, cell by cell, then add.
- Save the confusion matrix as `confusion_matrix.png` in the output folder. Use `matplotlib.use("Agg")` so it saves without opening a window.
- Use only packages that are already installed (numpy, pandas, matplotlib, scikit-learn). Do not install anything.

## Step 3: Print the results
Print:
1. The confusion matrix as a labelled table (`Actual ...` rows, `Predicted ...` columns), positive class first.
2. A short results table with these rows: holdout accuracy, precision, recall and F1 for the positive class, total cost (in dollars), and cross-validation mean accuracy +/- standard deviation.
3. Where the PNG was saved.

Show every rate as a percentage with two decimals (for example `85.80%`).

## Step 4: Run it and hand it back
- Run the script with the Python that has the lab packages. On this computer, the plain `python` command does **not** have matplotlib or scikit-learn. Use Anaconda's base Python: `C:\ProgramData\anaconda3\python.exe`, or run `conda activate base` first.
- If it fails, fix the script and run it again.
- Show me the printed results, and tell me how to run the script myself from `comm4259-work`, with both the `python ...` command and the Anaconda alternative.
- Remind me to check the numbers against my own results. Do not fill in any comparison table I am asked to complete without AI.

## Corrections from the first session (Lab 08)
- The skill is named `evaluate-classifier`. The script it writes is `evaluate.py`. These are two different things, so do not mix up the names.
- The plain `python` command failed with `ModuleNotFoundError: No module named 'matplotlib'`. The fix was to run the script with `C:\ProgramData\anaconda3\python.exe` (the notebook's "base" kernel). Use that Python from the start.
- Check results for the wine data, from the first session (`lab_08/WineQuality.csv`, target `quality`, positive class Good, `DecisionTreeClassifier(max_depth=5, random_state=1)`, cost `[[0, 2], [10, 0]]`): holdout accuracy 85.80%, precision 84.41%, recall 78.30%, F1 81.24%, total cost $598, 5-fold CV 84.74% +/- 0.81%. If you run the same settings and get different numbers, something is wrong.
