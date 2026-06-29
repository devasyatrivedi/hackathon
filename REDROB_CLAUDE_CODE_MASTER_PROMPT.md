# REDROB HACKATHON — CLAUDE CODE MASTER PROMPT
## Senior AI Engineer Candidate Ranking System

**Execution Mode:** Scrumban (Kanban with sprint-based task organization)  
**Challenge Type:** AI/ML Systems Engineering + Data Intelligence  
**Time-Box:** 5-minute CPU ranking pipeline (no GPUs, no network)  
**Submission Limit:** 3 total (final is binding)  
**Outcome:** Top-100 CSV + working sandbox + production-grade code

---

## 📋 CHALLENGE SUMMARY (CONTEXT LAYER)

### **The Ask**
Rank the top 100 candidates from a pool of 100,000 for a **Senior AI Engineer role** at Redrob (Series A AI talent platform). Produce a **CSV file** with `[candidate_id, rank, score, reasoning]` where:
- Rank 1 = best fit; rank 100 = 100th best
- Scores are **strictly non-increasing** by rank (ties allowed, broken by candidate_id ascending)
- Reasoning is 1-2 sentence justification per candidate

### **JD Core Requirements (Read Carefully)**
The role seeks someone who bridges **deep ML systems expertise** + **scrappy product-engineering mindset**:

**Must-Have Skills:**
1. Production embeddings-based retrieval systems (sentence-transformers, BGE, E5, etc.) deployed to real users
2. Vector database / hybrid search (Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS)
3. **Strong Python** (code quality matters)
4. Hands-on evaluation frameworks for ranking systems (NDCG, MRR, MAP, offline-to-online correlation, A/B testing)

**Nice-to-Have:**
- LLM fine-tuning (LoRA, QLoRA, PEFT)
- Learning-to-rank models (XGBoost, neural)

**Explicit Disqualifiers:**
- Pure research background (no production deployment in last 5+ years)
- Recent AI experience = only LangChain + OpenAI wrapper (< 12 months, no depth)
- Senior engineers who stopped writing production code 18+ months ago ("architecture" roles only)

### **Experience Range: 5–9 years**
- This is a rough proxy, not a hard cutoff
- Real signal: judgment, shipping speed, mentorship readiness
- Accept candidates with 4 years of exceptional judgment
- Reject candidates with 15 years in pure research

---

## 🎯 SCORING FRAMEWORK (Core Intelligence)

### **Four-Pillar Ranking System**

#### **Pillar 1: Skill Relevance Match (40%)**
Determine closeness to JD must-haves using multi-stage signal extraction:

**Tier-1 Skills (Explicit Match — Top Priority):**
- Embeddings frameworks: sentence-transformers, BGE, E5, OpenAI Embeddings, CLIP
- Vector databases: FAISS, Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch
- Evaluation frameworks: NDCG, MRR, MAP, ranking metrics (extract from profile + career descriptions)
- Python (strong indicator if years_of_experience ≥ 3 + explicit endorsements)

**Tier-2 Skills (Strong Proxy):**
- LLM fine-tuning: LoRA, QLoRA, PEFT, HuggingFace transformers
- Learning-to-rank: XGBoost, LambdaMART, neural ranking models
- ML Ops: MLflow, Weights & Biases, experiment tracking
- Distributed systems: Spark, Airflow, Kafka (data infrastructure proximity)

**Tier-3 Skills (Context):**
- Cloud platforms: AWS, GCP, Azure
- SQL, data warehousing (Snowflake, BigQuery)
- General ML: scikit-learn, PyTorch, TensorFlow

**Scoring Logic:**
```
skill_match_score = (
  (count_tier1_skills × 0.4) +
  (count_tier2_skills × 0.25) +
  (count_tier3_skills × 0.1) +
  (avg_endorsements_for_relevant_skills × 0.05)
) / total_possible_weight

Normalize to [0, 1].
```

**Special Case — Keyword Stuffing Detection:**
- If candidate has 20+ skills but profile/career history shows no depth in any: **reduce score by 0.3**
- If skill proficiency is "expert" but endorsements = 0 and duration_months < 3: flag as suspicious

---

#### **Pillar 2: Production Experience Validation (35%)**
Extract from career history and education tier.

**Production Engineering Signal (must be present):**
- Current or recent role title matches: Engineer, ML Engineer, Data Engineer, ML Ops, Architect, Tech Lead
- Company size: at least one role at company with 200+ headcount (indicates real systems)
- Role duration: ≥ 2 years in any relevant role (shows depth, not job-hopping)
- Career description explicitly mentions: deployment, production, scaling, users, systems (keyword presence)

**Red Flags — Disqualify if all true:**
1. All career history is in "Research", "Academic", "Kaggle", "Competition", "Side Project"
2. No role longer than 18 months
3. Current role is not technical (Sales, PM, HR)

**Experience Relevance Scoring:**
```
exp_score = 0
For each role in career_history:
  if role_type == "research_only" and duration < 24 months:
    continue
  if role_type in ["Engineer", "ML Engineer", "Data Engineer"] and duration ≥ 24:
    exp_score += (duration_months / 12) × 0.15
  if company_size ≥ 200:
    exp_score += 0.10
  if profile_summary contains keywords ["production", "deployment", "scale", "users"]:
    exp_score += 0.10

Normalize exp_score to [0, 1].
```

**Education Tier Modifier:**
- Tier 1 (IIT, Stanford, MIT, CMU): +0.05
- Tier 2 (good private unis, reputable state schools): +0.02
- Tier 3 (others): +0.00
- BUT: weight education at only 5% of total (production > credentials)

---

#### **Pillar 3: Experience Years + Role Alignment (15%)**
Match against 5–9 year range and role seniority.

**Years of Experience Scoring:**
```
if years_in_profile < 3:
  years_score = years_in_profile / 3 × 0.5  # penalize juniors
elif 3 ≤ years_in_profile ≤ 9:
  years_score = 1.0  # full credit in band
elif 9 < years_in_profile ≤ 15:
  years_score = 1.0 - (years_in_profile - 9) / 6 × 0.1  # mild decay
else:
  years_score = 0.85  # 15+ years, check for "research drift"
```

**Role Seniority Signal:**
- Current title contains "Senior", "Lead", "Staff": +0.1
- Recent promotion visible in career history: +0.05
- Mentorship indicators (team lead role, tech lead): +0.05

**Honeypot Detection (Kill Signal):**
- If years_in_profile = 8 but current_company founded 4 years ago: **disqualify**
- If years_in_profile = 10 but newest role dated in last 18 months with higher years: **disqualify**
- If education end_year is 2020 and years_in_profile = 15: **disqualify** (impossible)

---

#### **Pillar 4: Behavioral Engagement Signals (10%)**
Multiply final score by behavioral likelihood of hire.

**Key Signals from `redrob_signals` object:**

| Signal | Weight | Interpretation |
|--------|--------|-----------------|
| `recruiter_response_rate` | 0.25 | Actual likelihood candidate responds (>0.5 is good) |
| `open_to_work_flag` | 0.20 | Explicit interest in moving |
| `interview_completion_rate` | 0.20 | Follow-through on interviews (>0.6 is good) |
| `offer_acceptance_rate` | 0.15 | Actual conversion to hire |
| `verified_email` + `verified_phone` | 0.10 | Profile credibility |
| `willing_to_relocate` | 0.05 | Org flexibility |
| `notice_period_days` | 0.05 | Can join soon (30–60 is good; >90 is risk) |

**Behavioral Score Calculation:**
```
behavioral_multiplier = (
  (recruiter_response_rate × 0.25) +
  (open_to_work_flag × 0.20 if true else 0.0) +
  (interview_completion_rate × 0.20) +
  (offer_acceptance_rate × 0.15) +
  (0.10 if verified_email and verified_phone else 0.0) +
  (0.05 if willing_to_relocate else 0.0) +
  (0.05 if 30 ≤ notice_period_days ≤ 90 else 0.0)
) / total_weight

Clamp to [0.7, 1.2]  # Don't let behavior override skills; allow modest boost
```

**Special Handling:**
- If `avg_response_time_hours` > 336 (14 days): reduce multiplier by 0.1
- If `github_activity_score` ≥ 8.0: +0.05 to multiplier (active engineer signal)
- If `skill_assessment_scores` exists for relevant skills: average them, use as tie-breaker

---

### **Final Composite Score**

```python
def calculate_score(candidate):
    skill_score = pillar_1_skill_match(candidate)
    exp_score = pillar_2_production_experience(candidate) 
    yoe_score = pillar_3_experience_years(candidate)
    behav_multiplier = pillar_4_behavioral(candidate)
    
    # Weighted composite
    composite = (
        skill_score * 0.40 +
        exp_score * 0.35 +
        yoe_score * 0.15
    )
    
    # Apply behavioral multiplier
    final_score = composite * behav_multiplier
    
    # Honeypot check (kill signal)
    if is_honeypot(candidate):
        final_score = -1.0  # Rank at bottom
    
    return final_score  # Range [0.0, 1.0] for valid candidates
```

---

## 🔴 TRAP DETECTION (Honeypot & Anomaly Layer)

The dataset contains **~80 honeypots** with impossible profiles. A good system naturally avoids them; you don't need to special-case all 80.

### **Honeypot Red Flags (Automated Detection)**

**Type 1: Impossible Timeline**
```
if role.end_date < candidate.education.end_year:
    # Working before graduating? Suspicious (or double-major, rare)
    flag_as_suspicious()

if years_in_profile > current_year - profile.signup_date.year:
    # Claims 8 years but joined platform 2 years ago
    flag_as_suspicious()
```

**Type 2: Skill Inflation**
```
if count(skills) > 20 and avg(endorsements_per_skill) < 3:
    # Keyword stuffer; real experts get endorsed
    reduce_score_by(0.3)

if all_skills_proficiency == "expert" and sum(endorsements) < 10:
    # Impossible: expert in everything but no validation
    flag_as_suspicious()
```

**Type 3: Company Timeline Mismatch**
```
if role.duration_months > 0 and company.founded_year > role.start_date.year:
    # "5 years at Company X" but Company founded 2 years ago
    disqualify()
```

**Type 4: Behavioral Twins** (same profile data, different ID)
```
# Don't rank multiple candidates with near-identical skill/experience profiles
# Take only top 1–2 per "cluster"
```

---

## 📦 SYSTEM ARCHITECTURE (Implementation Guide)

### **Stage 0: Setup & Data Loading**
```
1. Load candidates.jsonl.gz (100,000 records)
2. Parse each JSON line into structured Candidate object
3. Validate schema against expected structure
4. Initialize scoring pipeline state
```

### **Stage 1: Parallel Scoring (CPU-Optimized)**
```
1. Create thread pool (4–8 workers depending on CPU cores)
2. Distribute candidates across workers
3. Each worker:
   a. Extract skill keywords using regex/simple matching
   b. Compute pillar scores independently
   c. Perform honeypot checks
   d. Return (candidate_id, final_score, metadata)
4. Collect results into in-memory list
```

### **Stage 2: Ranking & Tie-Breaking**
```
1. Sort by score descending (non-increasing)
2. For ties (same score):
   - Secondary sort by candidate_id ascending
3. Select top 100
4. Assign ranks 1–100
```

### **Stage 3: Reasoning Generation**
```
For each top-100 candidate:
1. Extract: current_title, years_of_experience, top 3 skills, key behavioral signal
2. Format: "{title} with {yoe} yrs; {skill_count} core skills; response rate {rate}."
3. Keep under 2 sentences; make it defensible
```

### **Stage 4: CSV Export & Validation**
```
1. Create DataFrame with [candidate_id, rank, score, reasoning]
2. Validate using provided validator script
3. Write to team_<id>.csv
4. Check: 100 rows, scores non-increasing, no duplicates
5. Return success or error log
```

---

## 🛠️ TECHNICAL REQUIREMENTS

### **Dependencies (CPU-Only)**
```
python==3.11+
pandas>=2.0
numpy>=1.24
gzip (stdlib)
json (stdlib)
re (stdlib)
concurrent.futures (stdlib)
```

### **Memory Budget**
- 100,000 candidates in JSON: ~465 MB uncompressed
- Scoring state (candidate_id, score, metadata): ~100 MB
- Total: ~600 MB typical (well under 16 GB limit)

### **Runtime Budget**
- Data loading: ~5–10 seconds
- Scoring (100K candidates): ~120–180 seconds (1.2–1.8ms per candidate)
- Sorting + ranking: ~5 seconds
- CSV export: ~2 seconds
- **Total: 150–200 seconds (under 5 minutes ✓)**

### **Parallelization Strategy**
```
# Pseudo-code: thread pool scoring
from concurrent.futures import ThreadPoolExecutor

def score_candidate(candidate):
    return (
        candidate['candidate_id'],
        calculate_score(candidate),
        generate_reasoning(candidate)
    )

with ThreadPoolExecutor(max_workers=6) as executor:
    results = executor.map(score_candidate, candidates)

scored = list(results)
```

---

## 📋 PHASE BREAKDOWN (Scrumban Workflow)

### **Phase 1: Data Inspection & Schema Validation (Immediate)**
- [ ] Load sample_candidates.json (50 records)
- [ ] Inspect keys: candidate_id, profile, career_history, education, skills, redrob_signals
- [ ] Map schema to Python dataclasses or TypedDict
- [ ] Print sample candidate to understand nesting depth
- [ ] Estimate full 100K dataset memory footprint

### **Phase 2: Skill Matching Engine (Parallel Task)**
- [ ] Define Tier-1/Tier-2/Tier-3 skill hierarchies as constants
- [ ] Implement skill extraction function (exact match + fuzzy match)
- [ ] Implement keyword stuffer detection
- [ ] Test on sample candidates (verify scoring logic)
- [ ] Benchmark: speed per candidate (target <1ms)

### **Phase 3: Production Experience Extractor (Parallel Task)**
- [ ] Parse career_history array
- [ ] Identify role types: Engineer, Research, Sales, etc.
- [ ] Extract company sizes from career records
- [ ] Scan profile summary for production keywords
- [ ] Implement honeypot timeline detection
- [ ] Test on sample candidates

### **Phase 4: Years + Seniority Scorer (Parallel Task)**
- [ ] Extract years_of_experience from profile
- [ ] Parse current_title for seniority keywords
- [ ] Scan career history for promotions
- [ ] Implement honeypot year-validation logic
- [ ] Test on sample candidates

### **Phase 5: Behavioral Signal Integration (Parallel Task)**
- [ ] Extract redrob_signals object
- [ ] Map 23 signals to 5-key summary (response_rate, open_to_work, etc.)
- [ ] Implement multiplier calculation
- [ ] Handle missing/null signals gracefully
- [ ] Test on sample candidates

### **Phase 6: Composite Scoring (Integration)**
- [ ] Merge all 4 pillars with weights (0.40, 0.35, 0.15, multiplier)
- [ ] Test composite on sample candidates
- [ ] Verify score distribution (should be [0.0, 1.0])
- [ ] Validate that top candidate != bottom candidate

### **Phase 7: Honeypot Detection & Filtering (Integration)**
- [ ] Implement timeline validation (impossible profiles)
- [ ] Implement skill inflation detection
- [ ] Implement company timeline cross-check
- [ ] Test on sample candidates (should catch obvious honeypots)
- [ ] Calculate honeypot rate in top 100

### **Phase 8: Ranking & Tie-Breaking (Integration)**
- [ ] Sort by score descending
- [ ] Break ties by candidate_id ascending
- [ ] Assign ranks 1–100
- [ ] Verify no duplicate ranks, IDs
- [ ] Test on sample candidates

### **Phase 9: Reasoning Generation (Parallel Task)**
- [ ] Extract: title, years, top skills, key signal (response_rate, etc.)
- [ ] Generate short 1-2 sentence justification per candidate
- [ ] Keep under 100 characters
- [ ] Test on sample candidates

### **Phase 10: CSV Export & Validation (Integration)**
- [ ] Create DataFrame with required columns
- [ ] Export to team_<id>.csv
- [ ] Run provided validate_submission.py
- [ ] Fix any schema/format errors
- [ ] Verify 100 rows, scores non-increasing, all IDs exist

### **Phase 11: Production Orchestration (Final)**
- [ ] Wrap all phases into single `rank.py` script
- [ ] Accept command-line args: `--candidates <path> --out <path>`
- [ ] Handle gzip'd candidates.jsonl.gz
- [ ] Add logging (informational, not verbose)
- [ ] Test end-to-end: load 100K candidates → output CSV in <5 min

### **Phase 12: Sandbox Deployment (Packaging)**
- [ ] Create GitHub repo with full code
- [ ] Write README.md with setup + reproduce command
- [ ] Add requirements.txt with pinned versions
- [ ] Fill submission_metadata.yaml (team info, sandbox link, methodology)
- [ ] Deploy to HuggingFace Spaces / Streamlit Cloud
- [ ] Verify sandbox can run on small sample (100 candidates)

### **Phase 13: Submission & Documentation (Final)**
- [ ] Double-check CSV with validator
- [ ] Prepare portal metadata (team name, emails, AI tools declaration)
- [ ] Write brief methodology summary (100–200 words)
- [ ] Verify GitHub repo is readable
- [ ] Submit via portal

---

## 🚨 CRITICAL CONSTRAINTS & PITFALLS

### **Compute Constraints (Non-Negotiable)**
1. **5-minute CPU window**: No GPUs, no CUDA, no MPS (Apple Silicon GPU)
2. **16 GB RAM ceiling**: Can load full 465 MB JSON + scoring state (~600 MB total)
3. **No network during ranking**: Cannot call OpenAI, Claude API, HuggingFace inference, etc. during scoring phase
   - **Allowed**: Pre-computed embeddings (stored locally), static models, rule-based logic
4. **Enforcement**: Top-N submissions reproduced in sandboxed Docker; any network access = auto-fail

### **Output Format (Exact Match Required)**
- Header: `candidate_id,rank,score,reasoning`
- Exactly 100 data rows (rows 2–101; row 1 is header)
- Each rank 1–100 appears exactly once
- Each candidate_id appears exactly once
- Scores strictly non-increasing (with tie-breaking by candidate_id ascending)
- Validation script will auto-reject if format is wrong

### **Honeypot Filter (Soft but Important)**
- If honeypot rate in top 100 > 10%, submission is disqualified at Stage 3
- Don't over-engineer honeypot detection (causes false positives)
- Let scoring logic naturally penalize impossible profiles

### **Three-Submission Cap (Plan Carefully)**
- Only 3 submissions total; final one is binding
- No live leaderboard feedback
- Use first submission to catch format errors
- Use second submission for scoring algorithm refinement (if needed)
- Use third submission for final polish

### **AI Tools Declaration (Be Honest)**
- Permitted: Claude, ChatGPT, Copilot, Cursor for code review, architecture discussion, debugging
- Forbidden: AI-only approach (no human engineering work)
- Truth-test: Can you explain every design choice? Can you defend the scoring formula?
- Contradiction between declaration and code = red flag at interview stage

---

## ✅ SUCCESS CRITERIA

### **Immediate (Format & Functionality)**
1. ✓ CSV validates with provided validator script
2. ✓ 100 rows, 4 columns, correct header, no duplicates
3. ✓ Scores strictly non-increasing (with correct tie-breaking)
4. ✓ All candidate_ids exist in candidates.jsonl
5. ✓ Reasoning is human-readable (1-2 sentences)

### **Algorithmic (Scoring Quality)**
1. ✓ Top 100 candidates have >0 production experience
2. ✓ Top 100 candidates have >0 relevant skills (embeddings, vector DB, Python, evaluation)
3. ✓ Honeypot rate in top 100 < 10%
4. ✓ Score distribution is well-spread (not collapsed to narrow range)
5. ✓ Top-ranked candidates align with JD must-haves (spot-check 5–10)

### **Performance (Runtime & Resources)**
1. ✓ End-to-end ranking completes in <5 minutes on CPU
2. ✓ Memory usage stays under 2 GB (well under 16 GB limit)
3. ✓ No GPU access required
4. ✓ No network calls during ranking step

### **Reproducibility (Sandbox & Code)**
1. ✓ GitHub repo contains full source + README
2. ✓ Single command reproduces CSV: `python rank.py --candidates ./candidates.jsonl --out ./submission.csv`
3. ✓ Sandbox (HuggingFace Spaces, Streamlit, etc.) runs same code on small sample
4. ✓ requirements.txt pinned to exact versions
5. ✓ submission_metadata.yaml matches portal submission

---

## 🔗 FILES & REFERENCES

### **Provided in Bundle**
- `candidates.jsonl.gz` → 100,000 candidate records (you need to gunzip + parse)
- `sample_candidates.json` → 50 records for testing/inspection
- `job_description.docx` → Full JD (must read)
- `submission_spec.docx` → Submission rules + evaluation stages (must read)
- `redrob_signals_doc.docx` → 23 behavioral signals reference (recommended)
- `candidate_schema.json` → JSON schema of candidate fields
- `sample_submission.csv` → Format reference (NOT high-quality ranking)
- `validate_submission.py` → Format validator (must pass before submitting)
- `submission_metadata_template.yaml` → Metadata template (fill out + commit to repo)

### **Your Outputs**
1. `rank.py` → Main ranking script (entry point)
2. `team_<id>.csv` → Top-100 submission
3. `submission_metadata.yaml` → Filled-out metadata (copy of template)
4. `README.md` → Setup + reproduce instructions
5. `requirements.txt` → Pinned dependencies
6. GitHub repo (private or public) + sandbox link

---

## 💡 TIPS FOR SUCCESS

1. **Start with the validator script** — understand the CSV format before writing scoring logic
2. **Profile the sample candidates by hand** — spot-check top 5 expected candidates to calibrate scoring
3. **Test incrementally** — score 50 candidates, verify top 5 make sense, then scale to 100K
4. **Use timeit for profiling** — target <1ms per candidate to stay under 5-minute budget
5. **Document your scoring rationale** — if you make top 50, you'll be interviewed on design choices
6. **Honeypot check last** — don't over-engineer; natural scoring should avoid most traps
7. **Keep reasoning concise** — 1–2 sentences, extract title + years + key signal
8. **Test the full pipeline end-to-end** on a subset (e.g., 1K candidates) before running full 100K
9. **Sandbox is not optional** — budget 30 minutes to deploy to HuggingFace Spaces
10. **Use AI tools for rubber-ducking** — discuss your scoring logic with Claude, verify it covers edge cases

---

## 🎯 NEXT STEPS (Immediate Actions)

1. **Read this prompt end-to-end** (you're reading it now ✓)
2. **Run the validator on sample_submission.csv** to understand format
3. **Load sample_candidates.json and inspect** the first 3 candidates by hand
4. **Design Pillar 1 (Skill Matching)** — define your Tier-1/2/3 skills list
5. **Design Pillar 2 (Production Experience)** — define role type regex patterns + keywords
6. **Build a scoring function for 50-candidate sample** and test it
7. **Extend to 100K candidates** with parallelization
8. **Implement honeypot detection** (timeline + inflation checks)
9. **Rank top 100, generate reasoning, export CSV**
10. **Validate CSV, then submit**

---

**Ready to build? Let's go. 🚀**
