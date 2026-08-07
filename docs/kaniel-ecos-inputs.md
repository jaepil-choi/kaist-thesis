# Kaniel replication용 한국은행 ECOS 입력

기준일: 2026-08-07  
원천: 한국은행 ECOS Open API

## 판정

ECOS에서 **무위험수익률(RF)**, **경기상태 robustness proxy**, 그리고 논문의
전체 실행을 위한 **불완전한 ECOS-only sentiment proxy**를 확보했다. 이 proxy는
시장 회전율과 개인 수급·예탁금·신용융자잔고만 사용하므로 원 논문의
Baker–Wurgler 지수와 동일하지 않다. 모든 설정·manifest·산출물에서 `proxy`로
표시하며 exact replication 결과와 구분한다.

## 수집한 시계열

모든 시계열은 월별(`M`)이며, 표와 항목은 ECOS metadata에서 먼저 확인했다.

| 역할 | ECOS 표 | 항목 코드 | 항목명 | 단위 | 기간 |
|---|---|---|---|---|---|
| primary RF | `721Y001` | `6010300` | 통안증권(91일) | 연% | 2006-09~2026-07 |
| RF robustness | `721Y001` | `2010000` | CD(91일) | 연% | 1991-03~2026-07 |
| activity proxy | `513Y001` | `E1000` | 경제심리지수(원계열) | 지수 | 2003-01~2026-07 |
| activity proxy | `513Y001` | `E2000` | 경제심리지수(순환변동치) | 지수 | 2003-01~2026-07 |
| macro robustness | `511Y002` | `FME / 99988` | 소비자심리지수, 전체 | 지수 | 2008-07~2026-07 |
| sentiment component | `901Y014` | `1090000` | KOSPI 상장주식 회전율 | % | 2005-01~2026-06 |
| sentiment component | `901Y014` | `2110000` | KOSDAQ 상장주식 회전율 | % | 2004-01~2026-06 |
| sentiment component | `901Y055` | `S22BB / VA` | 개인 매수 거래대금 | 백만원 | 2004-01~2026-06 |
| sentiment component | `901Y055` | `S22AB / VA` | 개인 매도 거래대금 | 백만원 | 2004-01~2026-06 |
| sentiment component | `901Y056` | `S23A` | 투자자 예탁금 | 원 | 1998-06~2026-07 |
| sentiment component | `901Y056` | `S23E` | 신용융자 잔고 | 원 | 1998-06~2026-07 |

원 응답 11개 파일은 총 3,191개 관측치다. API key는 저장하지 않았고 manifest의
request URL은 `{key}`로 redaction했다.

## 채택한 변환

### 무위험수익률

primary series는 단기·저신용위험 원화 금리에 가까운 통안증권 91일물이다.
연율 percent 금리 $y_t$를 월 decimal 수익률로 다음과 같이 변환한다.

$$
RF_t = (1 + y_t / 100)^{1/12} - 1.
$$

CD 91일물은 은행 신용위험이 섞이므로 primary RF가 아니라 robustness 비교용이다.

### 경기상태

`korea_activity_monthly.csv`의 `activity`는 ESI 순환변동치에서 기준값 100을 뺀
값이다. ESI는 기업·소비자 심리를 합성한 지수이므로 CFNAI와 동일한 실물활동
지표가 아니다. 따라서 **한국 경기상태 robustness proxy**로만 사용한다.

ECOS 관측월은 발표일 또는 당시 공개 vintage를 담지 않는다. 예측변수로 사용할
때는 원칙적으로 다음 달부터 가용하다고 보고 최소 1개월 lag를 적용하거나,
별도 발표일 자료로 point-in-time 정렬해야 한다.

### 투자심리 구성 후보

개인 매수·매도 거래대금으로 `(매수-매도)/(매수+매도)`를 만들고, 예탁금과
신용융자잔고는 양수 수준의 로그차분을 제공한다.

`korea_sentiment_proxy_monthly.csv`는 다음 5개 구성요소로 만든다.

- KOSPI 회전율
- KOSDAQ 회전율
- 개인 매수·매도 불균형
- 투자자예탁금 로그증감
- 신용융자잔고 로그증감

2005-01~2014-12의 120개월을 고정 calibration 표본으로 사용해 평균과 표준편차,
첫 번째 PCA loading을 추정한다. 첫 PC는 calibration 변동의 42.18%를 설명한다.
부호는 KOSPI·KOSDAQ 회전율과 신용융자 증가의 평균과 양의 상관을 갖도록
고정한다. calibration 계수는 2015년 이후 다시 추정하지 않는다.

ECOS 관측월 값을 다음 월의 `sentiment`로 기록해 1개월 availability lag를
강제한다. 최종 proxy는 2015-01~2026-07의 139개월이며, 이는 **불완전한
ECOS-only market-sentiment proxy**이지 원 논문의 최종 sentiment series가 아니다.

Baker–Wurgler에 가까운 한국형 합성지수를 완성하려면 ECOS 밖에서 최소한 다음을
추가해야 한다.

- 월별 IPO 수
- IPO 첫날 수익률
- 총 주식·채권 발행 중 주식발행 비중
- dividend premium

이 자료를 확보하면 현재 ECOS-only proxy와 별도로 exact-definition에 가까운
확장 지수를 만들고 결과의 민감도를 비교한다.

## 파일과 재현

- raw: `data/kaist_pilot/canonical/kaniel_2023/ecos/raw/`
- derived: `data/kaist_pilot/canonical/kaniel_2023/ecos/derived/`
- sentiment proxy: `data/kaist_pilot/canonical/kaniel_2023/ecos/derived/korea_sentiment_proxy_monthly.csv`
- manifest: `data/kaist_pilot/metadata/manifests/113_kaniel_ecos_inputs_20260807.json`
- 변환 코드: `scripts/kaist_pilot/build_kaniel_ecos_inputs.py`

```powershell
uv run python scripts/kaist_pilot/build_kaniel_ecos_inputs.py
uv run python kaniel-2023-replication/run.py validate-inputs
```

변환기는 raw service, redacted request, 전체 row 회수 여부, 표·항목 코드, 단위,
숫자 변환, 월 중복·누락을 검사한 뒤 CSV와 SHA-256 manifest를 다시 만든다.
기본 설정은 ECOS RF·activity·sentiment proxy와 생성된 non-PIT Carhart
sensitivity를 읽는다. `validate-inputs`의 네 항목이 모두 `OK`여야
`run-parsimonious`를 실행할 수 있다.