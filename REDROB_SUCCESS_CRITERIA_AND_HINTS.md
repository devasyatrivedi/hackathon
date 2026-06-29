# REDROB HACKATHON — QUICK REFERENCE & EVALUATION CRITERIA
## Success Signals, Top-Tier Hints & Spot-Check Strategies

---

## 🎯 EVALUATION PIPELINE (5 Stages)

### **Stage 1: Format Validation (Auto-Reject)**
**What:** Validator script checks CSV format
**Criteria:**
- ✓ Exactly 100 data rows (rows 2–101)
- ✓ Header is `candidate_id,rank,score,reasoning`
- ✓ No duplicate ranks, IDs
- ✓ Scores non-increasing with rank
- ✓ All candidate_ids exist in candidates.jsonl
- ✓ UTF-8 encoding

**Fail Rate:** ~15% of submissions (format errors)
**Your Action:** Run `validate_submission.py` locally before uploading. Fix any schema errors.

---

### **Stage 2: Honeypot Filter (Soft)**
**What:** Top 100 submission screened for impossible profiles
**Criteria:**
- Honeypot rate in top 100 ≤ 10%
- No honeypots in top 10 preferred (soft)

**Honeypot Examples:**
- "8 years of experience, company founded 3 years ago"
- "PhD in ML, 15+ years, but all 15 years are in undergraduate projects"
- "Expert in 12 skills, 0 endorsements on all"

**Your Action:** Use timeline validation + skill inflation detection. Natural scoring should catch most.

---

### **Stage 3: Code Reproducibility (Top-N Screening)**
**What:** Top submissions' code is reproduced in sandboxed Docker
**Criteria:**
- Single command produces identical CSV: `python rank.py --candidates ./candidates.jsonl --out ./submission.csv`
- Runtime < 5 minutes on CPU (Intel Xeon equivalent)
- Memory usage < 2 GB (well under 16 GB limit)
- No GPU access, no network calls during ranking
- GitHub repo matches submitted code
- Metadata matches portal submission

**Fail Rate:** ~5% of top-N (reproducibility issues)
**Your Action:**
- Test your command end-to-end before submitting
- Ensure requirements.txt is complete + pinned versions
- Verify GitHub repo is readable + has clear README

---

### **Stage 4: Ranking Quality (Scoring Metrics)**
**What:** Top candidates ranked by human + automated scoring
**Criteria:**
- Composite score correlates with hiring likelihood
- Top 10 candidates have strong production experience signals
- Skill match for embeddings/vector DB/evaluation frameworks present
- Years of experience in 5–9 band
- Behavioral signals (response rate, interview completion) favorable

**Metrics Used (Hidden):**
- Precision@10: how many of top 10 are genuinely strong fits?
- nDCG (discounted cumulative gain): are best fits ranked first?
- Mean reciprocal rank of known good candidates

**Your Action:** Spot-check top 5–10 candidates by hand. Do they match the JD? Can you defend each one?

---

### **Stage 5: Interview (Top-50 Shortlist)**
**What:** If you reach top 50, you'll be interviewed on your system
**Questions:**
- Walk me through your scoring formula. Why 0.40 for skills, 0.35 for experience?
- How did you detect honeypots? What's your honeypot rate?
- What did you try that didn't work? Why?
- If you had 3 more days, what would you change?
- How would this system scale to 1M candidates?
- Defend your top 5 candidates. Why are they ranked #1–5?

**Your Action:**
- Document your rationale (1-2 page methodology summary)
- Be prepared to explain trade-offs
- Have spot-check examples ready
- Understand your own code deeply

---

## 📊 SCORING DYNAMICS (What Actually Wins)

### **Top 1% Characteristics**
- **Skill Match:** 5–8 Tier-1 skills (embeddings + vector DB + evaluation frameworks)
- **Experience:** 6–9 years, senior or lead title, >2 years at 200+ person company
- **Production Signals:** Multiple keywords (deployment, production, users, scale) in career descriptions
- **Behavioral:** Response rate > 0.5, open to work, interview completion > 0.6
- **Red Flags:** Zero (no timeline impossibilities, no keyword stuffer patterns)

**Score Range:** 0.85–1.0

### **Top 10% Characteristics**
- **Skill Match:** 3–5 Tier-1 skills + 2–3 Tier-2 skills
- **Experience:** 5–10 years, relevant titles (Engineer, Lead, Architect)
- **Production Signals:** At least 2–3 keywords in recent roles
- **Behavioral:** Response rate > 0.3, interview completion > 0.5
- **Red Flags:** None critical (maybe one minor anomaly)

**Score Range:** 0.70–0.84

### **Top 25% Characteristics**
- **Skill Match:** 2–3 Tier-1 skills + 1–2 Tier-2 skills
- **Experience:** 4–12 years, mixed technical/leadership roles
- **Production Signals:** At least 1 keyword in career history
- **Behavioral:** Response rate > 0.1, not on "do not contact" list
- **Red Flags:** One red flag (e.g., 15+ years but only research, or keyword stuffer)

**Score Range:** 0.50–0.69

### **Ranked but Not Top 25%**
- **Skill Match:** <2 Tier-1 skills, mostly Tier-3
- **Experience:** <4 years or all in academia/competitions
- **Production Signals:** None (or contradicted by career history)
- **Behavioral:** Response rate < 0.1, not open to work
- **Red Flags:** Multiple red flags (timeline mismatch, skill inflation, etc.)

**Score Range:** 0.0–0.49

---

## 🎁 QUICK CALIBRATION CHECKLIST

### **Before You Submit, Spot-Check Your Top 5:**

**Candidate 1 (Rank 1):**
- [ ] Current title contains "Senior", "Lead", "Staff", or "Engineer"
- [ ] Years of experience: 5–9 (or exceptional 4 years)
- [ ] Profile/career mentions 3+ of: {embeddings, vector DB, FAISS, retrieval, ranking, evaluation}
- [ ] Has endorsements (≥5 for relevant skills)
- [ ] Response rate > 0.5 OR open to work flag = true
- [ ] No timeline impossibilities
- [ ] No honeypot signals

**Candidate 2–5 (Ranks 2–5):**
- [ ] At least 2 of the above checks pass
- [ ] Experience ≥ 4 years (preferably 5+)
- [ ] At least 2 Tier-1 skills + 1 Tier-2 skill
- [ ] No honeypots
- [ ] Scores ≥ 0.80

**Candidates 6–100 (Ranks 6–100):**
- [ ] Scores smoothly decrease (no sudden drops)
- [ ] No honeypots in top 100
- [ ] All candidates have ≥ 1 Tier-1 or Tier-2 skill
- [ ] No candidates from first few rows of candidates.jsonl (unless they're genuinely good)

---

## 🚩 RED FLAGS (Kill Signals)

### **Definite Disqualifiers (Score = -1.0 or near-zero)**

1. **Timeline Impossibility**
   - Years of experience: 8, but current company founded 3 years ago
   - Graduated 2020, claims 15 years of experience
   - Role start date before education end date (no gap)

2. **Skill Inflation**
   - 25 skills, all "expert" proficiency, but 0 endorsements on 20 of them
   - Multiple skills with duration < 1 month + "advanced" proficiency

3. **Honeypot Company Mismatch**
   - Claims 10-year tenure at startup founded 2 years ago
   - Career history shows 12 different jobs, each <3 months

4. **Non-Technical Current Role + No Relevant Recent Experience**
   - Current title: "Sales Manager"
   - Career history: all sales/HR (no engineering)
   - → Automatic disqualify for AI Engineer role

---

## 🎯 SPOT-CHECK STRATEGY (Manual Validation)

### **Pick 3 Random Candidates from Top 50**
1. Open candidates.jsonl, find candidate by ID
2. Check 4 criteria:
   - **Is the title relevant?** (Should mention Engineer, Senior, Lead, etc.)
   - **Do skills match?** (Should have 2+ Tier-1 skills)
   - **Is the experience real?** (Career history is coherent, no timeline issues)
   - **Are they likely to accept/interview?** (Behavioral signals positive)
3. If 3+ of 4 pass, your scoring is probably good
4. If <3 pass, investigate your formula

### **Pick 1 Honeypot (If You Can Identify One)**
1. Find an obvious honeypot in your bottom 50 (should be easy to spot)
2. Check: Is it ranked below #50? (Probably not if you did honeypot detection)
3. If it's ranked in top 50, your scoring needs work

---

## 🔧 COMMON MISTAKES (Avoid These)

### **Mistake 1: Overfitting to Sample Candidates**
- The 50 sample candidates are NOT representative
- They're just format examples
- Don't hardcode scores for them

**Fix:** Never reference candidate_id in your scoring logic. If you must handle special cases, use profile patterns (not IDs).

---

### **Mistake 2: Missing "Evaluation Frameworks" Signal**
- The JD emphasizes: "hands-on experience designing evaluation frameworks for ranking systems — NDCG, MRR, MAP"
- Many rankers miss this because it's not a single "skill name"
- You need to search for keywords: NDCG, MRR, MAP, "ranking metrics", "information retrieval", "A/B testing"

**Fix:** Make evaluation frameworks its own Tier-1 category. Search profile + career descriptions for these keywords.

---

### **Mistake 3: Not Penalizing Pure Research**
- JD disqualifier: "If you've spent your career in pure research environments...without production deployment"
- Many candidates have PhDs + only Kaggle/academic projects
- But they get high skill scores because they have lots of ML skills

**Fix:** Check career history for "Research", "Academic", "Lab" titles. If all roles are research + total production experience < 24 months, reduce score by 50%.

---

### **Mistake 4: Ignoring "Recent LangChain Wrapper" Warning**
- JD disqualifier: "If your 'AI experience' consists primarily of recent (under 12 months) projects using LangChain to call OpenAI"
- Many candidates have recent LLM skills but only via simple API wrappers
- Hard to detect automatically, but look for: recent_date + "LangChain" + no fine-tuning/vector DB experience

**Fix:** If a candidate has "LLM" skills only from last 6 months, and no other Tier-1 skills, mark as suspicious.

---

### **Mistake 5: Not Scaling Runtime**
- 100K candidates * 5ms per candidate = 500 seconds (too slow)
- Threading alone won't help if your score function is O(n²)
- Most common bottleneck: fuzzy matching or regex search on every candidate

**Fix:**
- Use exact match for skills (not regex)
- Pre-compile regex patterns before loop
- Use thread pool with 4–8 workers (don't spawn per candidate)
- Target <1ms per candidate

---

### **Mistake 6: Not Handling Missing Fields**
- Some candidates might have null/empty fields
- If your code assumes `candidate["profile"]["headline"]` exists, it will crash

**Fix:** Use `.get()` with defaults everywhere. Example:
```python
headline = candidate.get("profile", {}).get("headline", "")
```

---

## 📈 OPTIMIZATION TACTICS (If You're Close to Time Limit)

### **Quick Wins (5–10 minutes each)**
1. **Boost Tier-1 Skill Weight:** Increase from 0.40 to 0.45 (prioritize direct JD match)
2. **Add "GitHub Activity" Signal:** If `github_activity_score` ≥ 8, +0.05 to final score
3. **Penalize Long Response Time:** If `avg_response_time_hours` > 336, reduce by 0.10
4. **Promote Recent Role Relevance:** If current title matches JD better than past titles, boost by 0.05

### **Medium Effort (30–60 minutes)**
1. **Implement Skill Endorsement Ratio:** Favor high-endorsement skills over low-endorsement ones
2. **Add Career Stability Score:** Penalize >5 jobs in 5 years (high churn = risk)
3. **Cross-Validate with Sample:** Manually score top 10 from sample_candidates.json, compare with your algo
4. **A/B Test Weights:** Try [0.45, 0.30, 0.15, ×mult] vs [0.40, 0.35, 0.15, ×mult], see which feels better

### **High Effort (2+ hours)**
1. **Implement Skill Clustering:** Group similar skills (e.g., "Pinecone" + "Weaviate" + "Qdrant" all count as "vector DB")
2. **Add Company Ranking Tier:** Large tech (Google, Meta, Microsoft) +0.05; startups neutral; consulting -0.05
3. **Implement Role Evolution Scoring:** Detect if candidate is progressing toward AI/ML roles
4. **Build Feedback Loop:** Score 1K candidates, spot-check top 50, adjust weights, rescore, repeat

---

## 📋 SUBMISSION CHECKLIST (Final)

### **Code & Repo (2 hours before deadline)**
- [ ] `rank.py` works end-to-end: `python rank.py --candidates ./candidates.jsonl --out ./submission.csv`
- [ ] Tested on full 100K dataset (in <5 minutes)
- [ ] GitHub repo is public or private with access granted
- [ ] `requirements.txt` is complete + pinned versions
- [ ] `README.md` has clear setup + reproduce instructions
- [ ] `submission_metadata.yaml` filled out correctly
- [ ] No hard-coded paths or environment-specific code

### **CSV Output (1 hour before deadline)**
- [ ] CSV file: `team_<id>.csv`
- [ ] Run validator: `python validate_submission.py team_<id>.csv` → "Submission is valid."
- [ ] Spot-check top 10 candidates (do they make sense?)
- [ ] Spot-check for honeypots in top 100 (roughly count red flags)
- [ ] CSV is UTF-8 encoded

### **Portal Submission (30 min before deadline)**
- [ ] Team name filled in
- [ ] Primary contact email + phone
- [ ] All team members listed
- [ ] GitHub repo URL (accessible)
- [ ] Sandbox link (HuggingFace Spaces / Streamlit / Colab) tested + working
- [ ] Reproduce command: `python rank.py --candidates ./candidates.jsonl --out ./submission.csv`
- [ ] AI tools declared (be honest)
- [ ] Methodology summary written (100–200 words)
- [ ] All declarations checked (read specs, original work, no collusion, reproduction tested)

### **Backup (At Submission)**
- [ ] Keep local copy of CSV + metadata
- [ ] Screenshot of validator output showing "Submission is valid"
- [ ] Note exact submission timestamp
- [ ] Save sandbox link

---

## 🏆 AIMING FOR TOP-50 (Interview Prep)

### **If You Make Top 50, You'll Be Asked:**

1. **"Walk me through your scoring algorithm."**
   - Have the 4-pillar breakdown memorized
   - Explain why each weight (0.40, 0.35, 0.15)
   - Be ready to defend if questioned

2. **"How did you handle honeypots?"**
   - Describe 2–3 detection patterns (timeline, skill inflation, company mismatch)
   - Show code snippet if you have it
   - Explain why you didn't over-engineer it

3. **"Pick your top 5 candidates. Defend them."**
   - Have 5 candidates selected + reasoning memorized
   - Explain why they beat everyone else
   - Be ready if they challenge one of your picks

4. **"What's one thing you'd change?"**
   - Show you thought about this
   - Don't say "nothing"; that's a red flag
   - Example: "I'd add company-size ranking tier" or "I'd implement skill clustering"

5. **"How would you scale this to 1M candidates or 1K job descriptions?"**
   - Think about: vectorization, caching, batch processing, distributed compute
   - Show you understand production constraints

---

## 🎓 LEARNING FROM YOUR SUBMISSION

### **After You Submit, Ask Yourself:**
1. Was your top candidate actually the best? (You'll know after results)
2. What was your honeypot rate? (Stage 3 will reveal)
3. Did your reasoning resonate? (Interview feedback if you make top-50)
4. What score gaps exist in top 100? (0.95 → 0.85 → 0.45?) ← Should be smooth
5. How many candidates scored >0.80 vs 0.50-0.80 vs <0.50? ← Should be distributed

---

**You've got this. Submit with confidence. 🚀**
