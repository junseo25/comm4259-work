# Assignment 3 Section 3
**Assistant used:** Claude Code
**Time Spent:** ~3 hours
**Prompt used:**
Work only in assignment_03/dashboard/: create and edit files only there.
My Streamlit version is 1.66.0. Only use features available in that version, and do not install or upgrade any packages.
Plan a Streamlit app: app.py (read the data with Path(__file__).parent / "data") with one tab, Model Evaluation,
plus requirements.txt (include pyarrow<17), README.md, an empty ai_sessions/ folder and an empty AI_USE_LOG.md (I write the log myself).
Use data/titanic_train_clean.csv. The target is Survived and the positive class is 1. Drop PassengerId.
The tab must let a user:
1. set max_depth with a slider (1 to 15) for DecisionTreeClassifier(criterion="entropy", random_state=42);
2. choose a validation method and see the accuracy: holdout (test-size slider from 0.10 to 0.50, default 0.30,
   passed to train_test_split as a fraction, stratified, random_state=1),
   k-fold cross validation (k slider 3 to 10, StratifiedKFold with shuffle=True and random_state=1, mean and
   standard deviation), or bootstrap (rounds slider 10 to 200, round b uses resample(..., random_state=b),
   out-of-bag accuracy, mean and the middle 95%);
3. see the confusion matrix on the same holdout split as item 2 (rows actual, columns predicted, Survived = 1 first),
   with precision, recall and F1 for the positive class;
4. enter the cost of a false positive and of a false negative, and see the total cost of the holdout predictions.
Show every rate as a percentage with two decimals, and show the scikit-learn line each result comes from.
The app makes no decisions on its own and uses no AI model. Keep the code simple enough for a beginner to read.
Ask me if anything in this plan is unclear.

**What changed:**
I asked Claude Code to add an in-site dark/light mode to have easier access to this. Especially as a person who dislikes reading code or large blocks of writing in dark mode, I felt it was important to have this as an option outside of the system mode that is already in streamlit.

Alongside this, I asked the AI to provide calculations on how it got to the result as well instead of just providing the code, I wanted people to better understand how the result was generated so that they could get a better understanding of the method used, the calculations necessary to be able to do these calculations without the use of AI or coding.