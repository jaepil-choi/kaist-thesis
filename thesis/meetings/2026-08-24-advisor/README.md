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

## 구성 (37장)

논문의 논증 순서를 따라가면서, 각 단계에서 한국 재현 결과가 그 단계의 주장에
답하도록 배치했다. 논문 요약을 앞에 몰아두고 결과를 뒤에 붙이는 구성이 아니다.

- **선정 배경** — enhanced index 펀드의 active 부분에 필요한 factor neutral long-short alpha
- **1. 논문의 핵심 명제** — 잔차를 예측하지 않고 거래정책을 학습한다 / 잔차는 비어 있는
  집합이 아니다 (무조건부 평균은 0에 가깝지만 조건부로 거래하면 최대 50배) /
  예측 목적함수와 거래 목적함수의 차이
- **2. 방법론적 방어** — 짧은 시계열·낮은 신호대잡음·고차원 패널에서 딥러닝이 성립하는
  네 가지 장치(횡단면 pooling, 구조적 귀납편향, 절제된 사양, 제약의 정칙화 효과)와
  원 논문의 두 ablation
- **3. 무엇을 새로 찾았나** — OU·Fourier의 표현력 한계, 학습된 국소 필터 8개와
  attention head 4개, 시간 가중의 비대칭성, SDF와의 직교성
- **4. 한국 재현** — 부품별(① 잔차 ② 신호 ③ 정책)로 원 논문 주장의 성립 여부
- **5. 방어 검정** — 알파, 단순 반전, 마찰, 강건성
- **6. 갈린 지점과 유보사항**
- **7. 논의사항 3건**

논의사항 3건은 재현 설계 대조표에서 `논의`로 표시한 항목과 일대일로 연결된다.

1. 잔차 표본과 정책 표본외 기간을 얼마나 늘려야 하는가
   (enhanced index 확장을 학위논문의 기여로 삼을 수 있는지를 4번 질의로 포함)
2. 현금배당을 제외한 price return을 사용해도 되는가
3. IPCA에 사용할 팩터와 기업특성을 무엇으로 정할 것인가

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

| 슬라이드 | 미국 (원 논문) | 한국 (재현 산출물 원본) |
|---|---|---|
| Figure 5 대표 사양 | Figure 5 panel (b) CNN+Trans, PCA 5 | `fig_05_korean_cumulative_returns.png`의 CNN+Transformer 패널 crop |
| Figure 5 전 사양 | Figure 5 전체 (3×3) | `fig_05_korean_cumulative_returns.png` |
| Figure 6 turnover | Figure 6 (2 패널) | `fig_06_korean_turnover.png` |
| Figure 11 단순 반전 | Figure 11 (3 패널) | `fig_11_naive_reversal.png` |

### 그림 대응 검증

- 원 논문 Figure 5는 행 = 정책, 열 = FF5·PCA5·IPCA5다. 한국 그림은 열 = 정책, 색 = 잔차
  모형이므로 구조가 전치되어 있다. 대표 사양 슬라이드는 양쪽 모두 PCA5·CNN+Transformer로
  맞춰 잘라 썼다. 다만 y축 단위가 다르다 (미국 = 누적배수, 한국 = 누적수익률). 슬라이드에 명시.
- **원 논문 Figure 6과 Figure 11은 IPCA 5팩터 잔차 기준이다.** 한국 재현은 IPCA가 아직 없어
  PCA5(Figure 11) 및 PCA·FF 계열(Figure 6)로 대응시켰다. 이 차이는 해당 슬라이드와 마지막
  유의사항 슬라이드에 모두 적었다. IPCA가 준비되면 다시 그려야 한다.
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
  있다. 마지막 슬라이드에 이 쟁점을 구두로 밝힐 항목으로 정리해 두었다.
- 알파 검정 기준은 한국 FF5 + MOM 6팩터이며 원 논문의 FF8이 아니다.
- `table_01_korean_performance.csv`에서 PCA5의 `fourier_ffn` · `ou_threshold`
  행은 `factor_model`이 `PCA5`가 아니라 `PCA`로 적혀 있다. 값 자체는 PCA5
  결과이므로 발표자료는 이를 PCA5로 표기했으나, 라벨은 재현 코드에서 정리할
  필요가 있다.
