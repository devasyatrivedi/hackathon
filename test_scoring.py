#!/usr/bin/env python3
"""
Calibration + unit tests for the Redrob ranker.

Run:  python -m pytest test_scoring.py -v
  or: python test_scoring.py        (no pytest needed - falls back to a runner)

These tests encode the *intended* behavior from IMPROVED_DESIGN.md:
  * ideal candidates score high (>=0.80)
  * keyword-stuffer / wrong-title traps score low
  * structurally-impossible profiles are disqualified (-1.0)
  * pillars and honeypot rules behave as specified
They are deliberately synthetic and do NOT reference any real candidate_id.
"""

from __future__ import annotations

import copy
from typing import Dict

import rank


# ---------------------------------------------------------------------------
# Synthetic profile builders
# ---------------------------------------------------------------------------

def _signals(**over) -> Dict:
    base = {
        "profile_completeness_score": 90,
        "signup_date": "2019-01-01",
        "last_active_date": "2026-06-01",
        "open_to_work_flag": True,
        "recruiter_response_rate": 0.8,
        "avg_response_time_hours": 12,
        "interview_completion_rate": 0.8,
        "offer_acceptance_rate": 0.7,
        "notice_period_days": 30,
        "expected_salary_range_inr_lpa": {"min": 25, "max": 40},
        "willing_to_relocate": True,
        "github_activity_score": 80,
        "verified_email": True,
        "verified_phone": True,
        "linkedin_connected": True,
    }
    base.update(over)
    return base


def make_candidate(cid="CAND_0000000", title="Senior AI Engineer", yoe=7,
                   location="Bangalore", country="India", skills=None,
                   career=None, education=None, signals=None) -> Dict:
    return {
        "candidate_id": cid,
        "profile": {
            "anonymized_name": "Test Person",
            "headline": title,
            "summary": "Engineer.",
            "location": location,
            "country": country,
            "years_of_experience": yoe,
            "current_title": title,
            "current_company": "Acme Product Co",
            "current_company_size": "1001-5000",
            "current_industry": "Software",
        },
        "career_history": career if career is not None else [],
        "education": education if education is not None else [
            {"institution": "Some Uni", "degree": "B.Tech", "field_of_study": "CS",
             "start_year": 2012, "end_year": 2016, "grade": "8.0", "tier": "tier_2"}],
        "skills": skills if skills is not None else [],
        "redrob_signals": signals if signals is not None else _signals(),
    }


def _skill(name, prof="advanced", end=20, dur=30):
    return {"name": name, "proficiency": prof, "endorsements": end, "duration_months": dur}


def _role(title, company, months, desc, size="1001-5000", start="2020-01-01", end="2023-01-01"):
    return {"company": company, "title": title, "start_date": start, "end_date": end,
            "duration_months": months, "is_current": False, "industry": "Software",
            "company_size": size, "description": desc}


IDEAL = make_candidate(
    title="Senior AI Engineer", yoe=7,
    skills=[_skill("FAISS"), _skill("sentence-transformers"), _skill("Pinecone"),
            _skill("Python"), _skill("LoRA"), _skill("Learning to Rank")],
    career=[
        _role("Senior ML Engineer", "Flipkart", 36,
              "Built and deployed an embeddings-based retrieval and ranking system "
              "serving production search to millions of users; ran A/B tests, NDCG "
              "evaluation, vector search with FAISS, semantic search relevance."),
        _role("ML Engineer", "Swiggy", 30,
              "Shipped a recommendation system in production; latency-optimized "
              "serving, offline-to-online evaluation."),
    ])

KEYWORD_STUFFER = make_candidate(  # all AI keywords, wrong title, no tech career
    title="Marketing Manager", yoe=6, cid="CAND_0000002",
    skills=[_skill("FAISS"), _skill("Pinecone"), _skill("RAG"), _skill("LoRA"),
            _skill("sentence-transformers"), _skill("Qdrant")],
    career=[_role("Marketing Manager", "Acme", 60,
                  "Ran marketing campaigns and managed budgets.")])

RESEARCH_ONLY = make_candidate(
    title="Research Scientist", yoe=8, cid="CAND_0000003",
    skills=[_skill("PyTorch"), _skill("Deep Learning")],
    career=[_role("Research Scientist", "University Lab", 96,
                  "Published papers on theoretical ML. Academic research only.")])

HONEYPOT_TENURE = make_candidate(  # single role longer than whole career
    title="ML Engineer", yoe=5, cid="CAND_0000004",
    skills=[_skill("FAISS")],
    career=[_role("ML Engineer", "Startup", 120,  # 10 yrs at job, claims 5 yrs total
                  "Built ranking systems.")])

HONEYPOT_EXPERT = make_candidate(  # expert in many skills, zero substance
    title="AI Engineer", yoe=6, cid="CAND_0000005",
    skills=[_skill("FAISS", "expert", 0, 0), _skill("Pinecone", "expert", 0, 0),
            _skill("RAG", "expert", 0, 0), _skill("LoRA", "expert", 0, 0)],
    career=[_role("AI Engineer", "Acme", 60, "Worked on AI.")])

BORDERLINE = make_candidate(  # adjacent: data eng, some ML exposure, services firm
    title="Data Engineer", yoe=6, cid="CAND_0000006",
    skills=[_skill("Spark"), _skill("Airflow"), _skill("Python"), _skill("SQL")],
    career=[_role("Data Engineer", "Infosys", 48,
                  "Built data pipelines with Spark and Airflow; some ML feature work.",
                  size="10001+")])


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_ideal_scores_high():
    s = rank.calculate_final_score(IDEAL)
    assert s >= 0.80, f"ideal candidate should score >=0.80, got {s:.3f}"


def test_keyword_stuffer_disqualified_or_low():
    s = rank.calculate_final_score(KEYWORD_STUFFER)
    assert s <= 0.30, f"wrong-title keyword stuffer should score low, got {s:.3f}"


def test_research_only_penalized():
    s = rank.calculate_final_score(RESEARCH_ONLY)
    assert s < rank.calculate_final_score(IDEAL)
    assert s <= 0.55, f"pure research should be penalized, got {s:.3f}"


def test_honeypot_tenure_disqualified():
    assert rank.calculate_final_score(HONEYPOT_TENURE) == -1.0


def test_honeypot_expert_disqualified():
    assert rank.calculate_final_score(HONEYPOT_EXPERT) == -1.0


def test_borderline_mid_range():
    s = rank.calculate_final_score(BORDERLINE)
    # adjacent profile at a services firm with no ranking/retrieval evidence:
    # should land clearly below the strong band but well above honeypot territory.
    assert 0.25 <= s <= 0.80, f"borderline should be mid-range, got {s:.3f}"


def test_ordering():
    ideal = rank.calculate_final_score(IDEAL)
    border = rank.calculate_final_score(BORDERLINE)
    stuffer = rank.calculate_final_score(KEYWORD_STUFFER)
    assert ideal > border > stuffer


def test_evidence_beats_keywords():
    """A plain-language candidate who BUILT a recsys should beat a keyword list
    with no career evidence (the JD's Tier-5 case)."""
    builder = make_candidate(
        title="Software Engineer", yoe=6, cid="CAND_0000007",
        skills=[_skill("Python")],
        career=[_role("Software Engineer", "Myntra", 48,
                      "Designed and shipped a product recommendation and search "
                      "ranking system to production; embeddings retrieval, relevance "
                      "tuning, A/B testing at scale for millions of users.")])
    keyword_only = make_candidate(
        title="Software Engineer", yoe=6, cid="CAND_0000008",
        skills=[_skill("FAISS", end=0, dur=0), _skill("Pinecone", end=0, dur=0),
                _skill("RAG", end=0, dur=0)],
        career=[_role("Software Engineer", "Acme", 48, "Wrote backend code.")])
    assert rank.calculate_final_score(builder) > rank.calculate_final_score(keyword_only)


def test_behavioral_multiplier_bounds():
    for cand in (IDEAL, BORDERLINE, RESEARCH_ONLY):
        m, _ = rank.calculate_behavioral_multiplier(cand)
        assert 0.80 <= m <= 1.10


def test_offer_rate_minus_one_neutral():
    """offer_acceptance_rate == -1 (no history) must not penalize."""
    base = copy.deepcopy(IDEAL)
    base["redrob_signals"]["offer_acceptance_rate"] = 0.7
    no_hist = copy.deepcopy(IDEAL)
    no_hist["redrob_signals"]["offer_acceptance_rate"] = -1
    m1, _ = rank.calculate_behavioral_multiplier(base)
    m2, _ = rank.calculate_behavioral_multiplier(no_hist)
    assert abs(m1 - m2) < 0.05, "no offer history should be ~neutral, not a penalty"


def test_github_minus_one_neutral():
    cand = copy.deepcopy(IDEAL)
    cand["redrob_signals"]["github_activity_score"] = -1
    m, _ = rank.calculate_behavioral_multiplier(cand)
    assert m >= 0.80


def test_location_outside_india_downweighted():
    abroad = make_candidate(location="Toronto", country="Canada",
                            signals=_signals(willing_to_relocate=False))
    mod_abroad, _ = rank.calculate_location_modifier(abroad)
    india = make_candidate(location="Pune", country="India")
    mod_india, _ = rank.calculate_location_modifier(india)
    assert mod_abroad < mod_india


def test_missing_fields_no_crash():
    assert rank.calculate_final_score({"candidate_id": "CAND_0000009"}) >= -1.0
    assert rank.calculate_final_score({}) >= -1.0


def test_reasoning_is_specific_and_bounded():
    bd = rank.score_breakdown(IDEAL)
    s = rank.calculate_final_score(IDEAL, bd)
    r = rank.generate_reasoning(IDEAL, bd, s)
    assert len(r) <= 230
    assert "Senior AI Engineer" in r
    assert r.endswith(".")


# ---------------------------------------------------------------------------
# Minimal runner (so it works without pytest installed)
# ---------------------------------------------------------------------------

def _run() -> int:
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
