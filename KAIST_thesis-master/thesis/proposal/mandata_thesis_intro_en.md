# Thesis: Text-Based Industry Momentum in Korean Stock Market

Mandata Applicant **Jaepil Choi**

---

## **Executive Summary**

This research leverages alternative data from Korean listed companies' Business Report (10-K) texts to identify hidden competitive relationships that existing industry classification systems (such as FnGuide WICS) fail to capture, thereby improving the profitability of industry momentum investment strategies. This is an **ongoing research project (working paper)**.

Key achievements:

- Collection and processing of 15 years of Business Report text data from all Korean listed companies (2010-2024)
- Development of open-source Python package: [`dart-fss-text`](https://github.com/jaepil-choi/dart-fss-text) - automated DART disclosure collection/parsing tool
- Construction of NLP pipeline: Korean morphological analysis → text similarity computation → peer firm network generation
- Ongoing empirical analysis: validation of momentum predictive power of text-based industry classification

Investment strategy implications:

- Enhanced momentum strategy profitability by identifying text-based peer firm groups independent of FnGuide WICS
- Alpha generation by exploiting delayed market incorporation of return shocks from "hidden peer firms"

---

## **Data and Methodology**

### **1. Alternative Data: Business Report Texts**

Data source: Korean SEC's electronic disclosure system DART (Data Analysis, Retrieval and Transfer System)

Collection target:

- "Business Overview" section from Korean listed companies' Business Reports (2010-2024, 15 years)
- Construction of firm-year text document database

Technical challenges and solutions:

While DART provides a public API, extracting specific sections from Business Reports requires complex XML/XBRL parsing. To address this challenge, we developed a dedicated Python package.

#### `dart-fss-text` Package

GitHub: <https://github.com/jaepil-choi/dart-fss-text>

Core value:

- Automated querying of Business Reports via DART API and extraction of specific sections
- Automated processing of complex XML/XBRL parsing
- Provision of reproducible data collection pipeline
- Research transparency through open-source release

---

### **2. NLP Processing: Text → Firm Similarity**

Objective: Identify "actual competing firm pairs" from Business Report texts

Pipeline:

```
Text → Morphological Analysis → Vectorization → Similarity Computation → Text-Based Industry Network Construction
```

For example, Samsung Electronics is classified under the semiconductor industry in FnGuide classification, but in reality, it also manufactures consumer electronics and thus competes with LG Electronics. Additionally, due to its battery business, it is related to Samsung SDI. Such cross-industry competitive relationships are not captured by traditional industry classification systems but can be identified through Business Report text similarity.

---

### **3. Quantitative Analysis: Investment Signal Validation**

Hypothesis:

- Return shocks to "hidden peer firms" identified by TNIC are slowly incorporated into the market
- Therefore, industry momentum strategies leveraging this information can be profitable

Analytical methodology:

#### **(1) Event Study: Turnover Analysis**

U.S. market results (Hoberg & Phillips 2018):

<img src="hoberg_phillips_turnover_graph.png" width="350">

Korean market replication results:

<img src="figure1a_unconditional_turnover.png" width="300">

<img src="figure1b_conditional_turnover.png" width="300">

#### **(2) Fama-MacBeth Regression Results**

Although the patterns differ from the U.S., in the Korean market, past returns of TNIC peer firms are also found to be significant in predicting future returns (detailed figures omitted).

---

## **Expected Outcome**

### **K-TNIC Industry Classification Construction**

Through this research, we can construct a text-based industry classification system (K-TNIC) specialized for the Korean market. This complements the existing FnGuide WICS classification by providing a dynamically updated industry network.

### **Investment Strategy Improvement**

Industry momentum strategies utilizing K-TNIC can improve the quality of investment signals by exploiting hidden competitive relationships that traditional classification systems fail to capture. In particular, cross-industry competitor information serves as an alternative signal that most market participants do not immediately recognize.

---

## **Conclusion**

This research leverages alternative data from Korean listed companies' Business Report texts to:

1. Identify hidden competitive relationships, and
2. Empirically validate improvements in the profitability of industry momentum strategies.

This suggests that alternative data can enhance the quality of investment signals by complementing rather than replacing traditional data (FnGuide WICS).

GitHub Repository: <https://github.com/jaepil-choi/>
