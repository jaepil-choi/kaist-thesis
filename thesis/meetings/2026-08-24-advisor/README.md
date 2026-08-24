# 2026-08-24 지도교수 미팅 자료

Guijarro-Ordonez, Pelger, and Zanotti (2025), "Deep Learning Statistical
Arbitrage" (*Management Science*)의 한국시장 재현 현황을 보고하고, 남은
설계 결정을 확인하기 위한 30분 미팅용 발표자료다. Quarto revealjs로 만든다.

## 파일

| 파일 | 설명 |
|---|---|
| `advisor-meeting-guijarro-korea.qmd` | 발표자료 원본 (Quarto revealjs) |
| `advisor-meeting-guijarro-korea.html` | 렌더 결과. self-contained 단일 파일이라 그대로 열면 된다 |
| `custom.scss` | 단색 테마 |
| `render.ps1` | 렌더 스크립트 (아래 "한글 사용자명 우회" 참고) |
| `extract_paper_figures.py` | 원 논문 PDF·한국 산출물에서 비교용 그림을 잘라내는 스크립트 |
| `figures/paper/` | 원 논문 PDF에서 추출한 그림 (미국) |
| `figures/korea/` | 재현 산출물에서 복사·crop한 그림 (한국) |

## 구성 (본문 16장 + 섹션 구분 3장)

목차는 세 갈래다 — 논문 소개, 한국 데이터 재현 결과(일부), 질문들. 논문을 먼저
소개하고 그 다음에 한국 재현으로 넘어간다. 30분 미팅이므로 설명은 문장 대신
표 + 그 아래 bullet point로 적고, 슬라이드 제목은 주장 문장이 아니라 명사구로 쓴다.

- **오늘 말씀드릴 내용** — 위 세 갈래
- **선정 배경** — 세 항목으로만 짧게. ① 개인적 관심(운용사 국내주식 팀, enhanced index
  펀드 전략 리서치 → active 부분의 의도치 않은 팩터 노출) ② 석사 논문 주제 적합성
  (2019-03 첫 초고 → 2025 Management Science 게재, 6년간 review) ③ 재현 용이성
- **1. 논문 소개** (6장)
  - 논문의 핵심 구조 — 목적함수 수식 한 줄 + 잔차·신호·배분 3행 표 + bullet
  - 선행연구에서의 위치 — 고전 stat arb(Gatev et al. 2006, Vidyamurthy 2004),
    팩터 기반 stat arb(Avellaneda & Lee 2010, Yeo & Papanicolaou 2017),
    ML 자산가격결정(Chen et al. 2022, Kelly et al. 2019),
    ML 수익률 예측(**Gu et al. 2020**, Freyberger et al. 2020),
    과거수익률 기반 예측(Krauss et al. 2017, Lim & Zohren 2021).
    인용은 원 논문 Related Literature 절과 참고문헌에서 확인한 것만 쓴다.
  - 무조건부 관점 vs 조건부 관점
  - 금융데이터에서의 딥러닝 (1) 입력과 출력 — 입력 구성과 각 블록의 shape을 명시한다.
    $x\in\mathbb{R}^{30}$ (종목별 30일 누적잔차) → CNN $\mathbb{R}^{30\times 8}$ →
    Transformer $\mathbb{R}^{8}$ → 배분 FFN $\mathbb{R}$ → 횡단면 $\lVert w\rVert_1=1$ 정규화.
    수치는 원 논문 2.4.3절 본문과 각주 8, Figure 3·4 설명에서 직접 확인했다.
  - 금융데이터에서의 딥러닝 (2) 왜 여기서 성립하는가 — 네 장치. OU·Fourier의 표현력
    한계와 attention의 비대칭성도 별도 장 없이 이 장의 2번 항목에서 함께 다룬다.
  - 논문의 결론 — 정책 × 팩터모형 Sharpe 표, 마찰 반영 후 값, SDF와의 직교성 수치
- **2. 한국 데이터 재현 결과 (일부)** (5장) — 재현 조건, 신호별 성과(잔차화 대조·비용
  반영값 포함 한 장), 전 사양 누적수익률, 원 논문과 갈린 네 지점, 유보사항
- **3. 질문들** (3장)

질문 3건은 재현 설계 대조표에서 `질문`으로 표시한 항목과 일대일로 연결된다.

1. 잔차 표본과 정책 표본외 기간을 얼마나 늘려야 하는가
   (enhanced index 확장을 학위논문의 기여로 삼을 수 있는지를 4번 질의로 포함)
2. 수익률 정의와 거래비용 — total return 대신 adjusted return을 써도 되는가(배당기산일
   시점 정렬 문제), 공매도 비용을 별도 모형화하지 않고 매도금액 기준 20 bp + 3 bp로
   처리해도 되는가
3. 팩터·기업특성을 재무 raw data에서 직접 구축할 것인가 JKP(Jensen, Kelly, Pedersen
   2023) 데이터를 쓸 것인가, 그리고 IPCA 사양을 어떻게 정할 것인가

### 이전 판본에서 뺀 것

논문 요약이 길어져 재현 결과가 뒤로 밀리는 문제가 있어 다음을 덜어냈다. 그림 파일은
`figures/` 아래 남겨 두었으니 필요하면 되살릴 수 있다.

- 원 논문 ablation(OU+FFN, 직접 FFN) 전용 장
- 학습된 국소 필터·attention head 전용 장 (핵심인 비대칭성만 딥러닝 (2)에 남김)
- 한국 ① 잔차 · ③ 정책 전용 장 (핵심 수치를 "신호별 성과" 한 장으로 합침)
- 방어 검정 4장 (알파, 단순 반전, 마찰, 강건성). 단순 반전 결과는 "갈린 네 지점"의
  2번 항목으로만 남았다.
- Figure 5 대표 사양 단독 비교 장 (전 사양 비교만 남김)

## 수치와 그림의 출처

한국 수치는 아래 실행 산출물에서 그대로 옮긴 값이며 발표자료가 별도로
계산하지 않는다.

- `guijarro-ordonez-2025-replication/paper-assets/tables/table_01_korean_performance.csv`
- `guijarro-ordonez-2025-replication/paper-assets/tables/table_02_korean_factor_alpha.csv`
- `guijarro-ordonez-2025-replication/paper-assets/tables/table_09_korean_performance.csv`
- `guijarro-ordonez-2025-replication/docs/execution-status.md`
- `guijarro-ordonez-2025-replication/guijarro-korea-replication.md`

발표자료는 저장소 경로를 슬라이드에 노출하지 않는다. `extract_paper_figures.py`가 미국
그림을 원 논문 PDF에서 잘라내고 한국 그림을 재현 산출물에서 `figures/` 아래로 복사하므로,
슬라이드 소스의 이미지 경로는 모두 이 디렉터리 기준 상대경로다. 미국 수치는 원 논문
Table 1, Table 2, Table 9에서 인용했다.

현재 슬라이드에서 쓰는 그림은 하나뿐이다.

| 슬라이드 | 미국 (원 논문) | 한국 (재현 산출물 원본) |
|---|---|---|
| 전 사양 비교 | Figure 5 전체 (3×3) | `fig_05_korean_cumulative_returns.png` |

나머지 네 파일(`fig_05_us_cnn_pca5.png`, `fig_05_korean_cnn_panel.png`,
`fig_06_us_turnover.png` · `fig_06_korean_turnover.png`, `fig_11_us_naive_reversal.png` ·
`fig_11_naive_reversal.png`)은 이번 판본에서 뺀 슬라이드의 그림이다. 삭제하지 않고
남겨 두었으므로 해당 장을 되살리면 그대로 쓸 수 있다.

### 그림 대응 검증

- 원 논문 Figure 5는 행 = 정책, 열 = FF5·PCA5·IPCA5다. 한국 그림은 열 = 정책, 색 = 잔차
  모형이므로 구조가 전치되어 있다. y축 단위도 다르다 (미국 = 15년 누적배수,
  한국 = 2.4년 누적수익률). 두 차이 모두 슬라이드에 명시했다.
- **원 논문 Figure 6과 Figure 11은 IPCA 5팩터 잔차 기준이다.** 한국 재현은 IPCA가 아직 없어
  PCA5(Figure 11) 및 PCA·FF 계열(Figure 6)로 대응시켰다. 해당 슬라이드를 되살릴 때
  이 단서를 다시 적어야 한다.
- 한국 Figure 11의 전략 정의는 원 논문과 같다 (과거 L일 누적잔차 하위 20% 매수, 상위 20%
  매도, lag 1~30). 재현 코드 `robustness.naive_reversal_returns`에서 확인했다.
- 한국 fig_05 · fig_06 · fig_11은 재현 manifest에서 모두 `generated_korean_partial`이다.
  즉 한국 데이터 실행 결과이며 논문 사양에서 합성한 그림이 아니다.

## 재생성

그림을 다시 뽑을 때 (원 논문 PDF가 `docs/pdfs/`에 있어야 한다):

```bash
uv run --with pymupdf python thesis/meetings/2026-08-24-advisor/extract_paper_figures.py
```

발표자료 렌더:

```bash
pwsh -File thesis/meetings/2026-08-24-advisor/render.ps1
```

### 한글 사용자명 우회

Windows 사용자명이 한글이면 이 저장소에서 `quarto render`가 theme(SCSS) 컴파일
단계에서 실패한다. Quarto는 dart-sass 호출을 임시 `.bat` 파일에 UTF-8로 적어
`cmd.exe`로 실행하는데, `cmd.exe`는 그 파일을 시스템 ANSI 코드페이지(cp949)로
읽으므로 경로 안의 한글이 깨져 "지정된 경로를 찾을 수 없습니다"로 끝난다.
`quarto check`조차 같은 이유로 실패한다.

`render.ps1`은 Quarto 설치 디렉터리를 `C:\tmp\quarto-ascii` junction으로 노출하고
`TMP`/`TEMP`와 `LOCALAPPDATA`도 ASCII 경로로 돌린 뒤 junction 안의 `quarto.exe`로
렌더한다. Quarto 설치본은 건드리지 않으며, 사용자명에 non-ASCII 문자가 없으면
우회 없이 그대로 렌더한다.

근본 원인, 세 경로(설치·임시·캐시)가 모두 ASCII여야 하는 이유, junction 없이
환경변수만 쓰는 대안은 `corporate-windows` skill의 `references/quarto.md`에 정리해 두었다.

## 유의사항

- **원 논문 Table 1의 Sharpe 4.16은 IPCA5 잔차 기준이며 PCA5가 아니다.** CNN+Transformer
  기준 `K` = 5 값은 FF5 3.21 · PCA5 3.36 · IPCA5 4.16이고, Fourier+FFN의 PCA5는 1.98,
  OU+Threshold의 PCA5는 0.73이다. 한국 PCA5 결과와 대조할 때는 반드시 미국 PCA 열을
  써야 한다. 초기 판본은 한국 PCA5(4.15)를 미국 IPCA5(4.16)와 대조해 "사실상 동일"이라고
  적었으나 이는 잘못된 비교였다. 값은 원 논문 PDF의 Table 1에서 직접 확인했고,
  본문 4805행의 "trading on the IPCA-5 residuals equals SR = 4.16" 문장과도 일치한다.
- 발표자료의 성과 수치는 거래비용 반영 여부를 슬라이드마다 명시한다.
  비용 미반영 Sharpe 4.15는 마찰 없는 상한이고, 비용 반영값은 1.37이다.
- PCA `K > 0` 결과는 저자 공개 코드의 시점 처리를 그대로 따른 값이다.
  공개 코드는 잔차 구성행렬 추정 창에 당일 수익률을 포함하므로 논문 본문의
  point-in-time 계약과 어긋난다. 상세 내용과 재실행 요건은
  `guijarro-ordonez-2025-replication/docs/issues/pca-current-day-look-ahead.md`에
  있다. "유보사항" 슬라이드에 이 쟁점을 구두로 밝힐 항목으로 정리해 두었다.
- "논문의 결론" 슬라이드와 "신호별 성과" 표의 미국 거래비용 반영값(0.94 ~ 1.24)만
  IPCA5 기준(Table 9)이고 같은 표의 나머지 미국 값은 PCA5 기준(Table 1)이다.
  두 기준이 섞여 있으므로 슬라이드 note에 적어 두었다.
- 표지 뒤 "선정 배경"의 "2019년 3월 첫 초고 → 2025년 Management Science 게재"는
  원 논문 PDF 첫 장의 "This draft: January 9, 2024 / First draft: March 15, 2019"에서
  확인한 값이다.
- 알파 검정 기준은 한국 FF5 + MOM 6팩터이며 원 논문의 FF8이 아니다. 이번 판본에서
  알파 슬라이드는 뺐으므로, 되살릴 때 이 단서를 다시 적어야 한다.
- `table_01_korean_performance.csv`에서 PCA5의 `fourier_ffn` · `ou_threshold`
  행은 `factor_model`이 `PCA5`가 아니라 `PCA`로 적혀 있다. 값 자체는 PCA5
  결과이므로 발표자료는 이를 PCA5로 표기했으나, 라벨은 재현 코드에서 정리할
  필요가 있다.
