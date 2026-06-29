"""
Redrob Ranker — Sandbox demo (Streamlit).

Satisfies the hackathon "working hosted sandbox" requirement (Section 10.5):
accepts a small candidate sample (<=100), runs the EXACT ranker from rank.py
end-to-end on CPU, and returns a ranked CSV — well within the compute budget.

Deploy on HuggingFace Spaces (SDK: Streamlit) or Streamlit Cloud:
  - put this folder's contents + a copy of ../rank.py at the repo root
  - requirements.txt is in this folder
Run locally:
  streamlit run sandbox/app.py
"""

import io
import json
import os
import sys

import streamlit as st

# Make the sibling rank.py importable whether app.py is run from repo root,
# from sandbox/, or from a flat Spaces checkout.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import rank  # noqa: E402

st.set_page_config(page_title="Redrob Ranker", page_icon="🎯", layout="wide")
st.title("🎯 Redrob Candidate Ranker — Sandbox")
st.caption(
    "Ranks Senior-AI-Engineer candidates. Career-history *evidence* is weighted "
    "above the raw skills list; structurally-impossible profiles are disqualified. "
    "Pure stdlib, CPU-only, no network."
)

st.markdown(
    "Upload a **JSONL** (one candidate per line) or **JSON array** file "
    "(≤100 candidates), or use the bundled sample."
)

uploaded = st.file_uploader("Candidate file (.jsonl / .json)", type=["jsonl", "json"])
top_n = st.slider("Top N to return", 5, 100, 25)


def _load(raw_bytes: bytes):
    text = raw_bytes.decode("utf-8")
    text_stripped = text.lstrip()
    cands = []
    if text_stripped.startswith("["):  # JSON array
        cands = json.loads(text)
    else:  # JSONL
        for line in text.splitlines():
            line = line.strip()
            if line:
                cands.append(json.loads(line))
    return cands


sample_path = os.path.join(os.path.dirname(__file__), "sample_candidates.json")
use_sample = st.button("▶ Run on bundled sample") if os.path.exists(sample_path) else False

candidates = None
if uploaded is not None:
    candidates = _load(uploaded.read())
elif use_sample:
    with open(sample_path, encoding="utf-8") as f:
        candidates = json.load(f)

if candidates:
    candidates = candidates[:100]
    scored = []
    for c in candidates:
        bd = rank.score_breakdown(c)
        score = rank.calculate_final_score(c, bd)
        reasoning = rank.generate_reasoning(c, bd, score)
        scored.append((c.get("candidate_id", ""), round(score, 4), reasoning))
    scored.sort(key=lambda x: (-x[1], x[0]))
    top = scored[:top_n]

    st.success(f"Ranked {len(candidates)} candidates — showing top {len(top)}.")
    st.dataframe(
        [{"rank": i, "candidate_id": cid, "score": sc, "reasoning": r}
         for i, (cid, sc, r) in enumerate(top, 1)],
        use_container_width=True, hide_index=True,
    )

    buf = io.StringIO()
    buf.write("candidate_id,rank,score,reasoning\n")
    for i, (cid, sc, r) in enumerate(top, 1):
        rr = '"' + r.replace('"', '""') + '"'
        buf.write(f"{cid},{i},{sc:.4f},{rr}\n")
    st.download_button("⬇ Download ranked CSV", buf.getvalue(),
                       file_name="submission.csv", mime="text/csv")
else:
    st.info("Waiting for input…")
