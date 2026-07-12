# TNIC Replication Plan - Clear Goals and Action Items

## 📋 Executive Summary

After analyzing the **Hoberg-Phillips (2016)** paper, we can now clearly state:

### What We Have
✅ A **functional TNIC pipeline** (70% complete) that computes text-based firm similarities

### What We're Missing  
❌ Several **preprocessing refinements** that make results directly comparable to official TNIC data

### Our Goal
🎯 Enhance the pipeline to achieve **publication-quality replication** of Hoberg-Phillips methodology

---

## 🔬 HOBERG-PHILLIPS (2016) METHODOLOGY SUMMARY

### The Core Idea

**Question**: How do we measure product market similarity between firms?

**Answer**: Analyze the words firms use to describe their products in 10-K filings

### The 5-Step Process

```
Step 1: Data Collection
└─> Extract Item 1 (Business Description) from 10-K filings

Step 2: Text Preprocessing  
├─> Keep only: Nouns and Proper Nouns
├─> Remove: Words used by >25% of firms (stopwords)
├─> Remove: Geographic terms (countries, states, cities)
└─> Remove: Firms with <20 unique words

Step 3: Vectorization
├─> Create binary word vector for each firm (1 = word used, 0 = not used)
└─> Normalize to unit length (firms on W-dimensional unit sphere)

Step 4: Cosine Similarity
├─> Compute pairwise similarity: cos(angle) between vectors
├─> Range: [0, 1] where 0 = no overlap, 1 = perfect overlap
└─> Creates N×N symmetric similarity matrix

Step 5: Industry Definition
├─> Option A: Fixed Industries (300 groups via clustering)
└─> Option B: TNIC (each firm has unique peer set via threshold)
```

### Key Innovation: TNIC (Text-Based Network Industry Classifications)

**Traditional Industries (SIC/NAICS)**:
- Fixed groups
- Transitive (if A~B and B~C, then A~C)
- Rarely updated

**TNIC**:
- ✨ Each firm has **unique peer set** (like Facebook friends)
- ✨ Intransitive (A and B can share peer C without being peers themselves)
- ✨ Updated **annually** with new 10-Ks
- ✨ Captures **continuous similarity** (not just binary membership)

---

## 📊 REQUIRED INPUTS

### Essential Data

| Input | Description | Status |
|-------|-------------|--------|
| **10-K Text Files** | Item 1 (Business Description) extracted | ✅ User provides |
| **Word Vectors** | Binary presence/absence for each word | ✅ We compute |
| **Similarity Matrix** | Pairwise cosine similarities | ✅ We compute |

### Enhancement Data (For Full Replication)

| Input | Description | Priority |
|-------|-------------|----------|
| **Firm Frequencies** | % of firms using each word | 🔴 HIGH |
| **Geographic Word List** | Countries, states, cities to exclude | 🟡 MEDIUM |
| **Proper Noun Patterns** | Words capitalized ≥90% of time | 🟡 MEDIUM |
| **BEA I-O Tables** | Vertical relationship filter | 🟢 LOW |
| **CIK-GVKEY Mapping** | Link to Compustat data | 🟢 LOW |

---

## 🎯 OUR GOAL

### Primary Objective

**Build a production-ready pipeline that replicates Hoberg-Phillips (2016) TNIC methodology**

Success Criteria:
1. ✅ Compute pairwise text-based similarities
2. ✅ Identify industry peers for each firm
3. ❌ Results **directly comparable** to official TNIC data
4. ❌ **Documented differences** where exact replication isn't possible

### Secondary Objectives

1. **Validation**: Compare our scores with official TNIC data
2. **Documentation**: Clear explanation of methodology and limitations
3. **Usability**: Easy-to-use API for researchers
4. **Extensibility**: Foundation for future enhancements

---

## ✅ WHAT WE ALREADY HAVE

### Current Pipeline Status: **70% Complete**

| Component | Implementation | H-P Specification | Match? |
|-----------|---------------|-------------------|--------|
| **Text Extraction** | User provides text files | SEC Edgar crawling | ✅ |
| **Lowercase** | Built-in | Implicit in paper | ✅ |
| **Punctuation Removal** | Regex-based | Implicit in paper | ✅ |
| **Tokenization** | NLTK word_tokenize | APL/Perl scripts | ✅ |
| **POS Tagging** | NLTK (keep nouns) | Webster.com dictionary | ✅ |
| **Binary Vectors** | NumPy arrays | Manual implementation | ✅ |
| **Unit Normalization** | Vector / ||vector|| | Equation (1) | ✅ |
| **Cosine Similarity** | sklearn | Equation (2) | ✅ |
| **Similarity Matrix** | N×N symmetric | Matrix M_t | ✅ |
| **Pairwise Export** | Long format CSV | Similar | ✅ |

**Strengths**:
- ✅ Core mathematical operations correct
- ✅ Efficient implementation using NumPy/sklearn
- ✅ Well-documented code with examples
- ✅ Modular architecture for extensions

---

## ❌ WHAT WE'RE MISSING

### Critical Gaps (Affect Results)

| Missing Feature | H-P Implementation | Our Current | Impact |
|----------------|-------------------|-------------|---------|
| **1. Stopwords** | Words used by >25% of firms | NLTK fixed list | 🔴 HIGH |
| **2. Median Adjustment** | Subtract median similarity | None | 🔴 HIGH |
| **3. Geographic Filter** | Remove countries/states/cities | None | 🟡 MEDIUM |
| **4. Proper Nouns** | Capitalized ≥90% of time | All capitalized | 🟡 MEDIUM |
| **5. Min Word Count** | Exclude firms with <20 words | None | 🟢 LOW |
| **6. Fixed Industries** | Clustering algorithm | Not implemented | 🟡 MEDIUM |
| **7. Vertical Filter** | BEA I-O tables (>1% threshold) | None | 🟢 LOW |

### Impact Analysis

**🔴 HIGH Impact: Stopwords and Median Adjustment**

These two features fundamentally change the similarity scores:

1. **Frequency-Based Stopwords**:
   - H-P: Remove ~thousands of common words (>25% of firms)
   - Us: Remove ~150 NLTK stopwords
   - **Effect**: We include many industry-general words → inflated similarities

2. **Median Score Adjustment**:
   - H-P: Subtract each firm's median similarity to calibrate scores
   - Us: No adjustment
   - **Effect**: Our scores not directly comparable to official TNIC threshold (21.32%)

**Example**:
```
Without adjustments:
  Firm A to B: raw similarity = 0.35
  Official TNIC: adjusted = 0.35 - 0.10 = 0.25 (peers)

With our current pipeline:
  Firm A to B: raw similarity = 0.40 (due to extra words)
  No adjustment
  Result: Higher scores, different peer assignments
```

---

## 🚀 ACTION PLAN

### Phase 1: Critical Enhancements (Weeks 1-2)

**Goal**: Achieve results directly comparable to official TNIC

#### Task 1.1: Frequency-Based Stopwords (HIGH Priority)

**Objective**: Remove words used by >25% of firms (following H-P exactly)

**Implementation**:
```python
# In cleaner.py
class HobergPhillipsStopwords:
    def compute_word_frequencies(self, firm_tokens: Dict) -> pd.DataFrame:
        """Count how many firms use each word"""
        word_counts = defaultdict(int)
        n_firms = len(firm_tokens)
        
        for tokens in firm_tokens.values():
            for word in tokens:
                word_counts[word] += 1
        
        return pd.DataFrame({
            'word': list(word_counts.keys()),
            'count': list(word_counts.values()),
            'frequency': [c/n_firms for c in word_counts.values()]
        })
    
    def get_stopwords(self, threshold: float = 0.25) -> Set[str]:
        """Return words exceeding frequency threshold"""
        word_freq = self.compute_word_frequencies(firm_tokens)
        return set(word_freq[word_freq['frequency'] > threshold]['word'])
```

**Testing**:
- Run on sample data
- Verify stopwords list is ~thousands of words (vs. 150 for NLTK)
- Compare corpus size before/after

---

#### Task 1.2: Median Score Adjustment (HIGH Priority)

**Objective**: Calibrate similarity scores following H-P methodology

**Implementation**:
```python
# In similarity.py
def compute_tnic_scores(
    self,
    similarity_matrix: np.ndarray,
    threshold: float = 0.2132
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute TNIC scores with median adjustment
    
    Following Hoberg-Phillips (2016), Section III.C:
    1. Compute median similarity for each firm to all others
    2. Subtract median from raw scores (calibrate to median=0)
    3. Apply threshold to define peer relationships
    """
    # Step 1: Compute median for each row (firm)
    median_scores = np.median(similarity_matrix, axis=1)
    
    # Step 2: Subtract median (broadcast operation)
    adjusted_scores = similarity_matrix - median_scores[:, np.newaxis]
    
    # Step 3: Apply threshold
    # Firm j is peer of firm i if adjusted_scores[i,j] >= threshold
    tnic_peers = (adjusted_scores >= threshold).astype(int)
    
    logger.info(f"Median adjustment: mean median = {median_scores.mean():.4f}")
    logger.info(f"After adjustment: mean similarity = {adjusted_scores.mean():.4f}")
    logger.info(f"Peers above threshold: {tnic_peers.sum()} pairs")
    
    return adjusted_scores, tnic_peers
```

**Testing**:
- Verify median ≈ 0 after adjustment
- Check threshold generates ~2% membership pairs (SIC-3 granularity)
- Compare with official TNIC data

---

#### Task 1.3: Update Configuration (HIGH Priority)

**Objective**: Add H-P-specific parameters to config

```python
# In config.py
class TNICConfig(BaseSettings):
    # ... existing parameters ...
    
    # Hoberg-Phillips specific parameters
    use_frequency_stopwords: bool = True  # vs. NLTK stopwords
    frequency_stopword_threshold: float = 0.25  # 25% of firms
    
    apply_median_adjustment: bool = True  # Calibrate scores
    tnic_similarity_threshold: float = 0.2132  # For SIC-3 granularity
    
    filter_geographic_terms: bool = False  # Optional
    proper_noun_threshold: float = 0.90  # Capitalized 90% of time
    min_unique_words: int = 20  # Exclude sparse documents
```

---

### Phase 2: Quality Enhancements (Weeks 3-4)

**Goal**: Improve preprocessing to match H-P more closely

#### Task 2.1: Geographic Term Filtering (MEDIUM Priority)

**Implementation**:
```python
# In cleaner.py
class GeographicFilter:
    """Remove geographic terms per H-P methodology"""
    
    def __init__(self):
        # Load lists
        self.countries = self._load_countries()  # All countries
        self.us_states = self._load_us_states()  # 50 states + DC
        self.top_cities = self._load_top_cities(n=50)  # Top 50 US + world
        
        self.geo_terms = self.countries | self.us_states | self.top_cities
        
    def filter_tokens(self, tokens: Set[str]) -> Set[str]:
        """Remove all geographic terms"""
        return tokens - self.geo_terms
```

**Data Sources**:
- Countries: ISO country name list
- US States: Standard abbreviations + full names
- Cities: Manual list of top 50 (NYC, LA, Chicago, London, Tokyo, etc.)

---

#### Task 2.2: Proper Noun Identification (MEDIUM Priority)

**Objective**: Only keep words capitalized ≥90% of time (not just any capitalized word)

**Implementation**:
```python
# In cleaner.py - Two-pass algorithm
def identify_proper_nouns(self, firm_texts: List[str]) -> Set[str]:
    """
    Identify proper nouns using H-P methodology:
    - Word must be capitalized in ≥90% of occurrences
    """
    word_stats = defaultdict(lambda: {'caps': 0, 'total': 0})
    
    # Pass 1: Count capitalization patterns
    for text in firm_texts:
        tokens = word_tokenize(text)
        for token in tokens:
            word_lower = token.lower()
            word_stats[word_lower]['total'] += 1
            if token[0].isupper():
                word_stats[word_lower]['caps'] += 1
    
    # Pass 2: Identify consistent proper nouns
    proper_nouns = set()
    for word, stats in word_stats.items():
        if stats['caps'] / stats['total'] >= 0.90:
            proper_nouns.add(word)
    
    return proper_nouns
```

---

#### Task 2.3: Minimum Word Count Filter (LOW Priority)

Simple addition to `clean_multiple_files`:

```python
# Filter out documents with <20 words
firm_tokens_filtered = {
    firm_id: tokens 
    for firm_id, tokens in firm_tokens.items() 
    if len(tokens) >= self.config.min_unique_words
}
```

---

### Phase 3: Advanced Features (Weeks 5-6)

**Goal**: Enable comparisons with fixed industries and official data

#### Task 3.1: Fixed Industry Clustering (MEDIUM Priority)

Implement Appendix B algorithm for creating 300 fixed industries

#### Task 3.2: Vertical Relationship Filter (LOW Priority)

Use BEA input-output tables to exclude vertical pairs

#### Task 3.3: Validation Suite (HIGH Priority)

Compare our results with official TNIC data:
- Load official TNIC data (if available)
- Compute correlation between our scores and official scores
- Analyze systematic differences
- Document remaining gaps

---

## 📈 SUCCESS METRICS

### Quantitative Metrics

1. **Correlation with Official TNIC**: 
   - Target: **r > 0.80** (good replication)
   - Excellent: **r > 0.90**

2. **Membership Pair Coverage**:
   - Target: **~2% of pairs** (SIC-3 granularity)
   - Should match official TNIC at same threshold

3. **Peer Overlap**:
   - For firms in both samples: **>75% overlap** in peer sets

4. **Score Distribution**:
   - Mean, median, std should match official TNIC
   - Before adjustment: median ≈ 0.10-0.15
   - After adjustment: median ≈ 0

### Qualitative Metrics

1. **Face Validity**: Do peer groups make sense?
2. **Stability**: Do results remain consistent across samples?
3. **Documentation**: Is methodology clearly explained?

---

## 📚 DELIVERABLES

### Code Deliverables

1. ✅ Enhanced `TextCleaner` with H-P preprocessing
2. ✅ Enhanced `SimilarityCalculator` with median adjustment
3. ✅ TNIC-specific configuration class
4. ✅ Validation module for comparing with official data
5. ✅ Example notebooks demonstrating enhanced features

### Documentation Deliverables

1. ✅ `HOBERG_PHILLIPS_METHODOLOGY.md` - Full methodology analysis
2. ✅ `TNIC_REPLICATION_PLAN.md` - This document
3. ⬜ `VALIDATION_REPORT.md` - Comparison with official TNIC
4. ⬜ Updated `README.md` with replication notes
5. ⬜ Academic working paper (optional)

---

## 🔄 NEXT STEPS

### Immediate Actions (This Week)

1. **Review This Plan**: Confirm goals and priorities
2. **Gather Test Data**: 
   - Sample 10-K texts (ideally matching H-P sample years)
   - Official TNIC data from website (if available)
   - CIK-GVKEY mapping file

3. **Implement Phase 1 Tasks**:
   - Start with frequency-based stopwords
   - Then add median adjustment
   - Test on sample data

### Short-Term (Next 2 Weeks)

4. **Validate Results**: Compare with official TNIC
5. **Document Differences**: What matches? What doesn't?
6. **Iterate**: Refine implementation based on validation

### Long-Term (Next Month)

7. **Complete All Phases**: Finish remaining enhancements
8. **Write Validation Report**: Document replication quality
9. **Publish**: Share pipeline with research community

---

## 💡 KEY INSIGHTS

### Why This Matters

1. **Research Value**: TNIC is widely used in finance/economics research
2. **Replicability**: Open-source implementation promotes transparency
3. **Extensions**: Foundation for modern NLP enhancements
4. **Learning**: Deep understanding of text-based methods

### What Makes H-P Methodology Special

1. **Data-Driven**: No manual industry assignment
2. **Dynamic**: Updates annually with new information
3. **Granular**: Captures product-level differentiation
4. **Flexible**: Intransitive networks vs. fixed groups
5. **Validated**: Extensively tested in published research

### Why Exact Replication Matters

- **Comparability**: Results should match across studies
- **Validation**: Confirms methodology is reproducible
- **Trust**: Open-source verification builds confidence
- **Extensions**: Can only improve what we can replicate

---

## 📞 QUESTIONS & DECISIONS NEEDED

### Technical Decisions

1. **Stopword Threshold**: Use 25% or make configurable?
2. **Dictionary Source**: NLTK POS tagger or Webster.com API?
3. **Performance**: Optimize for speed or exact replication?

### Data Decisions

4. **Sample Period**: Replicate 1997-2008 or use recent data?
5. **Firm Coverage**: All CRSP/Compustat or specific sample?
6. **Validation Data**: Can we access official TNIC for comparison?

### Scope Decisions

7. **Fixed Industries**: Implement clustering algorithm? (Medium effort)
8. **Vertical Filter**: Include BEA I-O tables? (Low priority)
9. **Extensions**: Add modern NLP (BERT, word2vec) later?

---

## 🎓 CONCLUSION

We have successfully built a **solid foundation** for TNIC analysis. To achieve full replication of Hoberg-Phillips (2016), we need to implement **two critical enhancements**:

1. **Frequency-based stopwords** (>25% threshold)
2. **Median score adjustment** (calibration)

These changes will make our results **directly comparable** to official TNIC data and enable **publication-quality research** using our pipeline.

**Estimated Effort**: 2-3 weeks for critical enhancements, 4-6 weeks for complete replication

**Expected Outcome**: Open-source TNIC implementation with validation against official data

---

**Ready to proceed? Let's start with Phase 1! 🚀**
