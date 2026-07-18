# KAIST Thesis 3-Year Pilot 데이터 추출 요청서

작성일: 2026-07-17

## 1. Pilot 범위

시계열 자료의 공통 기간은 **2023-01-01~2025-12-31**로 고정한다. 2026년은
완결되지 않은 연도이므로 포함하지 않는다.

- Kaniel: 3년 자료로 fund return·TNA·flow, share-class, family join을 검증
- Arnott: **2024년에 효력이 발생한 KOSPI200 정기변경**을 대상으로 전후
  1년인 2023~2025년 자료를 검증
- Beber: 현재 약관 snapshot과 2023~2025년 스타일·성과자료를 연결할 수
  있는지 검증

이 pilot은 최종 가설검정용 표본이 아니다. Kaniel의 36개월 rolling beta나
장기 성과 지속성, Arnott의 여러 리밸런싱 cycle, Beber의 장기 성과평가는
pilot 통과 후 기간을 확장한다.

## 2. 공통 fund master와 분류자료

이 테이블들은 시계열이 아니라 현재 snapshot/reference table이므로 기간
조건을 걸지 않는다. 추출 기준일을 metadata에 기록한다.

### 2.1 `WRDSS.DW_ZI_펀드기본정보`

요청 컬럼:

```text
협회펀드코드
운용사코드
운용사펀드코드
한글펀드명
펀드구분
협회분류코드
대유형코드
유형코드
설정일
해지구분
해지일
최초설정액
최초설정좌수
최초기준가
전체주식편입한도
코스닥편입한도
제로인평가여부
운용사평가여부
BM코드
BM한글명
BM영문명
환헷지여부
집합투자분류코드
```

필터: 없음. 해지펀드도 포함한다.

### 2.2 `WRDSS.DW_ZI_클래스펀드`

요청 컬럼:

```text
펀드구분
대표펀드코드
서브펀드코드
설정구분
```

필터: 없음.

### 2.3 Fund type·attribute codebook

다음 테이블은 전 컬럼을 요청한다.

```text
WRDSS.DW_ZI_펀드별속성코드
  - 협회펀드코드, 속성코드

WRDSS.DW_ZI_속성코드
  - 속성코드, 레벨, 속성코드명, 상위속성코드

WRDSS.DW_ZI_유형코드
  - 대유형코드, 유형코드, 대유형명, 유형명

WRDSS.DW_ZI_코드정보
  - 상위코드, 코드, 코드명, 비고
```

필터: 없음.

이 자료를 먼저 받은 뒤 내가 **국내 공모 주식형 fund code whitelist**를
확정해 전달한다. 담당자가 임의로 active fund나 현재 생존펀드만 선택하지
않는다. whitelist에는 다음을 구분해 유지한다.

```text
active / passive / enhanced-index
대표펀드 / share class
존속 / 해지
국내주식형 / 해외주식형
운용사코드
```

## 3. Kaniel 3-Year Pilot

### 3.1 Fund-day core panel

소스:

```text
WRDSS.DW_ZI_펀드일별분석
```

기간:

```text
기준일자 BETWEEN '20230101' AND '20251231'
```

대상:

```text
공통 master로 확정해 전달하는 국내 공모 주식형 협회펀드코드 whitelist
active, passive, enhanced-index를 모두 받고 분석 단계에서 구분
해지펀드와 해지 전 과거자료 포함
모든 share class 포함
```

요청 컬럼:

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

변환하지 말아야 할 항목:

- `실현수익률`과 `BM수익률`은 원본 factor 형식 그대로 제공
- 설정일의 `순자산=0`, `실현수익률=1` placeholder row 유지
- NULL을 0으로 바꾸지 않음
- 일별자료를 월말자료로 사전 집계하지 않음

Pilot 확인사항:

- 월별 fund return을 일별 factor로 정확히 복리 계산할 수 있는지
- `순자산_t / (순자산_(t-1) × 실현수익률_t) - 1` flow 계산의 안정성
- 설정일·해지일과 일별자료의 연결
- 대표펀드와 share class의 중복 없는 TNA 가중 통합
- active/passive 분류와 국내주식 exposure의 일관성

### 3.2 Asset-manager daily validation panel

소스:

```text
WRDSS.DW_ZI_운용사일별분석
```

기간:

```text
기준일자 BETWEEN '20230101' AND '20251231'
```

대상:

```text
fund whitelist에 포함된 운용사코드
fund whitelist에 대응하는 제로인유형코드
```

요청 컬럼:

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

용도: fund-level 합산으로 만든 family TNA·return·flow와 vendor의
운용사자료가 일치하는지 검산한다.

### 3.3 Monthly factor series

회사에 이미 한국 Carhart factor가 있으면 다음 형식으로 요청한다.

기간:

```text
2023-01~2025-12
```

요청 컬럼:

```text
기준월
MKT_RF
SMB
HML
MOM
RF
각 factor의 산출 universe
각 factor의 value-weight/equal-weight 구분
```

기존 factor가 없으면 1차 pilot에서는 raw stock data를 추가 요청하지 않고,
fund panel의 return·flow·join 검증부터 수행한다. 한국형 sentiment는
한국은행 공개자료로 별도 구축하므로 회사 추출 대상에서 제외한다.

## 4. Arnott 3-Year Pilot

Pilot 대상 지수는 **KOSPI200 한 개**로 제한한다.

```text
지수 ISIN = 'KRD020020016'
구성·지수 시계열 = 2023-01-01~2025-12-31
분석 대상 event = effective date가 2024-01-01~2024-12-31인 변경
```

2024년 event만 쓰면 2023년의 사전 1년과 2025년의 사후 1년을 완결된
calendar year로 관측할 수 있다.

### 4.1 KOSPI200 daily constituents

소스:

```text
WRDSS.DW_KRX지수구성
```

필터:

```text
지수ISIN = 'KRD020020016'
AND 일자 BETWEEN '20230101' AND '20251231'
```

요청 컬럼:

```text
일자
지수ISIN
지수명국문
종목코드1
종목코드2
종목명국문
증권종류
국가코드1
통화코드
MIC
표준산업분류코드
지수업종코드
상장주식수
상장시가총액
지수주식수
유동비율
CAP비율
조정가중치
지수시가총액
지수내비중
적용일
WEIGHT_TR
```

용도:

- 일자별 membership과 weight 복원
- 변경 직전일과 효력일의 종목코드 set difference로 편입·편출 식별
- KRX 공시의 편입·편출 목록과 교차검증

### 4.2 KOSPI200 daily index series

소스:

```text
WRDSS.DW_KRX지수산출
```

필터:

```text
ISIN = 'KRD020020016'
AND 일자 BETWEEN '20230101' AND '20251231'
```

요청 컬럼:

```text
일자
변경여부
ISIN
지수명국문
지수명영문
기준시점
기준지수값
종가지수값
전일대비
비교시가총액변경전
비교시가총액변경후
구성종목수변경전
구성종목수변경후
다음정기변경일
지수PER
지수PBR
지수배당수익률
적용일
```

`변경여부`는 단독 event signal로 쓰지 않는다. `다음정기변경일`의 전환과
구성종목 set difference를 함께 사용한다.

### 4.3 2024 KOSPI200 change announcements

KRX 공시 또는 회사 내부 event archive에서 요청한다.

기간:

```text
effective date BETWEEN '20240101' AND '20241231'
```

요청 컬럼:

```text
지수ISIN
지수명
announcement date
announcement time
effective date
actual index trade date
종목코드
종목명
편입/편출 구분
정기/수시 구분
변경사유
공시문서 ID
원문 파일 또는 URL
```

해당 원천이 없으면 없는 것으로 명시해 달라고 요청한다. effective date를
announcement date로 대체하지 않는다.

### 4.4 Event-stock daily market data

대상:

```text
4.1과 4.3에서 확정된 2024년 KOSPI200 편입·편출 종목
```

기간:

```text
2023-01-01~2025-12-31
```

요청 컬럼:

```text
일자
영구 종목 ID
6자리 종목코드
종목명
수정종가
현금배당과 corporate action을 포함한 daily total return
거래량
거래대금
시가총액
상장주식수
유동주식수
bid
ask
거래정지 flag
상장폐지일
상장폐지 return
시장구분
산업분류
```

bid/ask가 없으면 그 사실을 명시하고 나머지 컬럼을 제공한다. total return과
단순 수정주가수익률을 혼동하지 않도록 vendor field definition을 첨부한다.

## 5. Beber 3-Year Pilot

약관 table은 날짜 컬럼이 없는 **현재 snapshot**이다. 따라서 2023~2025년
필터를 걸 수 없다. 추출일 현재 상태라는 사실을 metadata에 기록한다.

공통 master를 받은 뒤 내가 전달하는 국내 active equity **30개
협회펀드코드 whitelist**만 pilot에 사용한다. 30개는 share class 중복을
제거하고 10년 이상 return record가 있는 펀드에서 선정한다.

### 5.1 Current mandate limits

소스:

```text
WRDSS.DW_ZI_펀드약관한도
```

필터:

```text
협회펀드코드 IN (내가 전달하는 30개 whitelist)
```

요청 컬럼:

```text
협회펀드코드
투자대상구분코드
주투자대상명
최소투자비율
최대투자비율
```

row가 없는 경우를 0으로 생성하지 않는다.

### 5.2 Current mandate text

소스:

```text
WRDSS.DW_ZI_펀드약관투자
```

필터:

```text
협회펀드코드 IN (내가 전달하는 30개 whitelist)
```

요청 컬럼:

```text
협회펀드코드
데이터구분코드
내용
```

`내용`은 VARCHAR2 원문 전체를 잘림 없이 제공한다.

### 5.3 Monthly style panel

소스:

```text
WRDSS.DW_ZI_펀드스타일분석
```

필터:

```text
협회펀드코드 IN (내가 전달하는 30개 whitelist)
AND 기준일자 BETWEEN '20230101' AND '20251231'
```

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

Pilot 통과 조건:

- 30개 펀드에서 size/value-growth 9-box가 월별로 안정적으로 합계 100%
- 약관한도에서 row 부재와 명시적 0%가 구분됨
- `내용`에서 borrowing/leverage, short sale, securities lending,
  derivatives, turnover 중 최소 세 가지를 동일 규칙으로 코딩 가능
- current mandate와 2023~2025년 style이 경제적으로 모순되지 않음

위 조건이 실패하면 Beber용 추가 추출을 중단한다.

## 6. 이번 pilot에서 요청하지 않을 데이터

- `DW_ZI_펀드자산내역`: top-10뿐이므로 full holdings 분석에 부적합
- `DW_ZI_펀드지표분석`: raw return으로 성과지표를 직접 계산
- `DW_ZI_운용사기간분석`: fund-level 합산 검증 후 필요할 때 요청
- `DW_ZI_펀드약관보수`: 현재값만 있어 2023~2025년 fee history가 아님
- `FA_대차자산`, `DW_FA_대차담보명세`: 시장 대차자료가 아님
- 개인 펀드매니저 자료와 기관별 종목 holdings: WRDSS에 전용 table 없음
- KOSDAQ150·KRX300: KOSPI200 pilot 통과 후 확장
- 2026년 자료: incomplete year이므로 제외

## 7. 전달 형식과 검수

- Parquet 형식, UTF-8, 원본 numeric precision 유지
- 날짜는 원본 `YYYYMMDD` 또는 ISO date 중 하나로 통일
- NULL, 0, 빈 문자열을 서로 변환하지 않음
- 해지펀드, 거래정지종목, 상장폐지종목을 임의로 제거하지 않음
- 각 파일에 source table, extraction timestamp, SQL, column definition 첨부
- 각 파일에 min/max date와 key duplicate 검사 결과 첨부

예상 grain은 아래와 같다. 실제 key가 다르거나 이 grain에서 중복이 있으면
임의 제거하지 말고 중복 원인을 함께 전달한다.

```text
펀드일별분석: 기준일자 × 협회펀드코드
운용사일별분석: 기준일자 × 운용사코드 × 제로인유형코드
KRX지수구성: 일자 × 지수ISIN × 종목코드
KRX지수산출: 일자 × ISIN
펀드스타일분석: 기준일자 × 협회펀드코드
```

## 8. 담당자에게 보낼 요청 순서

fund whitelist와 Beber 30개 표본은 master를 본 뒤 내가 정해야 한다. 따라서
두 번으로 요청한다.

### 8.1 지금 보낼 1차 메시지

```text
안녕하세요. KAIST thesis 주제 feasibility 확인을 위해 3-year pilot 데이터
추출을 요청드립니다.

공통 시계열 기간은 2023-01-01~2025-12-31입니다. 2026년은 포함하지 않습니다.

1. ZI fund master/class/type/attribute/codebook snapshot
2. KOSPI200(ISIN KRD020020016) 구성종목·비중과 지수산출:
   2023-01-01~2025-12-31
3. effective date가 2024년인 KOSPI200 편입·편출 공시와 해당 종목의
   2023-01-01~2025-12-31 일별 시장자료

정확한 컬럼 목록과 필터는 첨부 명세에 기재했습니다. 일별 return factor,
NULL/0, 설정일 placeholder를 변환하지 말고 원자료로 부탁드립니다.
해지펀드와 상장폐지종목도 제외하지 말아 주세요.

파일별 추출 SQL, extraction timestamp, min/max date, column definition을 함께
부탁드립니다.
```

### 8.2 Master 검토 후 보낼 2차 메시지

```text
앞서 받은 master 기준으로 국내 공모 주식형 fund whitelist와 Beber pilot
30개 fund code를 첨부드립니다.

1. 첨부 whitelist의 DW_ZI_펀드일별분석:
   기준일자 2023-01-01~2025-12-31
2. whitelist에 대응하는 운용사코드·제로인유형코드의
   DW_ZI_운용사일별분석: 기준일자 2023-01-01~2025-12-31
3. 첨부 30개 fund code의 현재 DW_ZI_펀드약관한도·펀드약관투자
4. 같은 30개 fund code의 DW_ZI_펀드스타일분석:
   기준일자 2023-01-01~2025-12-31

컬럼과 원자료 보존 조건은 기존 명세와 동일하게 부탁드립니다.
```
