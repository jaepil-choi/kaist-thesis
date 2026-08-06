# Replication checklist

## 원 논문 산출물

- [ ] Table 1: additions/deletions by subperiod — announcement history 필요
- [ ] Table 2: announcement·grace·effective-date returns — announcement 필요
- [ ] Table 3: additions/deletions valuation — announcement와 변경사유 필요
- [ ] Table 4: trade-on-announcement/after/effective variants — announcement 필요
- [ ] Table 5: alternative top-500 constituent rules — 한국 방법론 사전 확정 필요
- [ ] Table 6: alternative-index returns and factor alpha — Table 5 이후
- [ ] Figure 1: additions vs discretionary deletions — 변경사유 필요
- [ ] Figure 2: cumulative trade-date variants — announcement 필요
- [ ] Figure 3: alternative constituent-selection indices — Table 5 이후

## 현재 데이터로 구현한 한국 extension

- [x] KOSPI200 인접 snapshot 편입·편출 diff
- [x] `NEXT_REBALANCE_DATE`의 사전 가용값으로 정기변경 gate
- [x] 효력일 기준 시장조정 event-window returns
- [x] 편출 minus 편입 reversal spread와 누적 path
- [x] 결측 post-return을 0 또는 상장폐지수익률로 임의 대체하지 않음

## 남은 데이터 gate

- [ ] KRX announcement date/time과 장중·장후 구분
- [ ] 정기·수시 변경사유와 discretionary/nondiscretionary 분류
- [ ] 현금배당·상장폐지를 포함한 total-return 정의 확인
- [ ] KOSPI200 방법론을 반영한 alternative-universe 규칙 사전등록
