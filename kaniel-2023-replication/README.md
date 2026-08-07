# Kaniel et al. (2023) 한국시장 Replication

이 디렉터리는 Kaniel, Lin, Pelger, and Van Nieuwerburgh (2023),
“Machine-Learning the Skill of Mutual Fund Managers”의 본문과 부록 산출물을
한국 펀드 데이터로 재현하기 위한 실행 프로젝트다.

원 논문의 일부 결과만 선택적으로 구현하지 않는다. 본문 Figure 1–14와
Table 1–9, 부록 Figure A.1–A.26, Table A.1–A.14, Table B.1을 모두
`config/output-registry.yml`에 등록한다. 원 데이터와 동일하게 만들 수 없는
항목은 결과를 조용히 생략하지 않고 `blocked` 상태와 원인, 필요한 입력,
한국 적용에서의 방법론 변경을 남긴다.

## 현재 구현 범위

- 원 논문 64개 Figure/Table의 machine-readable registry
- 입력 Parquet schema 및 행 수 감사
- 국내 active equity class-month 패널의 streaming 구축
- Carhart rolling abnormal return과 fund momentum 산식
- 국내주식 raw input의 월별 MKT·SMB·HML·MOM factor builder와 PIT hard gate
- random/chronological 3-fold cross-OOS 64-unit ReLU MLP ensemble
- 논문 식 (4)–(6)의 prediction-weighted top/bottom decile portfolio
- Table 1, Table 2, Figure 3, Table B.1의 정적 산출물 생성
- 한국 factor와 sentiment 입력 계약 및 검증
- ECOS 통안증권 91일 RF, ESI 경기상태, 고정-calibration PCA sentiment proxy
- proxy sentiment와 non-PIT 3개월-lag Carhart를 사용한 parsimonious 전구간 실행
- 합성 자료 기반 단위 테스트
- share-class TNA 일치, 수익률 차이, 통합 판정 진단 Figure

대표펀드 단위 share-class 통합은 아직 기본 실행에서 수행하지 않는다.
`DW_ZI_클래스펀드`가 현재 snapshot이고 대표코드 행이 class 합계인지 독립
class인지 검증되지 않았기 때문이다. 검증 전 합산은 TNA와 수익률을 이중집계할
수 있다.

전체 검증 결과 대표 TNA는 클래스 합계와 대체로 일치하지만 대표수익률은
클래스 전월 TNA 가중수익률보다 중앙값 월 10.78bp 높았다. 따라서 TNA와
수익률의 consolidation 판정을 분리하며, 상세 규칙은
`docs/share-class-validation.md`를 따른다.

## 실행

모든 명령은 저장소 루트에서 `uv run`으로 실행한다.

```powershell
uv run python kaniel-2023-replication/run.py status
uv run python kaniel-2023-replication/run.py audit
uv run python kaniel-2023-replication/run.py static
uv run python kaniel-2023-replication/run.py build-panel --start 2023-01-01 --end 2023-12-31
uv run python kaniel-2023-replication/run.py validate-share-classes
uv run python kaniel-2023-replication/run.py share-class-figures
uv run python scripts/kaist_pilot/build_kaniel_ecos_inputs.py
uv run python kaniel-2023-replication/run.py build-stock-factors --start 2015-01-01 --end 2026-07-20 --reporting-lag-months 3 --allow-non-pit-book-equity
uv run python kaniel-2023-replication/run.py run-parsimonious
uv run pytest kaniel-2023-replication/tests
uv run ruff check kaniel-2023-replication
```

`build-panel`은 원천의 `실현수익률`과 `BM수익률`을 일별 return factor로
해석해 월별로 복리 연결한다. 실행 전 audit와 vendor 정의 확인이 필요하며,
첫 설정행의 `순자산=0, 실현수익률=1` placeholder는 제외한다.
일별 return factor가 설정 범위(기본 0.5~1.5)를 벗어나면 임의 winsorize하지
않고 해당 fund-month의 수익률과 flow를 결측 처리하며 별도 quarantine
Parquet에 원 행을 남긴다.

`validate-share-classes`는 각 대표펀드의 월 수익률을 하위 클래스의 전월 TNA
가중수익률과 비교하고, 대표 TNA와 클래스 TNA 합계 및 대표코드 기간 coverage를
함께 검사한다. 검증을 통과한 그룹만 대표코드 우선 규칙의 대상이 된다.

`share-class-figures`는 검증 결과에서 TNA 허용오차별 일치율, 대표수익률과
클래스 가중수익률의 월별 차이, 최종 consolidation 판정 분포를 생성한다.
이들은 원 논문의 번호가 붙은 Figure가 아니라 한국 데이터 통합 규칙을
확정하기 위한 품질진단 산출물이다.

## 외부 입력

`inputs/README.md`의 계약에 맞춰 다음 월별 파일을 사용한다.

- **확보**: ECOS 통안증권 91일물 기반 월 무위험수익률
- **확보(robustness proxy)**: ECOS ESI 순환변동치 기반 경기상태
- **확보(sensitivity)**: 3개월 reporting lag를 적용한 non-PIT Carhart 4요인
- **확보(proxy)**: 5개 ECOS 시장활동 구성요소의 고정-calibration PCA sentiment
- **미확보(exact)**: 공시일 기반 PIT HML과 Baker–Wurgler 정의에 가까운 sentiment

ECOS-only sentiment는 2005~2014의 평균·표준편차·첫 PC loading을 고정하고
관측값에 1개월 availability lag를 적용한다. 상세 항목 코드·loading·추가
필요자료는 `docs/kaniel-ecos-inputs.md`에 있다.

역사적 fee, turnover, full holdings가 확보되기 전에는 해당 변수가 필수인
Figure/Table을 가짜 proxy로 채우지 않는다. 다만 parsimonious 모형과 macro
단계는 명시적인 ECOS-only sentiment proxy로 계속 구현한다.

`build-stock-factors`의 기본 동작도 hard fail이다. 현재 재무 facts에는 당시
실제 announcement timestamp가 없고 2026년에 수집한 여러 dump revision이
섞여 있기 때문이다. `--allow-non-pit-book-equity`와 명시적 reporting lag를
함께 준 실행만 sensitivity output으로 허용하며 exact factor로 승격하지 않는다.

`run-parsimonious`는 factor·RF·sentiment와 class-month panel이 모두 있을 때만
실행된다. 2026-08-07 sensitivity 실행은 136,641개 OOS prediction과 45개월
portfolio를 생성했다. 출력 파일명과 manifest에 `proxy`를 명시한다. 현재
sklearn backend는 논문의 64-unit ReLU, Adam, L2, 8-model ensemble을 구현하지만
dropout 0.95는 구현하지 않으므로 exact neural-network 결과로 간주하지 않는다.

## 데이터 계보

분석 코드는 `data/kaist_pilot/canonical/`만 읽는다. 원천 Parquet는 불변으로
취급하고, 생성 결과와 실행 manifest는 `outputs/`에 둔다. 설정과 registry,
코드만으로 산출물을 다시 만들 수 있어야 한다.
