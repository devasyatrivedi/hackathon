# IMPROVED DESIGN — Redrob Ranker

This document completes the improvement plan in `data/improvement.md`. It is the
implementation spec for `rank.py`. Every decision is grounded in the **actual**
`candidate_schema.json`, the real `job_description` / `submission_spec` docs, and
the hidden scoring metrics — not the assumptions baked into the original skeleton.

---

## 0. What changed vs. the original skeleton (and why it matters)

Reading the JD + spec + schema together flips several skeleton assumptions:

1. **The decisive signal is career-history *evidence*, not the skills list.**
   The JD says explicitly: a candidate with every AI keyword but a "Marketing
   Manager" title is *not* a fit, while a "Tier-5" candidate who never writes
   "RAG"/"Pinecone" but *built a recommendation system at a product company* IS a
   fit. → We extract **what they built** from `career_history[].description`, and
   weight that above the `skills[]` keyword list. Skills become corroboration, not
   the primary signal.

2. **Scoring is top-heavy.** Hidden metric =
   `0.50·NDCG@10 + 0.30·NDCG@50 + 0.15·MAP + 0.05·P@10`.
   → **Top-10 precision is half the score.** The ranker must be *conservative at the
   top*: zero honeypots, zero traps, zero "perfect-on-paper-but-unavailable" in the
   top 50. We prefer a clearly-defensible top 50 over squeezing marginal gains lower.

3. **Product vs. services/consulting matters.** JD rejects pure-services careers
   (TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini, Mindtree, …). Currently at
   one *with prior product experience* is OK.

4. **Location is a real signal.** Role is Pune/Noida, India. India Tier-1 cities
   (Bangalore, Hyderabad, Pune, Mumbai, Delhi NCR, Chennai, …) or
   `willing_to_relocate=true` are favored; outside-India without relocate is
   down-weighted (no visa sponsorship).

5. **Schema-correct behavioral handling** (the skeleton had real bugs):
   - `github_activity_score` is **0–100**, `-1` = no GitHub (skeleton treated 8.0 as high).
   - `offer_acceptance_rate` can be **-1** = no history → must be treated as neutral, not penalty.
   - `notice_period_days` max **180** (skeleton's 720 honeypot is impossible).
   - `education[].tier` is **already provided** (`tier_1..tier_4`, `unknown`) — use it.
   - `skills[].duration_months`, `expected_salary_range_inr_lpa`, `last_active_date`,
     `signup_date`, `skill_assessment_scores` are all present and used below.

6. **Reasoning is graded** (Stage 4): must be specific, varied, JD-connected, honest
   about concerns, non-hallucinated, rank-consistent. → Reasoning is generated from
   *real extracted facts* with concern-flagging, not a fixed template.

7. **Dependencies: Python stdlib only.** No pandas/numpy. Removes a reproducibility
   risk in the no-network Docker sandbox and is plenty fast. Fuzzy matching via
   `difflib` (stdlib).

---

## 1. Algorithm optimization — weights & structure

**Composite (additive pillars) × behavioral multiplier**, then honeypot kill.

| Pillar | Weight | Rationale |
|---|---|---|
| P1 Skills + **evidence** | **0.30** | Reduced from 0.40 — keyword skills alone are a trap. Half of this comes from career-description evidence. |
| P2 Production experience | **0.45** | Raised from 0.35 — "shipped end-to-end ranking/search/recsys at a product company" is the core JD ask. |
| P3 Years + seniority | **0.15** | Unchanged; 5–9 band is a soft proxy. |
| P4 Behavioral multiplier | ×[0.80, 1.10] | Multiplier, not weight. Availability gates an otherwise-strong candidate. |
| P5 Location modifier | +[-0.08, +0.03] | Additive nudge inside composite; small but real. |

```
composite = 0.30*skill + 0.45*exp + 0.15*yoe + location_mod
final     = clamp(composite, 0, 1) * behavioral_mult
if honeypot: final = -1.0
```

**Non-linear adjustments:**
- Skill score uses **diminishing returns** (sqrt-like) on tier counts so a keyword
  stuffer with 25 skills doesn't beat a focused expert with 4 deep ones.
- Production-evidence uses a **saturating** curve: the first concrete "built X
  ranking system in production" is worth far more than the fifth keyword hit.

**Interaction effects (the part the skeleton missed):**
- `skills present` × `no production evidence in career` → skills capped (the trap).
- `strong production evidence` × `weak skills list` → still scores well (the JD's
  "Tier-5 who built a recsys" case). Evidence can carry a thin skills list.
- `high response_rate` × `high interview_completion` → availability bonus.
- `open_to_work` × `not active in 90 days` → contradiction, dampened.

---

## 2. Skill matching enhancement (Pillar 1)

**Tier-1 (must-haves):** embeddings frameworks (sentence-transformers/sbert, BGE, E5,
OpenAI embeddings, CLIP, word2vec, glove), vector DB / hybrid search (FAISS,
Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, Vespa, Chroma),
ranking/IR evaluation (NDCG, MRR, MAP, learning-to-rank, information retrieval,
recommendation, semantic search, RAG), strong Python.

**Tier-2 (strong proxy):** LoRA/QLoRA/PEFT, HuggingFace/transformers, fine-tuning,
XGBoost/LambdaMART/RankNet/neural ranking, MLflow/W&B/experiment tracking,
Spark/Airflow/Kafka.

**Tier-3 (context):** AWS/GCP/Azure, SQL/Snowflake/BigQuery, scikit-learn/PyTorch/
TensorFlow, Docker/Kubernetes/REST.

**Fuzzy / alias matching (stdlib):**
- A normalized alias map (`"sbert"→sentence-transformers`, `"faiss"`, `"facebook ai
  similarity search"→faiss`, `"vector db"→vector database`, etc.).
- `difflib.SequenceMatcher` ratio ≥ 0.88 for typo tolerance, applied only against
  the tier vocabularies (bounded, fast). Exact/alias hit first; fuzzy as fallback.

**Skill trust (endorsement + duration quality), per matched skill:**
```
trust = clamp(0.4 + 0.5*min(endorsements,20)/20 + 0.3*min(duration_months,36)/36, 0.4, 1.2)
```
A skill with 0 endorsements AND 0 duration but "advanced/expert" → trust floored and
flagged for inflation (honeypot signal #4).

**Career-description evidence (the important half of P1):** scan
`profile.summary` + each `career_history[].description` for Tier-1/Tier-2 *concepts*
(retrieval, embedding, ranking, recommendation, vector search, semantic search,
relevance, NDCG, A/B test, …). Evidence found in a *job description* counts more than
the same word sitting in the skills list.

```
skill_score = 0.5 * normalized_skill_keyword_score   # tiers × trust, diminishing returns
            + 0.5 * normalized_evidence_score          # concepts in career/summary text
# keyword-only (evidence==0) is capped at 0.55 to defuse the stuffer trap
```

**Inflation penalty:** >15 skills with avg endorsements <3 → ×0.7; ≥3 "advanced/expert"
skills with 0 endorsements AND 0 duration → strong inflation flag.

---

## 3. Production experience validation (Pillar 2) — the heaviest pillar

Per role in `career_history`, accumulate evidence then normalize:

**Role type** (from title): engineer/ml/data/research-scientist/architect/tech-lead →
technical; sales/hr/marketing/finance/recruiter/PM → non-technical.

**Company-type tier:**
- Services/consulting (TCS, Infosys, Wipro, Accenture, Cognizant, Capgemini,
  Mindtree, HCL, Tech Mahindra, LTI, Mphasis, …) → **0.0** (and a soft career-wide
  penalty if *entire* career is services).
- Big-tech / product (Google, Meta, Amazon, Microsoft, Netflix, Uber, Airbnb,
  Flipkart, Swiggy, Zomato, Razorpay, etc.) → **+0.10**.
- Other product company (non-services) → **+0.05**.
- Company size (current schema enum): 1001+ → +0.08, 201–1000 → +0.05.

**Production evidence keywords** in description: production, deployed, shipped, scale,
users, latency, real-time, pipeline, serving, A/B, monitoring, on-call, infra.
Saturating bonus, capped.

**Domain relevance** in description (the JD's actual ask): ranking, retrieval, search,
recommendation, embeddings, vector, relevance, matching, personalization → strong
bonus (this is what "built it" looks like).

**Duration:** ≥24 months in a relevant role = depth bonus; partial credit below.

**Disqualify-to-low (not -1, just heavy penalty) if:**
- All roles research/academic/kaggle/competition and total production < 24 months.
- Current title non-technical AND no technical role in last 5 years.
- No role longer than 18 months (job-hopper / title-chaser) → ×0.7.

**Education modifier (small, ±0.05 max):** use provided `education[].tier`
(`tier_1`→+0.05, `tier_2`→+0.02), capped — production ≫ credentials.

---

## 4. Years & seniority (Pillar 3)

```
yoe bands:  <3 → ramp 0→0.5 ; 3–9 → 1.0 ; 9–15 → decay to 0.9 ; >15 → 0.85
+0.10 if title has senior/lead/staff/principal
+0.05 promotion detected (ascending seniority across career_history, chronological)
career-stability: avg tenure < 18 months across ≥3 roles → ×0.85 (title-chaser signal)
```
Clamp to [0,1].

---

## 5. Behavioral multiplier (Pillar 4) — schema-correct

Component score in [0,1], then mapped to multiplier **[0.80, 1.10]** (availability can
modestly boost and meaningfully dampen, but never dominate skills):

| Signal | Handling |
|---|---|
| recruiter_response_rate | weight 0.25 |
| interview_completion_rate | weight 0.20 |
| open_to_work_flag | 0.15 if true |
| offer_acceptance_rate | weight 0.15 **but if == -1 → treat as neutral (0.5), no penalty** |
| verified_email & verified_phone | 0.10 if both |
| recency: last_active within 30d → 0.10; 30–90d → 0.05; >180d → 0 | engagement |
| notice_period_days | ≤30 → +0.05; 31–90 → +0.02; >90 → 0 (JD: sub-30 preferred) |

**Response-time buckets:** ≤24h +0.03; ≤72h +0.01; >336h −0.05; null/0 → neutral.
**GitHub:** score ≥70 → +0.03; `-1` (none) → neutral, no penalty.
**Consistency interactions:** high response × high interview-completion → +0.03;
open_to_work × inactive>90d → −0.05; high response × very-low interview-completion
(flaky) → −0.03.
**Salary realism:** `expected_salary.min` absurd for YoE (e.g. >60 LPA at <4 yrs) → −0.03.

Final: `mult = clamp(0.80 + 0.30*component, 0.80, 1.10)`.

---

## 6. Honeypot detection — 10 patterns with severity

Severity = **DISQUALIFY** (final = -1.0) or **PENALTY** (subtract / multiply).

| # | Pattern | Check | Severity |
|---|---|---|---|
| 1 | Impossible timeline (work before grad) | earliest career start < earliest edu end_year − 1 | DISQUALIFY |
| 2 | Tenure > company age | role.duration implies start before plausible founding (proxy: YoE > years-since-signup by large margin, or role start < 2000 with modern tech) | DISQUALIFY |
| 3 | YoE vs education impossible | `years_of_experience` > (current_year − edu.end_year) + 1 | DISQUALIFY |
| 4 | Expertise with zero substance | ≥3 skills "expert/advanced" with endorsements==0 AND duration_months==0 | DISQUALIFY |
| 5 | Title–skill contradiction | non-technical current title (Marketing/Sales/HR) + skills 80%+ AI/ML + no technical career role | DISQUALIFY |
| 6 | YoE vs career sum mismatch | profile YoE far exceeds sum of career durations (e.g. claims 15, career sums 3) | PENALTY heavy |
| 7 | Skill inflation | >20 skills, avg endorsements <2 | PENALTY ×0.7 |
| 8 | Job-hopper extreme | ≥5 roles all <6 months | PENALTY ×0.7 |
| 9 | All-services career | every company is a known services firm, no product role | PENALTY ×0.8 |
| 10 | Geographic/availability contradiction | open_to_work but inactive >180d, OR data-quality contradiction | PENALTY light |

We compute `honeypot_score` + a list of triggered flags (for the reasoning/audit).
**False-positive guard:** DISQUALIFY patterns require *structural impossibility*
(timeline/education), not soft signals — to protect top-100 from false kills.
Track honeypot rate in top-100 (must stay <10%; target ~0%).

---

## 7. Reasoning generation (graded at Stage 4)

Built from extracted facts, **varied** and **honest**:
- Always include: current title, YoE, strongest 1–2 *evidence* facts (named skill or
  "built X" from career), one behavioral signal.
- For ranks with concerns: append an honest caveat ("services-only background",
  "notice 120d", "low response rate", "outside India, relocation unclear").
- Vary sentence structure by score band; never reference `candidate_id`; never claim a
  skill/employer not in the profile. ≤ ~200 chars.

---

## 8. Code quality, performance, calibration

- **Structure:** pure functions per pillar + a thin `score_candidate`; `.get()` with
  defaults everywhere (no KeyErrors on missing fields). Full type hints.
- **Performance:** stream JSONL line-by-line (don't hold raw + parsed simultaneously
  more than needed); pre-compiled regexes; precomputed lowercase sets; exact/alias
  before bounded fuzzy. Target ≪1 ms/candidate → <60s for 100K single-thread; add a
  `ProcessPoolExecutor` (CPU-bound, GIL-bound work) only if needed. Heap-based top-N
  (`heapq.nlargest`) instead of full sort.
- **Tests (`test_scoring.py`):** unit tests per pillar + synthetic calibration cases:
  5 ideal (≥0.85), 5 borderline (0.5–0.7), 5 weak (<0.3), 5 honeypots (-1.0). Assert
  ordering and honeypot kills.
- **Submission strategy:** S1 dry-run (this full ranker, validated) to confirm format;
  S2 after spot-checking top-20 + honeypot audit; S3 final polish. Given no
  leaderboard, rely on local calibration, not submission feedback.

---

## 9. Acceptance criteria for the implementation

- `python rank.py --candidates data/candidates.jsonl --out submission.csv` → valid per
  `validate_submission.py`, exactly 100 rows, scores non-increasing, ID tie-break.
- Runs <5 min on CPU, no network, stdlib-only.
- Top-10 contains no honeypots and no non-technical/services-only profiles.
- Reasoning is specific, varied, concern-aware.
