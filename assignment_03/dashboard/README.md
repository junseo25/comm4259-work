# Model Evaluation app (Assignment 3)

A small Streamlit app with one tab, **Model Evaluation**. It shows how the way a model is evaluated changes what you conclude about it. The model is a decision tree that predicts Titanic survival.

## Data
`data/titanic_train_clean.csv` holds 891 passengers. The target is `Survived`, and the positive class is 1 (survived). `PassengerId` is dropped because it is only an ID. The tree is `DecisionTreeClassifier(criterion="entropy", random_state=42)`.

## What the tab shows
1. **max_depth slider (1 to 15):** how deep the tree may grow.
2. **Accuracy from the chosen validation method:**
   - **Holdout:** one stratified split with `random_state=1`. A slider sets the test size, from 0.10 to 0.50 (default 0.30).
   - **K-fold cross validation:** `StratifiedKFold` with `shuffle=True` and `random_state=1`. A slider sets k from 3 to 10. The app shows the mean and standard deviation of the k accuracies.
   - **Bootstrap:** 10 to 200 rounds. Round `b` trains on `resample(..., random_state=b)` and tests on the out-of-bag passengers, the ones that were not drawn. The app shows the mean accuracy and the middle 95% (the 2.5th to 97.5th percentile).
3. **Confusion matrix** on the same holdout split. Rows are the actual class and columns the predicted class, with Survived = 1 first. Below it are precision, recall and F1 for Survived = 1.
4. **Total cost:** you type the cost of one false positive and of one false negative. The app shows the total cost of the holdout predictions: false positives x their cost + false negatives x their cost.

Every rate is shown as a percentage with two decimals. Each result has the scikit-learn line it comes from under it. The app only reports numbers. It makes no decisions and uses no AI model.

## How to run
From the `comm4259-work` folder:

```
streamlit run assignment_03/dashboard/app.py
```

If the bare `streamlit` command does not work, use `python -m streamlit run assignment_03/dashboard/app.py`. The Python you use must have the packages in `requirements.txt` (on my machine that is the Anaconda Python).

## Why holdout and cross validation accuracies can differ
Holdout tests the tree on **one** set of passengers. The result depends on who happens to land in that test set. If those passengers are unusually easy or hard to predict, the accuracy comes out too high or too low. Cross validation tests on k different folds, so every passenger is tested exactly once, and then averages the k accuracies. That average depends much less on one lucky or unlucky split. The standard deviation shows how much the accuracy moves from fold to fold. So a single holdout number can be several points away from the cross validation mean even when the tree is the same.
