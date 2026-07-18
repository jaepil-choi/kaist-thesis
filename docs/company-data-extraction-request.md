# KAIST Thesis 3-Year Pilot 추가 데이터 추출 요청서

작성일: 2026-07-18

## 1. 요청 목적과 현재 상태

KAIST thesis 후보인 Kaniel et al.의 fund-skill ML 연구와 Beber et al.의
bespoke benchmark 연구에 필요한 3-year pilot 자료를 추가로 요청한다.

공통 시계열 기간은 **2023-01-01~2025-12-31**이다. 2026년은 완결되지 않은
연도이므로 포함하지 않는다. 이 pilot은 데이터 구조와 계산 가능성을 확인하기
위한 것이며 최종 가설검정용 표본은 아니다.

현재 상태는 다음과 같다.

| 구분 | 상태 | 회사에 추가 요청 |
|---|---|---|
| 공통 fund master·분류자료 | 수령 완료 | 없음 |
| Arnott KOSPI200 구성·지수자료 | 수령 완료 | 없음 |
| Arnott 공시·종목별 시장자료 | 다른 원천에서 확보 가능 | 없음 |
| Kaniel fund-day panel | 미수령 | **필요** |
| Kaniel manager-day panel | 미수령 | **필요** |
| Beber 약관한도·약관투자·스타일 panel | 미수령 | **필요** |
| 한국 Carhart factor·sentiment | 외부에서 별도 구축 | 없음 |
| 기존 추출 manifest | 미수령 | 가능하면 재전달 요청 |

회사에 새로 요청하는 핵심은 아래 다섯 원천이다.

```text
WRDSS.DW_ZI_펀드일별분석
WRDSS.DW_ZI_운용사일별분석
WRDSS.DW_ZI_펀드약관한도
WRDSS.DW_ZI_펀드약관투자
WRDSS.DW_ZI_펀드스타일분석
```

## 2. 수령 완료 자료

### 2.1 Fund master·분류자료

다음 current snapshot/reference parquet 6개를 수령했다.

| 파일 | 행 수 | 검수 상태 |
|---|---:|---|
| `dw_zi_펀드기본정보.parquet` | 167,588 | `협회펀드코드` 중복·결측 0 |
| `dw_zi_클래스펀드.parquet` | 50,121 | 관계 유형별 분리 필요 |
| `dw_zi_펀드별속성코드.parquet` | 966,365 | `(협회펀드코드, 속성코드)` 중복 0 |
| `dw_zi_속성코드.parquet` | 385 | 수령 완료 |
| `dw_zi_유형코드.parquet` | 300 | 수령 완료 |
| `dw_zi_코드정보.parquet` | 708 | 수령 완료 |

이 자료로 국내 공모 주식형, active/passive/enhanced-index, share class,
해지 여부, 운용사코드를 로컬에서 분류한다. 회사 담당자가 임의로 현재
생존펀드나 active fund만 선별할 필요는 없다.

`DW_ZI_클래스펀드`에는 share-class 관계와 모자펀드 관계가 함께 있다.

- `펀드구분=1`: share-class 관계
- `펀드구분=2`: 모펀드-자펀드 관계

두 관계를 단순히 하나의 대표펀드 매핑으로 합치면 중복 집계가 발생하므로,
분석 단계에서 별도로 처리한다.

### 2.2 Arnott KOSPI200 자료

다음 자료를 수령했다.

| 파일 | 행 수 | 기간 |
|---|---:|---|
| `kaist_kospi200_constituents.parquet` | 146,253 | 2023-01-02~2025-12-30 |
| `kaist_kospi200_index_levels.parquet` | 731 | 2023-01-02~2025-12-30 |

KOSPI200 ISIN은 `KRD020020016`이고, 구성자료의 예상 키
`(일자, 지수ISIN, 종목코드1)` 중복은 0이다. 2024년 정기변경 effective
date와 편입·편출 종목도 구성종목 set difference로 복원할 수 있다.

Arnott에 추가로 필요한 다음 자료는 다른 원천에서 확보할 예정이므로 회사에
추출을 요청하지 않는다.

- 정기·수시변경 최초 공시일시와 정정공시 이력
- effective date와 실제 index trade date
- 편입·편출 구분, 변경사유, 공시문서 ID
- 종목별 total return, 거래량·거래대금, 시가총액, bid/ask
- 거래정지, 상장폐지, corporate action 자료

### 2.3 재전달을 요청하는 metadata

Parquet는 수령했지만 아래 manifest JSON은 전달받지 못했다. 기존 실행 결과가
남아 있다면 재추출 없이 파일만 전달해 주면 된다.

```text
097_manifest_*.json
098_manifest_*.json
099_manifest_*.json
```

manifest에는 최소한 source table, 실행시각, SQL, 컬럼, 행 수, 기간,
key duplicate 검사 결과가 포함되어야 한다.

## 3. DB 부하를 줄이기 위한 추출 원칙

### 3.1 사용하지 않을 방식

국내 공모 주식형 예비 universe는 수천 개의 `협회펀드코드`를 포함한다.
따라서 아래 방식은 사용하지 않는다.

- 수천 개 코드를 `WITH targets AS (... UNION ALL ...)`로 SQL에 삽입
- 대형 일별 table과 fund whitelist를 DB에서 join
- fund code chunk와 date chunk를 동시에 적용해 같은 table을 수백 번 반복 조회
- 전체 기간을 한 번에 조회

### 3.2 요청 방식

대형 일별자료는 **기간 chunk 단위의 단순 SELECT**로 추출한다.

- fund-day: 기간 조건 + `대유형코드='20'`
- manager-day: 기간 조건만 사용하거나, 필요하면 소수의 `운용사코드 IN (...)`
- Beber: 30개 fund code이므로 단순 `IN (...)`

월별 또는 분기별로 받은 결과는 DB 밖에서 다음과 같이 처리한다.

1. chunk별 parquet 저장
2. 로컬 `concat`
3. whitelist filter
4. 예상 key duplicate 검사
5. 정렬 후 canonical parquet 저장

SQL `UNION`처럼 중복을 자동 제거하지 않는다. 중복이 있으면 삭제하지 말고
원인을 확인한다.

## 4. 추가 요청 1: Kaniel fund-day core panel

### 4.1 소스와 기간

소스:

```text
WRDSS.DW_ZI_펀드일별분석
```

기간:

```text
기준일자 BETWEEN '20230101' AND '20251231'
```

### 4.2 대상과 필터

DB에서는 whitelist join을 하지 않고 국내 공모 주식형 대유형 전체를 받는다.

```sql
WHERE 기준일자 BETWEEN :chunk_start AND :chunk_end
  AND 대유형코드 = '20'
```

월별 또는 분기별 non-overlapping date chunk로 실행한다. active, passive,
enhanced-index, 해지펀드, 모든 share class를 포함한다. 현재 상태나 펀드명으로
추가 필터링하지 않는다.

active/passive, ETF/index, 생존기간, share-class는 수령한 master·codebook을
사용해 로컬에서 구분한다.

### 4.3 요청 컬럼

```text
기준일자
협회펀드코드
설정액
설정좌수
기준가
순자산
실현수익률
BM수익률
수익률지수
BM수익률지수
대유형코드
유형코드
주식평가액합
국내주식KSE평가액
국내주식KOSDAQ평가액
국내주식기타평가액
국외주식평가액
채권평가액합
유동성자산평가액
제로인평가여부
```

예상 grain:

```text
기준일자 × 협회펀드코드
```

### 4.4 원자료 보존 조건

- `실현수익률`과 `BM수익률`은 원본 decimal factor 형식 그대로 제공
- 설정일의 `순자산=0`, `실현수익률=1` placeholder row 유지
- NULL, 0, 빈 문자열을 임의로 변환하지 않음
- 해지펀드의 해지 전 과거자료를 제거하지 않음
- 일별자료를 월말자료로 사전 집계하지 않음
- 숫자 반올림 또는 소수점 자릿수 축소를 하지 않음

### 4.5 Pilot 검증 항목

- 일별 return factor의 월별 복리 집계
- 아래 flow 계산의 안정성

\[
\text{flow}_{i,t}
=
\frac{\text{TNA}_{i,t}}
{\text{TNA}_{i,t-1}\times\text{return factor}_{i,t}}
-1
\]

- 설정일·해지일과 일별자료의 연결
- share-class TNA 가중 fund-level return
- active/passive 분류와 실제 국내주식 exposure의 일관성
- survivorship-bias-free 표본 구성 가능성

## 5. 추가 요청 2: Kaniel manager-day validation panel

### 5.1 소스와 기간

소스:

```text
WRDSS.DW_ZI_운용사일별분석
```

기간:

```text
기준일자 BETWEEN '20230101' AND '20251231'
```

### 5.2 대상과 필터

원 논문의 family TNA는 국내주식형 한 유형만이 아니라 같은 운용사의 전체
펀드 family를 의미한다. 따라서 선택된 운용사에 대해
`제로인유형코드`를 국내주식형으로 제한하지 않는다.

선호안:

```sql
WHERE 기준일자 BETWEEN :chunk_start AND :chunk_end
```

운용사일별분석의 3년 전체 자료가 너무 크다면 다음 대안을 사용한다.

1. fund master에서 필요한 distinct `운용사코드` 목록을 로컬로 확정
2. 소수의 운용사코드만 `IN (...)`으로 전달
3. DB join 없이 기간 조건 + 운용사코드 조건으로 SELECT

```sql
WHERE 기준일자 BETWEEN :chunk_start AND :chunk_end
  AND 운용사코드 IN (전달하는 운용사코드 목록)
```

`(운용사코드, 제로인유형코드)` 수천 행짜리 target CTE는 만들지 않는다.

### 5.3 요청 컬럼

```text
기준일자
운용사코드
제로인유형코드
펀드수
설정액
설정좌수
순자산
실현수익률
BM수익률
수익률지수
BM수익률지수
주식평가액
KSE평가액
KOSDAQ평가액
국외주식평가액
채권평가액
유동성자산평가액
```

예상 grain:

```text
기준일자 × 운용사코드 × 제로인유형코드
```

### 5.4 용도

- fund-level 합산으로 만든 family TNA·펀드 수·return과 vendor 자료 검산
- 전체 유형을 합산한 true family TNA와 국내주식형 family TNA를 구분
- manager/family flow와 momentum 구축 가능성 검증

개인 펀드매니저 ID, 담당기간, 경력, team-managed 여부는 WRDSS에서 전용
table을 찾지 못했으며 Kaniel의 parsimonious model에는 필수가 아니므로
이번 요청에서 제외한다.

## 6. 추가 요청 3: Beber mandate·style pilot

### 6.1 대상 표본

수령한 fund master와 Kaniel fund-day coverage를 확인한 뒤, 다음 조건을
만족하는 국내 active equity 30개 펀드코드를 별도 전달한다.

- share-class 중복 제거
- 설정 후 최소 10년 이상 경과
- 장기 return record가 존재할 가능성이 높은 펀드
- 서로 다른 운용사와 스타일을 포함

30개 whitelist 전달 전에는 Beber 쿼리를 실행하지 않는다. 30개는 constraint
coding 가능성을 확인하는 pilot이고, 최종 연구는 50개 이상 표본이 필요하다.

### 6.2 Current mandate limits

소스:

```text
WRDSS.DW_ZI_펀드약관한도
```

필터:

```text
협회펀드코드 IN (별도 전달하는 30개 whitelist)
```

요청 컬럼:

```text
협회펀드코드
투자대상구분코드
주투자대상명
최소투자비율
최대투자비율
```

이 table은 날짜 컬럼이 없는 current snapshot이다. 추출일시를 metadata에
기록한다. row가 없는 경우를 0으로 생성하지 않는다.

### 6.3 Current mandate text

소스:

```text
WRDSS.DW_ZI_펀드약관투자
```

필터:

```text
협회펀드코드 IN (별도 전달하는 30개 whitelist)
```

요청 컬럼:

```text
협회펀드코드
데이터구분코드
내용
```

`내용`은 VARCHAR2 원문 전체를 잘림 없이 제공한다. 다음 제약의 일관된
코딩 가능성을 확인하는 것이 목적이다.

- borrowing/leverage
- short sale
- securities lending
- derivatives
- turnover
- 종목 수·집중도 제한

### 6.4 Monthly style panel

소스:

```text
WRDSS.DW_ZI_펀드스타일분석
```

필터:

```text
협회펀드코드 IN (별도 전달하는 30개 whitelist)
AND 기준일자 BETWEEN '20230101' AND '20251231'
```

30개 코드이므로 DB join 없이 단순 `IN (...)`과 기간 chunk를 사용한다.

요청 컬럼:

```text
기준일자
협회펀드코드
스타일구분
X축구분
X축값
Y축구분
Y축값
단기상가치대형비중
단기중가치중형비중
단기하가치소형비중
중기상혼합대형비중
중기중혼합중형비중
중기하혼합소형비중
장기상성장대형비중
장기중성장중형비중
장기하성장소형비중
펀드PER
스타일PER
시장PER대중소
시장PER전체
펀드PBR
스타일PBR
시장PBR대중소
시장PBR전체
펀드베타KOSPI200
펀드베타KOSPI
```

예상 grain:

```text
기준일자 × 협회펀드코드
```

### 6.5 Beber pilot 통과 조건

- 30개 펀드의 월별 size/value-growth 9-box 비중합이 안정적으로 100%
- 약관한도에서 row 부재와 명시적 0%가 구분됨
- 약관투자 원문에서 borrowing/leverage, short sale, securities lending,
  derivatives, turnover 중 최소 세 가지를 동일한 규칙으로 코딩 가능
- current mandate와 2023~2025년 style이 경제적으로 모순되지 않음
- Kaniel fund-day panel에서 같은 펀드의 return history가 연결됨

이 조건이 실패하면 Beber용 추가 추출과 장기 표본 구축을 중단한다.

## 7. 회사에 요청하지 않는 자료

다음 자료는 불필요하거나 다른 원천에서 확보하므로 이번 회사 추출 대상에서
제외한다.

- Arnott 정기·수시변경 공시와 event-stock 시장자료
- 한국 Carhart factor와 investor sentiment
- `DW_ZI_펀드자산내역`: 자산구분별 top-10이라 full holdings가 아님
- `DW_ZI_펀드지표분석`: raw return으로 성과지표를 직접 계산
- `DW_ZI_운용사기간분석`: manager-day 검증 후 필요할 때 재검토
- `DW_ZI_펀드약관보수`: 현재값만 있고 historical fee가 아님
- 개인 펀드매니저 자료와 기관별 종목 holdings: WRDSS 전용 table 없음
- 시장 대차·공매도 자료
- KOSDAQ150·KRX300 추가 지수자료
- 2026년 시계열 자료

## 8. 전달 형식과 검수자료

### 8.1 데이터 파일

- Parquet 형식
- 한글 컬럼명과 문자열은 UTF-8
- 원본 numeric precision 유지
- 날짜는 원본 `YYYYMMDD` 또는 ISO date 중 하나로 통일
- NULL, 0, 빈 문자열을 서로 변환하지 않음
- chunk별 컬럼 순서와 dtype을 동일하게 유지
- 해지펀드를 임의로 제거하지 않음

### 8.2 파일별 manifest

각 canonical parquet 또는 chunk 묶음에 다음 metadata를 함께 제공한다.

```text
source table
extraction timestamp
실행 SQL 또는 SQL template
chunk start/end
column definition
row count
min/max date
key columns
key duplicate count
```

### 8.3 중복 처리

예상 key에서 중복이 발견되어도 임의로 `drop_duplicates`하지 않는다. 중복
건수와 원인을 manifest에 기록하고 원자료를 그대로 전달한다.

## 9. 담당자에게 보낼 요약 메시지

```text
안녕하세요. 앞서 전달해 주신 KAIST thesis 1차 pilot 자료를 검수했습니다.

수령 완료:
1. ZI fund master/class/type/attribute/codebook 6개
2. KOSPI200 구성종목·비중 및 지수산출 2023~2025

Arnott 공시와 종목별 시장자료는 다른 원천에서 확보할 수 있어 회사에 추가
요청하지 않습니다.

추가로 필요한 회사 자료는 다음과 같습니다.

1. DW_ZI_펀드일별분석
   - 2023-01-01~2025-12-31
   - 대유형코드='20'
   - 월별 또는 분기별 단순 SELECT
2. DW_ZI_운용사일별분석
   - 2023-01-01~2025-12-31
   - 가능하면 기간 조건만 적용
   - 자료가 너무 크면 별도로 전달하는 운용사코드 IN 조건 사용
3. Beber 30개 whitelist 전달 후
   - 현재 DW_ZI_펀드약관한도
   - 현재 DW_ZI_펀드약관투자
   - DW_ZI_펀드스타일분석 2023-01-01~2025-12-31

수천 개 fund code target CTE, UNION ALL, 대형 table과 whitelist의 DB join은
사용하지 않습니다. 기간·대유형 기준으로 SELECT한 파일을 로컬에서
concat/filter하겠습니다.

정확한 컬럼 목록과 원자료 보존 조건은 첨부 명세에 기재했습니다.
기존 097/098/099 manifest JSON이 남아 있다면 함께 부탁드립니다.
감사합니다.
```
