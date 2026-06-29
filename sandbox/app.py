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

import csv
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
    """Load candidates from JSONL or JSON array format."""
    try:
        text = raw_bytes.decode("utf-8")
        text_stripped = text.lstrip()
        if not text_stripped:
            raise ValueError("Empty file")
        cands = []
        if text_stripped.startswith("["):  # JSON array
            cands = json.loads(text)
        else:  # JSONL
            for line in text.splitlines():
                line = line.strip()
                if line:
                    cands.append(json.loads(line))
        if not cands:
            raise ValueError("No candidates found")
        return cands
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    except UnicodeDecodeError:
        raise ValueError("File must be UTF-8 encoded")


sample_path = os.path.join(os.path.dirname(__file__), "sample_candidates.json")
use_sample = st.button("▶ Run on bundled sample") if os.path.exists(sample_path) else False

# Session state for caching scored results
if "scored_results" not in st.session_state:
    st.session_state.scored_results = None
if "input_hash" not in st.session_state:
    st.session_state.input_hash = None

candidates = None
input_source = None

try:
    if uploaded is not None:
        input_source = ("upload", uploaded.name, uploaded.getvalue())
        candidates = _load(uploaded.read())
    elif use_sample:
        input_source = ("sample", sample_path, None)
        with open(sample_path, encoding="utf-8") as f:
            candidates = json.load(f)
except ValueError as e:
    st.error(f"❌ Error loading candidates: {e}")
    candidates = None

if candidates:
    # Truncate and validate
    original_count = len(candidates)
    candidates = candidates[:100]
    if original_count > 100:
        st.warning(f"⚠️ File contained {original_count} candidates — truncated to 100 (sandbox limit).")

    # Check if we need to re-score (new input or cache miss)
    current_hash = str(input_source)
    if st.session_state.input_hash != current_hash:
        with st.spinner(f"Scoring {len(candidates)} candidates..."):
            scored = []
            try:
                for c in candidates:
                    if not isinstance(c, dict):
                        raise ValueError(f"Invalid candidate format (expected dict, got {type(c).__name__})")
                    bd = rank.score_breakdown(c)
                    score = rank.calculate_final_score(c, bd)
                    reasoning = rank.generate_reasoning(c, bd, score)
                    cid = c.get("candidate_id", "")
                    if not cid:
                        raise ValueError("Candidate missing 'candidate_id' field")
                    scored.append((cid, round(score, 4), reasoning))
                scored.sort(key=lambda x: (-x[1], x[0]))
                st.session_state.scored_results = scored
                st.session_state.input_hash = current_hash
            except Exception as e:
                st.error(f"❌ Scoring error: {e}")
                st.session_state.scored_results = None

    # Display results from cache
    if st.session_state.scored_results:
        scored = st.session_state.scored_results
        top = scored[:top_n]

        st.success(f"✅ Ranked {len(scored)} candidates — showing top {len(top)}.")
        st.dataframe(
            [{"rank": i, "candidate_id": cid, "score": sc, "reasoning": r}
             for i, (cid, sc, r) in enumerate(top, 1)],
            use_container_width=True, hide_index=True,
        )

        # Generate CSV with proper escaping
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for i, (cid, sc, r) in enumerate(top, 1):
            writer.writerow([cid, i, f"{sc:.4f}", r])

        st.download_button(
            "⬇ Download ranked CSV",
            buf.getvalue(),
            file_name="submission.csv",
            mime="text/csv"
        )
else:
    st.info("Waiting for input…")
