# GhostPermissions (starter, part 1)

Checks an Android manifest against what an app is supposed to do, and explains the risk.
This part has NO AI yet. It is the foundation the agents will sit on.

## Run it
    python -m venv .venv
    .venv\Scripts\activate          (Windows)   or   source .venv/bin/activate   (Mac/Linux)
    python -m pip install -r requirements.txt
    streamlit run app.py

## Test it
    python -m pytest -q

## What is where
- app.py                 the web page
- core/manifest_parser.py  reads permissions out of a manifest (safe XML reader)
- core/risk_rules.py       compares permissions with the app type and finds risky mixes
- data/permissions.json    what each permission means, its level and our own weight
- data/app_profiles.json   which permissions are expected for each type of app
- data/sample_manifests/   two fictional apps for the demo
- tests/                   automatic checks

The scores and thresholds are our own team's design, not an Android standard.
A manifest shows what an app MAY ask for, not what it actually does.
