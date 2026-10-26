# Assignment 2 Section 2C
**Assistant used:** Claude Code
**Time Spent:** ~5 hours
**Item 1:** 
### Number 1: The shape of the dataset
The workbench showed: Raw: (891, 14), Prepared (891, 23)
The calculation showed: Raw: (891, 14), Prepared (891, 23)
The results matched 

### Number 2: The missing values left
The workbench showed: 0
The calculation showed: 0
The results matched 

**Item 2:** 1. Used the wrong default data file. When the app was built, it said that titanic_features.csv did not exist and copied titanic_train.csv under that name instead based on my agreeing with its suggestion that this was the best move. Instead, it should have looked to use the real file from the notebook to load the 14 columns instead of the 12 from copying the file. I ensured the file was correctly saved from the notebook and copied it manually into dashboard/data/ so it loads correctly.

2. The README recipe did not follow the Name/Ticket decision. My decision was to ignore Name and ticket instead of dropping them as they can serve as useful examples later on. AI looked to drop both columns anyway. I went back and removed that step so that Name and Ticket stayed in the prepared dataset.

3. After ticking the "dummy_na" for one column, it remains ticked for the next dummy-code steps creating Sex_nan, Embarked_nan, and Pclass_nan which all show as 0s and turning Pclass dummies into Pclass_2.0 and Pclass_3.0. I decided to keep this file and report the bug to possibly ask a TA about it in the future on what could be done to resolve this issue.

Submitted late, apologies, I completely lost track of time and was working on other assignments and forgot this assignment.