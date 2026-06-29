# REDROB HACKATHON — TECHNICAL IMPLEMENTATION GUIDE
## Deep Dive: Data Structures, Edge Cases & Code Patterns

---

## 📊 CANDIDATE DATA STRUCTURE (Complete Reference)

### **Root Object**
```python
@dataclass
class Candidate:
    candidate_id: str                    # CAND_0000001 to CAND_0100000
    profile: Profile
    career_history: List[CareerEntry]
    education: List[EducationEntry]
    skills: List[Skill]
    certifications: List[str]            # Usually empty
    languages: List[Language]
    redrob_signals: BehavioralSignals
```

### **Profile Substructure**
```python
@dataclass
class Profile:
    anonymized_name: str                 # "Ira Vora", "Kumar Patel", etc.
    headline: str                        # "Backend Engineer | SQL, Spark, Cloud"
    summary: str                         # Long-form (~200-500 chars) profile text
    location: str                        # City (e.g., "Toronto", "Bangalore")
    country: str                         # "Canada", "India", "USA"
    years_of_experience: float           # 6.9, 8.2, etc.
    current_title: str                   # "Backend Engineer", "Senior ML Engineer"
    current_company: str                 # "Mindtree", "Google", "Startup"
    current_company_size: str            # "10001+", "501-1000", "11-50", etc.
    current_industry: str                # "IT Services", "Software", "Finance"

# Key extraction patterns:
# - years_of_experience: primary age signal (CRITICAL for scoring)
# - current_title: seniority signal ("Senior", "Lead", "Staff")
# - current_company_size: proxy for production experience
```

### **Career History Substructure**
```python
@dataclass
class CareerEntry:
    company: str
    title: str
    start_date: str                      # "2024-03-08" (ISO format)
    end_date: Optional[str]              # null if current role
    duration_months: int                 # Calculated duration (important!)
    is_current: bool
    industry: str
    company_size: str
    description: str                     # 100-300 chars; product/tech details

# Key extraction patterns:
# - Honeypot check: end_date < education[0].end_year?
# - Production signal: "pipeline", "production", "deployment", "users"
# - Role seniority: "Engineer" vs "Lead" vs "Manager" vs "Intern"
```

### **Education Substructure**
```python
@dataclass
class EducationEntry:
    institution: str
    degree: str                          # "B.E.", "B.Tech", "M.S.", "PhD"
    field_of_study: str                  # "Computer Science", "Physics", etc.
    start_year: int                      # 2017
    end_year: int                        # 2020
    grade: Optional[str]                 # "8.24 CGPA", "3.8 GPA", or null
    tier: str                            # "tier_1", "tier_2", "tier_3"

# Key extraction patterns:
# - Education end_year: youngest graduation year (for timeline validation)
# - Tier: modifier on overall score (+0.05 for tier_1, +0.02 for tier_2, etc.)
# - Degree: "PhD" in CS ≠ research-only (check career history too)
```

### **Skills Substructure**
```python
@dataclass
class Skill:
    name: str                            # "Python", "FAISS", "NLP", "LoRA"
    proficiency: str                     # "beginner", "intermediate", "advanced"
    endorsements: int                    # 0, 3, 37, 52 (endorsement count)
    duration_months: int                 # 8, 28, 36, 60 (how long using skill)

# Key extraction patterns:
# - name: exact match to Tier-1/2/3 skill lists (case-insensitive)
# - proficiency: "advanced" is strong signal (but check endorsements for honeypots)
# - endorsements: if "expert" proficiency but 0 endorsements, suspicious
# - duration_months: if skill proficiency="expert" but duration < 3 months, anomaly
```

### **Behavioral Signals Substructure**
```python
@dataclass
class BehavioralSignals:
    profile_completeness_score: float    # 86.9 (out of 100)
    signup_date: str                     # "2025-10-16"
    last_active_date: str                # "2026-05-20"
    open_to_work_flag: bool              # true/false
    profile_views_received_30d: int      # 23
    applications_submitted_30d: int      # 2
    recruiter_response_rate: float       # 0.34 (0.0 to 1.0)
    avg_response_time_hours: float       # 177.8
    skill_assessment_scores: Dict[str, float]  # {"NLP": 38.8, "Fine-tuning LLMs": 41.6}
    connection_count: int                # 356
    endorsements_received: int           # 35
    notice_period_days: int              # 60
    expected_salary_range_inr_lpa: Dict  # {"min": 18.7, "max": 36.1}
    preferred_work_mode: str             # "onsite", "hybrid", "remote"
    willing_to_relocate: bool            # true/false
    github_activity_score: float         # 9.2 (0-10 scale)
    search_appearance_30d: int           # 249 (views in search)
    saved_by_recruiters_30d: int         # 4
    interview_completion_rate: float     # 0.71
    offer_acceptance_rate: float         # 0.58
    verified_email: bool                 # true/false
    verified_phone: bool                 # true/false
    linkedin_connected: bool             # true/false
```

---

## 🎯 SKILL HIERARCHY (Master Reference)

### **Tier-1 Skills (Direct JD Requirements — Max Weight)**

**Embeddings Frameworks:**
- "Sentence Transformers" | "sentence-transformers" | "SBERT"
- "BGE" | "BAAI/bge"
- "E5" | "intfloat/e5"
- "OpenAI Embeddings" | "OpenAI API"
- "CLIP" (vision-text)
- "Word2Vec" | "GloVe" (older, but valid)

**Vector Databases & Retrieval:**
- "FAISS"
- "Pinecone"
- "Weaviate"
- "Qdrant"
- "Milvus"
- "OpenSearch"
- "Elasticsearch"
- "Vespa"
- "Chroma" (newer, but valid)

**Evaluation Frameworks (CRITICAL):**
- "NDCG" | "Normalized Discounted Cumulative Gain"
- "MRR" | "Mean Reciprocal Rank"
- "MAP" | "Mean Average Precision"
- "Ranking" (if in context of evaluation/metrics)
- "A/B Testing" | "Online Evaluation"
- "Offline Metrics" | "Online-Offline Correlation"
- "Information Retrieval" (if with retrieval/ranking context)

**Core Language & Systems:**
- "Python" (especially if >3 years or with "production" context)
- "C++" (rare, but valid for large-scale systems)

---

### **Tier-2 Skills (Strong Proxy — Medium Weight)**

**LLM Fine-tuning & Adaptation:**
- "LoRA" | "Low-Rank Adaptation"
- "QLoRA"
- "PEFT" | "Parameter Efficient Fine-tuning"
- "HuggingFace" (transformers, fine-tuning context)
- "Transformers"
- "Fine-tuning" (if with LLM context)

**Learning-to-Rank & Advanced ML:**
- "XGBoost" (especially if with ranking context)
- "LambdaMART" | "Learning to Rank"
- "RankNet" | "LambdaRank"
- "Neural Ranking"
- "Gradient Boosting" (if with ranking)

**ML Ops & Experiment Tracking:**
- "MLflow"
- "Weights & Biases" | "wandb"
- "DVC" (if with model management)
- "Experiment Tracking"
- "Model Monitoring"

**Distributed Systems & Data Infrastructure:**
- "Apache Spark" | "Spark" | "PySpark"
- "Apache Airflow" | "Airflow"
- "Apache Kafka" | "Kafka"
- "Data Pipelines" (if with production context)
- "Streaming" (if with production context)

---

### **Tier-3 Skills (Context & Foundation — Low Weight)**

**Cloud Platforms:**
- "AWS", "Amazon Web Services"
- "Google Cloud" | "GCP"
- "Azure"

**Databases & Data Warehousing:**
- "SQL" (especially if years ≥ 3)
- "Snowflake"
- "BigQuery"
- "Postgres" | "PostgreSQL"
- "MySQL"

**General ML & Deep Learning:**
- "Machine Learning" (generic, but valid)
- "Deep Learning" (generic, but valid)
- "scikit-learn"
- "PyTorch" | "Torch"
- "TensorFlow"
- "Keras"
- "NumPy", "Pandas" (data tools)

**Soft Infrastructure:**
- "Docker"
- "Kubernetes" | "K8s"
- "API Design" | "REST APIs"

---

## 🔍 SKILL EXTRACTION PATTERNS (Code)

### **Pattern 1: Exact Match (Case-Insensitive)**
```python
TIER_1_EXACT = {
    "faiss", "pinecone", "weaviate", "qdrant", "milvus", 
    "opensearch", "elasticsearch", "sentence-transformers",
    "sbert", "bge", "e5", "clip", "openai embeddings",
    "python", "ndcg", "mrr", "map"
}

def extract_skills_exact(candidate):
    skills = candidate.get("skills", [])
    found_tier1 = set()
    
    for skill in skills:
        skill_name = skill["name"].lower().strip()
        # Exact match
        if skill_name in TIER_1_EXACT:
            found_tier1.add(skill_name)
        # Fuzzy variants
        elif skill_name in {"lora", "qlora", "peft", "mlflow", "wandb"}:
            found_tier1.add(skill_name)  # Tier-2, but close
    
    return found_tier1
```

### **Pattern 2: Profile/Summary Text Matching**
```python
import re

PRODUCTION_KEYWORDS = [
    "production", "deployment", "deployed", "ship", "shipped",
    "users", "scale", "scaling", "system", "systems", "pipeline",
    "infrastructure", "real-time", "latency", "performance"
]

def extract_production_signals(candidate):
    profile = candidate.get("profile", {})
    summary = profile.get("summary", "").lower()
    career = candidate.get("career_history", [])
    
    production_count = 0
    for keyword in PRODUCTION_KEYWORDS:
        if keyword in summary:
            production_count += 1
    
    for entry in career:
        desc = entry.get("description", "").lower()
        for keyword in PRODUCTION_KEYWORDS:
            if keyword in desc:
                production_count += 1
    
    return min(production_count, 10)  # Cap at 10
```

### **Pattern 3: Career Title Extraction**
```python
SENIORITY_PATTERNS = {
    "senior": 2,
    "lead": 2,
    "staff": 2,
    "principal": 3,
    "director": 3,
    "manager": 1,  # Less technical signal
    "engineer": 0,  # Baseline
    "intern": -2,
    "junior": -1
}

def extract_seniority(candidate):
    current_title = candidate.get("profile", {}).get("current_title", "").lower()
    score = 0
    
    for keyword, weight in SENIORITY_PATTERNS.items():
        if keyword in current_title:
            score += weight
    
    return max(-2, min(score, 3))  # Clamp to [-2, 3]
```

---

## ⚠️ HONEYPOT DETECTION PATTERNS (Code)

### **Pattern 1: Impossible Timeline**
```python
def detect_timeline_honeypot(candidate):
    """Return True if candidate has impossible timeline."""
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    education = candidate.get("education", [])
    
    # Education end year (youngest)
    edu_end_years = [e.get("end_year", 2025) for e in education]
    earliest_grad_year = min(edu_end_years) if edu_end_years else 2025
    
    for entry in career:
        start_date = entry.get("start_date", "")
        if start_date:
            start_year = int(start_date.split("-")[0])
            # Working before graduation?
            if start_year < earliest_grad_year - 1:  # Allow 1-year gap
                return True
    
    return False

def detect_company_age_mismatch(candidate):
    """Return True if candidate claims work at company before it was founded."""
    # This requires external company founding year data (not provided)
    # As fallback, check if duration is impossibly long
    career = candidate.get("career_history", [])
    
    for entry in career:
        # If duration > 20 years at same company, suspicious
        if entry.get("duration_months", 0) > 240:
            # Cross-check: does career history overlap?
            # For now, just flag as potential anomaly
            pass
    
    return False
```

### **Pattern 2: Skill Inflation**
```python
def detect_skill_inflation_honeypot(candidate):
    """Return True if candidate has >15 skills but low avg endorsements."""
    skills = candidate.get("skills", [])
    
    if len(skills) > 15:
        avg_endorsements = sum(s.get("endorsements", 0) for s in skills) / len(skills)
        if avg_endorsements < 3:
            return True  # Keyword stuffer
    
    # Check for "expert" proficiency with 0 endorsements (multiple times)
    expert_no_endorsement_count = sum(
        1 for s in skills 
        if s.get("proficiency") == "advanced" and s.get("endorsements", 0) == 0
    )
    
    if expert_no_endorsement_count >= 3:
        return True  # Inflated profile
    
    return False
```

### **Pattern 3: Experience Inflation**
```python
def detect_experience_inflation(candidate):
    """Return True if years_of_experience doesn't match career history."""
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    
    years_claimed = profile.get("years_of_experience", 0)
    
    # Sum actual years from career history
    career_years = sum(e.get("duration_months", 0) for e in career) / 12.0
    
    # If claimed years > actual career years by >2 years, suspicious
    if years_claimed > career_years + 2:
        return True
    
    return False
```

---

## 🧮 SCORING IMPLEMENTATION (Detailed Formulas)

### **Pillar 1: Skill Match Score (40%)**
```python
def calculate_skill_score(candidate):
    """
    Components:
    - Tier-1 skill count (max 8, each worth 0.05)
    - Tier-2 skill count (max 8, each worth 0.03125)
    - Tier-3 skill count (max 8, each worth 0.0125)
    - Endorsement bonus (max +0.05)
    
    Penalties:
    - Keyword stuffer: -0.30
    - Skill inflation: -0.20
    """
    
    skills = candidate.get("skills", [])
    
    # Categorize skills
    tier1_count = 0
    tier2_count = 0
    tier3_count = 0
    total_endorsements = 0
    
    for skill in skills:
        name = skill["name"].lower().strip()
        endorsements = skill.get("endorsements", 0)
        proficiency = skill.get("proficiency", "").lower()
        duration_months = skill.get("duration_months", 0)
        
        # Tier assignment
        if name in TIER_1_EXACT:
            tier1_count += 1
            total_endorsements += endorsements
        elif name in TIER_2_SKILLS:
            tier2_count += 1
            total_endorsements += endorsements
        elif name in TIER_3_SKILLS:
            tier3_count += 1
            total_endorsements += endorsements
        
        # Honeypot check: expert with 0 endorsements, <3 months
        if proficiency == "advanced" and endorsements == 0 and duration_months < 3:
            # Flag for later penalty
            pass
    
    # Base score
    tier1_score = min(tier1_count, 8) * 0.05      # Max 0.40
    tier2_score = min(tier2_count, 8) * 0.03125   # Max 0.25
    tier3_score = min(tier3_count, 8) * 0.0125    # Max 0.10
    
    endorsement_bonus = min(total_endorsements / 100.0, 0.05)  # Max +0.05
    
    base_score = tier1_score + tier2_score + tier3_score + endorsement_bonus
    
    # Normalize to [0, 1]
    normalized_score = min(base_score / 0.80, 1.0)  # Assume max possible ~0.80
    
    # Penalties
    if detect_skill_inflation_honeypot(candidate):
        normalized_score *= 0.70  # Reduce by 30%
    
    if len(skills) > 20 and (total_endorsements / len(skills)) < 3:
        normalized_score *= 0.70  # Keyword stuffer penalty
    
    return normalized_score
```

### **Pillar 2: Production Experience Score (35%)**
```python
def calculate_experience_score(candidate):
    """
    Components:
    - Role type points (Engineer > Manager > Research)
    - Company size signal (+0.10 if ≥200 employees)
    - Role duration (2+ years = full credit)
    - Production keywords in description
    - Career progression (promotions)
    
    Disqualifiers:
    - All roles are research/academic AND no production
    - No role > 18 months
    - Current role is non-technical
    """
    
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    
    # Disqualifier checks
    non_tech_titles = {"sales", "hr", "finance", "marketing", "recruiter", "business"}
    current_title = profile.get("current_title", "").lower()
    
    if all(word in current_title for word in non_tech_titles):
        return 0.0  # Non-technical current role
    
    if not career:
        return 0.0  # No career history
    
    score = 0.0
    relevant_roles = 0
    max_duration = 0
    
    for i, entry in enumerate(career):
        title = entry.get("title", "").lower()
        duration = entry.get("duration_months", 0)
        company_size = entry.get("company_size", "")
        description = entry.get("description", "").lower()
        
        # Role type scoring
        if any(x in title for x in ["engineer", "architect", "tech lead"]):
            score += 0.20
            relevant_roles += 1
        elif any(x in title for x in ["research", "academic"]):
            if duration < 24:
                continue  # Skip short research roles
            score += 0.05  # Low weight for research
        else:
            score += 0.05  # Other roles, low weight
        
        # Duration signal
        if duration >= 24:
            score += 0.10  # Full credit for 2+ years
        else:
            score += (duration / 24.0) * 0.10  # Partial credit
        
        max_duration = max(max_duration, duration)
        
        # Company size signal
        if company_size in ["10001+", "5001-10000", "1001-5000"]:
            score += 0.10
        elif company_size in ["201-500", "501-1000"]:
            score += 0.05
        
        # Production keywords
        prod_count = sum(1 for kw in PRODUCTION_KEYWORDS if kw in description)
        score += min(prod_count * 0.02, 0.10)
    
    # Normalize
    normalized_score = min(score / 1.0, 1.0)  # Assume max ~1.0
    
    # Disqualifiers
    if max_duration < 18 and relevant_roles < 2:
        normalized_score *= 0.5  # Job hopper penalty
    
    if relevant_roles == 0:
        normalized_score *= 0.3  # No relevant roles
    
    return normalized_score
```

### **Pillar 3: Experience Years Score (15%)**
```python
def calculate_yoe_score(candidate):
    """
    Components:
    - Years in band [3, 9]: full credit
    - [0, 3): linear ramp-up
    - (9, 15]: mild decay
    - 15+: check for research drift
    
    Seniority bonuses:
    - "Senior" title: +0.10
    - Promotion visible: +0.05
    - Tech lead: +0.05
    """
    
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    
    yoe = profile.get("years_of_experience", 0)
    
    # Base years scoring
    if yoe < 3:
        years_score = (yoe / 3.0) * 0.5  # [0, 0.5]
    elif 3 <= yoe <= 9:
        years_score = 1.0  # Full credit
    elif 9 < yoe <= 15:
        years_score = 1.0 - ((yoe - 9) / 6.0) * 0.1  # [1.0, 0.9]
    else:  # 15+ years
        years_score = 0.85  # Mild penalty, check for drift
    
    # Seniority bonuses
    current_title = profile.get("current_title", "").lower()
    if "senior" in current_title:
        years_score += 0.10
    if "lead" in current_title or "tech lead" in current_title:
        years_score += 0.05
    if "principal" in current_title or "director" in current_title:
        years_score += 0.05
    
    # Check for promotion (title change in career history)
    if len(career) >= 2:
        titles = [e.get("title", "").lower() for e in career]
        if titles[0] != titles[-1]:  # Title changed
            years_score += 0.05
    
    # Check for research drift (15+ years but only in research roles)
    if yoe > 15:
        research_roles = sum(1 for e in career if "research" in e.get("title", "").lower())
        if research_roles == len(career):
            years_score *= 0.7  # Penalty: research-only at 15+ years
    
    return min(years_score, 1.0)
```

### **Pillar 4: Behavioral Multiplier**
```python
def calculate_behavioral_multiplier(candidate):
    """
    Multiplier components:
    - recruiter_response_rate (0–1, weight 0.25)
    - open_to_work_flag (0 or 1, weight 0.20)
    - interview_completion_rate (0–1, weight 0.20)
    - offer_acceptance_rate (0–1, weight 0.15)
    - verified email & phone (0 or 1, weight 0.10)
    - willing_to_relocate (0 or 1, weight 0.05)
    - notice_period (30–90 days ideal, weight 0.05)
    
    Penalties:
    - avg_response_time > 336 hours: -0.10
    - github_activity_score ≥ 8.0: +0.05
    
    Clamp: [0.7, 1.2]
    """
    
    signals = candidate.get("redrob_signals", {})
    
    components = {}
    
    # Response rate
    response_rate = signals.get("recruiter_response_rate", 0.0)
    components["response_rate"] = response_rate * 0.25
    
    # Open to work
    open_to_work = 1.0 if signals.get("open_to_work_flag", False) else 0.0
    components["open_to_work"] = open_to_work * 0.20
    
    # Interview completion
    interview_rate = signals.get("interview_completion_rate", 0.0)
    components["interview_rate"] = interview_rate * 0.20
    
    # Offer acceptance
    offer_rate = signals.get("offer_acceptance_rate", 0.0)
    components["offer_rate"] = offer_rate * 0.15
    
    # Verified contact
    verified = 1.0 if (signals.get("verified_email", False) and signals.get("verified_phone", False)) else 0.0
    components["verified"] = verified * 0.10
    
    # Willing to relocate
    relocate = 1.0 if signals.get("willing_to_relocate", False) else 0.0
    components["relocate"] = relocate * 0.05
    
    # Notice period (30-90 days ideal)
    notice_days = signals.get("notice_period_days", 60)
    if 30 <= notice_days <= 90:
        components["notice"] = 0.05
    else:
        components["notice"] = 0.0
    
    base_multiplier = sum(components.values())
    
    # Penalties & bonuses
    avg_response_time = signals.get("avg_response_time_hours", 0.0)
    if avg_response_time > 336:
        base_multiplier -= 0.10
    
    github_score = signals.get("github_activity_score", 0.0)
    if github_score >= 8.0:
        base_multiplier += 0.05
    
    # Clamp
    multiplier = max(0.7, min(base_multiplier, 1.2))
    
    return multiplier
```

### **Composite Score**
```python
def calculate_final_score(candidate):
    """
    Composite = (
        skill_score * 0.40 +
        exp_score * 0.35 +
        yoe_score * 0.15
    ) × behavioral_multiplier
    
    Range: [0.0, 1.0] for valid candidates, -1.0 for honeypots
    """
    
    # Honeypot filter (kill signal)
    if (detect_timeline_honeypot(candidate) or 
        detect_experience_inflation(candidate)):
        return -1.0  # Will be ranked last
    
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
    
    # Clamp to [0, 1]
    return max(0.0, min(final, 1.0))
```

---

## 🔄 PARALLELIZATION STRATEGY (CPU Optimization)

### **Thread Pool Pattern**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import json

def load_and_score(candidates_path):
    """Load candidates and score in parallel."""
    
    # Load candidates
    candidates = []
    if candidates_path.endswith('.gz'):
        with gzip.open(candidates_path, 'rt', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    candidates.append(json.loads(line))
    else:
        with open(candidates_path, 'r') as f:
            for line in f:
                if line.strip():
                    candidates.append(json.loads(line))
    
    print(f"Loaded {len(candidates)} candidates")
    
    # Score in parallel
    results = []
    
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(score_single_candidate, c): c['candidate_id'] 
            for c in candidates
        }
        
        for i, future in enumerate(as_completed(futures)):
            if i % 10000 == 0:
                print(f"Scored {i}/{len(candidates)}")
            
            candidate_id = futures[future]
            score, reasoning = future.result()
            results.append({
                'candidate_id': candidate_id,
                'score': score,
                'reasoning': reasoning
            })
    
    return results

def score_single_candidate(candidate):
    """Score a single candidate. Called by thread pool."""
    score = calculate_final_score(candidate)
    reasoning = generate_reasoning(candidate, score)
    return score, reasoning
```

---

## 📝 REASONING GENERATION (1-2 Sentence Template)

```python
def generate_reasoning(candidate, score):
    """Generate 1-2 sentence justification."""
    
    profile = candidate.get("profile", {})
    current_title = profile.get("current_title", "")
    yoe = profile.get("years_of_experience", 0)
    
    signals = candidate.get("redrob_signals", {})
    response_rate = signals.get("recruiter_response_rate", 0.0)
    
    skills = candidate.get("skills", [])
    relevant_skills = [s["name"] for s in skills if is_tier1_skill(s["name"])]
    skill_count = len(relevant_skills)
    
    # Template
    reason = f"{current_title} with {yoe:.1f} yrs; {skill_count} core skills; response rate {response_rate:.2f}."
    
    # Add second sentence if score is very high or very low
    if score >= 0.85:
        reason += f" Strong production experience across embeddings and vector systems."
    elif score <= 0.40:
        reason += f" Limited relevant experience or behavioral signals."
    
    return reason[:150]  # Cap at 150 chars
```

---

## ✅ VALIDATION CHECKLIST (Pre-Submission)

- [ ] CSV has exactly 100 data rows + 1 header row
- [ ] Header is `candidate_id,rank,score,reasoning`
- [ ] Ranks 1–100 appear exactly once each (no duplicates)
- [ ] Candidate IDs appear exactly once each
- [ ] All candidate IDs exist in candidates.jsonl
- [ ] Scores strictly non-increasing (no score reversal)
- [ ] Tie-breaking by candidate_id ascending (when scores equal)
- [ ] All scores in range [0.0, 1.0]
- [ ] Reasoning is 1–2 sentences, under 150 chars
- [ ] No honeypots in top 10 (spot-check)
- [ ] Honeypot rate in top 100 < 10% (if possible)
- [ ] End-to-end runtime < 5 minutes on CPU
- [ ] No GPU access during ranking
- [ ] No network calls during ranking
- [ ] GitHub repo has full code + README + requirements.txt
- [ ] Sandbox runs successfully on small sample
- [ ] submission_metadata.yaml filled out and committed

---

**Ready to build. Execute Phase 1 immediately. 🚀**
