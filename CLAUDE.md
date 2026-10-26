# COMM 4259: rules for Claude Code

## About me
I am a student in COMM 4259 (Foundations of Machine Learning and AI with Python). Explain things in plain language.
These rules apply to the whole course: Labs 08-12, Assignments 2-5, and the final project.

## Environment
- My Streamlit version is 1.66.0. Only use features available in that version.
- The bare `streamlit` command does not work on my machine. Use `python -m streamlit ...` instead (for example, `python -m streamlit run app.py`).
- Do not install or upgrade any packages. If something seems to need a new package, ask me first.

## How to explain
- Walk me through any new code line by line, in simple language, with suggestions and the reasons behind them.
- Define ML terms in the Claude Code chat, never inside code cells or markdown cells.
- Put a short comment above each block of code that says what it does. Keep the comments at that level, no more and no less.

## Folders
- Only create or edit files in the folder for the current task. Ask me before changing anything else.
- Folder names: lab_01 to lab_04, lab_05_06, lab_07, lab_08, assignment_01, assignment_02, and agent_demo. New tasks follow the same pattern (lab_09, assignment_03, and so on). Subfolders such as assignment_02/dashboard/ or lab_07/agent_demo/ belong to their task.
- The final project has its own folder, project/. You may work anywhere inside it.

## When you are unsure
- If my instructions are unclear, always stop and ask me. Do not guess.
- If something fails, show me the error with suggestions on how to fix it, and wait for my decision.
- If there are several reasonable approaches, show me the options and let me choose.

## Never do
- Never commit or push to git unless I ask.
- Never delete files unless I explicitly ask.
- Only use outside data or APIs when I explicitly tell you to.
- Ask me first, case by case, before editing raw data files or clearing or re-running notebook outputs.
- Follow my data-preparation decisions exactly. If one looks wrong, ask me; do not change it yourself.

## When you finish a task
- Give me a short summary, in simple terms, of what you created or changed and why.
- Check that the code actually runs before saying it is done.
- List anything you skipped, were unsure about, or think I should double-check. For each one, ask me how I want it handled.
- Suggest next steps. When relevant, give several options with the pros and cons of each.
- Tell me how to run what you built.

## Academic integrity
- Never write or suggest answers for a notebook section marked "no generative AI" (for example, Assignment 2 Sections 1 and 2A). If I ask, remind me of this rule.
- Remind me to note my AI use when an assignment requires it.

## My own rules
-  Do not add tabs, charts or files I did not ask for. Suggest them to me instead.
-  When I run into a problem or error in my code, give me options, context, and suggestions for how to approach and fix it instead of fixing it for me, unless I say that section should be done entirely with AI.