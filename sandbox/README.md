# Redrob Ranker — Sandbox (HuggingFace Spaces / Streamlit Cloud)

A minimal hosted demo that runs the **exact** ranker (`rank.py`) on a small
candidate sample (≤100), as required by submission spec §10.5.

## Deploy on HuggingFace Spaces (recommended, free tier)

1. Create a new Space → **SDK: Streamlit**.
2. Add these files at the Space repo root:
   - `app.py`            (from this folder)
   - `rank.py`           (copy of the repo-root ranker)
   - `requirements.txt`  (from this folder)
   - `sample_candidates.json` (optional, enables the "Run on bundled sample" button)
3. The Space builds and serves automatically. Upload a `.jsonl`/`.json` sample or
   click **Run on bundled sample**; download the ranked CSV.

## Deploy on Streamlit Cloud

Point it at this repo with main file path `sandbox/app.py` (the app adds the repo
root to `sys.path`, so it imports the top-level `rank.py` directly).

## Run locally

```bash
pip install -r sandbox/requirements.txt
streamlit run sandbox/app.py
```

The ranker itself has **no dependencies** — Streamlit is only for this demo UI.
