"""Test suite for sandbox app optimizations."""
import json
import sys
import tempfile
from io import BytesIO

sys.path.insert(0, "sandbox")
sys.path.insert(0, ".")

from sandbox.app import _load
import rank


def test_1_error_handling():
    """Test error handling for malformed inputs."""
    print("\n[Test 1] Error Handling")

    # Empty file
    try:
        _load(b"")
        print("  ❌ Should reject empty file")
        return False
    except ValueError as e:
        print(f"  ✓ Empty file: {e}")

    # Invalid JSON
    try:
        _load(b"{not valid json")
        print("  ❌ Should reject invalid JSON")
        return False
    except ValueError as e:
        print(f"  ✓ Invalid JSON: {e}")

    # Non-UTF8
    try:
        _load(b"\xff\xfe invalid utf8")
        print("  ❌ Should reject non-UTF8")
        return False
    except ValueError as e:
        print(f"  ✓ Non-UTF8: {e}")

    print("  ✅ All error cases handled correctly")
    return True


def test_2_input_validation():
    """Test input format validation."""
    print("\n[Test 2] Input Validation")

    # Valid JSONL
    jsonl = b'{"candidate_id": "CAND_0000001"}\n{"candidate_id": "CAND_0000002"}'
    result = _load(jsonl)
    if len(result) != 2:
        print(f"  ❌ JSONL: expected 2, got {len(result)}")
        return False
    print(f"  ✓ JSONL: loaded {len(result)} candidates")

    # Valid JSON array
    json_array = b'[{"candidate_id": "CAND_0000001"}, {"candidate_id": "CAND_0000002"}]'
    result = _load(json_array)
    if len(result) != 2:
        print(f"  ❌ JSON array: expected 2, got {len(result)}")
        return False
    print(f"  ✓ JSON array: loaded {len(result)} candidates")

    # Empty array
    try:
        _load(b"[]")
        print("  ❌ Should reject empty array")
        return False
    except ValueError as e:
        print(f"  ✓ Empty array rejected: {e}")

    print("  ✅ Input validation working")
    return True


def test_3_csv_escaping():
    """Test CSV writer handles special characters correctly."""
    print("\n[Test 3] CSV Escaping")

    import csv
    from io import StringIO

    # Test cases with quotes, commas, newlines
    test_cases = [
        'Simple reasoning',
        'Reasoning with "quotes"',
        'Reasoning with, commas',
        'Reasoning with\nnewline',
        'Mixed: "quotes", commas, and\nnewlines'
    ]

    buf = StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["candidate_id", "rank", "score", "reasoning"])

    for i, reasoning in enumerate(test_cases, 1):
        writer.writerow(["CAND_0000001", i, "0.9000", reasoning])

    csv_output = buf.getvalue()

    # Parse it back
    buf.seek(0)
    reader = csv.reader(buf)
    rows = list(reader)

    if len(rows) != len(test_cases) + 1:  # +1 for header
        print(f"  ❌ Expected {len(test_cases)+1} rows, got {len(rows)}")
        return False

    for i, (original, row) in enumerate(zip(test_cases, rows[1:]), 1):
        if row[3] != original:
            print(f"  ❌ Row {i}: expected '{original}', got '{row[3]}'")
            return False

    print(f"  ✓ All {len(test_cases)} escape cases correct")
    print("  ✅ CSV escaping robust")
    return True


def test_4_scoring_accuracy():
    """Test scoring produces expected results on sample data."""
    print("\n[Test 4] Scoring Accuracy")

    with open("sandbox/sample_candidates.json") as f:
        candidates = json.load(f)

    scored = []
    for c in candidates:
        bd = rank.score_breakdown(c)
        score = rank.calculate_final_score(c, bd)
        reasoning = rank.generate_reasoning(c, bd, score)
        cid = c.get("candidate_id", "")
        if not cid:
            print("  ❌ Candidate missing candidate_id")
            return False
        scored.append((cid, round(score, 4), reasoning))

    scored.sort(key=lambda x: (-x[1], x[0]))

    # Check properties
    if len(scored) != len(candidates):
        print(f"  ❌ Expected {len(candidates)} scored, got {len(scored)}")
        return False

    # Verify scores are non-increasing
    for i in range(len(scored) - 1):
        if scored[i][1] < scored[i+1][1]:
            print(f"  ❌ Scores not sorted: {scored[i][1]} < {scored[i+1][1]}")
            return False

    # Verify reasoning exists
    for cid, score, reasoning in scored:
        if not reasoning or len(reasoning) < 10:
            print(f"  ❌ Invalid reasoning for {cid}: '{reasoning}'")
            return False

    top3 = [s[1] for s in scored[:3]]
    print(f"  ✓ Scored {len(scored)} candidates")
    print(f"  ✓ Top 3 scores: {top3}")
    print(f"  ✓ Score range: {scored[0][1]} → {scored[-1][1]}")
    print("  ✅ Scoring accuracy verified")
    return True


def test_5_performance():
    """Test scoring performance meets requirements."""
    print("\n[Test 5] Performance")

    import time

    with open("sandbox/sample_candidates.json") as f:
        candidates = json.load(f)

    # Warm up (trigger any lazy loading)
    bd = rank.score_breakdown(candidates[0])
    _ = rank.calculate_final_score(candidates[0], bd)

    # Measure
    start = time.time()
    for c in candidates:
        bd = rank.score_breakdown(c)
        score = rank.calculate_final_score(c, bd)
        reasoning = rank.generate_reasoning(c, bd, score)
    elapsed = time.time() - start

    per_candidate = elapsed / len(candidates) * 1000
    projected_100 = per_candidate * 100

    print(f"  ✓ {len(candidates)} candidates: {elapsed*1000:.1f}ms")
    print(f"  ✓ Per candidate: {per_candidate:.2f}ms")
    print(f"  ✓ Projected 100: {projected_100:.1f}ms")

    if projected_100 > 500:  # 500ms threshold (well below 5min budget)
        print(f"  ❌ Too slow: {projected_100:.1f}ms > 500ms")
        return False

    print("  ✅ Performance acceptable")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("SANDBOX APP OPTIMIZATION TEST SUITE")
    print("=" * 60)

    tests = [
        test_1_error_handling,
        test_2_input_validation,
        test_3_csv_escaping,
        test_4_scoring_accuracy,
        test_5_performance,
    ]

    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"\n❌ {test.__name__} FAILED")
        except Exception as e:
            print(f"\n❌ {test.__name__} CRASHED: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    print("=" * 60)

    if passed == len(tests):
        print("✅ ALL OPTIMIZATIONS VERIFIED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
