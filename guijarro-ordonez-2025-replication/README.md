# Guijarro-Ordonez et al. (2025) 한국시장 Replication

이 디렉터리는 Guijarro-Ordonez, Pelger, and Zanotti (2025),
“Deep Learning Statistical Arbitrage”, *Management Science*의 전체 본문·부록
산출물을 한국 주식시장에 재현하기 위한 실행 프로젝트다.

## 원칙과 현재 범위

- exact replication과 한국시장 extension을 분리한다.
- 원 논문의 Figure 1–19, Table 1–9, Appendix Figure A.1–A.7,
  Table A.I–A.X 총 45개를 `config/output-registry.yml`에 등록한다.
- 데이터가 없으면 결과를 생략하거나 임의 proxy로 채우지 않고 `blocked` 상태와
  필요한 입력을 기록한다.
- 현재 구현은 논문 식 (1)의 residual composition과 식 (3)의
  residual-to-stock weight 변환, registry 검증, 4종목 합성 예시까지다.
- 현재 한국 자료로 가능한 실증 범위는 2015년 이후 PCA residual pilot이다.
  이는 원 논문의 1978–2016 입력 및 1998–2016 OOS 설계를 exact replicate한
  결과가 아니다.

## 실행

모든 명령은 저장소 루트에서 실행한다.

```powershell
uv run python guijarro-ordonez-2025-replication/run.py status
uv run python guijarro-ordonez-2025-replication/run.py demo-residuals
uv run python guijarro-ordonez-2025-replication/run.py build-kimchi-factors --allow-non-pit-statements
uv run python guijarro-ordonez-2025-replication/run.py build-factors-proxy --allow-non-pit-statements
uv run python guijarro-ordonez-2025-replication/run.py build-ipca-characteristics --allow-non-pit-statements --impute-missing-characteristics
uv run python guijarro-ordonez-2025-replication/run.py estimate-ipca --ipca-factors 5 --ipca-window-months 60 --allow-short-history-ipca
uv run pytest guijarro-ordonez-2025-replication/tests
uv run ruff check guijarro-ordonez-2025-replication
```

`demo-residuals`는 외부 데이터 없이 4종목·1factor 예시를 실행한다. 네 개의
residual portfolio를 만든 뒤 residual allocation을 겹치는 실제 종목 주문으로
상계하고 gross exposure를 1로 정규화한다.

`build-factors-proxy`는 로컬 일별 주가와 연결재무제표로 RM·SMB·HML·RMW·CMA·MOM·
LTR·STR을 직접 만들고, 공통 6개 style/market 팩터는
`data/kimchi-factor/`와 공통 일자에서 비교한다. 재무값은 사용자의
지시에 따라 회계연도 말에서 3개월 뒤부터 사용하지만, 로컬 dump에는 실제
공시·정정 시각 이력이 없으므로 `--allow-non-pit-statements`를 명시해야 한다.
이 결과는 **3개월-lag non-PIT proxy sensitivity**이지
`docs/kimchi-factor-methodology.md`를 따른 exact Kimchi Factor 산출이 아니다.

proxy의 구성 규칙은 전체 가용 표본의 6월 말 size median 및 characteristic
30/70 breakpoint, 다음 7월부터
1년 보유, MOM/LTR/STR 월별 재구성, 전 거래일 시가총액 value-weight다. LTR은
보유월 기준 60~13개월 수익률, STR은 직전 1개월 수익률의 loser-minus-winner다.
RMRF의 RF만
Kimchi 파일에서 가져오며, 독립적인 시장 포트폴리오 검증에는 RM을 사용한다.
결과와 2×3 bucket 진단은 `outputs/factors/`에 생성된다.
실측 비교 결과와 해석은 `docs/factor-validation.md`에 기록한다.

`build-kimchi-factors`는 2018년 이후 월말 FGSC 역사 스냅샷을 사용해 문서화된
KOSPI breakpoint와 유니버스 규칙을 적용한다. 일간·월간을 독립 계산하고,
VW/EW, 2×3 및 5분위 수익률과 종목 멤버십을 `outputs/kimchi-exact/`에 만든다.
현금배당이 없는 가격수익률과 최신 revision 재무제표를 사용하므로 결과의 정확한
분류는 **price-return variant + fixed-3-month-lag non-PIT accounting
sensitivity**다. 이는 과거 broad-universe proxy보다 방법론에 훨씬 가깝지만,
total-return/PIT 원천을 보유한 완전한 replication이라는 뜻은 아니다.

정확한 산출 규범은 저장소 루트의 `docs/kimchi-factor-methodology.md`다. 현재
builder는 역사 월말 종목 마스터와 KOSPI·RF 원계열을 확보해 universe, KOSPI
breakpoint, 금융업 처리, VW/EW 및 일간/월간 독립 산출을 통과한다. 남은 원천
제약은 위 분류와 audit에 명시하며, 과거 proxy 결과를 exact 입력으로 사용하지
않는다.

## 데이터 상태

현재 재사용 가능한 자료:

- `adjusted_prices.parquet`: 2015-01-02~2026-07-20, 4,962종목의 가격·수익률·
  거래량·거래대금·시가총액
- `fng_statement_facts/`: FY 2016~2026 재무 원천
- 일·연간 주식수, 배당 항목, 시점별 산업분류
- 월별 ECOS 91일물 무위험수익률 proxy

`adjusted_prices.return`은 현금배당을 포함하지 않는다고 확인됐고, 월말
KOSPI/KOSDAQ·FGSC·SPAC 스냅샷도 2018-01~2026-06 구간을 확보했다. 다만
시가총액 주식수 필드의 경제적 명칭, 상장폐지수익률, 재무 revision의 PIT vintage는
완전히 닫히지 않았다. IPCA용 240개월 이력과 공시일 기준 46개 characteristic도
없다. 상세한 확보·누락·판정은 `docs/data-requirements.md`를 따른다.

## 공식 코드와 의존성 경계

저자 공식 코드는 저장소 루트의 `Deep_Learning_Statistical_Arbitrage_Code/`에
참고용으로 보존되어 있다. 공식 코드는 Python 3.10/Linux, PyTorch와 GPU를
전제로 하고, full replication은 저자 README 기준 RAM 384GB, 저장공간 2TB,
GPU VRAM 36GB가 필요하다. 현재 루트 환경에 PyTorch를 즉시 추가하지 않는다.
먼저 데이터 gate와 PCA CPU pilot을 통과한 뒤 별도 GPU 실행환경을 고정한다.

46개 characteristic builder와 IPCA alternating-least-squares/residual core는
구현되어 있다. 현재 자료로 실행할 때에는 고정 3개월 lag, 일부 한국 proxy 및
240개월보다 짧은 window를 각각 명시적인 warning/audit로 남긴다. 자세한 계약은
`docs/ipca-methodology.md`를 따른다.

공식 코드의 공개 라이선스는 상업적 사용을 금지한다. 이 프로젝트에서 코드를
복사·수정할 때는 provenance와 라이선스 경계를 별도로 기록한다.
