# Arnott et al. (2023) 한국시장 Replication

Arnott, Brightman, Kalesnik, and Wu (2023), “Earning Alpha by Avoiding the
Index Rebalancing Crowd”의 한국시장 재현 프로젝트다.

원 논문의 6개 Table과 3개 Figure는 `config/output-registry.yml`에 모두
등록한다. 현재 회사 데이터에는 KOSPI200 일별 구성·비중과 효력일은 있지만
announcement timestamp와 변경사유가 없다. 따라서 발표일을 효력일로 바꾸어
exact replication처럼 보고하지 않는다.

## 현재 구현

- 인접 membership snapshot의 집합 차이로 편입·편출 종목 복원
- 과거에 알려진 `NEXT_REBALANCE_DATE`로 정기변경과 수시변경 구분
- 효력일 전후 stock-over-KOSPI200 복리수익률 event study
- 편출 minus 편입 reversal spread, Welch t-statistic, 누적 event path
- 원 논문 output registry와 한국 extension output의 분리
- 입력 SHA-256과 실행 parameter manifest

## 실행

```powershell
uv run python arnott-2023-replication/run.py status
uv run python arnott-2023-replication/run.py audit
uv run python arnott-2023-replication/run.py build-events
uv run python arnott-2023-replication/run.py core
uv run pytest arnott-2023-replication/tests
uv run ruff check arnott-2023-replication
```

`core` 산출물은 논문의 announcement-window Table 2/Figure 1을 대체하지 않는
**효력일 기준 한국 extension**이다. announcement date/time과 변경사유를
확보한 뒤 동일 event engine에 연결해 exact replication을 실행한다.
