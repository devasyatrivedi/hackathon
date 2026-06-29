# REDROB HACKATHON — EXECUTIVE SUMMARY
## Complete Challenge Overview & File Navigation Guide

**Date:** June 28, 2026  
**Challenge:** Intelligent Candidate Discovery & Ranking (Redrob AI, Series A)  
**Submission Deadline:** TBD (3-submission limit)  
**Estimated Time-to-Submit:** 15–20 hours  

---

## 🎯 CHALLENGE IN 60 SECONDS

**The Ask:**
Rank the top **100 candidates** from a pool of **100,000** for a **Senior AI Engineer role** at Redrob. Produce a CSV with `[candidate_id, rank, score, reasoning]` where rank 1 = best fit.

**Why Hard:**
- Only 5-minute CPU window (no GPUs, no network during ranking)
- Dataset contains ~80 "honeypots" (impossible profiles designed to catch lazy systems)
- Evaluation has 5 stages: format validation → honeypot check → code reproduction → quality scoring → interviews for top-50
- Must cite production experience + specific ML skills (embeddings, vector DBs, evaluation frameworks)

**Why Worth It:**
- Top-50 candidates get interviews
- Ranking system design is exactly what Redrob does (real product relevance)
- AI/ML opportunity on real data with real constraints (distributed systems problem-solving)

---

## 📁 DELIVERABLES YOU'LL CREATE

| File | Purpose | Format |
|------|---------|--------|
| `rank.py` | Main ranking script | Python (executable) |
| `team_<id>.csv` | Top-100 submission | CSV (100 data rows + header) |
| `submission_metadata.yaml` | Submission metadata | YAML (team info, methodology) |
| `README.md` | Setup + reproduce instructions | Markdown (clear, step-by-step) |
| `requirements.txt` | Python dependencies | TXT (pinned versions) |
| GitHub Repo | Full code + version control | Git (public or private w/ access) |
| Sandbox | Working demo on small sample | HuggingFace Spaces / Streamlit / Colab |

---

## 📚 DOCUMENT NAVIGATION (Your Guides)

### **1. Master Prompt (START HERE FOR CLAUDE CODE)**
**File:** `REDROB_CLAUDE_CODE_MASTER_PROMPT.md`  
**What:** 
- Complete challenge brief (JD, constraints, rules)
- 4-pillar scoring framework (detailed formulas + rationale)
- Honeypot detection strategies
- System architecture + parallelization approach
- 13-phase Scrumban workflow

**When to Read:** Before writing any code. Reference section-by-section as you build.

---

### **2. Technical Implementation Guide**
**File:** `REDROB_TECHNICAL_IMPLEMENTATION_GUIDE.md`  
**What:**
- Complete candidate data structure (all fields, nested objects, types)
- Skill hierarchy: Tier-1/2/3 with 50+ examples
- Skill extraction patterns (regex, fuzzy matching, context)
- Honeypot detection code patterns (timeline, inflation, company mismatch)
- Detailed scoring function implementations (copy-paste ready)
- Parallelization strategy + thread pool patterns
- Reasoning generation templates
- Full validation checklist

**When to Read:** After understanding the master prompt. Use as reference while coding.

---

### **3. Success Criteria & Hints**
**File:** `REDROB_SUCCESS_CRITERIA_AND_HINTS.md`  
**What:**
- 5-stage evaluation pipeline (what's actually being judged)
- Scoring dynamics (top 1% vs top 10% vs top 25% characteristics)
- Quick calibration checklist (spot-check your top 5)
- Red flags (definite disqualifiers)
- Spot-check strategy (manual validation methods)
- Common mistakes (6 common pitfalls + fixes)
- Optimization tactics (quick wins vs medium effort)
- Final submission checklist (2 hours before deadline)
- Interview prep for top-50

**When to Read:** After building MVP. Use to polish before submission.

---

### **4. Python Skeleton & Scrumban Board**
**File:** `REDROB_PYTHON_SKELETON_AND_SCRUMBAN_BOARD.md`  
**What:**
- Production-ready `rank.py` skeleton (500+ lines, copy-paste ready)
- 13-sprint Scrumban task board with:
  - Estimated time per task (1–2 hours each)
  - Clear acceptance criteria
  - Execution dependencies
- Risk mitigation strategies
- Submission strategy (when to use each of 3 submissions)

**When to Use:** 
- Copy Python skeleton → `rank.py`
- Follow Scrumban board task-by-task
- Use as checklist for progress tracking

---

## 🚀 QUICK START (Next 30 Minutes)

### **Step 1: Read Master Prompt (15 min)**
File: `REDROB_CLAUDE_CODE_MASTER_PROMPT.md`  
Focus on:
- Challenge summary (page 1)
- 4-pillar scoring framework (pages 4–10)
- Phase breakdown (pages 11–15)

### **Step 2: Inspect Data (10 min)**
Files: `/mnt/user-data/uploads/sample_candidates.json` (already in your context)  
Do:
- Look at first candidate JSON structure
- Identify key fields: profile, career_history, redrob_signals
- Note the data types (strings, floats, lists)

### **Step 3: Clone Skeleton Code (5 min)**
File: `REDROB_PYTHON_SKELETON_AND_SCRUMBAN_BOARD.md`  
Do:
- Copy the Python skeleton (full `rank.py` code)
- Create your own `rank.py` file
- Save a requirements.txt with basic deps (pandas, numpy)

### **Step 4: Execute Sprint 1**
File: `REDROB_PYTHON_SKELETON_AND_SCRUMBAN_BOARD.md` (Task Board section)  
Do:
- Load sample_candidates.json
- Run provided validator on sample_submission.csv
- Set up environment

**Total Time:** 30 minutes → ready to code.

---

## 🎯 YOUR PATH TO SUCCESS

### **Week 1: Algorithm Development (Sprints 1–9, ~12 hours)**
- [ ] Day 1: Sprints 1–3 (skills + experience engines)
- [ ] Day 2: Sprints 4–6 (years + behavioral + honeypots)
- [ ] Day 3: Sprints 7–9 (ranking + CSV export + end-to-end testing)

### **Week 2: Optimization & Submission (Sprints 10–13, ~4 hours)**
- [ ] Day 4: Sprint 10 (production run on 100K candidates)
- [ ] Day 5: Sprint 11 (documentation)
- [ ] Day 6: Sprint 12 (sandbox deployment)
- [ ] Day 7: Sprint 13 (final submission)

### **Parallel: Reference as Needed**
- Use `Technical Implementation Guide` while coding
- Use `Success Criteria & Hints` to debug quality issues
- Use `Master Prompt` to clarify ambiguities

---

## 🏆 EVALUATION CRITERIA (What You're Optimizing For)

### **Stage 1: Format ✓**
- CSV validates: 100 rows, correct header, non-increasing scores

### **Stage 2: Honeypots ✓**
- Honeypot rate in top 100 ≤ 10%

### **Stage 3: Reproducibility ✓**
- Code runs in < 5 min on CPU
- Single command: `python rank.py --candidates ./candidates.jsonl --out ./submission.csv`
- GitHub repo + sandbox working

### **Stage 4: Quality 📊**
- Top 100 candidates genuinely strong fits for Senior AI Engineer role
- Top 5 defensible (you can explain each one)
- Score distribution smooth (no sudden drops)

### **Stage 5: Interview 🎤** (If top-50)
- Can walk through scoring formula
- Understand trade-offs
- Defend design choices

---

## 💡 KEY INSIGHTS (Read Carefully)

### **Insight 1: Skill Match ≠ Just Keyword Count**
The role requires **production embeddings systems** + **vector databases** + **evaluation frameworks**. A candidate with 20 generic ML skills but 0 experience with these specific areas should rank low. **Tier-1 skills matter most.**

### **Insight 2: Honeypots Are Detection, Not Disqualification**
Don't over-engineer honeypot detection. The scoring formula should naturally penalize:
- Career timeline mismatches
- Skill inflation (many skills, few endorsements)
- Research-only backgrounds

Use simple checks; let scoring do the heavy lifting.

### **Insight 3: Behavioral Signals Are Multipliers, Not Weights**
A candidate with perfect skills but 0% response rate is still hirable (maybe they're distracted). But a candidate with 0.8 response rate should get a +0.1 boost. **Behavioral signals multiply, not override.**

### **Insight 4: 5-Minute CPU Budget Is Real**
- Loading 100K JSON: ~5 seconds
- Scoring 100K: ~150 seconds (thread pool)
- Sorting + CSV: ~10 seconds
- **Total: 165 seconds (~3 minutes) ✓**

Parallelization is mandatory. Single-threaded will timeout.

### **Insight 5: The First Submission is Free (For Learning)**
Use submission #1 to catch format errors. Don't submit your "final" ranking until you've spot-checked top 10 manually.

---

## ⚠️ CRITICAL CONSTRAINTS (Don't Violate These)

1. **No GPUs:** CPU-only ranking
2. **No Network:** No API calls during ranking (pre-compute if needed)
3. **5 Minutes:** Total runtime limit
4. **3 Submissions:** Final count; choose wisely
5. **100 Rows Exactly:** Not 99, not 101—exactly 100
6. **Non-Increasing Scores:** Must decrease (or stay same with ID tie-break)
7. **Format Exact:** Header = `candidate_id,rank,score,reasoning` (no extra columns)

---

## 🔥 RED FLAGS (Self-Check)

- ❌ Your top 3 candidates have no production experience → **Recalibrate experience scoring**
- ❌ Your honeypot rate > 10% → **Add timeline validation**
- ❌ Runtime > 5 minutes → **Reduce workers, use exact match only**
- ❌ Can't explain top 5 candidates → **Adjust weights**
- ❌ Reasoning is generic ("good candidate") → **Add specific details (title + years + signals)**

---

## 📞 WHEN TO USE EACH DOCUMENT

| Scenario | Document to Read |
|----------|-----------------|
| Starting fresh | Master Prompt (REDROB_CLAUDE_CODE_MASTER_PROMPT.md) |
| Writing scoring code | Technical Implementation Guide |
| Debugging quality issues | Success Criteria & Hints |
| Following structured workflow | Scrumban Board (PYTHON_SKELETON_AND_SCRUMBAN_BOARD.md) |
| Checking edge cases | Technical Implementation Guide (edge case section) |
| Preparing for interview | Success Criteria & Hints (interview prep section) |
| 2 hours before deadline | Success Criteria & Hints (final submission checklist) |

---

## 🎓 WHAT YOU'LL LEARN

By completing this challenge, you'll understand:

1. **Ranking Systems at Scale** → How to score 100K+ items in constrained compute environments
2. **Production ML** → Embeddings, vector databases, evaluation metrics (real tools Redrob uses)
3. **Anomaly Detection** → Identifying impossible profiles, keyword stuffers, behavioral twins
4. **System Design** → CPU parallelization, memory budgeting, runtime profiling
5. **Product Thinking** → Scoring formula as business logic (why each pillar matters)
6. **Reproducibility** → Code, dependencies, containerization (real software engineering)

---

## 🚀 READY TO START?

1. **Open** `REDROB_CLAUDE_CODE_MASTER_PROMPT.md`
2. **Read** pages 1–3 (challenge brief + JD must-haves)
3. **Copy** Python skeleton from `REDROB_PYTHON_SKELETON_AND_SCRUMBAN_BOARD.md`
4. **Execute** Sprint 1–3 following the Scrumban board
5. **Reference** Technical Implementation Guide + Success Criteria as you build

**Estimated time to first working submission:** 10–12 hours  
**Estimated time to polished submission:** 15–20 hours  

---

## 📋 FILE CHECKLIST (Everything You Have)

- ✓ `00_START_HERE_EXECUTIVE_SUMMARY.md` (you're reading this)
- ✓ `REDROB_CLAUDE_CODE_MASTER_PROMPT.md` (complete challenge brief + scoring framework)
- ✓ `REDROB_TECHNICAL_IMPLEMENTATION_GUIDE.md` (code patterns + data structures)
- ✓ `REDROB_SUCCESS_CRITERIA_AND_HINTS.md` (evaluation + polish tips)
- ✓ `REDROB_PYTHON_SKELETON_AND_SCRUMBAN_BOARD.md` (code + task board)
- ✓ Sample data files (uploaded): job_description.docx, redrob_signals_doc.docx, etc.
- ✓ Validator script: validate_submission.py (provided in bundle)

**All files are in `/mnt/user-data/outputs/` ready for download.**

---

**Let's build something great. Execute immediately. 🚀**

---

*Last Updated: June 28, 2026*  
*Challenge Complexity: Hard (Scrumban-organized, 15–20 hours)*  
*Submission Limit: 3 (final is binding)*  
*Top-50 Benefit: Interview at Redrob AI (Series A funding, real problems)*
