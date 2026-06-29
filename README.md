# Redrob Ranker — Senior AI Engineer Candidate Ranking

Ranks the top 100 candidates from a 100,000-candidate pool for the Redrob
"Senior AI Engineer — Founding Team" role. Pure Python standard library, CPU-only,
no network — produces a validated submission CSV in **~25 seconds** for 100K candidates.

## Quickstart (1 minute)

```bash
# Python 3.11+ ; no dependencies to install (stdlib only)
python rank.py --candidates data/candidates.jsonl --out submission.csv

# validate the output against the official format rules
python data/validate_submission.py submission.csv
```

Accepts gzipped input too: `--candidates data/candidates.jsonl.gz`.

## What it does

The job description warns that the dataset is full of traps: the "right answer" is
**not** the candidates with the most AI keywords. A "Marketing Manager" with every
buzzword is not a fit; a plain-language engineer who *actually built a recommendation
system at a product company* is. So the ranker reads **career-history evidence**
(what the candidate built) above the raw skills list.

### Architecture (4 pillars + honeypot gate)

```
                 ┌─────────────────────────────────────────────┐
 candidate JSON ─┤  honeypot gate  → if structurally impossible │→ score = -1.0
                 └─────────────────────────────────────────────┘
                                     │ (survives)
        ┌────────────────────────────┼─────────────────────────────┐
        ▼                ▼            ▼               ▼              ▼
  P1 Skills+Evidence  P2 Production  P3 Years+    Location      P4 Behavioral
     (0.30)             Exp (0.45)    Senior(0.15)  modifier       multiplier
        │                │            │            (±)            ×[0.80,1.10]
        └──── composite = 0.30·P1 + 0.45·P2 + 0.15·P3 + loc ──────┘
                                     │
                          final = composite × P4
```

- **P1 Skills + Evidence (0.30):** tiered skill vocab (Tier-1 embeddings/vector-DB/
  ranking, Tier-2 fine-tuning/MLops, Tier-3 general) with alias + `difflib` fuzzy
  matching and an endorsement×duration *trust* weight. **Half the pillar comes from
  career-description evidence** (retrieval, ranking, recommendation, A/B testing…).
  A keyword list with no career evidence is capped — this defuses the stuffer trap.
- **P2 Production Experience (0.45, heaviest):** role-type, product-vs-services
  company tier, production/operational keywords, domain relevance ("built ranking/
  search/recsys"), tenure depth. Penalizes pure-research and services-only careers.
- **P3 Years + Seniority (0.15):** 5–9 band gets full credit; seniority &
  promotion bonuses; title-chaser (job-hopping) penalty.
- **P4 Behavioral (×[0.80, 1.10]):** availability multiplier from response rate,
  interview completion, recency, notice period, verification — schema-correct
  handling of `-1` sentinels (no offer history / no GitHub = neutral, not a penalty).
- **Location modifier:** small nudge for India Tier-1 cities / willingness to relocate
  (role is Pune/Noida; no visa sponsorship).

### Honeypot handling

The ground truth contains ~80 structurally-impossible profiles (forced to relevance
tier 0); >10% in the top 100 disqualifies the submission. We disqualify (−1.0) only on
**internally-consistent impossibility** — a single role longer than the whole career,
total tenure exceeding claimed experience, or "expert in N skills with 0 endorsements
& 0 months used" — plus the wrong-title keyword-stuffer trap. We deliberately do **not**
gate on education year (the data has many legitimate career-changers whose degree
post-dates their work). **Result: 0 honeypots in the top 100.**

## Results on the released pool (100K)

| Metric | Value |
|---|---|
| Runtime (100K, single CPU) | ~25 s |
| Honeypots in top 100 | **0 / 100** |
| Non-technical / services-only titles in top 100 | 0 |
| YoE range (top 100) | 4.2 – 9.0 (median 6.4) |
| Score range | 0.998 → 0.877 (smooth, no cliffs) |
| Disqualified in full pool | 130 (~80 honeypots + wrong-title traps) |

Top ranks are Recommendation Systems / Applied ML / Senior AI / NLP / Search Engineers
with production ranking-and-retrieval evidence — exactly the JD's ideal profile.

## Files

| File | Purpose |
|---|---|
| `rank.py` | The ranker (entry point). |
| `test_scoring.py` | Calibration + unit tests (`python test_scoring.py`). |
| `IMPROVED_DESIGN.md` | Full design rationale and formulas. |
| `requirements.txt` | Dependencies (none — stdlib only). |
| `submission_metadata.yaml` | Portal metadata (fill in team fields). |
| `sandbox/` | Streamlit demo app for the required hosted sandbox. |

## Reproduce

```bash
python rank.py --candidates data/candidates.jsonl --out submission.csv
python test_scoring.py                              # -> "14 passed, 0 failed"
```

## Troubleshooting

- **`UnicodeEncodeError` on Windows console:** set `PYTHONIOENCODING=utf-8` (the CSV
  itself is always written UTF-8; this only affects stderr logging).
- **Input is a JSON array, not JSONL:** the full pool is JSONL (one object per line).
  `sample_candidates.json` is a pretty-printed array — convert with
  `python -c "import json;[print(json.dumps(c)) for c in json.load(open('data/sample_candidates.json'))]" > sample.jsonl`.
- **Validator complains about tie-breaks:** scores are rounded to 4 decimals *before*
  sorting so ties break deterministically by `candidate_id` — re-run `rank.py` if you
  changed the rounding.

## Methodology summary

Rule-based, fully explainable ranker. The decisive design choice is weighting
**career-history evidence over the skills keyword list**, because the JD explicitly
builds keyword traps into the dataset. Production experience is the heaviest pillar
(0.45); behavioral signals act as an availability multiplier, never overriding skills.
Honeypots are caught with internally-consistent career-duration math (not unreliable
education-year gates), yielding 0 honeypots in the top 100. Runs in ~25s on CPU with
zero dependencies for trivial reproducibility.
