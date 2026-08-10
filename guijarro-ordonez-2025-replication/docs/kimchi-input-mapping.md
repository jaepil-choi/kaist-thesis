# Kimchi Factor 입력 및 계정 매핑

## 판정

이 문서는 저장소 루트의 `docs/kimchi-factor-methodology.md`를 실제 로컬 필드에
연결한 실행 계약이다. 방법론의 산식과 로컬 필드가 충돌하면 차이를 숨기지 않고
여기에 기록한다.

## 가격과 수익률

- 가격 원천: `adjusted_prices.parquet`
- 팩터 산출 시작: 2018-01-02
- `return`: 권리·분할 조정 가격수익률이며 현금배당을 포함하지 않는다.
- `종가`: 해당 거래일의 비조정 종가다.
- ME는 저장된 `market_cap`을 그대로 신뢰하지 않고 `종가 × 유통주식수`로 다시
  계산한 뒤 저장값과 전 행 exact equality를 검사한다. 이 원천 필드는 삼성전자
  표본에서 `ending_common_shares`와 일치하지만, KOSPI200-ever 교집합 670,310행
  중 exact match는 96.56%였다. 별도 `ending_common_shares` 파일은 309종목만
  포함하므로 전체 유니버스 ME에 사용할 수 없다. 따라서 산출은 가격 원천의
  주식수 필드를 쓰되 이 명칭·시점 차이를 audit 제약으로 남긴다.

현금배당 원천 `fng_dividend_items.parquet`에는 회계연도 전체 DPS만 있고 개별
배당락일과 중간·분기·결산 배당의 사건별 DPS가 없다. 따라서 이 파일만으로 일별
total return을 정확히 복원할 수 없다. 사용자의 2026-08-10 확인에 따라 이번
산출은 `adjusted_prices.return`을 사용하는 **price-return variant**로 만들며,
total-return exact replication이라고 표시하지 않는다.

## 시장과 유니버스

- 시장·종목 원천: `DW_FNG_FGSC종목`
- `시장구분='1'`: KOSPI
- `시장구분='2'`: KOSDAQ
- FGSC 구성 종목을 보통주 기본 universe로 사용한다. 우선주처럼 FGSC 산업분류
  구성에 없는 종목은 제외된다.
- 원천 `종목명`에 `스팩`, `SPAC` 또는 `기업인수목적`이 포함되면 DB 내부에서
  `SPAC_YN=1`로 판정하고 원문 이름은 내려받지 않는다. 합병 후 이름이 바뀐 row는
  이후 리밸런싱부터 `SPAC_YN=0`으로 포함한다. 원문 이름을 제외하는 이유는 2018년
  일부 row가 SQLPlus client 변환에서 `ORA-29275`를 일으키기 때문이다.
- 거래정지는 `adjusted_prices.is_trading_halt`를 리밸런싱일에 적용한다.
- 금융업은 같은 월말 스냅샷의 `FGSC지수코드`가 `FGSC.40`으로 시작하는지로
  판정한다.

로컬 2018~2025 FGSC parquet에는 `시장구분`이 빠져 있다. 월별 MOM과 연간 6월
리밸런싱에 필요한 월말 102개 날짜만 조회하는 제한 SQL을
`sql/fng_fgsc_market_rebalance_snapshots_201801_202606.sql`에 고정한다.

## 시장수익률과 무위험수익률

- RM: ECOS `802Y001`, 항목 `0001000` KOSPI지수의 일별 지수수익률
- RF: ECOS `817Y002`, 항목 `010502000` CD(91일)의 252일 복리 환산수익률
- RMRF: `RM - RF`
- 월간 RM은 일간 RM의 합산이 아니라 월말 KOSPI 지수 수준의 한 달 보유수익률로
  독립 계산한다.
- 월간 RF 환산은 별도 기준자료가 없으므로 일별 RF를 합산하지 않고
  `(1 + 연율/100)^(1/12) - 1`을 월말 관측금리에 적용한다. 이 convention은
  산출 audit에 명시한다.

## 연결 재무제표 계정

검토 근거는 `kwam-enhanced-index/configs/mappings/dataguide_statement_mapping.csv`,
`configs/data/datasets/market.yaml` 및
`docs/thoughts/mp-fng-financials-truth-discovery.md`다.

| 항목 | primary account | 검증 및 fallback |
|---|---|---|
| 총자산 | `4001110000` | clean exact single account |
| 총부채 | `4001140000` | clean exact single account; 과거 자본총계 결측 시 대차대조표 항등식에만 사용 |
| 자본총계 | `4001160000` | `4001570000`은 중복 후보; overlap 값이 같은 경우에만 fallback |
| 지배주주지분 교차검증 | `4001160050` | clean exact single account |
| 비지배주주지분 | `4001167500` | `4001550000`은 중복 후보; overlap 값이 같은 경우에만 fallback |
| 영업이익 | `4001230000` | clean exact single account |
| 이자비용 | `4001250100` | clean exact single account |
| 유형자산감가상각비 | `4001410500` | cash-flow mapping의 clean exact single account |
| 무형자산상각비 | `4001410600` | cash-flow mapping의 clean exact single account |

직접 EBITDA account는 mapping에 없다. 다음 구성식으로 산출한다.

$$
EBITDA = 영업이익 + 유형자산감가상각비 + 무형자산상각비
$$

따라서 방법론의 영업수익성은 다음과 같다.

$$
OPE/BE = \frac{EBITDA-이자비용}{BE}
$$

BE는 우선 `자본총계 - 비지배주주지분`으로 계산하고, 비지배주주지분 row가
없으면 0으로 둔다. 과거 계정체계에서 자본총계가 없는 경우 `4001160050`
지배주주지분을 사용하고, 이것도 없으면 마지막으로
`총자산 - 총부채 - 비지배주주지분`의 대차대조표 항등식을 사용한다. 각 행의
경로는 `book_equity_source`에 저장한다.

`4001160000/4001570000`과 `4001167500/4001550000`은 mapping상 ambiguous
multi-account다. 실제 overlap 25,634 key 중 533 key에서 값이 달랐으므로 서로를
동일 계정으로 간주하지 않는다. 표의 primary를 우선하고 primary가 없을 때만
secondary를 사용한다.

동일 달력연도에 `D` 결산 row가 두 개인 19개 issuer-year는 결산기 변경 사례다.
6월 Y 리밸런싱에는 달력연도 Y-1 안에서 마지막으로 끝난 annual `D` statement를
선택한다.

## SMB의 정렬 신호

제공된 Kimchi 파일에서 SMB와 HML의 2×3 construction bucket 14,712행은 수익률과
종목 수가 모두 완전히 동일하다. 따라서 SMB는 BM 2×3 정렬의 size leg이며,
HML과 같은 S1~B3 포트폴리오에서 다음처럼 계산한다.

$$
SMB = mean(S1,S2,S3)-mean(B1,B2,B3)
$$

HML은 같은 포트폴리오의 high-minus-low leg다. RMW, CMA 및 MOM은 각자 자신의
신호로 별도 2×3 및 quintile 포트폴리오를 만든다.
