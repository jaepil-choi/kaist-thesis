# Thesis: Text-Based Industry Momentum in Korean Stock Market

Mandata 지원자 **최재필**

---

## **Executive Summary**

본 연구는 한국 상장기업의 사업보고서 텍스트를 alternative data로 활용하여 (FnGuide WICS같은) 기존 산업분류 체계가 포착하지 못하는 숨겨진 경쟁 관계를 발굴하고, 이를 통해 산업 모멘텀 투자 전략의 수익성을 개선하는 **진행 중인 연구(working paper)** 입니다.

핵심 성과:
- 15년치 한국 전체 상장사 사업보고서 텍스트 데이터 수집 및 처리 (2010-2024)
- 오픈소스 Python 패키지 개발: [`dart-fss-text`](https://github.com/jaepil-choi/dart-fss-text) - DART 공시 자동 수집/파싱 도구
- NLP 파이프라인 구축: 한국어 형태소 분석 → 텍스트 유사도 계산 → 동료 기업 네트워크 생성
- 실증 분석 진행 중: 텍스트 기반 산업분류의 모멘텀 예측력 검증

투자 전략 시사점:
- FnGuide WICS에 의존하지 않고 텍스트 기반 동료 기업 그룹을 식별하여 모멘텀 전략 수익성 향상
- "숨겨진 동료 기업"의 수익률 충격이 시장에 느리게 반영되는 현상을 활용한 알파 창출

---

## **Data and Methodology**

### **1. Alternative Data: 사업보고서 텍스트**

데이터 소스: 금융감독원 전자공시시스템 DART (Data Analysis, Retrieval and Transfer System)

수집 대상:
- 한국 상장기업 사업보고서 "사업의 개요" 섹션 (2010-2024, 15년)
- 기업-연도 텍스트 문서 데이터베이스 구축

기술적 과제 및 해결:

DART는 공개 API를 제공하지만, 사업보고서의 특정 섹션만 추출하는 것은 복잡한 XML/XBRL 파싱을 요구합니다. 이를 해결하기 위해 전용 Python 패키지를 개발했습니다.

#### `dart-fss-text` 패키지

GitHub: https://github.com/jaepil-choi/dart-fss-text

핵심 가치:
- DART API를 통한 사업보고서 자동 조회 및 특정 섹션 추출
- 복잡한 XML/XBRL 파싱 자동 처리
- 재현 가능한 데이터 수집 파이프라인 제공
- 오픈소스로 공개하여 연구 투명성 확보

---

### **2. NLP Processing: 텍스트 → 기업 유사도**

목표: 사업보고서 텍스트로부터 "실제로 경쟁하는 기업 쌍"을 식별

파이프라인:

```
텍스트 → 형태소 분석 → 벡터화 → 유사도 계산 → 텍스트 기반 산업 네트워크 구축
```

예를 들어, 삼성전자는 FnGuide 분류상 반도체 산업으로 분류되어 있지만, 실제로는 가전제품도 생산하기 때문에 LG전자와도 경쟁 관계에 있습니다. 이러한 cross-industry 경쟁 관계는 전통적 산업분류 체계에서는 포착되지 않지만, 사업보고서 텍스트 유사도를 통해 식별할 수 있습니다.

---

### **3. Quantitative Analysis: 투자 신호 검증**

가설:
- TNIC으로 식별된 "숨겨진 동료 기업"의 수익률 충격은 시장에 느리게 반영됨
- 따라서 이를 활용한 산업 모멘텀 전략이 수익성을 가짐

분석 방법론:

#### **(1) Event Study: 회전율 분석**

미국 시장 결과 (Hoberg & Phillips 2018):

<img src="hoberg_phillips_turnover_graph.png" width="350">

한국 시장 재현 결과:

<img src="figure1a_unconditional_turnover.png" width="300">

<img src="figure1b_conditional_turnover.png" width="300">

#### **(2) Fama-MacBeth 회귀분석 결과**

미국과 양상은 다르지만, 한국 시장에서도 TNIC 동료 기업의 과거 수익률이 미래 수익률 예측에 유의미한 것으로 나타났습니다 (상세 수치는 생략)

---

## **Expected Outcome**

### **K-TNIC 산업 분류 구축**

본 연구를 통해 한국 시장에 특화된 텍스트 기반 산업 분류 체계(K-TNIC)를 구축할 수 있습니다. 이는 기존 FnGuide WICS 분류를 보완하여 동적으로 업데이트되는 산업 네트워크를 제공합니다.

### **투자 전략 개선**

K-TNIC을 활용한 산업 모멘텀 전략은 전통적 분류 체계가 포착하지 못하는 숨겨진 경쟁 관계를 활용하여 투자 신호의 질을 향상시킬 수 있습니다. 특히 cross-industry 경쟁자 정보는 대부분의 시장 참여자가 즉시 인지하지 못하는 alternative signal로 작용합니다.

---

## **Conclusion**

본 연구는 한국 상장사 사업보고서 텍스트를 alternative data로 활용하여:

1. 숨겨진 경쟁 관계를 발굴하고
2. 산업 모멘텀 전략의 수익성을 개선할 수 있음을 실증적으로 검증하고 있습니다.

이는 alternative data가 전통적 데이터(FnGuide WICS)를 대체하는 것이 아니라 보완하여 투자 신호의 질을 향상시킬 수 있음을 시사합니다.

GitHub Repository: https://github.com/jaepil-choi/
