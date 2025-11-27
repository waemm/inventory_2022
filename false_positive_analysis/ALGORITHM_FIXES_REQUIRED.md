# Fuzzy Matching Algorithm - Required Fixes

**Date:** 2025-11-27
**Status:** CRITICAL - Algorithm not production-ready
**Priority:** P0 - Must fix before any production use

---

## Executive Summary

The enhanced fuzzy matching algorithm has a **critical flaw** in SAME_DOMAIN handling that results in an estimated **20-30% false positive rate** (target: <5%). This document provides specific, actionable fixes required before production deployment.

**Key Issue:** SAME_DOMAIN alone scores 2.0, triggering HIGH confidence, but institutional domains (.ac.uk, .edu.cn, .nih.gov) host dozens of unrelated databases.

**Impact:**
- 355+ confirmed false positive candidates
- 468 baseline databases incorrectly matched to multiple extracted databases
- One baseline (memprotmd) matched to 37 different databases

---

## Required Fixes (Priority Order)

### 🔴 FIX #1: Reduce SAME_DOMAIN Scoring Weight
**Priority:** P0 - Critical
**Effort:** Low (1-2 hours)
**Impact:** Eliminates majority of false positives

#### Current Code (pseudocode):
```python
if extracted_domain == baseline_domain:
    score += 2.0  # ← PROBLEM: This alone triggers HIGH confidence
```

#### Required Fix:
```python
# Differentiate between generic and specific domains
if extracted_domain == baseline_domain:
    # Generic institutional domains (many databases)
    if is_generic_domain(extracted_domain):  # .ac.uk, .edu.cn, .nih.gov, etc.
        score += 0.25
    # Specific database-focused domains
    else:
        score += 0.75
```

#### Generic Domain List:
```python
GENERIC_DOMAINS = [
    '.ac.uk',    # UK universities
    '.edu.cn',   # Chinese universities
    '.ac.cn',    # Chinese academic
    '.edu.tw',   # Taiwan universities
    '.ac.jp',    # Japanese universities
    '.ac.kr',    # Korean universities
    '.ac.in',    # Indian universities
    '.res.in',   # Indian research institutes
    '.nih.gov',  # US NIH (multiple institutes)
    '.edu.au',   # Australian universities
    'github.io', # GitHub pages (many users)
    'gbif.org',  # GBIF (many datasets)
]
```

#### Validation:
After fix, re-run and verify:
- No matches should have is_match='Y' from SAME_DOMAIN alone
- SAME_DOMAIN + other signals should still work correctly

---

### 🔴 FIX #2: Require Multiple Signals for HIGH Confidence
**Priority:** P0 - Critical
**Effort:** Low (2-3 hours)
**Impact:** Prevents single weak signal from triggering HIGH confidence

#### Current Code:
```python
if score >= 2.0:
    is_match = 'Y'  # ← Can be triggered by single signal
```

#### Required Fix:
```python
# Count distinct signal types
signal_count = 0
if has_same_domain: signal_count += 1
if has_url_similarity > 0.8: signal_count += 1
if has_name_similarity: signal_count += 1
if has_edit_distance <= 2: signal_count += 1
if has_contains: signal_count += 1
if has_digit_diff: signal_count += 1

# Require multiple signals for HIGH confidence
if score >= 2.0 and signal_count >= 2:
    is_match = 'Y'
elif score >= 1.0:
    is_match = 'MAYBE'
else:
    is_match = 'N'
```

#### Special Cases:
```python
# EXACT match always Y regardless of signal count
if match_type == 'EXACT':
    is_match = 'Y'

# Very high URL similarity can override signal count requirement
if url_path_sim >= 0.95 and long_sim >= 0.95:
    if score >= 2.0:
        is_match = 'Y'
```

---

### 🔴 FIX #3: Add Subdomain Distinction
**Priority:** P0 - Critical
**Effort:** Medium (3-4 hours)
**Impact:** Prevents matching different databases on same platform

#### Problem Example:
```
breastcancer.gxbsidra.org vs sepsis.gxbsidra.org
→ Currently: SAME_DOMAIN ✓
→ Should be: DIFFERENT_SUBDOMAIN ✗
```

#### Required Fix:
```python
def get_effective_domain(url):
    """
    Extract domain including subdomain for multi-database hosts.

    Examples:
    - breastcancer.gxbsidra.org → breastcancer.gxbsidra.org
    - www.ebi.ac.uk → ebi.ac.uk (strip www)
    - http://2d.bjmu.edu.cn → 2d.bjmu.edu.cn
    """
    parsed = urlparse(url)
    hostname = parsed.netloc or parsed.path.split('/')[0]

    # Strip www prefix
    if hostname.startswith('www.'):
        hostname = hostname[4:]

    # For known multi-database platforms, keep full subdomain
    MULTI_DB_PLATFORMS = [
        'gxbsidra.org',
        'github.io',
        'shinyapps.io',
        'gbif.org',
    ]

    for platform in MULTI_DB_PLATFORMS:
        if hostname.endswith(platform):
            return hostname  # Keep subdomain

    # For others, extract base domain
    parts = hostname.split('.')
    if len(parts) >= 2:
        # Keep last 2-3 parts depending on TLD
        if parts[-2] in ['ac', 'co', 'edu', 'gov']:
            return '.'.join(parts[-3:])
        else:
            return '.'.join(parts[-2:])

    return hostname

# Then in matching logic:
extracted_effective = get_effective_domain(extracted_url)
baseline_effective = get_effective_domain(baseline_url)

if extracted_effective == baseline_effective:
    # Apply SAME_DOMAIN logic
```

---

### 🔴 FIX #4: Enforce One-to-One Mapping
**Priority:** P0 - Critical
**Effort:** Medium (4-5 hours)
**Impact:** Ensures database uniqueness

#### Current Behavior:
- One baseline database can match multiple extracted databases
- Example: memprotmd matched by 37 different databases

#### Required Fix:
```python
def resolve_conflicts(all_matches):
    """
    For each baseline database matched by multiple extracted databases,
    keep only the best match.
    """
    # Group by baseline_name
    grouped = all_matches[all_matches['is_match'] == 'Y'].groupby('baseline_name')

    best_matches = []
    for baseline, group in grouped:
        if len(group) == 1:
            best_matches.append(group.iloc[0])
        else:
            # Multiple matches - select best
            # Priority:
            # 1. EXACT match
            # 2. Highest score
            # 3. Lowest edit distance
            # 4. Shortest name (fewer chars difference)

            exact = group[group['match_type'] == 'EXACT']
            if len(exact) > 0:
                best_matches.append(exact.iloc[0])
                continue

            # Sort by score desc, edit_distance asc
            sorted_group = group.sort_values(
                by=['score', 'edit_distance', 'extracted_name'],
                ascending=[False, True, True]
            )
            best_matches.append(sorted_group.iloc[0])

            # Mark others as conflicts
            conflicts = sorted_group.iloc[1:]
            for idx, row in conflicts.iterrows():
                print(f"CONFLICT: {row['extracted_name']} → {baseline} "
                      f"(score={row['score']:.2f}) "
                      f"rejected in favor of {sorted_group.iloc[0]['extracted_name']}")

    return pd.DataFrame(best_matches)
```

---

### ⚠️ FIX #5: Increase Edit Distance Weights
**Priority:** P1 - High
**Effort:** Low (1 hour)
**Impact:** Reduces false negatives

#### Current Code:
```python
if edit_distance == 1:
    score += 0.5  # → MAYBE category
if edit_distance == 2:
    score += 0.5  # → MAYBE category
```

#### Recommended Fix:
```python
if edit_distance == 0:
    score += 2.0  # Identical (should be rare, handled by EXACT)
elif edit_distance == 1:
    score += 1.0  # Very close (typo, capitalization)
elif edit_distance == 2:
    score += 0.75  # Close (minor abbreviation)
elif edit_distance == 3:
    score += 0.5
else:
    # Don't add score for edit_distance > 3
    pass
```

#### Rationale:
- Edit distance of 1 is often a typo or capitalization difference
- Examples: "PSIMR" vs "psmir", "5SRNAdb" vs "sRNAdb"
- Current scoring (0.5) puts these in MAYBE, but they're likely matches

---

### ⚠️ FIX #6: Add Context-Aware Contains Matching
**Priority:** P1 - High
**Effort:** Medium (2-3 hours)
**Impact:** Reduces false positives from substring matches

#### Problem Examples:
- "UCSC" contains "USC" (but different databases)
- "contains" currently adds 1.0 score regardless of context

#### Required Fix:
```python
def calculate_contains_score(shorter, longer):
    """
    Score substring containment based on context.
    """
    if shorter not in longer:
        return 0.0

    # If shorter is complete token in longer, strong signal
    # Example: "GWAS" in "GWAS Catalog"
    tokens = re.findall(r'\b\w+\b', longer.lower())
    if shorter.lower() in tokens:
        return 1.0

    # If shorter is significant portion of longer (>50%), medium signal
    # Example: "ProBiS-Dock" in "ProBiS-Dock Database"
    if len(shorter) / len(longer) >= 0.5:
        return 0.75

    # If shorter is acronym of longer, strong signal
    # Example: "UMCD" in "UCLA Multimodal Connectivity Database"
    if is_acronym(shorter, longer):
        return 1.0

    # Otherwise, weak signal
    return 0.25

def is_acronym(short, long):
    """Check if short is acronym of long."""
    words = re.findall(r'\b\w+\b', long)
    if len(short) != len(words):
        return False

    for i, word in enumerate(words):
        if short[i].upper() != word[0].upper():
            return False
    return True
```

---

### ⚠️ FIX #7: Add Manual Review Flags
**Priority:** P1 - High
**Effort:** Low (1-2 hours)
**Impact:** Improves review efficiency

#### Implementation:
```python
def add_review_flags(match_record):
    """Add flags for cases requiring manual review."""
    flags = []

    # High edit distance but marked as match
    if match_record['edit_distance'] > 10 and match_record['is_match'] == 'Y':
        flags.append('HIGH_ED_MATCH')

    # SAME_DOMAIN only (no other signals)
    if 'SAME_DOMAIN' in match_record['reasoning']:
        if not any(x in match_record['reasoning'] for x in
                   ['url_path_sim', 'long_sim', 'contains', 'edit_dist']):
            flags.append('SAME_DOMAIN_ONLY')

    # Score near threshold
    if 1.9 <= match_record['score'] < 2.1:
        flags.append('THRESHOLD_EDGE')

    # Low edit distance but marked as non-match
    if match_record['edit_distance'] <= 2 and match_record['is_match'] == 'N':
        flags.append('LOW_ED_NOMATCH')

    match_record['review_flags'] = ','.join(flags) if flags else ''
    return match_record
```

---

## Implementation Plan

### Phase 1: Critical Fixes (Days 1-2)
1. ✓ Implement FIX #1: Reduce SAME_DOMAIN weight
2. ✓ Implement FIX #2: Multi-signal requirement
3. ✓ Implement FIX #3: Subdomain distinction
4. ✓ Implement FIX #4: One-to-one mapping
5. ✓ Run algorithm on test dataset
6. ✓ Verify fixes resolve major false positives

### Phase 2: High Priority Fixes (Day 3)
1. ✓ Implement FIX #5: Edit distance weights
2. ✓ Implement FIX #6: Context-aware contains
3. ✓ Implement FIX #7: Review flags
4. ✓ Run full algorithm on complete dataset
5. ✓ Generate review sample files

### Phase 3: Manual Validation (Days 4-6)
1. Review suspicious_same_domain.csv (priority 1)
2. Review sample files (priority 2)
3. Verify false positive rate < 5%
4. Verify false negative rate < 10%
5. Document any edge cases discovered

### Phase 4: Final Validation (Day 7)
1. Run complete algorithm with all fixes
2. Generate final statistics
3. Compare before/after metrics
4. Document improvement
5. Get stakeholder approval for production use

---

## Testing Requirements

### Unit Tests
```python
def test_same_domain_generic():
    """Test that generic domains get reduced score."""
    assert calculate_domain_score('.ac.uk') == 0.25
    assert calculate_domain_score('specific.database.org') == 0.75

def test_multi_signal_requirement():
    """Test that single signal doesn't trigger HIGH."""
    score = 2.0
    signal_count = 1
    assert get_match_decision(score, signal_count) != 'Y'

    signal_count = 2
    assert get_match_decision(score, signal_count) == 'Y'

def test_subdomain_distinction():
    """Test that different subdomains are distinguished."""
    url1 = 'http://breastcancer.gxbsidra.org/dm3'
    url2 = 'http://sepsis.gxbsidra.org/dm3'
    assert get_effective_domain(url1) != get_effective_domain(url2)

def test_one_to_one_mapping():
    """Test that baseline maps to only one extracted DB."""
    matches = create_test_matches()
    resolved = resolve_conflicts(matches)
    baseline_counts = resolved.groupby('baseline_name').size()
    assert (baseline_counts == 1).all()
```

### Integration Tests
```python
def test_known_false_positives():
    """Test that known false positives are now rejected."""
    # Phasing Server should NOT match memprotmd
    result = match('Phasing Server', 'memprotmd',
                   'https://phasingserver.stats.ox.ac.uk/',
                   'http://memprotmd.bioch.ox.ac.uk')
    assert result['is_match'] != 'Y'

    # PMC BioC should NOT match TB Portals
    result = match('PMC BioC', 'tbpp',
                   'https://www.ncbi.nlm.nih.gov/research/bionlp/APIs/BioC-PMC/',
                   'http://TBPortals.niaid.nih.gov')
    assert result['is_match'] != 'Y'

def test_known_true_positives():
    """Test that known true positives still match."""
    # Exact matches should always work
    result = match('MemProtMD', 'memprotmd', url1, url2)
    assert result['is_match'] == 'Y'

    # High similarity with same domain should work
    result = match('UMCD', 'ucla multimodal connectivity database',
                   'http://umcd.neurology.ucla.edu',
                   'http://umcd.neurology.ucla.edu')
    if result['url_path_sim'] == 1.0 and result['long_sim'] == 1.0:
        assert result['is_match'] == 'Y'
```

---

## Success Criteria

Before production deployment, require:

1. **False Positive Rate < 5%**
   - Current: ~20-30%
   - Target: <5%
   - Measurement: Manual review of 100 random Y matches

2. **False Negative Rate < 10%**
   - Current: Unknown
   - Target: <10%
   - Measurement: Manual review of 50 random N matches with low edit distance

3. **One-to-One Mapping**
   - Current: 468 violations
   - Target: 0 violations
   - Measurement: Automated check

4. **No SAME_DOMAIN-Only HIGH Confidence**
   - Current: 355+ cases
   - Target: 0 cases
   - Measurement: Automated check

5. **Stakeholder Approval**
   - Review sample results
   - Approve for production use

---

## Rollback Plan

If fixes introduce regressions:

1. Keep previous version of algorithm in separate branch
2. Compare match counts before/after
3. If total matches drop >20%, investigate
4. If false positive rate doesn't improve, revert and reconsider approach

---

## Code Review Checklist

Before merging fixes:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No SAME_DOMAIN-only Y matches
- [ ] No baseline with >1 extracted match
- [ ] False positive rate verified < 5%
- [ ] Code reviewed by 2+ engineers
- [ ] Documentation updated
- [ ] Performance impact assessed (should be minimal)

---

## Appendix: Confirmed False Positives

### Sample Size: 36 confirmed

1. Phasing Server → memprotmd
2. Proteins API → memprotmd
3. BCAPE → memprotmd
4. Badger → memprotmd
5. miRAtlas → memprotmd
6. Lancaster Sensorimotor Norms → memprotmd
7. CCPN Metabolomics → memprotmd
8. BioStudies → memprotmd
9. MolClass → memprotmd
10. canSAR → memprotmd
11. PINOT → memprotmd
12. PSICQUIC → memprotmd
13. ID-TaxER → memprotmd
14. DRSASP → memprotmd
15. BLUEPRINT → memprotmd
16. WGE → memprotmd
17. FlowerNet → memprotmd
18. Platinum → memprotmd
19. Coiled Coils Atlas → memprotmd
20. PROSPERO → memprotmd
21. UniRule → memprotmd
22. PhenoScanner → memprotmd
23. BacillusRegNet → memprotmd
24. PolyTB → memprotmd
25. dbTF → memprotmd
26. ComplexPortal → memprotmd
27. AnatomyTagger → memprotmd
28. OPCRIT+ → memprotmd
29. Mespeus → memprotmd
30. SYNS → memprotmd
31. BμG@Sbase → memprotmd
32. Pathos → memprotmd
33. VirtualSeed → memprotmd
34. PDE3 → memprotmd
35. PRINTS → memprotmd
36. VSeed → memprotmd

**Pattern:** All share .ac.uk domain with memprotmd but are completely different databases from different UK universities.

---

**Document prepared by:** Code Review Team
**Date:** 2025-11-27
**Next Review:** After Phase 1 implementation
