#!/usr/bin/env python3
"""
Redrob Hackathon - Senior AI Engineer Candidate Ranking System
===============================================================

Produces a top-100 ranked CSV from a pool of up to 100K candidates.

Design (see IMPROVED_DESIGN.md for full rationale):
  * Career-history *evidence* (what the candidate actually BUILT) is weighted
    above the raw skills keyword list - this defuses the keyword-stuffer trap the
    JD explicitly warns about ("all AI keywords + Marketing Manager title").
  * Four pillars: Skills+Evidence (0.30), Production Experience (0.45),
    Years+Seniority (0.15), plus a small Location modifier, all multiplied by a
    Behavioral availability multiplier in [0.80, 1.10]. Honeypots -> -1.0.
  * Scoring is top-heavy by design (hidden metric is 0.50*NDCG@10 + ...), so the
    ranker is conservative at the top.
  * Standard library only - no pandas/numpy - for sandbox reproducibility.

Usage:
  python rank.py --candidates ./candidates.jsonl --out ./submission.csv
  python rank.py --candidates ./candidates.jsonl.gz --out ./submission.csv
"""

from __future__ import annotations

import argparse
import csv
import difflib
import gzip
import heapq
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

CURRENT_YEAR = 2026  # competition reference year (today: 2026-06-29)

# Pillar weights (sum of additive pillars = 0.90; behavioral is multiplicative).
W_SKILL = 0.30
W_EXP = 0.45
W_YOE = 0.15

# --- Skill vocabularies (canonical, lowercase) ---------------------------------
TIER_1_SKILLS = {
    # embeddings frameworks
    "faiss", "sentence-transformers", "sbert", "bge", "e5", "clip",
    "openai embeddings", "word2vec", "glove", "embeddings",
    # vector databases / hybrid search
    "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch",
    "vespa", "chroma", "vector database", "vector search", "hybrid search",
    # ranking / IR / evaluation
    "ndcg", "mrr", "map", "ranking metrics", "information retrieval",
    "learning to rank", "semantic search", "rag", "retrieval", "recommendation",
    "recommender systems", "search relevance",
    # core language
    "python", "c++",
}

TIER_2_SKILLS = {
    # LLM fine-tuning
    "lora", "qlora", "peft", "huggingface", "transformers", "fine-tuning",
    # learning-to-rank models
    "xgboost", "lambdamart", "ranknet", "neural ranking",
    # ML ops
    "mlflow", "weights & biases", "wandb", "dvc", "experiment tracking",
    # distributed data systems
    "apache spark", "spark", "pyspark", "apache airflow", "airflow",
    "apache kafka", "kafka",
    # nlp
    "nlp", "natural language processing",
}

TIER_3_SKILLS = {
    "aws", "google cloud", "gcp", "azure",
    "sql", "snowflake", "bigquery", "postgres", "postgresql", "mysql",
    "machine learning", "deep learning", "scikit-learn", "sklearn",
    "pytorch", "tensorflow", "keras",
    "docker", "kubernetes", "k8s", "rest api", "api design",
}

# Alias normalization: variant -> canonical token present in a tier set above.
SKILL_ALIASES = {
    "sentence transformers": "sentence-transformers",
    "sentencetransformers": "sentence-transformers",
    "s-bert": "sbert",
    "facebook ai similarity search": "faiss",
    "vector db": "vector database",
    "vectordb": "vector database",
    "vector databases": "vector database",
    "elastic search": "elasticsearch",
    "open search": "opensearch",
    "weights and biases": "weights & biases",
    "w&b": "weights & biases",
    "hugging face": "huggingface",
    "learning-to-rank": "learning to rank",
    "ltr": "learning to rank",
    "recommender": "recommender systems",
    "recommendation systems": "recommender systems",
    "recsys": "recommender systems",
    "fine tuning": "fine-tuning",
    "finetuning": "fine-tuning",
    "py-torch": "pytorch",
    "tensor flow": "tensorflow",
    "scikit learn": "scikit-learn",
    "natural-language-processing": "natural language processing",
}

_ALL_SKILL_VOCAB = TIER_1_SKILLS | TIER_2_SKILLS | TIER_3_SKILLS

# --- Career-description evidence concepts (what they actually BUILT) -----------
# Found in free text these carry MORE weight than the same word in skills[].
EVIDENCE_CONCEPTS = {
    "tier1": [
        "retrieval", "embedding", "embeddings", "ranking", "re-rank", "rerank",
        "recommendation", "recommender", "vector search", "semantic search",
        "relevance", "search system", "search engine", "matching", "nearest neighbor",
        "information retrieval", "ndcg", "mrr", "learning to rank", "personalization",
    ],
    "tier2": [
        "fine-tune", "fine tuning", "fine-tuning", "llm", "transformer",
        "a/b test", "ab test", "experiment", "evaluation framework", "offline metric",
        "feature pipeline", "model serving", "inference",
    ],
}

# Production / operational maturity keywords (career descriptions + summary).
PRODUCTION_KEYWORDS = {
    "production", "deployed", "deployment", "shipped", "ship", "users", "user",
    "scale", "scaling", "latency", "real-time", "realtime", "pipeline",
    "infrastructure", "serving", "throughput", "monitoring", "on-call", "oncall",
    "reliability", "sla", "uptime", "live",
}

# Domain relevance keywords (the JD's actual product surface).
DOMAIN_KEYWORDS = {
    "ranking", "retrieval", "search", "recommendation", "recommender", "embedding",
    "embeddings", "vector", "relevance", "matching", "personalization", "nlp",
    "information retrieval", "semantic",
}

RESEARCH_PATTERNS = {"research", "researcher", "scientist", "academic", "phd",
                     "postdoc", "lab", "kaggle", "competition"}

SENIORITY_KEYWORDS = ["principal", "staff", "lead", "senior", "head", "architect",
                      "manager", "director"]
SENIORITY_RANK = {  # for promotion detection (higher = more senior)
    "intern": 0, "junior": 1, "associate": 1, "": 2, "engineer": 2,
    "senior": 3, "lead": 4, "staff": 4, "principal": 5, "architect": 5,
    "head": 5, "director": 6, "vp": 7,
}

NON_TECH_TITLES = {"sales", "hr", "human resources", "finance", "marketing",
                   "recruiter", "recruiting", "business development", "account manager",
                   "customer success", "operations manager"}

TECH_TITLE_TOKENS = {"engineer", "developer", "scientist", "architect", "ml",
                     "data", "software", "sde", "programmer", "researcher",
                     "tech lead", "devops", "sre"}

# Indian services / consulting firms (JD negative signal if entire career here).
SERVICES_FIRMS = {
    "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "mindtree", "hcl", "tech mahindra", "ltimindtree", "lti",
    "mphasis", "hexaware", "birlasoft", "persistent systems", "ust global",
    "deloitte", "ibm", "dxc", "virtusa", "zensar", "coforge", "nttdata",
    "ntt data",
}

# Big-tech / strong product companies (positive signal).
BIG_TECH = {
    "google", "meta", "facebook", "amazon", "microsoft", "apple", "netflix",
    "uber", "airbnb", "linkedin", "nvidia", "openai", "anthropic", "stripe",
    "flipkart", "swiggy", "zomato", "razorpay", "phonepe", "cred", "paytm",
    "myntra", "ola", "sharechat", "dunzo", "meesho", "nykaa", "freshworks",
    "zoho", "postman", "browserstack", "salesforce", "adobe", "atlassian",
    "databricks", "snowflake", "spotify", "twitter", "pinterest", "dropbox",
}

# India Tier-1 cities (JD: Pune/Noida; Tier-1 Indian cities welcome).
INDIA_CITIES = {
    "pune", "noida", "bangalore", "bengaluru", "hyderabad", "mumbai", "delhi",
    "new delhi", "gurgaon", "gurugram", "chennai", "kolkata", "ahmedabad",
    "delhi ncr", "ncr",
}

_PROFICIENCY_HIGH = {"advanced", "expert"}

# ============================================================================
# DATA CLASSES
# ============================================================================


@dataclass
class ScoreBreakdown:
    skill: float = 0.0
    exp: float = 0.0
    yoe: float = 0.0
    location_mod: float = 0.0
    behavioral: float = 1.0
    honeypot_flags: List[str] = field(default_factory=list)
    facts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoredCandidate:
    candidate_id: str
    score: float
    reasoning: str


# ============================================================================
# SMALL HELPERS
# ============================================================================


def _lower(s: Any) -> str:
    return s.lower().strip() if isinstance(s, str) else ""


def _norm_skill(name: str) -> str:
    n = _lower(name)
    n = n.replace("_", " ")
    return SKILL_ALIASES.get(n, n)


_FUZZY_CACHE: Dict[str, Optional[str]] = {}


def _fuzzy_tier(name: str) -> Optional[str]:
    """Return 'tier1'/'tier2'/'tier3' for a (normalized) skill name, else None.

    Exact/alias match first; bounded difflib fuzzy fallback for typos.
    Memoized across candidates - skill names are highly repetitive in a 100K pool.
    """
    n = _norm_skill(name)
    if not n:
        return None
    cached = _FUZZY_CACHE.get(n, False)
    if cached is not False:
        return cached  # type: ignore[return-value]

    if n in TIER_1_SKILLS:
        result: Optional[str] = "tier1"
    elif n in TIER_2_SKILLS:
        result = "tier2"
    elif n in TIER_3_SKILLS:
        result = "tier3"
    else:
        result = None
        match = difflib.get_close_matches(n, _ALL_SKILL_VOCAB, n=1, cutoff=0.88)
        if match:
            m = match[0]
            result = "tier1" if m in TIER_1_SKILLS else "tier2" if m in TIER_2_SKILLS else "tier3"

    _FUZZY_CACHE[n] = result
    return result


def _year_from_date(s: Any) -> Optional[int]:
    if not isinstance(s, str) or not s:
        return None
    m = re.match(r"(\d{4})", s)
    return int(m.group(1)) if m else None


def _days_since(date_str: Any) -> Optional[int]:
    y = _year_from_date(date_str)
    if y is None:
        return None
    try:
        parts = date_str.split("-")
        d = date(int(parts[0]), int(parts[1]), int(parts[2]))
        return (date(CURRENT_YEAR, 6, 29) - d).days
    except (ValueError, IndexError):
        # fall back to year granularity
        return (CURRENT_YEAR - y) * 365


def _diminish(count: int, per: float, cap_count: int) -> float:
    """Diminishing-returns sum: each additional item worth less."""
    total = 0.0
    for i in range(min(count, cap_count)):
        total += per / (1.0 + 0.35 * i)
    return total


def _text_blob(candidate: Dict) -> str:
    profile = candidate.get("profile", {}) or {}
    parts = [_lower(profile.get("summary", "")), _lower(profile.get("headline", ""))]
    for entry in candidate.get("career_history", []) or []:
        parts.append(_lower(entry.get("description", "")))
        parts.append(_lower(entry.get("title", "")))
    return " \n ".join(parts)


# ============================================================================
# PILLAR 1: SKILLS + CAREER EVIDENCE  (weight 0.30)
# ============================================================================


def _skill_trust(skill: Dict) -> float:
    endorsements = skill.get("endorsements", 0) or 0
    duration = skill.get("duration_months", 0) or 0
    trust = 0.4 + 0.5 * min(endorsements, 20) / 20.0 + 0.3 * min(duration, 36) / 36.0
    return max(0.4, min(trust, 1.2))


def calculate_skill_score(candidate: Dict, blob: str) -> Tuple[float, Dict[str, Any]]:
    skills_data = candidate.get("skills", []) or []

    tier_trust = {"tier1": 0.0, "tier2": 0.0, "tier3": 0.0}
    tier_count = {"tier1": 0, "tier2": 0, "tier3": 0}
    matched_names: List[str] = []

    for skill in skills_data:
        tier = _fuzzy_tier(skill.get("name", ""))
        if tier is None:
            continue
        tier_count[tier] += 1
        tier_trust[tier] += _skill_trust(skill)
        if tier in ("tier1", "tier2") and len(matched_names) < 6:
            matched_names.append(skill.get("name", ""))

    # diminishing returns on count, scaled by average trust within tier
    def tier_component(tier: str, per: float, cap: int) -> float:
        if tier_count[tier] == 0:
            return 0.0
        avg_trust = tier_trust[tier] / tier_count[tier]
        return _diminish(tier_count[tier], per, cap) * avg_trust

    keyword_raw = (
        tier_component("tier1", 0.16, 6)
        + tier_component("tier2", 0.09, 5)
        + tier_component("tier3", 0.04, 5)
    )
    keyword_score = min(keyword_raw / 0.75, 1.0)

    # --- career evidence (what they BUILT) ---
    ev1 = sum(1 for kw in EVIDENCE_CONCEPTS["tier1"] if kw in blob)
    ev2 = sum(1 for kw in EVIDENCE_CONCEPTS["tier2"] if kw in blob)
    evidence_raw = _diminish(ev1, 0.20, 5) + _diminish(ev2, 0.10, 5)
    evidence_score = min(evidence_raw / 0.70, 1.0)

    # keyword-only (no real evidence) is capped: defuses the stuffer trap
    if evidence_score < 0.10:
        keyword_score = min(keyword_score, 0.55)

    skill_score = 0.5 * keyword_score + 0.5 * evidence_score

    # inflation penalty
    if len(skills_data) > 15:
        avg_end = sum(s.get("endorsements", 0) or 0 for s in skills_data) / len(skills_data)
        if avg_end < 3:
            skill_score *= 0.70

    facts = {
        "tier1_skills": tier_count["tier1"],
        "tier2_skills": tier_count["tier2"],
        "matched_skills": matched_names,
        "evidence_hits": ev1 + ev2,
    }
    return min(skill_score, 1.0), facts


def detect_skill_inflation(candidate: Dict) -> bool:
    skills_data = candidate.get("skills", []) or []
    if len(skills_data) > 15:
        avg_end = sum(s.get("endorsements", 0) or 0 for s in skills_data) / max(len(skills_data), 1)
        if avg_end < 3:
            return True
    expert_no_substance = sum(
        1 for s in skills_data
        if _lower(s.get("proficiency", "")) in _PROFICIENCY_HIGH
        and (s.get("endorsements", 0) or 0) == 0
        and (s.get("duration_months", 0) or 0) == 0
    )
    return expert_no_substance >= 3


# ============================================================================
# PILLAR 2: PRODUCTION EXPERIENCE  (weight 0.45)  - heaviest pillar
# ============================================================================


def _company_bonus(company: str, size: str) -> float:
    c = _lower(company)
    bonus = 0.0
    if any(f in c for f in SERVICES_FIRMS):
        bonus += 0.0  # services: no positive credit (career-wide penalty handled elsewhere)
    elif any(b in c for b in BIG_TECH):
        bonus += 0.10
    else:
        bonus += 0.05  # other (presumed product) company
    if size in ("10001+", "5001-10000", "1001-5000"):
        bonus += 0.08
    elif size in ("201-500", "501-1000"):
        bonus += 0.05
    return bonus


def _is_services(company: str) -> bool:
    return any(f in _lower(company) for f in SERVICES_FIRMS)


def calculate_experience_score(candidate: Dict) -> Tuple[float, Dict[str, Any]]:
    profile = candidate.get("profile", {}) or {}
    career = candidate.get("career_history", []) or []

    current_title = _lower(profile.get("current_title", ""))
    if any(word in current_title for word in NON_TECH_TITLES):
        # current role non-technical: only salvage if a recent technical role exists
        recent_tech = any(
            any(t in _lower(e.get("title", "")) for t in TECH_TITLE_TOKENS)
            and (e.get("duration_months", 0) or 0) >= 12
            for e in career[:3]
        )
        if not recent_tech:
            return 0.0, {"non_technical": True}

    if not career:
        return 0.0, {"no_career": True}

    score = 0.0
    relevant_roles = 0
    services_roles = 0
    research_roles = 0
    total_prod_months = 0
    built_evidence = False

    for entry in career:
        title = _lower(entry.get("title", ""))
        duration = entry.get("duration_months", 0) or 0
        company = entry.get("company", "")
        size = entry.get("company_size", "")
        desc = _lower(entry.get("description", ""))

        if _is_services(company):
            services_roles += 1
        is_research = any(p in title for p in RESEARCH_PATTERNS)
        if is_research:
            research_roles += 1

        # role type
        if any(t in title for t in TECH_TITLE_TOKENS) and not is_research:
            score += 0.18
            relevant_roles += 1
            if duration >= 12:
                total_prod_months += duration
        elif is_research:
            if duration < 24:
                continue  # short research stints contribute nothing
            score += 0.04
        else:
            score += 0.03

        # company bonus
        score += _company_bonus(company, size)

        # duration depth
        if duration >= 24:
            score += 0.10
        elif duration > 0:
            score += (duration / 24.0) * 0.10

        # production maturity (saturating)
        prod_hits = sum(1 for kw in PRODUCTION_KEYWORDS if kw in desc)
        score += _diminish(prod_hits, 0.04, 5)

        # domain relevance - this is "they built the thing"
        dom_hits = sum(1 for kw in DOMAIN_KEYWORDS if kw in desc)
        if dom_hits >= 2:
            built_evidence = True
        score += _diminish(dom_hits, 0.06, 5)

    normalized = min(score / 1.4, 1.0)

    # career-wide penalties
    if relevant_roles == 0:
        normalized *= 0.30
    if research_roles == len(career) and total_prod_months < 24:
        normalized *= 0.40  # pure research without production
    if services_roles == len(career):
        normalized *= 0.80  # entirely services/consulting

    # education tier modifier (small, provided in schema)
    edu_mod = 0.0
    for edu in candidate.get("education", []) or []:
        t = _lower(edu.get("tier", ""))
        if t == "tier_1":
            edu_mod = max(edu_mod, 0.05)
        elif t == "tier_2":
            edu_mod = max(edu_mod, 0.02)
    normalized = min(normalized + edu_mod, 1.0)

    facts = {
        "relevant_roles": relevant_roles,
        "built_evidence": built_evidence,
        "services_only": services_roles == len(career),
        "research_heavy": research_roles == len(career),
    }
    return normalized, facts


# ============================================================================
# PILLAR 3: YEARS + SENIORITY  (weight 0.15)
# ============================================================================


def calculate_yoe_score(candidate: Dict) -> Tuple[float, Dict[str, Any]]:
    profile = candidate.get("profile", {}) or {}
    yoe = profile.get("years_of_experience", 0) or 0

    if yoe < 3:
        years_score = (yoe / 3.0) * 0.5
    elif yoe <= 9:
        years_score = 1.0
    elif yoe <= 15:
        years_score = 1.0 - ((yoe - 9) / 6.0) * 0.10
    else:
        years_score = 0.85

    current_title = _lower(profile.get("current_title", ""))
    if any(k in current_title for k in ("senior", "lead", "staff", "principal")):
        years_score += 0.10

    career = candidate.get("career_history", []) or []
    # promotion detection: seniority ascending from oldest -> newest
    promoted = False
    ranks = []
    for e in sorted(career, key=lambda x: _year_from_date(x.get("start_date")) or 0):
        t = _lower(e.get("title", ""))
        r = 2
        for kw, rk in SENIORITY_RANK.items():
            if kw and kw in t:
                r = max(r, rk)
        ranks.append(r)
    if len(ranks) >= 2 and ranks[-1] > ranks[0]:
        promoted = True
        years_score += 0.05

    # career stability (title-chaser penalty)
    durations = [e.get("duration_months", 0) or 0 for e in career]
    if len(durations) >= 3 and (sum(durations) / len(durations)) < 18:
        years_score *= 0.85

    return min(years_score, 1.0), {"yoe": yoe, "promoted": promoted}


# ============================================================================
# PILLAR 4: BEHAVIORAL MULTIPLIER  [0.80, 1.10]
# ============================================================================


def calculate_behavioral_multiplier(candidate: Dict) -> Tuple[float, Dict[str, Any]]:
    s = candidate.get("redrob_signals", {}) or {}

    response_rate = s.get("recruiter_response_rate", 0.0) or 0.0
    interview_rate = s.get("interview_completion_rate", 0.0) or 0.0
    open_to_work = bool(s.get("open_to_work_flag", False))

    offer_rate = s.get("offer_acceptance_rate", -1)
    offer_component = 0.5 if (offer_rate is None or offer_rate < 0) else offer_rate

    verified = s.get("verified_email", False) and s.get("verified_phone", False)

    component = (
        response_rate * 0.25
        + interview_rate * 0.20
        + (0.15 if open_to_work else 0.0)
        + offer_component * 0.15
        + (0.10 if verified else 0.0)
    )

    # recency / engagement
    days_inactive = _days_since(s.get("last_active_date"))
    if days_inactive is not None:
        if days_inactive <= 30:
            component += 0.10
        elif days_inactive <= 90:
            component += 0.05
        elif days_inactive > 180:
            component += 0.0
    # notice period (JD: sub-30 preferred)
    notice = s.get("notice_period_days", 60)
    if notice is not None:
        if notice <= 30:
            component += 0.05
        elif notice <= 90:
            component += 0.02

    # response time buckets
    rt = s.get("avg_response_time_hours", None)
    if rt is not None and rt > 0:
        if rt <= 24:
            component += 0.03
        elif rt <= 72:
            component += 0.01
        elif rt > 336:
            component -= 0.05

    # github (0-100; -1 = none -> neutral)
    gh = s.get("github_activity_score", -1)
    if gh is not None and gh >= 70:
        component += 0.03

    # consistency interactions
    if response_rate >= 0.5 and interview_rate >= 0.5:
        component += 0.03
    if open_to_work and days_inactive is not None and days_inactive > 90:
        component -= 0.05
    if response_rate >= 0.5 and interview_rate < 0.2:
        component -= 0.03

    # salary realism
    yoe = (candidate.get("profile", {}) or {}).get("years_of_experience", 0) or 0
    sal = s.get("expected_salary_range_inr_lpa", {}) or {}
    sal_min = sal.get("min", 0) or 0
    if yoe < 4 and sal_min > 60:
        component -= 0.03

    component = max(0.0, min(component, 1.0))
    mult = 0.80 + 0.30 * component
    mult = max(0.80, min(mult, 1.10))

    facts = {
        "response_rate": response_rate,
        "interview_rate": interview_rate,
        "open_to_work": open_to_work,
        "days_inactive": days_inactive,
        "notice": notice,
    }
    return mult, facts


# ============================================================================
# LOCATION MODIFIER  (additive, small)
# ============================================================================


def calculate_location_modifier(candidate: Dict) -> Tuple[float, Dict[str, Any]]:
    profile = candidate.get("profile", {}) or {}
    s = candidate.get("redrob_signals", {}) or {}
    location = _lower(profile.get("location", ""))
    country = _lower(profile.get("country", ""))
    in_india = (country in ("india", "")) or any(c in location for c in INDIA_CITIES)
    tier1_city = any(c in location for c in INDIA_CITIES)
    willing = bool(s.get("willing_to_relocate", False))

    if tier1_city:
        mod = 0.03
    elif in_india:
        mod = 0.01
    elif willing:
        mod = 0.0
    else:
        mod = -0.08  # outside India, not willing to relocate (no visa sponsorship)
    return mod, {"location": profile.get("location", ""), "willing_relocate": willing,
                 "in_india": in_india}


# ============================================================================
# HONEYPOT DETECTION (10 patterns, severity-tagged)
# ============================================================================


def detect_honeypots(candidate: Dict) -> Tuple[bool, float, List[str]]:
    """Return (disqualify, penalty_multiplier, flags)."""
    flags: List[str] = []
    penalty = 1.0
    disqualify = False

    profile = candidate.get("profile", {}) or {}
    career = candidate.get("career_history", []) or []
    skills = candidate.get("skills", []) or []
    yoe = profile.get("years_of_experience", 0) or 0

    # NOTE: we deliberately do NOT use education end_year as a timeline gate.
    # The dataset contains many legitimate career-changers / recent-degree holders
    # whose graduation year post-dates their work history (e.g. "Accountant, 12
    # yrs, graduated 2022"). Education-based timeline checks produced ~28K false
    # positives. Instead we rely on internally-consistent career-duration math,
    # which matches the spec's actual honeypot signatures.

    durations = [e.get("duration_months", 0) or 0 for e in career]
    career_months = sum(durations)
    yoe_months = yoe * 12

    # 1. A single role longer than the candidate's entire claimed career is
    #    impossible ("8 years at a company founded 3 years ago" family).
    if yoe > 0 and durations and max(durations) > yoe_months + 24:
        disqualify = True
        flags.append("role_longer_than_career")

    # 2. Total tenure far exceeds claimed experience (overlapping/impossible jobs).
    if yoe > 0 and career_months > yoe_months + 48:
        disqualify = True
        flags.append("career_sum_exceeds_yoe")

    # 3. Claims far more experience than any listed work accounts for (>8 yr gap).
    if career and yoe >= 10 and (yoe_months - career_months) > 96:
        disqualify = True
        flags.append("yoe_vs_career_mismatch")

    # 4. Expertise with zero substance ("expert in N skills, 0 years used").
    expert_empty = sum(
        1 for s in skills
        if _lower(s.get("proficiency", "")) in _PROFICIENCY_HIGH
        and (s.get("endorsements", 0) or 0) == 0
        and (s.get("duration_months", 0) or 0) == 0
    )
    if expert_empty >= 3:
        disqualify = True
        flags.append("expert_zero_substance")

    # 5. title-skill contradiction (Marketing Manager + all AI skills, no tech role)
    current_title = _lower(profile.get("current_title", ""))
    if any(w in current_title for w in NON_TECH_TITLES):
        ai_skills = sum(1 for s in skills if _fuzzy_tier(s.get("name", "")) in ("tier1", "tier2"))
        has_tech_role = any(
            any(t in _lower(e.get("title", "")) for t in TECH_TITLE_TOKENS) for e in career
        )
        if ai_skills >= 4 and len(skills) > 0 and ai_skills / len(skills) >= 0.5 and not has_tech_role:
            disqualify = True
            flags.append("title_skill_contradiction")

    # --- soft penalties (do not disqualify) ---
    # 7. skill inflation
    if len(skills) > 20:
        avg_end = sum(s.get("endorsements", 0) or 0 for s in skills) / len(skills)
        if avg_end < 2:
            penalty *= 0.70
            flags.append("skill_inflation")

    # 8. extreme job hopper
    durs = [e.get("duration_months", 0) or 0 for e in career]
    if len(durs) >= 5 and all(d < 6 for d in durs):
        penalty *= 0.70
        flags.append("job_hopper")

    # 9. all-services career
    if career and all(_is_services(e.get("company", "")) for e in career):
        penalty *= 0.85
        flags.append("services_only")

    # 10. availability contradiction
    s = candidate.get("redrob_signals", {}) or {}
    di = _days_since(s.get("last_active_date"))
    if s.get("open_to_work_flag") and di is not None and di > 180:
        penalty *= 0.95
        flags.append("stale_open_to_work")

    return disqualify, penalty, flags


# ============================================================================
# COMPOSITE SCORING
# ============================================================================


def score_breakdown(candidate: Dict) -> ScoreBreakdown:
    bd = ScoreBreakdown()
    disq, penalty, flags = detect_honeypots(candidate)
    bd.honeypot_flags = flags
    if disq:
        bd.facts["disqualified"] = True
        return bd  # scores left at 0; final handled below

    blob = _text_blob(candidate)
    bd.skill, skill_facts = calculate_skill_score(candidate, blob)
    bd.exp, exp_facts = calculate_experience_score(candidate)
    bd.yoe, yoe_facts = calculate_yoe_score(candidate)
    bd.location_mod, loc_facts = calculate_location_modifier(candidate)
    bd.behavioral, beh_facts = calculate_behavioral_multiplier(candidate)
    bd.facts.update(skill_facts)
    bd.facts.update(exp_facts)
    bd.facts.update(yoe_facts)
    bd.facts.update(loc_facts)
    bd.facts.update(beh_facts)
    bd.facts["penalty"] = penalty
    return bd


def calculate_final_score(candidate: Dict, bd: Optional[ScoreBreakdown] = None) -> float:
    if bd is None:
        bd = score_breakdown(candidate)
    if bd.facts.get("disqualified"):
        return -1.0
    composite = W_SKILL * bd.skill + W_EXP * bd.exp + W_YOE * bd.yoe + bd.location_mod
    composite = max(0.0, min(composite, 1.0))
    final = composite * bd.behavioral * bd.facts.get("penalty", 1.0)
    return max(0.0, min(final, 1.0))


# ============================================================================
# REASONING GENERATION (specific, varied, honest)
# ============================================================================


def generate_reasoning(candidate: Dict, bd: ScoreBreakdown, score: float) -> str:
    profile = candidate.get("profile", {}) or {}
    title = profile.get("current_title", "Candidate") or "Candidate"
    yoe = profile.get("years_of_experience", 0) or 0
    f = bd.facts

    parts: List[str] = [f"{title}, {yoe:.0f} yrs"]

    # strongest evidence
    if f.get("built_evidence"):
        parts.append("career shows production ranking/retrieval work")
    matched = f.get("matched_skills") or []
    if matched:
        parts.append("skills incl. " + ", ".join(matched[:3]))
    elif f.get("tier1_skills"):
        parts.append(f"{f['tier1_skills']} core ML skills")

    # one behavioral signal
    rr = f.get("response_rate")
    if rr is not None:
        parts.append(f"response rate {rr:.0%}")

    base = "; ".join(parts) + "."

    # honest concerns (rank-consistent)
    concerns = []
    if f.get("services_only"):
        concerns.append("services-only background")
    if f.get("research_heavy"):
        concerns.append("research-heavy, limited production")
    if not f.get("in_india", True) and not f.get("willing_relocate", False):
        concerns.append("outside India, relocation unclear")
    di = f.get("days_inactive")
    if di is not None and di > 120:
        concerns.append(f"inactive ~{di//30} months")
    notice = f.get("notice")
    if notice and notice > 90:
        concerns.append(f"notice {notice}d")
    if "skill_inflation" in bd.honeypot_flags:
        concerns.append("many low-endorsement skills")

    if concerns and score < 0.85:
        base += " Concern: " + ", ".join(concerns[:2]) + "."
    elif score >= 0.85:
        base += " Strong end-to-end fit."

    return base[:230]


# ============================================================================
# PIPELINE
# ============================================================================


def iter_candidates(path: str) -> Iterator[Dict]:
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def score_candidate(candidate: Dict) -> Tuple[str, float, str]:
    cid = candidate.get("candidate_id", "")
    bd = score_breakdown(candidate)
    score = calculate_final_score(candidate, bd)
    reasoning = generate_reasoning(candidate, bd, score)
    return cid, score, reasoning


def rank_candidates(path: str, top_n: int = 100, log_every: int = 20000
                    ) -> Tuple[List[ScoredCandidate], int]:
    """Stream, score, keep a running top-N heap. Returns (top, total_count)."""
    heap: List[Tuple[float, str, str]] = []  # (score, neg-id-sortable, reasoning)
    total = 0
    t0 = time.time()
    for cand in iter_candidates(path):
        total += 1
        cid, score, reasoning = score_candidate(cand)
        if not cid:
            continue
        # Round to the exact precision written to CSV so the (score, id) sort
        # below is consistent with what the validator reads (avoids tie-break
        # violations when distinct full-precision scores round to equal values).
        score = round(score, 4)
        # We want highest score; tie-break candidate_id ASCending.
        # heapq is a min-heap, so use key (score, -id_rank) won't work for strings.
        # Keep all qualifying then sort; but to bound memory keep heap of size top_n*5.
        heap.append((score, cid, reasoning))
        if len(heap) > top_n * 50:
            heap.sort(key=lambda x: (-x[0], x[1]))
            del heap[top_n * 10:]
        if log_every and total % log_every == 0:
            print(f"  scored {total} ({total/(time.time()-t0):.0f}/s)", file=sys.stderr)

    heap.sort(key=lambda x: (-x[0], x[1]))
    top = [ScoredCandidate(cid, sc, rsn) for sc, cid, rsn in heap[:top_n]]
    return top, total


def export_csv(scored: List[ScoredCandidate], output_path: str) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, sc in enumerate(scored, 1):
            writer.writerow([sc.candidate_id, rank, f"{sc.score:.4f}", sc.reasoning])


# ============================================================================
# CLI
# ============================================================================


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Rank candidates for the Redrob hackathon")
    parser.add_argument("--candidates", required=True, help="Path to candidates.jsonl[.gz]")
    parser.add_argument("--out", required=True, help="Output CSV path")
    parser.add_argument("--top", type=int, default=100, help="Top-N to output (default 100)")
    args = parser.parse_args(argv)

    t0 = time.time()
    print(f"Loading + scoring from {args.candidates} ...", file=sys.stderr)
    top, total = rank_candidates(args.candidates, top_n=args.top)
    print(f"Scored {total} candidates in {time.time()-t0:.1f}s", file=sys.stderr)

    export_csv(top, args.out)
    print(f"Wrote {len(top)} ranked candidates to {args.out} "
          f"(total {time.time()-t0:.1f}s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
