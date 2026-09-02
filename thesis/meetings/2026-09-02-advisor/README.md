# 2026-09-02 지도교수 미팅 자료

Guijarro-Ordonez, Pelger, and Zanotti (2025), *Deep Learning Statistical Arbitrage*
(Management Science)의 한국시장 재현 현황 보고용 발표자료다. 2026-08-24 자료는
미팅이 성사되지 않아 사용하지 않았고, 이번 판은 구성을 3부로 단순화해 다시 썼다.

## 파일

| 파일 | 설명 |
|---|---|
| `advisor-meeting.qmd` | 발표자료 원본 (Quarto revealjs) |
| `advisor-meeting.html` | 렌더 결과. self-contained 단일 파일 |
| `custom.scss` | 단색 테마 (2026-08-24 자료에서 그대로 가져옴) |
| `render.ps1` | 렌더 스크립트. 한글 사용자명 우회 포함 |
| `figures/original_paper_screenshots/` | 원 논문에서 직접 캡처한 그림·표 |
| `figures/` | 한국 재현 산출물 그림 |

## 구성

2026-08-24 판은 논문의 논증 순서를 그대로 따라 37장이었다. 이번 판은 미팅 시간에
맞춰 3부로 줄이고, 파트 2를 전부 미국-한국 대조 형태로 다시 짰다.

- **1. 논문 소개** — 선정 배경, 3단계 분해, 각 단계에서 이 논문이 기존과 다른 점.
  그림과 표는 원 논문 캡처를 그대로 쓴다 (Figure 2·3·4, Table 1).
- **2. 구현 현황** — 모든 결과 슬라이드가 미국 수치와 한국 수치를 같은 축으로
  나란히 놓는다. 표본·실행계약 / 정책 비교 / 누적수익 / K 스윕 / 팩터모형 종류별 /
  알파 / 거래비용 / 강건성 / 종합 대조표.
- **3. 쟁점 및 질문** — PCA look-ahead, IPCA blocker, 표본기간, 미확보 데이터,
  논문을 읽으며 생긴 의문 2건, 논의사항 5건.

## 그림

원 논문 캡처는 `figures/original_paper_screenshots/`에 있다.

| 파일 | 쓰이는 곳 |
|---|---|
| `figure 2 examples of local filters.png` | 파트 1, 학습된 국소 필터 |
| `figure 3 convolutional network architecture.png` | 파트 1, CNN 구조 |
| `figure 4 transformer network architecture.png` | 파트 1, Transformer 구조 |
| `table 1 oos annualized performance ...png` | 파트 1, 미국 결과 |
| `figure 5 cumulative oos returns ...png` | 파트 2, 누적수익 미국 측 |
| `table 2 significance of arbitrage alphas ...png` | 파트 2, 알파 미국 측 |

한국 산출물 그림은 `figures/` 바로 아래에 있다.

| 파일 | 출처 |
|---|---|
| `fig_05_korean_cumulative_returns.png` | `guijarro-ordonez-2025-replication/paper-assets/figures/` |
| `fig_06_korean_turnover.png` | 같음 |

## 수치 출처

발표자료는 숫자를 따로 계산하지 않는다. 아래에서 그대로 옮겼다.

- 미국: 원 논문 Table 1, Table 2
- 한국 성과·회전율: `guijarro-ordonez-2025-replication/paper-assets/tables/table_01_korean_performance.csv`
- 한국 알파: 같은 디렉터리의 `table_02_korean_factor_alpha.csv`
- 실행 이력·강건성: `guijarro-ordonez-2025-replication/docs/execution-status.md`
- 완료·미완료 항목: `guijarro-ordonez-2025-replication/docs/replication-checklist.md`
- 쟁점 1 상세: `guijarro-ordonez-2025-replication/docs/issues/pca-current-day-look-ahead.md`
- 데이터 blocker: `guijarro-ordonez-2025-replication/docs/data-requirements.md`

## 유의사항

- **미국 PCA 열과 대조해야 한다.** 원 논문 Table 1의 CNN+Transformer `K=5`는
  FF5 3.21 · PCA5 3.36 · IPCA5 4.16이다. 한국 PCA5(4.15)를 미국 IPCA5(4.16)와
  비교하면 안 된다. 이번 자료의 모든 대조표는 PCA 열(3.36) 기준으로 맞췄다.
- 성과 수치는 슬라이드마다 거래비용 반영 여부를 명시했다. 비용 미반영 4.15는 마찰 없는
  상한이고 비용 반영값은 1.37이다. 5bp / 1bp는 가정값이므로 원 논문 Table 9와의
  직접 대조는 비용 가정을 맞춘 뒤에 해야 한다.
- PCA `K > 0` 결과는 저자 공개 코드의 시점 처리를 따른 값이라 논문 본문의 point-in-time
  계약과 어긋난다. 쟁점 1 슬라이드에서 이를 명시적으로 다룬다. 고치면 4.15를 포함해
  PCA 계열 전체를 재실행해야 한다.
- 알파 검정 기준은 한국 FF5 + MOM 6팩터이며 원 논문의 FF8이 아니다.
- 한국에서만 갈린 결과가 하나 있다. FF5 잔차가 PCA5보다 뚜렷하게 약하다 (2.27 vs 4.15).
  미국은 세 팩터모형이 3.2~4.2로 비슷했다. 팩터 구축 품질 문제인지 시장 특성인지 미확인.
- `table_01_korean_performance.csv`에서 PCA5의 `fourier_ffn` · `ou_threshold` 행은
  `factor_model`이 `PCA5`가 아니라 `PCA`로 적혀 있다. 값 자체는 PCA5 결과다.

## 렌더

```bash
pwsh -File thesis/meetings/2026-09-02-advisor/render.ps1
```

Windows 사용자명이 한글이면 Quarto의 SCSS 컴파일이 실패한다. `render.ps1`이 Quarto
설치 디렉터리를 `C:\tmp\quarto-ascii` junction으로 노출하고 `TMP`/`TEMP`/`LOCALAPPDATA`를
ASCII 경로로 돌린 뒤 렌더한다. 근본 원인은 `corporate-windows` skill의
`references/quarto.md`에 정리되어 있다.

원 논문 캡처 파일명에 공백이 있어 qmd의 이미지 경로는 `%20`으로 인코딩되어 있다.
파일명을 바꾸면 qmd도 같이 고쳐야 한다.
