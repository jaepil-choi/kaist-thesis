# 2026-08-24 지도교수 미팅 자료

Guijarro-Ordonez, Pelger, and Zanotti (2025), "Deep Learning Statistical
Arbitrage" (*Management Science*)의 한국시장 재현 현황을 보고하고, 남은
설계 결정을 확인하기 위한 30분 미팅용 발표자료다.

## 파일

| 파일 | 설명 |
|---|---|
| `advisor-meeting-guijarro-korea.pptx` | 발표자료 11장 |
| `build_deck.js` | 위 pptx를 생성하는 스크립트 |

## 구성

- 파트 1 (슬라이드 2–3): 원 논문 요약과 미국 결과
- 파트 2 (슬라이드 4–8): 재현 설계 대조, Table 1·2 및 Figure 5 재현, 거래비용·강건성
- 파트 3 (슬라이드 9–11): 논의사항 3건

논의사항 3건은 슬라이드 4의 대조표에서 `논의`로 표시한 항목과 일대일로
연결된다.

1. 잔차 표본과 정책 표본외 기간을 얼마나 늘려야 하는가
2. 현금배당을 제외한 price return을 사용해도 되는가
3. IPCA에 사용할 팩터와 기업특성을 무엇으로 정할 것인가

## 수치의 출처

발표자료의 모든 한국 수치는 아래 실행 산출물에서 그대로 옮긴 값이며 이
스크립트가 별도로 계산하지 않는다.

- `guijarro-ordonez-2025-replication/docs/execution-status.md`
- `guijarro-ordonez-2025-replication/guijarro-korea-replication.md`

슬라이드 7의 그림은 재현 실행이 생성한 산출물을 그대로 삽입한다.

- `guijarro-ordonez-2025-replication/paper-assets/figures/fig_05_korean_cumulative_returns.png`

미국 수치는 원 논문 Table 1, Table 2, Table 9에서 인용했다.

## 재생성

`pptxgenjs`가 필요하다. 저장소 루트 경로는 스크립트 위치에서 유도하므로
별도 설정 없이 실행할 수 있고, 필요하면 `THESIS_REPO`와 `DECK_OUT`
환경변수로 덮어쓴다.

```bash
npm install pptxgenjs
node thesis/meetings/2026-08-24-advisor/build_deck.js
```

## 유의사항

- 발표자료의 성과 수치는 거래비용 반영 여부를 슬라이드마다 명시한다.
  비용 미반영 Sharpe 4.15는 마찰 없는 상한이고, 비용 반영값은 1.37이다.
- PCA `K > 0` 결과는 저자 공개 코드의 시점 처리를 그대로 따른 값이다.
  공개 코드는 잔차 구성행렬 추정 창에 당일 수익률을 포함하므로 논문
  본문의 point-in-time 계약과 어긋난다. 상세 내용과 재실행 요건은
  `guijarro-ordonez-2025-replication/docs/issues/pca-current-day-look-ahead.md`에
  있다. 이 발표자료에는 해당 쟁점을 넣지 않았으므로, 슬라이드 5·6·8의
  수치를 제시할 때 공개 코드 기준이며 PIT 재실행이 필요하다는 점을
  구두로 함께 밝힌다.
- 알파 검정 기준은 한국 FF5 + MOM 6팩터이며 원 논문의 FF8이 아니다.
