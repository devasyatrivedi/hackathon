# REDROB HACKATHON — PYTHON SKELETON CODE
## Ready-to-Use Foundation + Scrumban Task Board

---

## 🚀 SKELETON CODE (rank.py)

```python
#!/usr/bin/env python3
"""
Redrob Hackathon - Senior AI Engineer Candidate Ranking System
Produces top-100 ranked CSV from 100K candidate pool.

Usage:
  python rank.py --candidates ./candidates.jsonl.gz --out ./submission.csv
  python rank.py --candidates ./candidates.jsonl --out ./submission.csv
"""

import argparse
import csv
import gzip
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

TIER_1_SKILLS = {
    # Embeddings frameworks
    "faiss", "sentence-transformers", "sbert", "bge", "e5", "clip",
    "openai embeddings", "word2vec", "glove",
    # Vector databases
    "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch",
    "vespa", "chroma",
    # Evaluation frameworks
    "ndcg", "mrr", "map", "ranking metrics", "information retrieval",
    # Core language
    "python", "c++",
}

TIER_2_SKILLS = {
    # LLM fine-tuning
    "lora", "qlora", "peft", "huggingface", "transformers", "fine-tuning",
    # Learning-to-rank
    "xgboost", "lambdamart", "ranknet", "neural ranking",
    # ML ops
    "mlflow", "weights & biases", "wandb", "dvc", "experiment tracking",
    # Distributed systems
    "apache spark", "spark", "pyspark", "apache airflow", "airflow", "apache kafka", "kafka",
}

TIER_3_SKILLS = {
    # Cloud
    "aws", "google cloud", "gcp", "azure",
    # Databases
    "sql", "snowflake", "bigquery", "postgres", "postgresql", "mysql",
    # General ML
    "machine learning", "deep learning", "scikit-learn", "pytorch", "tensorflow", "keras",
    # Infrastructure
    "docker", "kubernetes", "k8s", "rest api", "api design",
}

PRODUCTION_KEYWORDS = {
    "production", "deployment", "deployed", "ship", "shipped", "users",
    "scale", "scaling", "system", "systems", "pipeline", "infrastructure",
    "real-time", "latency", "performance", "database", "warehouse",
}

RESEARCH_ONLY_PATTERNS = {"research", "academic", "kaggle", "competition", "side project"}

SENIORITY_KEYWORDS = {"senior", "lead", "staff", "principal", "director"}

NON_TECH_TITLES = {"sales", "hr", "finance", "marketing", "recruiter", "business"}

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ScoredCandidate:
    candidate_id: str
    score: float
    reasoning: str

# ============================================================================
# SCORING FUNCTIONS (PILLAR 1: SKILLS)
# ============================================================================

def extract_skills(candidate: Dict) -> Dict[str, int]:
    """Extract and categorize skills from candidate profile."""
    skills_data = candidate.get("skills", [])
    categorized = {"tier1": 0, "tier2": 0, "tier3": 0, "endorsements": 0}
    
    for skill in skills_data:
        name = skill.get("name", "").lower().strip()
        endorsements = skill.get("endorsements", 0)
        
        if name in TIER_1_SKILLS:
            categorized["tier1"] += 1
            categorized["endorsements"] += endorsements
        elif name in TIER_2_SKILLS:
            categorized["tier2"] += 1
            categorized["endorsements"] += endorsements
        elif name in TIER_3_SKILLS:
            categorized["tier3"] += 1
    
    return categorized

def detect_skill_inflation(candidate: Dict) -> bool:
    """Detect keyword stuffing or skill inflation."""
    skills_data = candidate.get("skills", [])
    
    if len(skills_data) > 15:
        avg_endorsements = sum(s.get("endorsements", 0) for s in skills_data) / len(skills_data)
        if avg_endorsements < 3:
            return True  # Keyword stuffer
    
    # Check for many "advanced" proficiency with 0 endorsements
    expert_no_endorsement = sum(
        1 for s in skills_data
        if s.get("proficiency", "").lower() == "advanced" and s.get("endorsements", 0) == 0
    )
    if expert_no_endorsement >= 3:
        return True
    
    return False

def calculate_skill_score(candidate: Dict) -> float:
    """Calculate Pillar 1: Skill Relevance Match (40%)."""
    categorized = extract_skills(candidate)
    
    # Base score from skill counts
    tier1_score = min(categorized["tier1"], 8) * 0.05  # Max 0.40
    tier2_score = min(categorized["tier2"], 8) * 0.03125  # Max 0.25
    tier3_score = min(categorized["tier3"], 8) * 0.0125  # Max 0.10
    
    endorsement_bonus = min(categorized["endorsements"] / 100.0, 0.05)
    
    base_score = tier1_score + tier2_score + tier3_score + endorsement_bonus
    normalized_score = min(base_score / 0.80, 1.0)
    
    # Penalties
    if detect_skill_inflation(candidate):
        normalized_score *= 0.70
    
    return normalized_score

# ============================================================================
# SCORING FUNCTIONS (PILLAR 2: PRODUCTION EXPERIENCE)
# ============================================================================

def detect_timeline_honeypot(candidate: Dict) -> bool:
    """Detect impossible timeline (e.g., working before graduation)."""
    career = candidate.get("career_history", [])
    education = candidate.get("education", [])
    
    if not education:
        return False
    
    edu_end_years = [e.get("end_year", 2025) for e in education]
    earliest_grad_year = min(edu_end_years)
    
    for entry in career:
        start_date = entry.get("start_date", "")
        if start_date:
            try:
                start_year = int(start_date.split("-")[0])
                if start_year < earliest_grad_year - 1:  # Allow 1-year gap
                    return True
            except (ValueError, IndexError):
                pass
    
    return False

def extract_production_signals(candidate: Dict) -> int:
    """Count production-related keywords in profile and career history."""
    profile = candidate.get("profile", {})
    summary = profile.get("summary", "").lower()
    career = candidate.get("career_history", [])
    
    count = 0
    for keyword in PRODUCTION_KEYWORDS:
        if keyword in summary:
            count += 1
    
    for entry in career:
        desc = entry.get("description", "").lower()
        for keyword in PRODUCTION_KEYWORDS:
            if keyword in desc:
                count += 1
    
    return min(count, 10)

def calculate_experience_score(candidate: Dict) -> float:
    """Calculate Pillar 2: Production Experience Validation (35%)."""
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    
    # Current role must be technical
    current_title = profile.get("current_title", "").lower()
    if any(word in current_title for word in NON_TECH_TITLES):
        return 0.0
    
    if not career:
        return 0.0
    
    score = 0.0
    relevant_roles = 0
    
    for entry in career:
        title = entry.get("title", "").lower()
        duration = entry.get("duration_months", 0)
        company_size = entry.get("company_size", "")
        description = entry.get("description", "").lower()
        
        # Role type scoring
        if any(x in title for x in ["engineer", "architect", "tech lead"]):
            score += 0.20
            relevant_roles += 1
        elif any(x in title for x in RESEARCH_ONLY_PATTERNS):
            if duration < 24:
                continue
            score += 0.05
        else:
            score += 0.05
        
        # Duration signal
        if duration >= 24:
            score += 0.10
        else:
            score += (duration / 24.0) * 0.10 if duration > 0 else 0
        
        # Company size signal
        if company_size in ["10001+", "5001-10000", "1001-5000"]:
            score += 0.10
        elif company_size in ["201-500", "501-1000"]:
            score += 0.05
        
        # Production keywords
        prod_count = extract_production_signals({"profile": {}, "career_history": [entry]})
        score += min(prod_count * 0.02, 0.10)
    
    normalized_score = min(score / 1.0, 1.0)
    
    if relevant_roles == 0:
        normalized_score *= 0.3
    
    return normalized_score

# ============================================================================
# SCORING FUNCTIONS (PILLAR 3: EXPERIENCE YEARS)
# ============================================================================

def calculate_yoe_score(candidate: Dict) -> float:
    """Calculate Pillar 3: Experience Years + Seniority (15%)."""
    profile = candidate.get("profile", {})
    yoe = profile.get("years_of_experience", 0)
    
    # Years scoring
    if yoe < 3:
        years_score = (yoe / 3.0) * 0.5
    elif 3 <= yoe <= 9:
        years_score = 1.0
    elif 9 < yoe <= 15:
        years_score = 1.0 - ((yoe - 9) / 6.0) * 0.1
    else:
        years_score = 0.85
    
    # Seniority bonuses
    current_title = profile.get("current_title", "").lower()
    if "senior" in current_title:
        years_score += 0.10
    if "lead" in current_title or "tech lead" in current_title:
        years_score += 0.05
    
    return min(years_score, 1.0)

# ============================================================================
# SCORING FUNCTIONS (PILLAR 4: BEHAVIORAL SIGNALS)
# ============================================================================

def calculate_behavioral_multiplier(candidate: Dict) -> float:
    """Calculate Pillar 4: Behavioral Multiplier (applies to all)."""
    signals = candidate.get("redrob_signals", {})
    
    # Components
    response_rate = signals.get("recruiter_response_rate", 0.0) * 0.25
    open_to_work = (1.0 if signals.get("open_to_work_flag", False) else 0.0) * 0.20
    interview_rate = signals.get("interview_completion_rate", 0.0) * 0.20
    offer_rate = signals.get("offer_acceptance_rate", 0.0) * 0.15
    verified = (1.0 if (signals.get("verified_email", False) and signals.get("verified_phone", False)) else 0.0) * 0.10
    relocate = (1.0 if signals.get("willing_to_relocate", False) else 0.0) * 0.05
    notice_days = signals.get("notice_period_days", 60)
    notice = (0.05 if 30 <= notice_days <= 90 else 0.0)
    
    base_multiplier = response_rate + open_to_work + interview_rate + offer_rate + verified + relocate + notice
    
    # Penalties & bonuses
    avg_response_time = signals.get("avg_response_time_hours", 0.0)
    if avg_response_time > 336:
        base_multiplier -= 0.10
    
    github_score = signals.get("github_activity_score", 0.0)
    if github_score >= 8.0:
        base_multiplier += 0.05
    
    # Clamp
    return max(0.7, min(base_multiplier, 1.2))

# ============================================================================
# COMPOSITE SCORING
# ============================================================================

def calculate_final_score(candidate: Dict) -> float:
    """Calculate composite final score."""
    # Honeypot filter
    if detect_timeline_honeypot(candidate):
        return -1.0
    
    # Pillar scores
    skill_score = calculate_skill_score(candidate)
    exp_score = calculate_experience_score(candidate)
    yoe_score = calculate_yoe_score(candidate)
    
    # Composite
    composite = (
        skill_score * 0.40 +
        exp_score * 0.35 +
        yoe_score * 0.15
    )
    
    # Behavioral multiplier
    behav_mult = calculate_behavioral_multiplier(candidate)
    
    # Final
    final = composite * behav_mult
    
    return max(0.0, min(final, 1.0))

# ============================================================================
# REASONING GENERATION
# ============================================================================

def generate_reasoning(candidate: Dict, score: float) -> str:
    """Generate 1-2 sentence reasoning."""
    profile = candidate.get("profile", {})
    current_title = profile.get("current_title", "")
    yoe = profile.get("years_of_experience", 0)
    
    signals = candidate.get("redrob_signals", {})
    response_rate = signals.get("recruiter_response_rate", 0.0)
    
    skills_data = candidate.get("skills", [])
    tier1_count = sum(1 for s in skills_data if s.get("name", "").lower() in TIER_1_SKILLS)
    
    reason = f"{current_title} with {yoe:.1f} yrs; {tier1_count} core skills; response rate {response_rate:.2f}."
    
    if score >= 0.85:
        reason += " Strong production experience."
    elif score <= 0.40:
        reason += " Limited relevant experience."
    
    return reason[:150]

# ============================================================================
# MAIN RANKING PIPELINE
# ============================================================================

def load_candidates(candidates_path: str) -> List[Dict]:
    """Load candidates from JSONL or gzipped JSONL."""
    candidates = []
    
    if candidates_path.endswith('.gz'):
        with gzip.open(candidates_path, 'rt', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        candidates.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    else:
        with open(candidates_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        candidates.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    
    return candidates

def score_single_candidate(candidate: Dict) -> Tuple[str, float, str]:
    """Score a single candidate. Called by thread pool."""
    candidate_id = candidate.get("candidate_id", "")
    score = calculate_final_score(candidate)
    reasoning = generate_reasoning(candidate, score)
    return candidate_id, score, reasoning

def rank_candidates(candidates: List[Dict]) -> List[ScoredCandidate]:
    """Score all candidates in parallel."""
    results = []
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(score_single_candidate, c): c.get("candidate_id", "")
            for c in candidates
        }
        
        for i, future in enumerate(as_completed(futures)):
            if i % 10000 == 0:
                print(f"Scored {i}/{len(candidates)}")
            
            candidate_id, score, reasoning = future.result()
            results.append(ScoredCandidate(candidate_id, score, reasoning))
    
    return results

def export_csv(scored: List[ScoredCandidate], output_path: str, top_n: int = 100):
    """Export top-N candidates to CSV."""
    # Sort by score descending, then by ID ascending (tie-breaker)
    scored.sort(key=lambda x: (-x.score, x.candidate_id))
    
    # Select top N
    top = scored[:top_n]
    
    # Assign ranks
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['candidate_id', 'rank', 'score', 'reasoning'])
        
        for rank, sc in enumerate(top, 1):
            writer.writerow([sc.candidate_id, rank, f"{sc.score:.4f}", sc.reasoning])
    
    print(f"Exported {top_n} candidates to {output_path}")

# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Rank candidates for Redrob hackathon")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl or candidates.jsonl.gz")
    parser.add_argument("--out", required=True, help="Output CSV path")
    
    args = parser.parse_args()
    
    print(f"Loading candidates from {args.candidates}...")
    candidates = load_candidates(args.candidates)
    print(f"Loaded {len(candidates)} candidates")
    
    print("Scoring candidates...")
    scored = rank_candidates(candidates)
    
    print("Exporting CSV...")
    export_csv(scored, args.out)
    
    print("Done!")

if __name__ == "__main__":
    main()
```

---

## 📋 SCRUMBAN TASK BOARD (Immediate Execution)

### **BACKLOG → IN PROGRESS → DONE**

```
SPRINT 1: Foundation & Testing (Est. 1–2 hours)
═══════════════════════════════════════════════════════════

[ ] Task 1.1: Load & inspect sample_candidates.json
    Subtask: Extract first candidate JSON, print keys
    Subtask: Count total candidates (should be 50)
    Owner: You
    Time: 10 min
    Acceptance: Can see full JSON structure, understand nesting

[ ] Task 1.2: Run validator on sample_submission.csv
    Subtask: Execute: python validate_submission.py sample_submission.csv
    Subtask: Read output, understand format expectations
    Owner: You
    Time: 5 min
    Acceptance: Validator runs without error, prints "valid" or lists issues

[ ] Task 1.3: Set up Python environment
    Subtask: Create requirements.txt with pandas, numpy
    Subtask: Create rank.py skeleton file
    Owner: You
    Time: 10 min
    Acceptance: Can run: python rank.py --candidates sample.json --out test.csv


SPRINT 2: Skill Matching Engine (Est. 2–3 hours)
═══════════════════════════════════════════════════════════

[ ] Task 2.1: Define Tier-1/2/3 skill lists
    Subtask: Read job_description.docx "Skills Inventory" section
    Subtask: Define TIER_1_EXACT set (8+ skills minimum)
    Subtask: Define TIER_2_SKILLS set
    Subtask: Define TIER_3_SKILLS set
    Owner: You
    Time: 30 min
    Acceptance: Can cite 5 examples for each tier from JD

[ ] Task 2.2: Implement skill extraction function
    Subtask: Write extract_skills(candidate) function
    Subtask: Return {tier1_count, tier2_count, tier3_count, endorsements}
    Subtask: Test on 5 sample candidates
    Owner: You
    Time: 30 min
    Acceptance: Function returns correct counts for test candidates

[ ] Task 2.3: Implement skill inflation detection
    Subtask: Write detect_skill_inflation(candidate) function
    Subtask: Check: >15 skills + low avg endorsements
    Subtask: Check: multiple "advanced" with 0 endorsements
    Owner: You
    Time: 20 min
    Acceptance: Function correctly identifies keyword stuffers in sample

[ ] Task 2.4: Implement calculate_skill_score()
    Subtask: Combine tier scores with weights
    Subtask: Add endorsement bonus
    Subtask: Apply inflation penalty
    Subtask: Test on sample candidates
    Owner: You
    Time: 30 min
    Acceptance: Scores normalize to [0, 1], top candidates have high scores


SPRINT 3: Production Experience Engine (Est. 2–3 hours)
═══════════════════════════════════════════════════════════

[ ] Task 3.1: Extract production keywords & patterns
    Subtask: Define PRODUCTION_KEYWORDS set
    Subtask: Define role type patterns (engineer, research, etc.)
    Owner: You
    Time: 20 min
    Acceptance: Can manually check 3 career entries against patterns

[ ] Task 3.2: Implement timeline honeypot detection
    Subtask: Write detect_timeline_honeypot(candidate) function
    Subtask: Check: start_date before education end_year
    Subtask: Test on sample candidates
    Owner: You
    Time: 20 min
    Acceptance: Function catches obvious timeline mismatches

[ ] Task 3.3: Implement production signal extraction
    Subtask: Write extract_production_signals(candidate) function
    Subtask: Count keywords in profile + career descriptions
    Owner: You
    Time: 20 min
    Acceptance: Function scores production signals 0–10

[ ] Task 3.4: Implement calculate_experience_score()
    Subtask: Check current role is technical
    Subtask: Score role types (engineer > manager > research)
    Subtask: Score company size + duration
    Subtask: Add production keyword bonus
    Subtask: Test on sample candidates
    Owner: You
    Time: 40 min
    Acceptance: Scores normalize to [0, 1], match intuition


SPRINT 4: Years & Seniority Engine (Est. 1–2 hours)
═══════════════════════════════════════════════════════════

[ ] Task 4.1: Implement calculate_yoe_score()
    Subtask: Score [0-3), [3-9], (9-15], 15+ bands
    Subtask: Add seniority bonuses (Senior, Lead, Staff)
    Subtask: Check for promotion in career history
    Subtask: Test on sample candidates
    Owner: You
    Time: 30 min
    Acceptance: Scores [0, 1], mid-career candidates score high


SPRINT 5: Behavioral Signals Engine (Est. 1.5–2 hours)
═══════════════════════════════════════════════════════════

[ ] Task 5.1: Implement calculate_behavioral_multiplier()
    Subtask: Extract 7 key signals from redrob_signals
    Subtask: Weight each (0.25, 0.20, 0.20, 0.15, 0.10, 0.05, 0.05)
    Subtask: Apply penalties (response time > 336 hours: -0.10)
    Subtask: Apply bonuses (github_activity >= 8.0: +0.05)
    Subtask: Clamp to [0.7, 1.2]
    Subtask: Test on sample candidates
    Owner: You
    Time: 45 min
    Acceptance: Multiplier correctly boosts/reduces scores


SPRINT 6: Composite & Honeypots (Est. 1–2 hours)
═══════════════════════════════════════════════════════════

[ ] Task 6.1: Implement calculate_final_score()
    Subtask: Combine 4 pillars: skill (0.40) + exp (0.35) + yoe (0.15) × mult
    Subtask: Apply honeypot filter (-1.0 for impossible profiles)
    Subtask: Test on sample candidates
    Owner: You
    Time: 30 min
    Acceptance: Final scores [0, 1], honeypots score negative

[ ] Task 6.2: Implement honeypot detection
    Subtask: Implement experience inflation check
    Subtask: Combine timeline + inflation + company checks
    Owner: You
    Time: 20 min
    Acceptance: Catches 2+ types of honeypots


SPRINT 7: Ranking & Export (Est. 1–2 hours)
═══════════════════════════════════════════════════════════

[ ] Task 7.1: Implement reasoning generation
    Subtask: Write generate_reasoning(candidate, score) function
    Subtask: Extract: title, years, skill count, response rate
    Subtask: Format 1–2 sentences, <150 chars
    Owner: You
    Time: 20 min
    Acceptance: Reasoning is human-readable, makes sense

[ ] Task 7.2: Implement sorting & tie-breaking
    Subtask: Sort by score descending
    Subtask: Break ties by candidate_id ascending
    Subtask: Assign ranks 1–100
    Owner: You
    Time: 15 min
    Acceptance: No duplicate ranks, no missing IDs

[ ] Task 7.3: Implement CSV export
    Subtask: Write export_csv(scored, output_path) function
    Subtask: Export header + 100 rows
    Subtask: Test on sample candidates
    Owner: You
    Time: 15 min
    Acceptance: CSV validates with validate_submission.py


SPRINT 8: Scaling & Performance (Est. 1–2 hours)
═══════════════════════════════════════════════════════════

[ ] Task 8.1: Implement parallel scoring with ThreadPoolExecutor
    Subtask: Write load_candidates() function
    Subtask: Handle gzipped + uncompressed JSONL
    Owner: You
    Time: 20 min
    Acceptance: Can load 100K candidates in <10 seconds

[ ] Task 8.2: Implement thread pool scoring
    Subtask: Create ThreadPoolExecutor(max_workers=6)
    Subtask: Submit score_single_candidate() for each candidate
    Subtask: Collect results with as_completed()
    Subtask: Print progress every 10K
    Owner: You
    Time: 30 min
    Acceptance: Scores 100K in <3 min on single machine

[ ] Task 8.3: Profile & optimize runtime
    Subtask: Time each scoring phase (skills, exp, yoe, behav)
    Subtask: Target: <1ms per candidate
    Subtask: Check memory usage
    Owner: You
    Time: 30 min
    Acceptance: Total runtime <5 minutes for 100K


SPRINT 9: End-to-End Integration (Est. 1–2 hours)
═══════════════════════════════════════════════════════════

[ ] Task 9.1: Test full pipeline on sample_candidates.json
    Subtask: Execute: python rank.py --candidates sample_candidates.json --out test.csv
    Subtask: Verify output CSV validates
    Subtask: Spot-check top 5 candidates (make sense?)
    Owner: You
    Time: 30 min
    Acceptance: CSV valid, top 5 are coherent choices

[ ] Task 9.2: Validate with provided validator
    Subtask: Run: python validate_submission.py test.csv
    Subtask: Fix any format errors
    Owner: You
    Time: 20 min
    Acceptance: Validator says "valid"

[ ] Task 9.3: Test on subset of full dataset
    Subtask: Extract first 1K candidates from candidates.jsonl
    Subtask: Run ranking, verify in <30 seconds
    Owner: You
    Time: 20 min
    Acceptance: Performance matches projections


SPRINT 10: Production Deployment (Est. 1–2 hours)
═══════════════════════════════════════════════════════════

[ ] Task 10.1: Run on full 100K dataset
    Subtask: Execute: python rank.py --candidates ./candidates.jsonl.gz --out submission.csv
    Subtask: Time the run (should be <5 min)
    Subtask: Check output file size (~5-10 KB for CSV)
    Owner: You
    Time: 10 min (actual run) + monitoring
    Acceptance: CSV produced in <5 min, validates

[ ] Task 10.2: Spot-check submission
    Subtask: Open submission.csv, visually inspect top 10 rows
    Subtask: Check scores decrease smoothly
    Subtask: Check for honeypots in top 100 (roughly)
    Owner: You
    Time: 20 min
    Acceptance: Top 10 make intuitive sense, no obvious bad choices


SPRINT 11: Documentation (Est. 1–2 hours)
═══════════════════════════════════════════════════════════

[ ] Task 11.1: Write README.md
    Subtask: Setup instructions (pip install -r requirements.txt)
    Subtask: Reproduce command
    Subtask: Brief methodology summary (50–100 words)
    Owner: You
    Time: 30 min
    Acceptance: README clear enough for someone else to follow

[ ] Task 11.2: Write requirements.txt with pinned versions
    Subtask: List all dependencies with versions
    Owner: You
    Time: 10 min
    Acceptance: Can install: pip install -r requirements.txt

[ ] Task 11.3: Fill submission_metadata.yaml
    Subtask: Copy template
    Subtask: Fill team info, GitHub repo, sandbox link, methodology
    Owner: You
    Time: 20 min
    Acceptance: All required fields filled


SPRINT 12: Sandbox Deployment (Est. 2–3 hours)
═══════════════════════════════════════════════════════════

[ ] Task 12.1: Deploy to HuggingFace Spaces
    Subtask: Create account if needed
    Subtask: Create new Space (Streamlit or Docker)
    Subtask: Upload code + requirements.txt
    Owner: You
    Time: 30 min
    Acceptance: Space is public, can be accessed

[ ] Task 12.2: Test sandbox on small sample
    Subtask: Upload 100–500 sample candidates
    Subtask: Run ranking via sandbox UI
    Subtask: Verify CSV output
    Owner: You
    Time: 30 min
    Acceptance: Sandbox produces valid CSV on sample


SPRINT 13: Final Submission (Est. 30 min)
═══════════════════════════════════════════════════════════

[ ] Task 13.1: Double-check CSV
    Subtask: Run validator one final time
    Subtask: Spot-check top 10 (manual review)
    Owner: You
    Time: 10 min
    Acceptance: Validator passes, top 10 defensible

[ ] Task 13.2: Submit via portal
    Subtask: Gather all required fields (team name, emails, GitHub, sandbox)
    Subtask: Upload CSV
    Subtask: Fill metadata
    Subtask: Submit
    Owner: You
    Time: 20 min
    Acceptance: Confirmation email received

[ ] Task 13.3: Archive locally
    Subtask: Save copy of CSV + metadata + GitHub link
    Subtask: Screenshot validator output
    Owner: You
    Time: 5 min
    Acceptance: Backup copies secured
```

---

## 🏁 EXECUTION GUIDELINES

### **Timing**
- **Total Estimated Time:** 15–20 hours (spread over 3–7 days)
- **Critical Path:** Sprints 1–8 (scoring algorithm)
- **Can Be Paralleled:** Sprints 2–5 (independent pillar implementations)
- **Blocking:** Sprint 10 (must run on full dataset before submitting)

### **Quality Checkpoints**
1. **After Sprint 5:** Each pillar should independently score test candidates reasonably
2. **After Sprint 6:** Composite score should range [0, 1] with intuitive ordering
3. **After Sprint 9:** Full pipeline runs, output validates
4. **After Sprint 10:** Production run completes in <5 minutes

### **Risk Mitigation**
- **If runtime > 5 min:** Profile bottleneck, reduce thread workers to 4, use exact match only (no fuzzy)
- **If quality seems off:** Spot-check top 10 manually. Adjust pillar weights if needed.
- **If honeypot rate > 10%:** Add stricter timeline checks or skill inflation penalties.

### **Submission Strategy**
1. **Submission 1:** Use as dry-run; submit early to catch format errors (day 1–2)
2. **Submission 2:** After optimizing weights based on spot-checks (day 5)
3. **Submission 3:** Final polish; submit day before deadline (day 6–7)

---

**Ready to execute. Start with Sprint 1 immediately. 🚀**
