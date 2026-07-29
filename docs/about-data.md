# 논문 데이터 안내 및 카탈로그

작성일: 2026-07-29  
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
│   ├── common/zi_reference/   # 펀드 master·class·속성·codebook
│   ├── kaniel_2023/           # 현재 1순위 key paper 입력
│   └── arnott_2023/           # 현재 2순위 후보 입력
├── metadata/                  # 추출 manifest와 범위 확인 결과
└── archive/                   # no-go 판정 근거
```

중복 정리 후 vendor 산출물은 27개, 2,811,417,336바이트다. 구성은 canonical
11개, metadata 13개, archive 3개다. `data/kaist_pilot/`에는 이 데이터·계보
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
- 한국 Carhart factor와 sentiment는 아직 별도 구축이 필요하다.
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
