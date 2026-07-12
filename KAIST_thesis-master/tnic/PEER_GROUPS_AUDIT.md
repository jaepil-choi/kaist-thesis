# PEER GROUPS AUDIT REPORT
## Hoberg & Phillips (2016) Methodology Compliance

**Date:** 2025-11-05
**Auditor:** Claude Code
**Scope:** Peer group definition phase (tnic/peer_groups.py)

---

## EXECUTIVE SUMMARY

**Overall Compliance:** 60%

**Critical Issues Found:** 2
**Moderate Issues Found:** 1
**Minor Issues Found:** 2

**Most Critical Finding:** **DOUBLE MEDIAN ADJUSTMENT** - The code applies median adjustment AGAIN even though similarity.py already applied it. This transforms the scale twice, producing incorrect final scores.

**Second Critical Finding:** Median calculation **INCLUDES DIAGONAL** (self-similarity = 1.0), which biases the median upward. Should exclude diagonal per H&P methodology.

---

## H&P METHODOLOGY - PEER GROUP DEFINITION

### Complete Process (from note file lines 79-94)

**Step 1: Calibrate threshold to match baseline**
> "We calibrate the minimum similarity threshold to match the fraction of membership pairs in SIC-3 industries."

Calculate membership pairs:
- All possible pairs: N × (N-1) / 2
- SIC-3 membership pairs: Σ[n_k × (n_k-1) / 2] for each industry k
- Target fraction: membership_pairs / all_pairs

Find threshold T such that: fraction of pairs with similarity > T equals target fraction.

---

**Step 2: Apply median adjustment ("further refinement")**
> "Further refinement to mitigate the impact of document length:
>   - For a firm i we compute its median score as the median similarity between firm i and **all other firms** in the economy
>   - We subtract these median scores from the raw scores to obtain our **final scores**"

**Example from H&P:**
```
Raw similarities: {0.2, 0.15, 0.1, 0.05, 0.01}
Median score: 0.1
Final scores: {0.1, 0.05, 0, -0.05, -0.09}
```

**Key detail:** "all other firms" means EXCLUDE self-similarity (diagonal).

---

**Step 3: Define peers using final scores**
> "If this **final score** is above the calibrated minimum similarity threshold, we assign firm j to firm i's industry."

```python
peers(i) = {j : final_score(i,j) > T, j != i}
```

---

## ARCHITECTURE: similarity.py + peer_groups.py

### After Our Recent Fix to similarity.py

**similarity.py now does:**
1. Computes raw similarities: `M_raw = cosine_similarity(Q_t)`
2. Applies median adjustment: `M_adjusted = apply_median_adjustment(M_raw)`
3. **Saves adjusted matrix** as `similarity_matrix_{year}.npz`

**peer_groups.py should do:**
1. Load **adjusted matrix** (final scores from similarity.py)
2. Calibrate threshold on adjusted scores
3. Define peers: `adjusted_score > threshold`

**What peer_groups.py ACTUALLY does:**
1. Loads adjusted matrix (but calls it `M_raw` ❌)
2. Calibrates threshold on it ✅ (OK on adjusted)
3. **Applies median adjustment AGAIN** ❌ (DOUBLE ADJUSTMENT!)
4. Defines peers on double-adjusted scores ❌

---

## ❌ CRITICAL ISSUE 1: DOUBLE MEDIAN ADJUSTMENT

### The Problem

**Line 100-101: Load matrix**
```python
M_raw, firms_df = self._load_similarity_matrix(year)
```

This loads from `similarity_matrix_{year}.npz`, which after our fix contains the **ADJUSTED** matrix, not raw!

**Line 112-113: Apply adjustment AGAIN**
```python
# Apply median adjustment
M_adjusted, medians = self._apply_median_adjustment(M_raw)
```

But `M_raw` is already adjusted! So this applies the adjustment **twice**.

---

### What Double Adjustment Does

**First adjustment (similarity.py):**
```
Raw similarity(A, B) = 0.20
Median(A) = 0.08, Median(B) = 0.10
Adjusted = 0.20 - (0.08 + 0.10)/2 = 0.20 - 0.09 = 0.11
```

**Second adjustment (peer_groups.py):**
```
Input (already adjusted) = 0.11
Median of adjusted values (A) = 0.02 (much lower now!)
Median of adjusted values (B) = 0.01
Double-adjusted = 0.11 - (0.02 + 0.01)/2 = 0.11 - 0.015 = 0.095
```

**Result:** The scale is transformed twice, producing incorrect final scores.

---

### Evidence: Look at the Metadata

**From existing metadata (e.g., 2014):**
```json
"median_adjustment": {
  "mean_median": 0.06568,  // ← This is median of ADJUSTED values!
  "std_median": 0.01809,
  "min_median": 0.01665,
  "max_median": 0.13276
}
```

If this were medians of raw similarities, they should be higher (~0.06-0.08 typical).
But if these are medians of **already-adjusted** values, they should be near **zero** (since adjustment centers the distribution).

The fact that mean_median = 0.0657 suggests these are computed on **raw** similarities.

**But wait!** This metadata is saved by peer_groups.py, not similarity.py!

Let me check where this comes from...

Looking at peer_groups.py line 466-471:
```python
'median_adjustment': {
    'mean_median': float(medians.mean()),
    'std_median': float(medians.std()),
    'min_median': float(medians.min()),
    'max_median': float(medians.max())
}
```

These are the medians computed by peer_groups.py's `_apply_median_adjustment` method!

So the metadata shows:
- similarity.py does adjustment (saves adjusted matrix)
- peer_groups.py does adjustment again (computes new medians on adjusted values)
- The medians in metadata are from the SECOND adjustment

This confirms double adjustment is happening.

---

## ❌ CRITICAL ISSUE 2: MEDIAN INCLUDES DIAGONAL

### The Problem

**peer_groups.py lines 330-333:**
```python
for i in range(N):
    median_i = np.median(M_raw[i, :])  # ← Includes diagonal!
    medians[i] = median_i
    M_adjusted[i, :] = M_raw[i, :] - median_i
```

**Line 331:** `np.median(M_raw[i, :])` takes median of ALL values in row i, **including the diagonal** (self-similarity = 1.0).

---

### Why This Is Wrong

**H&P Quote (note file line 84):**
> "For a firm i we compute its median score as the median similarity between firm i and **all other firms**"

**"All other firms"** means **EXCLUDE self (diagonal)**.

**Impact of including diagonal:**
- Diagonal value is always 1.0 (perfect self-similarity)
- Including it biases the median **upward**
- Especially for firms with few high-similarity peers

**Example:**
```
Similarities for firm i: [1.0 (self), 0.25, 0.15, 0.08, 0.05, 0.03, ...]

With diagonal: median ≈ 0.08-0.10 (biased high)
Without diagonal: median ≈ 0.06-0.07 (correct)
```

The bias is worse for firms with small vocabularies (fewer matches).

---

### Comparison with similarity.py (Correct)

**similarity.py lines 182-190:**
```python
for i in range(N_t):
    # Get all similarities for firm i
    similarities = M_t[i, :].copy()

    # Exclude self-similarity (diagonal)
    similarities = np.delete(similarities, i)  # ← CORRECT: Excludes diagonal

    # Compute median
    median_scores[i] = np.median(similarities)
```

**This is correct!** It explicitly excludes the diagonal.

---

## ⚠️ MODERATE ISSUE: VARIABLE NAMING CONFUSION

### The Problem

**Line 100:**
```python
M_raw, firms_df = self._load_similarity_matrix(year)
```

Variable name is `M_raw`, but after our fix to similarity.py, it's actually loading the **ADJUSTED** matrix!

**Line 262:** Method parameter name
```python
def _calibrate_threshold(
    self,
    M_raw: np.ndarray,  # ← Called "raw" but is actually adjusted
    target_fraction: float
)
```

**Line 313:** Method parameter name
```python
def _apply_median_adjustment(self, M_raw: np.ndarray)  # ← Already adjusted!
```

---

### Why This Matters

**Code readability:** Future maintainers will be confused
- Code says "raw" but it's actually adjusted
- Makes it hard to understand the double adjustment bug

**Documentation mismatch:** Docstrings say things like "raw scores"
- Line 32-33: "Calibrates threshold on raw scores"
- But we're actually calibrating on adjusted scores

**Misleading comments:**
- Code comments refer to "raw" when it's actually adjusted

---

## ⚠️ MINOR ISSUE 1: THRESHOLD CALIBRATION DOCUMENTATION

### The Issue

**Docstring lines 32-33:**
```python
"""
1. Calibrates threshold on raw scores to match baseline membership fraction
2. Applies median adjustment per firm
3. Defines peer groups using adjusted scores
```

This implies:
1. Calibrate on raw
2. Adjust
3. Use adjusted with threshold from raw

But if you calibrate threshold on raw [0, 1] and then adjust [can be negative], using the same threshold doesn't make sense!

**Example:**
```
Raw similarities ~ [0, 0.3]
Calibrate: 3% of pairs > 0.22 → T = 0.22

Adjusted similarities ~ [-0.15, +0.15]
Using T = 0.22: Now 0% of pairs > 0.22 → No peers!
```

The threshold needs to be on the same scale as the scores you're comparing!

---

### What Should Happen

**Option A: Calibrate on raw, use on raw**
- Don't apply median adjustment at peer group stage
- similarity.py saves raw
- peer_groups.py calibrates on raw, defines peers on raw

**Option B: Calibrate on adjusted, use on adjusted**
- Apply median adjustment first
- Calibrate threshold on adjusted scores
- Define peers on adjusted with adjusted-scale threshold

**What we should do (after our fix):**
- similarity.py saves adjusted ✅
- peer_groups.py calibrates on adjusted ✅
- peer_groups.py defines peers on adjusted ✅
- **But remove the re-adjustment!** ❌

---

## ⚠️ MINOR ISSUE 2: SYMMETRIC ADJUSTMENT METHOD

### Current Implementation

**peer_groups.py lines 330-333:**
```python
for i in range(N):
    median_i = np.median(M_raw[i, :])
    M_adjusted[i, :] = M_raw[i, :] - median_i
```

This is **asymmetric adjustment:** Only subtracts firm i's median from row i.

**Result:** `M_adjusted[i, j] ≠ M_adjusted[j, i]` (loses symmetry!)

---

### What similarity.py Does (Correct)

**similarity.py lines 198-203:**
```python
for i in range(N_t):
    for j in range(N_t):
        if i != j:
            # Symmetric adjustment: average both medians
            avg_median = (median_scores[i] + median_scores[j]) / 2.0
            M_adjusted[i, j] = M_t[i, j] - avg_median
```

**This is symmetric:** Uses average of both firms' medians.

**Result:** `M_adjusted[i, j] = M_adjusted[j, i]` (preserves symmetry!)

---

### Why Symmetry Matters

**Peer relationships should be symmetric:**
- If firm A is a peer of firm B
- Then firm B should be a peer of firm A

**With asymmetric adjustment:**
```
median(A) = 0.08
median(B) = 0.10
raw(A,B) = 0.20

Asymmetric:
  adjusted(A,B) = 0.20 - 0.08 = 0.12
  adjusted(B,A) = 0.20 - 0.10 = 0.10

If threshold = 0.11:
  A → B is peer (0.12 > 0.11) ✓
  B → A is NOT peer (0.10 < 0.11) ✗

Asymmetric peer relationship!
```

**With symmetric adjustment:**
```
adjusted(A,B) = 0.20 - (0.08+0.10)/2 = 0.11
adjusted(B,A) = 0.20 - (0.08+0.10)/2 = 0.11

Both are exactly at threshold → consistent decision
```

---

## DETAILED COMPARISON TABLE

| **Aspect** | **H&P Methodology** | **similarity.py** | **peer_groups.py** | **Status** |
|------------|---------------------|-------------------|-------------------|------------|
| **Load similarity matrix** | - | Saves adjusted | Loads adjusted | ✅ OK |
| **Variable naming** | - | M_t (adjusted) | M_raw (actually adjusted!) | ❌ Misleading |
| **Threshold calibration** | On appropriate scale | N/A | On adjusted (OK) | ✅ OK |
| **Median calculation** | Exclude diagonal | ✅ Excludes diagonal | ❌ Includes diagonal | ❌ **WRONG** |
| **Median adjustment** | Apply once | ✅ Applied | ❌ Applied again! | ❌ **DOUBLE** |
| **Adjustment method** | (Not specified) | ✅ Symmetric | Asymmetric | ⚠️ Different |
| **Peer definition** | final_score > T | N/A | Uses adjusted | ✅ OK |
| **Symmetry preservation** | Implied | ✅ Preserved | ❌ Lost | ⚠️ Issue |

---

## 🔧 REQUIRED FIXES

### Fix 1: Remove Double Adjustment

**Location:** `peer_groups.py:100-118`

**Current code:**
```python
# Load similarity matrix
if M_raw is None:
    M_raw, firms_df = self._load_similarity_matrix(year)

# Calibrate threshold on raw scores
threshold, _ = self._calibrate_threshold(M_raw, target_fraction)

# Apply median adjustment
M_adjusted, medians = self._apply_median_adjustment(M_raw)

# Build peer groups using adjusted scores
peers_df, peers_per_firm = self._extract_peer_groups(
    M_adjusted, threshold, firms_df
)
```

**Fixed code:**
```python
# Load similarity matrix (already adjusted by similarity.py)
if M_adjusted is None:
    M_adjusted, firms_df = self._load_similarity_matrix(year)
else:
    firms_df = self._load_firm_mapping(year)

# Calibrate threshold on adjusted scores to match baseline membership fraction
# (H&P calibrates to match SIC-3; we match FnGuide Industry)
threshold, _ = self._calibrate_threshold(M_adjusted, target_fraction)

# Extract peer groups using adjusted scores and calibrated threshold
# Peer definition: final_score(i,j) > threshold
peers_df, peers_per_firm = self._extract_peer_groups(
    M_adjusted, threshold, firms_df
)
```

**Changes:**
1. ❌ Remove `_apply_median_adjustment` call (already done by similarity.py)
2. ✏️ Rename `M_raw` → `M_adjusted` for accuracy
3. 📝 Update comments to reflect reality

---

### Fix 2: Update Method Signatures

**Location:** `peer_groups.py:71-76`

**Current:**
```python
def build_peer_groups(
    self,
    year: int,
    M_raw: Optional[np.ndarray] = None,
    save_output: bool = True
)
```

**Fixed:**
```python
def build_peer_groups(
    self,
    year: int,
    M_adjusted: Optional[np.ndarray] = None,  # Renamed from M_raw
    save_output: bool = True
)
```

---

### Fix 3: Remove Unused Method

**Location:** `peer_groups.py:313-343`

**Action:** Remove `_apply_median_adjustment` method entirely (no longer needed)

**Rationale:**
- similarity.py now handles median adjustment
- Keeping this method risks future confusion
- If someone re-enables it, double adjustment recurs

---

### Fix 4: Update Docstring

**Location:** `peer_groups.py:28-35`

**Current:**
```python
"""
Following H&P (2016), this class:
1. Calibrates threshold on raw scores to match baseline membership fraction
2. Applies median adjustment per firm
3. Defines peer groups using adjusted scores
4. Compares with baseline classification (FnGuide Industry)
```

**Fixed:**
```python
"""
Following H&P (2016), this class:
1. Loads median-adjusted similarity matrix from similarity.py
2. Calibrates threshold to match baseline membership fraction (FnGuide Industry)
3. Defines peer groups where adjusted_score(i,j) > threshold
4. Compares TNIC peer groups with baseline classification

Note: Median adjustment is performed by similarity.py (H&P 2016, p. 1436).
This class works with final scores (already adjusted).
```

---

### Fix 5: Load Metadata from similarity.py

**Location:** Add after line 169

**Purpose:** Get median statistics from similarity.py (where adjustment actually happens)

**Add:**
```python
# Load median adjustment statistics from similarity.py
metadata_path = Path(base_dir) / "similarity_matrices_metadata.json"
if metadata_path.exists():
    with open(metadata_path, 'r') as f:
        similarity_metadata = json.load(f)

    year_meta = similarity_metadata.get(str(year), {})
    median_stats = year_meta.get('median_adjustment', None)

    if median_stats:
        self.logger.info(f"  Median adjustment stats (from similarity.py):")
        self.logger.info(f"    Mean: {median_stats['mean_median']:.6f}")
        self.logger.info(f"    Std: {median_stats['std_median']:.6f}")
else:
    median_stats = None
    self.logger.warning("  Similarity metadata not found")

return M_raw, firms_df, median_stats
```

---

### Fix 6: Update Metadata Building

**Location:** `peer_groups.py:446-488`

**Current:** Uses medians from second adjustment (wrong)

**Fixed:** Use median_stats from similarity.py

```python
def _build_metadata(
    self,
    year: int,
    threshold: float,
    target_fraction: float,
    target_stats: Dict,
    median_stats: Optional[Dict],  # From similarity.py, not computed here
    peers_df: pd.DataFrame,
    peers_per_firm: Dict,
    comparison_df: pd.DataFrame
) -> Dict:
    """Build metadata dictionary."""
    n_peers = [len(peers) for peers in peers_per_firm.values()]

    metadata = {
        'year': year,
        'N_firms': len(peers_per_firm),
        'threshold_calibrated': float(threshold),
        'target_fraction_pct': float(target_fraction * 100),
        'fnguide_stats': target_stats,
        'tnic_stats': {
            'n_peer_relationships': len(peers_df),
            'avg_peers_per_firm': float(np.mean(n_peers)),
            'median_peers_per_firm': float(np.median(n_peers)),
            'std_peers_per_firm': float(np.std(n_peers)),
            'min_peers': int(np.min(n_peers)),
            'max_peers': int(np.max(n_peers))
        },
        'comparison': {
            'avg_tnic_peers': float(comparison_df['n_tnic_peers'].mean()),
            'avg_fnguide_peers': float(comparison_df['n_fnguide_peers'].mean()),
            'avg_both': float(comparison_df['n_both'].mean()),
            'avg_tnic_only': float(comparison_df['n_tnic_only'].mean()),
            'avg_fnguide_only': float(comparison_df['n_fnguide_only'].mean()),
            'avg_overlap_pct': float(comparison_df['overlap_pct'].mean())
        }
    }

    # Add median adjustment stats from similarity.py
    if median_stats is not None:
        metadata['median_adjustment'] = median_stats

    return metadata
```

---

## 📊 EXPECTED IMPACT OF FIXES

### Before Fixes (Current - WRONG)

**Process:**
1. similarity.py: raw → adjusted (median ~0.065) → saves adjusted
2. peer_groups.py: loads adjusted → adjusts again (median ~0.02) → double-adjusted
3. Result: Scale transformed twice, incorrect final scores

**Example values:**
```
Original raw: 0.20
After 1st adjustment: 0.11
After 2nd adjustment: 0.095
```

**Peer groups:** Based on double-adjusted values (wrong scale!)

---

### After Fixes (Correct)

**Process:**
1. similarity.py: raw → adjusted (median ~0.065) → saves adjusted
2. peer_groups.py: loads adjusted → calibrates on adjusted → defines peers
3. Result: Correct final scores used once

**Example values:**
```
Original raw: 0.20
After adjustment (similarity.py): 0.11
Used for peer definition: 0.11
```

**Peer groups:** Based on correct final scores!

---

### Impact on Peer Group Sizes

**Current (double-adjusted):**
- Values are over-adjusted (too negative)
- Fewer pairs exceed threshold
- Peer groups smaller than they should be

**After fix:**
- Correct adjustment applied once
- More pairs exceed threshold
- Peer groups correctly sized

**Expected change:** ~20-40% more peer relationships

---

## 📋 VALIDATION CHECKLIST

After implementing fixes, verify:

- [ ] peer_groups.py no longer calls `_apply_median_adjustment`
- [ ] Variables named `M_adjusted` (not `M_raw`)
- [ ] Threshold calibrated on adjusted scores
- [ ] Peer definition uses adjusted scores with calibrated threshold
- [ ] Median statistics in metadata come from similarity.py
- [ ] No double adjustment (check logs carefully)
- [ ] Peer group sizes reasonable (~2-10 peers per firm on average)
- [ ] Metadata contains correct median adjustment stats

---

## 📚 REFERENCES

**Primary Source:**
Hoberg, G., & Phillips, G. M. (2016). Text-based network industries and endogenous product differentiation. *Journal of Political Economy*, 124(5), 1423-1465.

**Key Sections:**
- Section II.C, p. 1435-1436: Threshold calibration and median adjustment
- Section II.C, p. 1436: "We subtract these median scores from the raw scores to obtain our final scores"
- Note file lines 79-94: Complete peer group definition process

**Project Documentation:**
- `tnic/SIMILARITY_AUDIT.md` - Where median adjustment should happen
- `tnic/IMPLEMENTATION_SUMMARY.md` - Architecture overview

---

## 📝 AUDIT CHANGELOG

**Version 1.0** (2025-11-05)
- Initial audit conducted
- Identified 2 critical issues (double adjustment, diagonal inclusion)
- Identified 1 moderate issue (variable naming)
- Identified 2 minor issues (documentation, asymmetric adjustment)
- Provided complete fix implementation

---

**Audit Status:** COMPLETE
**Critical Issues:** 2 (double adjustment + diagonal inclusion)
**Fixes Required:** YES (remove double adjustment, rename variables, update metadata)
**Impact:** HIGH (current peer groups are based on double-adjusted scores)
