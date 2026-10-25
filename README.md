# Emerging Disease Risk and Decision Tool (version 3)

Files in this folder (all seven must be uploaded):

| File | What it does |
|---|---|
| app.py | The web page (what users see). This is the "main file". |
| model.py | The maths: simulation, uncertainty, sensitivity, cost of waiting, real-world comparison. |
| diseases.py | The disease catalogue and the real-outbreak benchmarks. |
| evidence.py | Cited studies, the 1.13 hospital-overload source, and the glossary. |
| requirements.txt | Tells Streamlit which packages to install. |
| test_model.py | Optional checks of the maths (`python test_model.py`). |
| README.md | This file. |

## Relaunch as a separate version (keeps your old version untouched)

1. **Create a NEW GitHub repository** (do not reuse the old one). On github.com press the green "New" button,
   name it e.g. `outbreak-simulator-3`, set it Public, tick "Add a README" or leave it empty, and press Create.
2. Press **Add file > Upload files**. Drag in the seven files above. They must go in the **top level** of the repository,
   not inside a folder. Do not drag the folder itself, drag the files inside it. Press **Commit changes**.
3. Go to **share.streamlit.io**, press **Create app** (or "New app") and choose "Deploy a public app from GitHub".
4. Choose the new repository, branch `main`, and set **Main file path** to `app.py`.
5. Optional: choose a custom address in Advanced settings, e.g. `outbreak-simulator-3`. Press **Deploy**. The first
   build takes a few minutes.

Your old repository and old Streamlit app stay exactly as they are, so you can compare the two.
The main file path cannot be edited after an app is created, so always make a new app for a new layout.

## If something goes wrong
- "ModuleNotFoundError": a file is missing or sits in a subfolder. All files must be at the top level.
- App shows old content: you opened the old app's address. Each app has its own address.
- Slow first click on a button: simulations are running. Results are cached afterwards.

## Before presenting
Items marked ASSUMPTION in the catalogue notes (latent periods, route-of-transmission effectiveness, vaccine effectiveness)
need sources. The observed figures for Samoa 2019 measles and the Diamond Princess are from memory: check them against
the sources listed in the app before quoting them.
