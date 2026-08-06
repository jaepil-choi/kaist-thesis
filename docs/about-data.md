# 논문 데이터 안내 및 카탈로그

작성일: 2026-08-07  
데이터 루트: `data/kaist_pilot/`  
연구 우선순위의 source of truth: `docs/key-paper-selection.md`

## 1. 사용 원칙

- 분석 코드는 기본적으로 `canonical/` 아래 파일만 읽는다.
- vendor raw extract는 불변으로 취급한다. 문자열 숫자 컬럼을 원본 파일에서
  덮어쓰지 말고, 전처리 단계에서 별도 numeric 컬럼을 만든다.
- `archive/beber_2021_no_go/`는 no-go 판정의 근거 보존용이며 현재 논문 분석
  입력이 아니다.
- SQL, 원천 테이블, 실행 시각, 추출 범위와 키 검증은
  `metadata/manifests/`의 JSON을 기준으로 추적한다.

## 2. 디렉터리 구조

```text
data/kaist_pilot/
├── canonical/                 # 현재 분석에서 읽는 단일 진입점
│   ├── common/
│   │   ├── zi_reference/      # 펀드 master·class·속성·codebook
│   │   └── korean_equity/     # 국내주식 가격·재무·주식수·배당·산업
│   ├── kaniel_2023/           # 현재 1순위 key paper 입력
│   └── arnott_2023/           # 현재 2순위 후보 입력
├── metadata/                  # 추출/copy manifest, 매핑, 범위·해시 확인 결과
└── archive/                   # no-go 판정 근거
```

현재 물리 파일은 63개, 3,613,535,275바이트다. 구성은 canonical 39개,
metadata 21개, archive 3개다. `data/kaist_pilot/`에는 이 데이터·계보
파일만 두고, 설명 문서는 이 문서에서 관리한다.

## 3. Canonical 데이터셋

### 3.1 Kaniel et al. (2023) — 현재 1순위

| 파일 | 원천 | grain / key | 행 수 | 기간 |
|---|---|---|---:|---|
| `canonical/kaniel_2023/kaist_kaniel_fund_daily_full_history.parquet` | `DW_ZI_펀드일별분석`, `대유형코드='20'` | `기준일자 × 협회펀드코드` | 19,927,019 | 1996-01-03~2026-07-16 |
| `canonical/kaniel_2023/kaist_kaniel_manager_daily_full_history.parquet` | `DW_ZI_운용사일별분석` | `기준일자 × 운용사코드 × 제로인유형코드` | 12,617,477 | 1999-08-23~2026-07-16 |

두 파일 모두 manifest의 key duplicate 검사가 0건이다. fund-day는 return,
TNA, flow, fund momentum과 자산군 노출의 raw input이고, manager-day는 family
TNA·fund count·family momentum 검증용이다.

주의사항:

- 날짜 외 대부분의 수치가 Parquet에서 `large_string`이다. 단위와 빈 문자열을
  확인한 뒤 명시적으로 변환한다.
- `실현수익률`은 sample에서 기준가 return factor와 flow 공식에 맞지만,
  gross/net·분배금 처리는 vendor 정의 확인이 남아 있다.
- share-class는 `펀드구분=1` 관계만 사용하고 모자펀드 many-to-many 관계를
  같은 방식으로 합치지 않는다.
- 한국 Carhart factor의 국내주식 입력은 §3.4로 복사했지만 월별 factor 구성은
  아직 필요하다. sentiment는 별도 외부 입력이 필요하다.
- 역사적 fee와 turnover가 없으므로 현재 snapshot fee를 과거 전 기간에
  적용하거나 top-10 holdings로 turnover를 근사하지 않는다.

### 3.2 Arnott et al. (2023) — 현재 2순위

| 파일 | 원천 | grain / key | 행 수 | 기간 |
|---|---|---|---:|---|
| `canonical/arnott_2023/kaist_kospi200_constituents_extended.parquet` | `DW_KRX지수구성`, KOSPI200 ISIN | `일자 × 지수ISIN × 종목코드1` | 449,229 | 2017-05-24~2026-07-16 |
| `canonical/arnott_2023/kaist_kospi200_index_levels_extended.parquet` | `DW_KRX지수산출`, KOSPI200 ISIN | `ISIN × VALUE_DATE` | 2,243 | 2017-05-24~2026-07-16 |

두 파일 모두 manifest의 key duplicate 검사가 0건이다. 구성종목 파일에서
membership diff를 만들고 `적용일`로 effective date를 잡는다. `변경여부`는
단독 event flag로 쓰지 않는다.

남은 핵심 입력은 KRX announcement date/time, 정기·수시 변경사유, event-stock
total return·거래량·거래대금·시가총액이다. effective date를 announcement
date로 대체하면 look-ahead bias가 생긴다.

### 3.3 공통 ZI reference

경로: `canonical/common/zi_reference/`

| 파일 | 행 수 | 용도 |
|---|---:|---|
| `dw_zi_펀드기본정보.parquet` | 167,588 | 펀드명, 유형, 설정·해지, 운용사, BM |
| `dw_zi_클래스펀드.parquet` | 50,121 | 대표펀드–share class 및 모자펀드 관계 |
| `dw_zi_펀드별속성코드.parquet` | 966,365 | 펀드–속성 bridge |
| `dw_zi_속성코드.parquet` | 385 | 속성 codebook |
| `dw_zi_유형코드.parquet` | 300 | 대유형·세부유형 codebook |
| `dw_zi_코드정보.parquet` | 708 | 일반 ZI codebook |
| `dw_zi_운용사정보.parquet` | 365 | 운용사 코드–이름 매핑 |

### 3.4 공통 국내주식 입력 — qlibx에서 2026-08-07 복사

경로: `canonical/common/korean_equity/`

| 파일 | 행 수 | 종목 수 | 기간 | 용도 |
|---|---:|---:|---|---|
| `adjusted_prices.parquet` | 8,651,872 | 4,962 | 2015-01-02~2026-07-20 | MKT·SMB·MOM의 수익률, 거래량·거래대금·시가총액 |
| `fng_statement_facts/` (22개 partition) | 39,307,271 | 3,133 | FY 2016~2026 | HML 및 stock characteristic의 연결·별도 재무 원천 row |
| `fng_daily_share_counts.parquet` | 671,005 | 309 | 2015-01-02~2026-07-20 | 기말·자기주식수 검산 |
| `fng_annual_share_counts.parquet` | 3,122 | 309 | 2015-12-31~2025-12-31 | 연평균 주식수 검산 |
| `fng_dividend_items.parquet` | 6,714 | 280 | 2015-12~2025-12 | 배당·dividend-yield characteristic |
| `sector_classification.parquet` | 1,143,059 | 2,960 | 2018-01-02~2026-04-29 | 시점별 산업코드 |
| `industry_mapping.parquet` | 62 | — | snapshot | 산업코드 명칭·상하위 분류 |

재무 원천의 DataGuide item 매핑, IFRS/GAAP 계정코드와 반복 logical-key 감사표는
`metadata/mappings/korean_equity/`에 있다. 복사 manifest는
`metadata/manifests/112_qlibx_korean_equity_copy_20260807.json`, canonical
파일별 SHA-256·Parquet metadata는
`metadata/checks/qlibx_korean_equity/file_inventory.json`에 기록했다.

주의사항:

- `adjusted_prices.parquet`의 raw price·수정계수·수익률·시가총액을 사용한다.
  qlibx의 `daily_market.parquet`는 근거 없는 `available_at = date - 1 day` 규칙이
  있어 복사하지 않았다.
- qlibx의 `factor_returns.parquet`는 Carhart 계약이 아니라 별도 전략 sleeve
  수익률이므로 논문 factor 입력으로 복사하지 않았다.
- 재무 facts에는 여러 dump의 반복 logical key가 있다. 최신값을 무조건 고르지
  말고 `dump_last_modified`, 원천 경로와 반복키 감사표로 PIT 중복해소 규칙을
  먼저 확정한다.
- 실제 공시시각은 포함되지 않는다. 단순 결산일 기준 정렬은 look-ahead다.
  공시일 원천을 연결하거나 근거 있는 reporting lag를 사전에 고정해야 한다.
- 가격은 2015년, full-universe 재무는 2016년부터라 1996년부터 존재하는 펀드
  패널 전체를 덮지 못한다. 현재 교집합 표본으로 시작하되 장기 factor 분석에는
  과거 주식자료 추가 확보가 필요하다.
- `market_cap`은 원천 종가와 원천 주식수 필드의 곱이다. 해당 주식수가
  총발행주식수인지 유동주식수인지 vendor 정의를 검증한 뒤 size breakpoint를
  구성한다.

## 4. 보존과 삭제 정책

- `archive/beber_2021_no_go/`: mandate/style 30-fund gate 결과. 제약 변수
  coverage 부족으로 제외된 후보의 판정 근거라 보존한다.
- 월별 extraction chunk, checkpoint, incremental lake와 2023~2025 구버전
  KOSPI200 표본은 canonical 전체 이력으로 병합·검증된 뒤 2026-07-29에
  삭제했다.
- 삭제한 628개 파일은 3,901,981,094바이트다. 필요한 관측치는 canonical에
  남아 있으며, 추출 SQL·범위·키와 원본 스크립트명은 manifest에 남아 있다.
- canonical을 대체하는 새 추출분을 받을 때는 기존 파일을 덮어쓰지 말고 먼저
  별도 경로에서 행 수, 기간, key duplicate와 SHA-256을 검증한다.

## 5. 재현 및 검증

Parquet metadata와 선택적 SHA-256 인벤토리:

```powershell
uv run python scripts/kaist_pilot/inventory.py
uv run python scripts/kaist_pilot/inventory.py --hashes
```

2026-07-29에는 이동 전후 전체 655개 파일을 해시 비교했다. 파일 수, 총
바이트, SHA-256 multiset이 모두 일치했고, 읽을 수 없는 Parquet는 전후 모두
0개였다. 중복 삭제 후에는 남은 14개 Parquet 전부가 정상적으로 열리고,
canonical 11개 파일의 행 수·기간이 manifest와 일치함을 다시 확인했다.

2026-08-07에는 qlibx 원본 32개 파일, 802,066,493바이트를 복사했다. 원본과
목적지의 파일 크기 및 SHA-256은 32/32 일치했고, 새로 복사한 29개 Parquet는
모두 정상적으로 열렸다. `data/` Git 제외 규칙은 계속 유지한다.
