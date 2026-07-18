# 후보 논문 데이터 인벤토리

작성일: 2026-07-17  
대상: `docs/markdown/`의 논문 원문 7편과 `docs/markdown/summary/`의 요약 7편

## 1. 결론

데이터 기준 우선순위는 다음과 같다.

| 순위 | 논문 | 한국 핵심 replication | 원 논문에 가까운 완전복제 | 판단 |
|---:|---|---|---|---|
| 1 | Kaniel et al. (2023), *Machine-Learning the Skill of Mutual Fund Managers* | 매우 높음 | 중간 | ZI의 수익률·AUM·flow로 parsimonious model 가능. 보수는 현재값만 있고 turnover는 없어 13개 특성·gross-return 확장은 제한됨 |
| 2 | Arnott et al. (2023), *Avoiding the Index Rebalancing Crowd* | 높음 | 중상 | KRX 일별 구성종목·비중과 정기변경 효력일을 회사 DW에서 실측 확인. 실제 편입·편출 diff와 발표일·사유 연결이 남은 gate. 단, 저널은 tier 4 |
| 3(조건부) | Beber et al. (2021), *Bespoke Benchmarks* | 중상 | 조건부 | 자산군 한도·스타일·공식 BM은 강하지만 차입·공매도·대여·turnover가 구조화되지 않음. 자유서술/외부 약관 코딩이 gate |
| 4(축소) | Ahn & Patatoukas (2022), *Effect of Stock Indexing* | 중간 | 불가 | 지수 이벤트·가격발견 분석은 가능하지만 시장 전체 lendable supply·borrow fee·index ownership이 WRDSS에 없어 핵심 메커니즘 완전복제 불가 |
| 보류 | Chalmers & Dayani (2026), *Swing for the Fences or Bat for Average* | 낮음 | 불가 | ZI holdings가 자산구분별 top-10이고 주식 sample의 비중 합이 40.43%에 그쳐, 전 종목 동일가중 SF/BA를 식별할 수 없음. 별도 full-holdings 원천이 필요 |
| 보류 | Cao et al. (2017), *Institutional Investment Constraints* | 낮음 | 불가 | 한국의 13F 등가자료가 없고 WRDSS에도 기관별 종목 holdings가 없으며 ZI는 top-10뿐이라 overweight/underweight 구성 불가 |
| 제외 | Drobetz et al. (2025), *Estimating Stock Market Betas via ML* | 높음 | 높음 | 데이터 문제는 작지만 KAIST 선행논문이 이미 한국시장에 직접 적용하여 후보에서 제외 |

가장 안전한 선택은 **Kaniel의 핵심·간소화 모형**이다. 논문의 실제 예측력을 대부분 만드는 변수는 `fund flow`, `fund momentum`, `sentiment` 세 가지이며, 원 논문에서도 46개 holdings-based stock characteristic은 abnormal return 예측에 거의 기여하지 않는다. 따라서 holdings의 과거 coverage가 나빠도 핵심 thesis는 진행할 수 있다.

두 번째 선택은 **Arnott**다. `DW_KRX지수구성*`에서 일별 구성종목·비중을, `DW_KRX지수산출*`에서 정기변경 효력일을 복원할 수 있음을 KOSPI200으로 실측했다. 남은 작업은 실제 구성종목 전후 diff, announcement date, 변경사유 연결이다. 데이터 위험은 Beber보다 낮지만 Financial Analysts Journal(tier 4)이라 학교의 prestigious-journal 기준에서는 Beber보다 약하다.

세 번째 선택은 **조건부 Beber**다. 원 논문도 2009년 한 시점의 prospectus 제약을 쓰므로 현재 snapshot만 있다는 사실 자체는 단면 replication과 양립한다. 그러나 ZI에서 숫자로 확인된 것은 주로 자산군별 최소·최대 한도다. 차입·공매도·증권대여·회전율·종목수 상한은 구조화되지 않았고 turnover 원천도 없다. `FF02` 자유서술이나 외부 약관에서 이 제약들을 충분한 표본에 일관되게 코딩하지 못하면 exact replication은 성립하지 않는다. holdings top-10은 core benchmark를 막지는 않지만 portfolio 검증에는 사용할 수 없다.

**Chalmers의 SF/BA는 현재 보류/no-go**다. `DW_ZI_펀드자산내역`은 full holdings가 아니라 자산구분별 top-10이며, 확인한 주식형 펀드의 S1 비중 합은 40.43%였다. 원 논문은 모든 보유종목을 동일가중하므로 top-10으로 계산한 값은 단순한 noisy proxy가 아니라 포지션 크기에 의해 선택된 편향 지표다. 별도의 장기 full-holdings 원천을 확보하지 않으면 진행하면 안 된다.

## 2. 확인 수준의 의미

- **회사 DW 실측 확인**: 사내 `.kwam_cache`의 metadata와 2026-07-16~17의 제한적 실데이터 조회를 함께 사용했다. ZI의 return·holdings·보수·약관·운용사 구조와 KRX 지수 구성·산출 table을 확인했다. 반면 개인 매니저, 시장 전체 대차·공매도, 기관별 종목 holdings는 WRDSS에서 찾지 못했다. 다른 table은 여전히 장기 coverage까지 확인했다는 뜻은 아니다.
- **FnGuide 로컬 정의 확인**: 저장소의 기존 ETL/config에 사용 필드가 정의되어 있다. 현재 `data/`에는 실데이터 파일이 없으므로 이번 작업공간에서 값과 기간을 재검증하지는 못했다.
- **벤더 제공 가능**: FnGuide 공식 안내상 상품에 포함된다. 회사 계약·DW 적재 범위는 별도 확인이 필요하다.
- **미확인/공백**: 알려진 ZI 30개 테이블과 현재 FnGuide ETL 정의에서는 찾지 못했다.

FnGuide 공식 안내에 따르면 DataGuide는 주식(1980~), 이벤트(1980~), 지분(2003~), 재무(1983~), 컨센서스(2000~), 경제 데이터와 일·주·월·분기·연 시계열 출력을 제공한다. 그러나 이것은 **DataGuide 상품 전체 범위**이지 회사 DW 적재 범위와 같지는 않다.

- [FnGuide 제공 데이터 안내](https://help-dataguide.fnguide.com/ko/articles/%EC%A0%9C%EA%B3%B5-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EC%95%88%EB%82%B4-5c5347da)
- [FnGuide 시계열 데이터 안내](https://help-dataguide.fnguide.com/ko/articles/%EC%8B%9C%EA%B3%84%EC%97%B4-%EB%8D%B0%EC%9D%B4%ED%84%B0-%EB%B6%84%EC%84%9D%ED%95%98%EA%B8%B0-1b0a3469)
- [KRX Data Marketplace](https://data.krx.co.kr/)
- [KG제로인 서비스 소개](https://www.zeroin.co.kr/company/introduce.do)

## 3. 공통 데이터 마트

세 펀드 우선후보는 아래 다섯 개 공통 마트를 만들면 대부분 함께 사용할 수 있다.

### 3.1 Fund master

키: `협회펀드코드`, 대표펀드코드, share-class 코드, 운용사코드

필요 필드:

- 펀드명, 설정일, 해지일, 생존 여부
- 대유형/세부유형, 국내주식형 여부, active/passive/index/enhanced-index 여부
- 대표펀드와 share class 관계
- 운용사/family
- 공식 BM과 BM 변경이력
- retail/institutional class 또는 판매채널
- manager ID, 운용개시일, team-managed 여부

ZI 매핑:

- `DW_ZI_펀드기본정보`: 설정일, 해지일, 유형, 운용사, BM
- `DW_ZI_클래스펀드`: 대표펀드–서브펀드 매핑
- `DW_ZI_펀드별속성코드` + `DW_ZI_속성코드`: 인덱스/정통인덱스/인핸스드/롱숏/퀀트, 스타일, `D100` 판매방식, `E100` 대상고객 등
- manager ID·담당펀드·담당기간·경력·team 여부는 WRDSS 1,044개 object에서 전용 table이 없음

### 3.2 Fund-month/day panel

키: `기준일자 × 협회펀드코드`

필요 필드:

- 기준가 또는 total return, 순자산(TNA), 설정액, 설정좌수
- BM return
- 자산군별 평가액과 현금
- 보수율, turnover

ZI 매핑:

- `DW_ZI_펀드일별분석`: `설정액`, `설정좌수`, `기준가`, `순자산`, `실현수익률`, `BM수익률`, 자산군별 평가액
- `DW_ZI_펀드약관보수`: 보수종류별 `보수율`; percent 단위이며 `FA10=FA01+FA02+FA03+FA04+FA05` 확인
- `DW_ZI_펀드지표분석`: alpha, beta, R-square, Sharpe, IR 등은 검산용

주의:

- `실현수익률`이 기준가 기준 net return인지, 분배금 재투자 total return인지 정의를 확인해야 한다.
- 보수율은 수준상 연율로 보이지만 직접적인 annual flag는 없어 관행적 추정이다.
- `펀드약관보수`에는 날짜가 없어 **현재 보수만 존재**한다. 현재 보수를 과거 전 기간에 월할 가산해 gross return을 만들면 fee-change measurement error와 look-ahead가 생기므로 기본 분석에 쓰지 않는다.
- turnover ratio, 매수·매도금액, 평균순자산을 제공하는 전용 원천은 ZI 30개에서 찾지 못했다.

### 3.3 Fund holdings panel

키: `기준일자 × 협회펀드코드 × 종목코드`

ZI `DW_ZI_펀드자산내역`에서 확인된 필드:

- `자산구분`, `소속구분`, `종목코드`, `순위`
- `시가평가액`, `펀드내비중`, `수량`, `취득액`, `장부평가액`
- `종목업종명`, `섹터비중`

이미 확인된 적재 특성:

- 이름은 일자별이나 실제로는 **월 1회, 첫 영업일 근처 snapshot**이다.
- 2026-03-03, 2026-04-01, 2026-05-04가 확인되었고, 2026-07-16 조회 당시 2026-05-04 이후 적재가 없었다.
- 전체 141,698,365행, 246개 기준일자, 64,040개 펀드코드가 있으나 **full holdings가 아니라 자산구분별 top-10**이다. PK가 `(기준일자, 협회펀드코드, 자산구분, 순위)`이고 sample의 `MAX(순위)=10`이었다.
- 주식형 sample의 `S1` 종목 10개 비중 합은 40.43%에 불과해, 나머지 보유종목은 테이블에 없다. `S2` 업종 10개와 `C1` 유동성 1개를 포함해 총 21행이었다.
- 국내주식 `S1` 종목코드는 KRX 6자리 표준코드라 FnGuide와 직접 join 가능해 보인다. 다만 해외·채권·파생 코드체계와 코드변경 이력은 별도 확인이 필요하다.
- 따라서 concentration/overlap이나 top-position 분석에는 쓸 수 있지만, full portfolio가 필요한 SF/BA·active share·overweight/underweight에는 사용할 수 없다.

### 3.4 Stock PIT panel

키: `date × KRX 종목코드/표준코드`

필요 필드:

- 수정주가, 현금배당 포함 total return, 거래량·거래대금, 상장주식수·유동주식수, 시가총액
- 장부가치, 순이익, 영업현금흐름, 매출, 배당, 자사주매입, R&D, 부채/자산
- FnGuide/거래소 산업분류
- 실적발표일과 실제 EPS, 발표 직전 consensus EPS
- 상장·상장폐지, 합병·분할, 유상증자 등 corporate action
- 지수 구성종목과 비중, 편입·편출 발표일과 효력일

현재 로컬 FnGuide ETL/config에서 직접 확인된 필드:

- 수정주가, 일별수익률, 거래대금, 상장주식수, 유동주식수·비율, 시가총액
- 거래정지·관리종목 상태
- FnGuide sector/industry 및 KRX 업종
- 매출, 보통주자본금, 이연법인세부채, 이익잉여금, 자기주식, 자본잉여금
- 실적발표 event indicator

아직 회사 DB에서 확인해야 할 필드:

- 총수익률과 상장폐지수익률
- book equity를 정확히 구성할 전체 항목
- 순이익/EPS, 영업현금흐름, 배당, 자사주매입, R&D, 총자산·부채
- consensus **vintage**와 발표 직전 median forecast
- 지수 구성/비중의 역사적 snapshot, 발표일/효력일
- bid/ask, 고빈도 체결·호가

### 3.5 Factor and macro panel

필요 필드:

- 무위험수익률
- 한국형 MKT, SMB, HML, MOM; 확장 시 RMW, CMA, short/long reversal
- 한국 투자심리(sentiment)와 경기상태

권장 방식:

- factor는 FnGuide 주가·시가총액·장부가치로 직접 PIT 구성한다.
- sentiment는 두 버전으로 분석한다.
  1. 한국은행 소비자심리지수/경제심리지수와 같은 공개 월별 지표
  2. Baker–Wurgler에 가까운 한국형 합성지수: 시장 turnover, IPO 수·첫날 수익률, 주식발행 비중, dividend premium, 가능하면 closed-end-fund discount
- IPO 상장일·공모가·공모금액과 공모가 대비 주가 흐름은 [KRX KIND](https://kind.krx.co.kr/listinvstg/listingcompany.do?method=searchListingTypeMain)에서 확인할 수 있다.

## 4. 논문별 상세 요구사항

## 4.1 Kaniel et al. (2023)

### 최소 실행안: 논문의 parsimonious model

관측단위: fund-month

필수 변수:

| 변수 | 원 논문 정의 | 회사 DB 매핑 | 상태 |
|---|---|---|---|
| 다음 달 abnormal return | 최근 36개월 Carhart beta로 다음 달 factor compensation 제거 | ZI `실현수익률` + 직접 만든 한국 Carhart factors | 원자료 있음, factor 구축 필요 |
| `flow` | `TNA_t / (TNA_{t-1}(1+R_t)) - 1` | ZI `순자산`, `실현수익률` | 가능 |
| `F_r12_2` | 예측 직전 2~12개월 abnormal return 평균; 최소 8개 관측 | 위 abnormal return panel | 가능 |
| `sentiment` | Baker–Wurgler investor sentiment | 한국형 sentiment 별도 구축 | 핵심 미확정 |
| fee/net return | expense ratio 및 수수료 후 abnormal return | `DW_ZI_펀드약관보수` | 단위·합산식 확인; 현재값만 있어 역사적 gross return 복원 불가 |
| share-class 통합 | class TNA 가중 fund-level return | `DW_ZI_클래스펀드` + 일별분석 | 구조 확인; 가중합산 공식 검증 필요 |
| active domestic equity universe | 국내주식 중심 active fund | 유형/속성코드 + 자산평가액 | 가능 |
| survivorship-free universe | 해지 펀드 포함 | 기본정보 `해지구분`, `해지일` | 해지펀드의 전체 일별 이력 보존 확인 |

이 설계만으로 원 논문의 경제적 핵심인 “flow와 fund momentum이 skill을 예측하며 sentiment가 이를 조건화한다”를 검증할 수 있다.

### 부분 확장안: 13개 fund/family characteristic

추가 변수:

- 펀드: age, TNA, flow, expense ratio, turnover ratio
- 펀드 momentum: `F_ST_Rev`, `F_r2_1`, `F_r12_2`
- family: family TNA, 펀드 수, family momentum, family age, family flow

ZI 대응:

- age/TNA/flow: 가능. expense는 현재값만 있어 시계열 predictor로 부적합
- family TNA·펀드 수·return: `DW_ZI_운용사일별분석`, sample 기준 1999-08-23부터 존재
- family alpha 등: `DW_ZI_운용사지표분석` 검산 가능
- family age: 같은 운용사의 펀드 설정일 중 최소값으로 계산
- turnover ratio: ZI 30개에 전용 원천이 없음. top-10 holdings 변화량으로 근사하면 안 되며, 다른 ZI/운용사 원천 table을 찾아야 함
- manager characteristic은 WRDSS에 개인 매니저 table이 없어 추가할 수 없음. 원 논문의 parsimonious model에는 필수 아님
- retail/institutional은 `D100` 판매방식·`E100` 대상고객 속성으로 대용 가능성이 있으나 실측 미검증

### 완전복제: 46개 holdings-based stock characteristic

원 논문의 46개 항목은 과거수익 6개, investment 4개, profitability 11개, intangibles 4개, value 10개, trading frictions 11개다. 주요 입력은 다음과 같다.

- 주가와 1·2·6·12·36개월 수익률
- 총자산, 순영업자산, PPE 변화, 순주식발행
- 매출, 영업이익, 이익, 현금흐름, SG&A, 자산회전율, ROA/ROE
- accruals, operating leverage, price-cost margin
- book-to-market, cash, free cash flow, dividend, earnings, Tobin's Q, sales-to-price, leverage
- beta, idiosyncratic volatility, size, turnover, 52주 고가 근접도, spread, unexplained volume, variance

각 주식 characteristic을 횡단면 rank로 정규화한 뒤 직전 holdings weight로 펀드 수준에 합산한다. DataGuide 상품 전체에는 대부분 존재할 가능성이 높지만 현재 회사 FnGuide ETL 정의에는 일부만 있다. 더 근본적으로 ZI는 top-10만 보유하므로 46개 변수를 fund level로 정확히 합산할 수 없다. 이 블록은 **별도 full holdings를 확보한 뒤에만 가능한 확장**이다.

### Kaniel 진행 전 필수 확인

1. `실현수익률`의 gross/net/분배금 처리 정의
2. ~~일별분석의 최소·최대일과 해지 펀드 포함 여부~~ — 1996-01-03~2026-07-15, 해지펀드 이력 보존 확인
3. share-class 합산 시 대표펀드와 클래스가 중복 집계되지 않는지
4. ~~보수율의 과거 이력~~ — 이력 없음, 현재 snapshot만 존재; 역사적 gross return 복원에 사용하지 않음
5. ~~ZI turnover ratio 원천~~ — ZI 30개에는 없음; 외부 원천이 없으면 해당 predictor 제외
6. 운용사코드 변경·합병 history
7. 한국형 Carhart factor와 sentiment 선택

## 4.2 Chalmers & Dayani (2026) — ZI 기준 보류/no-go

### 핵심 SF/BA 구성

관측 순서:

1. 분기 `t-2` 말 holdings 관측
2. 각 종목의 `t-2 → t-1` 분기수익률에서 size/book-to-market peer return 차감
3. 같은 분기 횡단면 상위 10%를 HR, 하위 10%를 SO, 0 초과를 hit로 분류
4. 펀드별 보유종목 수 기준 동일가중 비율로 HR, SO, BA 계산
5. `t-1`의 전략변수로 `t`의 return, volatility, flow, fee를 설명

필수 입력:

| 데이터 | 필요한 세부사항 | 소스 | 상태 |
|---|---|---|---|
| 분기초 holdings | 종목코드, 비중, 평가액, 수량 | ZI `펀드자산내역` | **불충족**; 자산구분별 top-10만 존재, S1 sample 비중 합 40.43% |
| 종목 분기수익률 | total return | FnGuide | 수정주가 return은 확인, 현금배당 포함 여부 확인 |
| FF25 한국 대용 | 매년 size × B/M 5×5 peer | FnGuide 가격·시총·book equity | 가능, PIT 회계자료 필요 |
| 펀드 return·BM return | gross, net, benchmark-adjusted | ZI 일별분석 | net 정의 확인; gross는 보수 가산 근사 가능 |
| fund flow | TNA와 return | ZI 일별분석 | 가능 |
| fee | 연 expense ratio | ZI 약관보수 | 가능성 높음; 보수코드·시계열 확인 |
| risk | 최근 12개월 월 BM-adjusted return 또는 alpha의 표준편차 | ZI return + 직접 factor | 가능 |
| fund controls | size, family size, turnover, age, holdings 수 | ZI | turnover는 ZI 30개에 없음; holdings 수도 top-10이라 실제 값 아님 |
| active/passive | active, passive falsification sample | ZI 속성코드 | 가능성 높음 |
| retail/institutional | client focus | 속성/클래스/판매방식 | 정확한 대용변수 확인 필요 |
| manager experience/team | manager 운용개시일, 팀운용 여부 | WRDSS 전용 table 없음 | 사용 불가 |

### 논문 핵심을 강화하는 추가자료

- active share: full holdings가 없어 ZI만으로는 계산 불가
- industry concentration: holdings와 FnGuide industry
- MAX/lottery, high volatility, skewness: 일별 종목수익률
- Carhart alpha와 factor exposure: 한국 factor panel
- Morningstar-assigned BM의 한국 대용: ZI 유형 benchmark 또는 동일유형 peer benchmark가 펀드 자체 공식 BM보다 바람직

### 공시·마케팅 메커니즘

원 논문은 N-CSR의 `Management Discussion of Fund Performance`에서 HR/SO 종목명이 성과 기여·저해 종목으로 언급되는지 읽는다. 한국 대용은 자산운용보고서의 운용경과·성과요인 텍스트다.

필요 자료:

- 펀드별 자산운용보고서 PDF/HTML의 역사적 archive
- 보고기간, 협회펀드코드, 운용사 연결키
- 기여/저해 종목명·ticker 추출
- 보고서가 모펀드/자펀드/클래스 중 어느 수준인지

이 데이터는 ZI 30개 테이블에는 없다. 금융투자협회 전자공시 또는 운용사 archive를 수집해야 한다. 공시 텍스트 분석은 생략할 수 있지만, full holdings가 없으면 SF/BA 자체를 만들 수 없으므로 핵심 replication도 불가능하다.

### Chalmers 진행 전 필수 확인

1. ~~월별 snapshot 수~~: 246개 확인. 전체 최소·최대일은 아직 미조회
2. ~~top-N truncation 여부~~: **자산구분별 top-10으로 확인 — 필수조건 실패**
3. ~~국내주식 코드체계~~: KRX 6자리 코드 확인. 종목코드 변경 이력은 미확인
4. 보유 snapshot 시점이 실제 기준일인지 수집/적재일인지
5. 펀드 return의 보수 차감 단계
6. active/passive/enhanced-index 분류 정확도
7. retail/institutional, manager experience, team-managed 원천
8. 공식 BM 구성종목·가중치의 역사적 자료

2번이 핵심 식별변수의 필수조건이므로 나머지 항목을 추가 확인해도 ZI만으로는
go로 바뀌지 않는다. 먼저 별도 full-holdings 원천의 존재를 확인해야 한다.

## 4.3 Beber et al. (2021)

### 원 논문의 데이터 구조

원 논문은 미국 capital-appreciation fund 141개 중 10년 이상 기록이 있는 71개를 사용한다. 2009년 4분기 근처 prospectus/SAI **한 시점**에서 제약을 코딩하고, 1974~2013 월별 시장자료로 맞춤형 최소분산 benchmark를 만든다.

따라서 ZI 약관·기본정보에 날짜가 없는 것은 다음처럼 해석해야 한다.

- 원 논문식 단면 제약 replication: 설계상 가능하지만 **현재 시점 단면**으로 표본을 다시 정의해야 함
- 과거 성과에 현재 약관/BM/보수를 소급 적용: look-ahead와 변경오류 가능
- 해지펀드 return은 보존되어도 당시 약관 snapshot이 없으면 제약 표본은 현재 생존펀드 쪽으로 선택될 수 있음

### 필요한 제약과 ZI 매핑

| 원 논문 constraint | 필요한 값 | ZI 매핑 | 상태 |
|---|---|---|---|
| investment universe | 국내/해외, 주식/채권, size, value/growth, industry, 최대 종목 수 | 약관한도, 약관투자, 기본정보, 속성코드, 스타일분석 | 자산군·9-box 강함; 종목 수 상한 없음 |
| cash/fully invested | 현금 최소·최대, 완전투자 | 약관한도 `FB31`, 일별 유동성자산 | sample에서 숫자 확인; row 부재와 0 구분 필요 |
| borrowing/leverage | 차입·레버리지 허용과 상한 | `FB53` 코드, 약관투자 텍스트 | 코드만 존재; sample row·값 형태 미확인, 차입 전용 필드 없음 |
| short sale | 공매도 허용과 한도 | 약관투자 텍스트 후보 | 구조화 필드 없음 |
| securities lending | 대여 허용과 한도 | 약관투자 텍스트 후보 | 구조화 필드 없음 |
| derivatives | 파생상품 1~3 한도, 실제 exposure | `FB41~43`, 일별 선물·옵션·스왑 평가액 | 코드는 존재; sample row 없음, 표본 coverage 미확인 |
| turnover | 약관상 turnover 상한 | 약관투자 텍스트 후보 | 전용 필드·turnover table 없음; top-10 변화로 계산하면 안 됨 |
| transaction cost | 거래량·수익률 공분산 또는 turnover 비용 | FnGuide 가격·거래대금 + 약관 turnover | 시장 유동성 항은 가능; turnover 제약 확인 필요 |
| benchmark | 지정지수 | 기본정보 BM코드/명 | 현재값만 존재; 변경이력 없음 |
| realized performance/rank | 펀드 수익률 | ZI 일별분석 | 가능 |

### 시장자료

원 논문의 기업 characteristic은 세 개뿐이다.

- size: 6월 말 시가총액의 로그
- value: 전년도 회계연도 book equity / 전년도 12월 market equity의 로그
- momentum: 직전 1개월을 뺀 과거 1년 수익률
- 10개 industry classification

이는 FnGuide로 충분히 구성 가능하다. 이 후보는 Kaniel의 46개 주식 characteristic보다 시장자료 요구가 훨씬 작다.

### Beber 진행 전 필수 확인

1. ~~약관 snapshot 구조~~ — 날짜·변경이력 없이 현재값만 존재; 현재 시점 단면으로 표본 정의 필요
2. ~~최소/최대비율 단위와 결측 의미~~ — percent 수치, row 부재와 명시적 0은 구분됨
3. short, lending, derivatives, turnover의 정형 코드 또는 텍스트 규칙
4. BM 코드와 실제 BM return 시계열 연결
5. 클래스/모자펀드의 제약이 어느 수준에서 기록되는지
6. 10년 이상 수익률이 있고 폐쇄펀드를 포함하는 표본 크기

3번은 단순 보완항목이 아니라 **go/no-go gate**다. 차입·공매도·대여·turnover
중 충분한 수를 일관되게 코딩하지 못하면 “bespoke constraints”가 아니라
자산군 mandate만 반영한 축소 연구가 되어 원 논문과의 거리가 커진다.

## 4.4 Cao et al. (2017)

### exact replication에 필요한 핵심

- 기관별·종목별 분기말 전체 보유수량과 평가액
- 기관의 전체 주식 포트폴리오
- 종목별 aggregate institutional ownership
- 같은 기관의 분기 간 거래량

이 자료로 각 기관의 실제 종목비중을 “그 기관이 보유한 동일 종목집합의 시총가중 비중”과 비교해 overweight 여부를 만들고, 종목별 overweight 기관 비율을 계산한다.

한국에는 미국 13F와 같은 포괄적 기관별 전체 포트폴리오 공시가 없다. ZI
`펀드자산내역`도 자산구분별 top-10으로 확인되어 실제 종목비중과 aggregate
ownership을 만들 수 없다. 따라서 현재는 no-go이며, 별도 full holdings를
확보할 때만 아래와 같이 연구질문을 좁힐 수 있다.

- 기관 전체가 아니라 **국내 공모주식형 펀드**의 overweight constraint
- fund-by-stock overweight ratio와 aggregate mutual-fund ownership
- quasi-index fund와 active fund의 차이

추가 데이터:

- FnGuide 주가·시총·B/M·momentum·KOSPI200 membership
- 실제 EPS, 실적발표일, 발표 직전 consensus median EPS, 주당 book equity
- 6개월 과거수익률과 향후 3·6개월 수익률

ZI holdings가 top-10이고 WRDSS에도 기관별 종목 holdings table이 없음을
확인했다. 따라서 aggregate mutual-fund ownership과 fund-by-stock overweight를
계산할 수 없으며, 별도 full institutional holdings를 확보하지 않는 한
후보에서 제외한다.

## 4.5 Ahn & Patatoukas (2022) — 축소 replication만 가능

### 기본 RDD/Event 설계

한국 적용 시 KOSPI200, KOSDAQ150, KRX300 등의 정기변경 경계에서 편입·편출 종목을 비교한다.

회사 DW의 `DW_KRX지수구성*`에는 일별 구성종목·비중이 있고,
`DW_KRX지수산출*`에는 정기변경 일정과 변경 전후 종목 수가 있다. KOSPI200
sample에서 정기변경 효력일도 실측 확인했으므로 기본 event panel은 구축
가능성이 높다. 실제 종목별 편입·편출 diff와 announcement date는 추가 확인한다.

필요 데이터:

- 매년 정기변경의 rank date, announcement date, effective date
- 편입·편출 목록과 이전 지수소속
- 실제 선정변수와 breakpoint를 재현할 float market cap, 거래요건, 산업요건
- 지수 추종자금 또는 index-fund ownership 변화
- 전후 1년 가격·수익률·거래량·거래대금·bid/ask
- 주별 시장/산업/기업수익률로 구성한 synchronicity, systematic/idiosyncratic volatility, market/industry/firm/negative-news delay
- 실적발표일과 일별 또는 분별 return

### 원 논문의 메커니즘 자료

원 논문이 요구하는 Markit 대차자료는 다음과 같다.

- lendable quantity / shares outstanding
- quantity on loan / shares outstanding
- lender inventory concentration
- stock-loan fee
- 일별 stock-loan fee 변동성

KRX 공개 화면은 종목별 대차잔고, 공매도 거래, 공매도 순보유잔고 등을 제공하지만, 이는 lendable supply·대여자 집중도·실제 borrow fee와 같지 않다. [KRX 공매도·대차 안내](https://data.krx.co.kr/contents/MDC/STAT/srt/MDCSTAT317.jsp)도 대차잔고 증가가 곧 공매도 대기물량은 아니라고 설명한다.

따라서 다음 두 설계를 구분해야 한다.

- **축소 replication**: 지수편입 → 거래유동성·가격동조성·news delay
- **완전 replication**: 위 결과에 대차공급·borrow fee 및 index ownership 경로까지 포함

WRDSS 1,044개 object를 확인한 결과 시장 전체 lendable/on-loan quantity,
대차수수료, 공매도, 기관별 종목 holdings 전용 table은 없었다. 발견된
`FA_대차자산`과 `DW_FA_대차담보명세`는 KWAM 자사 펀드의 채권 차입·담보
자료다. 따라서 외부 Koscom/예탁결제원/증권금융/prime-broker 데이터를 새로
확보하지 않는 한 완전 replication은 **no-go**다. 회사 DW만 사용하면
지수편입 이후 유동성·동조성·news delay를 분석하는 축소 설계만 가능하다.

## 4.6 Arnott et al. (2023) — 데이터 기준 2순위

### 이벤트 분석

필수 데이터:

- 지수 편입·편출 종목
- announcement date, effective date, 실제 index trade date
- discretionary 변경과 합병·분할·상장폐지 등 비재량 변경의 구분
- 발표 전 1년, 발표–거래일, 거래 후 1년의 종목 total return
- 시장수익률과 factor return
- P/B, P/E, P/CF, P/S, P/D valuation

### 대체지수 백테스트

한국에서는 “500”을 “KOSPI200 또는 대형주 N개”로 바꾸면 된다.

필요 입력:

- 현재 시가총액 및 5년 평균 시가총액
- book value adjusted for intangibles
- 5년 평균 sales adjusted for debt/assets
- 5년 평균 cash flow adjusted for R&D
- 5년 평균 dividends + share repurchases
- 현재 market-cap weight
- annual rebalancing, corporate action, delisting 처리

20% banding/seasoning 규칙:

- 목표 200종목이면 보유종목은 rank 240 밖으로 나가야 퇴출 후보
- 비보유종목은 rank 160 안으로 들어와야 편입 보장
- 같은 상태가 2년 연속 지속되어야 편입/퇴출
- 종목 수를 정확히 200으로 맞추기 위해 160~240 구간에서 필요한 만큼 조정

회사 DW에서 다음을 확인했다.

- `DW_KRX지수구성`·`CLS`·`NP`: 일별 종목 구성, 지수내비중과 복수 weight, EPS/BPS/DPS, 유동비율·CAP비율·조정가중치
- `DW_KRX지수산출`·`NP`: 지수 일별 값, `변경여부`, 변경 전후 구성종목 수, `다음정기변경일`
- KOSPI200 sample에서 `다음정기변경일`이 2025-06-13 효력일에 다음 일정으로 전환됨을 실측

따라서 과거 구성종목·비중과 정기변경 effective date는 확보 가능성이 높다.
남은 go/no-go 항목은 실제 구성종목을 리밸런싱 전후 diff해 편입·편출 목록을
검증하고, announcement date와 변경사유를 공시 또는 별도 table에서 연결하는
것이다. `변경여부`는 주변 날짜에서 불규칙해 단독 event signal로 사용하지
않는다. 데이터 기준으로는 Beber보다 안전하지만, tier 4 practitioner journal인
점은 thesis key-paper 적합성의 별도 약점이다.

## 4.7 Drobetz et al. (2025)

데이터 요구는 일·월별 종목수익률, 여러 horizon의 과거 beta, turnover, size, 회계변수, 산업 dummy, 시장변수다. FnGuide로 구현 가능성이 높지만 KAIST 선행연구가 한국시장에 직접 적용했으므로 thesis 후보에서는 제외한다. 다른 후보의 beta·risk-control 구현 참고문헌으로만 둔다.

## 5. 회사 DB 확인 체크리스트

아래 질문에 답하면 주제 선택이 가능하다. `필수`부터 확인한다.

### 5.1 ZI 필수

- [ ] `DW_ZI_펀드일별분석`의 `MIN/MAX 기준일자`, 연도별 펀드 수, 해지펀드 포함률
- [ ] `실현수익률` 정의: 분배금 재투자, 보수·비용 차감, 세전/세후
- [x] `순자산`, `설정액`, `설정좌수` 중 flow 계산의 공식 권장 필드 — `순자산`과 `실현수익률` 조합을 sample에서 검증
- [ ] `DW_ZI_클래스펀드`의 대표/서브펀드 중복 방지 규칙 — 대표도 독립 class임을 확인; 합산 공식은 미검증
- [ ] `DW_ZI_펀드자산내역`의 최초일·최종일, 월별 snapshot 수, 2026-05 이후 적재상태 — 246개 snapshot·2026-05-04 이후 공백 확인; 최초일 미조회
- [x] holdings가 full holdings인지 top-N인지 — 자산구분별 top-10, S1 sample 비중 합 40.43%
- [ ] holdings `종목코드`의 코드체계, 해외/채권/파생 자산구분 decode — 국내주식 KRX 6자리·자산구분 `PFA1` decode 완료; 나머지 코드 미확인
- [ ] 해지된 펀드의 과거 holdings 보존 여부
- [x] `펀드약관보수` 보수코드·단위·이력 — percent 단위, `FA10` 합산식 확인, 현재값만 존재
- [x] `펀드약관한도/투자/기본정보` 이력 — 날짜 컬럼 없이 현재 snapshot만 존재
- [ ] actual turnover ratio 원천 — ZI 30개에는 없음; WRIMS/WRMIS 등 외부 owner 미탐색
- [x] manager ID, manager start date, team-managed 여부 table — WRDSS 전체에서 전용 table 없음
- [ ] retail/institutional client focus 또는 class 구분 table

### 5.2 KRX/FnGuide 필수

- [ ] 6자리 종목코드와 표준코드의 역사적 mapping, 코드변경/합병 처리
- [ ] 수정주가가 현금배당 포함 total return인지
- [ ] 상장폐지 종목과 delisting return 포함 여부
- [ ] 일별·월별 가격/거래량/거래대금/상장주식수/유동주식수의 최소일
- [ ] point-in-time 재무제표와 실제 공시가능일
- [ ] book equity, earnings/EPS, cash flow, sales, dividend, repurchase, R&D, intangibles, total assets/debt
- [ ] consensus forecast의 observation/vintage date와 실적발표 직전 median EPS
- [ ] 실적발표일과 장중/장후 timestamp
- [x] 지수 구성종목·가중치의 역사적 snapshot — `DW_KRX지수구성*` 일별 table 확인
- [ ] 지수 정기변경 announcement/effective date와 변경사유 — effective date 식별 확인; announcement date·사유 미확인
- [ ] bid/ask 또는 intraday quote/transaction
- [x] investor-type ownership, 공매도·대차·borrow fee — WRDSS에 시장 전체 자료 없음; 자사 채권 차입·담보만 존재

### 5.3 Join/PIT 품질

- [ ] `협회펀드코드 → 대표펀드 → 운용사 → holdings 종목코드 → FnGuide symbol` join 성공률
- [ ] 모펀드/자펀드가 같은 holdings를 이중 계산하지 않는지
- [ ] holdings 기준일과 실제 공개가능일 사이 lag
- [ ] 재무자료는 보고서 공시 전 사용하지 않도록 PIT lag 적용
- [ ] consensus는 최신값이 아니라 예측 당시 vintage 사용
- [ ] 지수효과는 발표일과 효력일을 구분
- [ ] 폐쇄펀드·상장폐지주를 남겨 survivorship bias 방지

## 6. 대형 ZI 테이블 안전 조회 예시

`펀드자산내역`, `펀드일별분석`, `펀드지표분석`은 1억 행 이상이다. 전체 `COUNT(*)`, 무필터 `DISTINCT`, `SELECT *`를 먼저 실행하지 말고 날짜와 펀드를 제한한다.

### 특정 월 holdings 완전성

```sql
SELECT 기준일자,
       협회펀드코드,
       COUNT(*) AS 보유라인수,
       MAX(순위) AS 최대순위,
       SUM(펀드내비중) AS 비중합,
       SUM(시가평가액) AS 평가액합
FROM WRDSS.DW_ZI_펀드자산내역
WHERE 기준일자 = '20260504'
  AND 협회펀드코드 IN ('확인할펀드코드1', '확인할펀드코드2')
GROUP BY 기준일자, 협회펀드코드;
```

### 한 펀드의 snapshot 주기

```sql
SELECT 기준일자,
       COUNT(*) AS 보유라인수,
       SUM(펀드내비중) AS 비중합
FROM WRDSS.DW_ZI_펀드자산내역
WHERE 협회펀드코드 = '확인할펀드코드'
  AND 기준일자 BETWEEN '20240101' AND '20261231'
GROUP BY 기준일자
ORDER BY 기준일자;
```

### 한 펀드의 return/TNA/flow 입력 점검

```sql
SELECT 기준일자,
       설정액,
       설정좌수,
       기준가,
       순자산,
       실현수익률,
       BM수익률
FROM WRDSS.DW_ZI_펀드일별분석
WHERE 협회펀드코드 = '확인할펀드코드'
  AND 기준일자 BETWEEN '20250101' AND '20251231'
ORDER BY 기준일자;
```

### 약관 제약·보수 코드 점검

```sql
SELECT 협회펀드코드,
       투자대상구분코드,
       주투자대상명,
       최소투자비율,
       최대투자비율
FROM WRDSS.DW_ZI_펀드약관한도
WHERE 협회펀드코드 = '확인할펀드코드'
ORDER BY 투자대상구분코드;

SELECT 협회펀드코드,
       보수종류코드,
       기관코드,
       보수율
FROM WRDSS.DW_ZI_펀드약관보수
WHERE 협회펀드코드 = '확인할펀드코드'
ORDER BY 보수종류코드, 기관코드;
```

## 7. 주제 선택을 위한 최소 판정 기준

### Kaniel을 선택해도 되는 조건

- 국내 active equity fund의 월별 return/TNA가 최소 10년 이상 존재
- 해지펀드가 보존됨
- share-class 통합 가능
- 운용사 mapping 가능
- 한국 factor 및 sentiment를 만들 수 있음

holdings와 turnover는 parsimonious model의 필수조건이 아니다. 역사적 fee가
없으므로 1차 thesis는 net-return 결과를 핵심으로 두고, gross-return 복제는
외부 fee history를 확보할 때만 수행한다.

### Chalmers를 선택해도 되는 조건

- 최소 8~10년의 월별 full holdings
- holdings–FnGuide 종목 join이 높음
- book-to-market peer를 PIT로 구성 가능
- fund return/TNA/fee가 같은 대표펀드 수준으로 합쳐짐

공시 텍스트, manager 경력, retail/institutional 변수는 없어도 핵심 replication은 가능하지만 논문의 마케팅 메커니즘과 이질성 분석은 줄어든다.

현재 ZI는 첫 번째 조건을 충족하지 못한다. 246개월의 snapshot은 있지만 각
자산구분이 top-10으로 잘리므로, 기간이 길다는 사실로 완전성 결손을 보완할
수 없다.

### Beber를 선택해도 되는 조건

- 한 기준시점에서 50개 이상 주식형 펀드의 약관 제약이 충분히 채워짐
- 각 펀드에 10년 이상 return record가 있음
- BM과 size/value/growth mandate가 해석 가능
- short/cash/leverage/turnover 중 최소 세 가지 제약을 수치화할 수 있음

현재는 자산군·cash 한도는 확인됐지만 short·lending·borrowing·turnover의
구조화 자료가 없어 마지막 조건을 충족했다고 볼 수 없다. `FF02` 자유서술의
표본 coverage와 코딩 일관성을 확인하기 전까지는 조건부 후보다.

### 나머지 후보의 go/no-go

- Cao: ZI top-10에 더해 WRDSS 기관별 종목 holdings 부재까지 확인되어 no-go
- Ahn: 지수 이벤트 기반 축소 replication만 가능. 시장 전체 lendable supply·borrow fee·index ownership이 없어 exact replication은 no-go
- Arnott: 과거 지수 구성·비중과 effective date는 확인. 실제 종목 diff와 announcement date·변경사유 연결이 남은 gate

## 8. 최종 권고

DB 확인 순서는 다음이 가장 효율적이다.

1. **Kaniel을 기본 선택**으로 두고, return의 보수·분배금 처리와 한국 factor/sentiment를 확인한다.
2. **Arnott를 데이터 기준 2순위**로 두고, KRX 구성종목 전후 diff와 announcement date·변경사유를 확인한다.
3. 최적화·mandate 주제를 선호하면 **Beber를 조건부 3순위**로 두되, short/lending/borrowing/turnover 자유서술 코딩과 표본 수를 gate test한다.
4. Kaniel의 share-class 합산과 운용사 변수를 검증한다. family data는 1999년부터 존재하지만 개인 manager 변수는 제외한다.
5. **Chalmers·Cao는 중단**하고, Ahn은 가격발견 중심 축소 설계를 명시적으로 수용할 때만 검토한다.

현재 데이터 실행확실성 기준 최종 권고는 **Kaniel > Arnott > Beber(조건부) > Ahn(축소)**이다.
다만 key paper의 학술지 prestige를 강하게 적용하면 tier 4인 Arnott보다 tier 3인
Beber가 선호될 수 있다. 이 경우에도 Beber의 constraint coding gate를 먼저
통과해야 하며, 데이터가 없는 상태에서 학술지 등급만으로 순위를 올리면 안 된다.
**Chalmers는 ZI top-10 때문에, Cao는 top-10과 기관 holdings 부재 때문에
보류/no-go**다. 이 결론을
뒤집으려면 최소 8~10년의 survivorship-bias-free full holdings를 다른
원천에서 확보해야 한다.
