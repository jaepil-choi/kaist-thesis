# Implementation status

기준일: 2026-07-29

## 구현 완료

- 본문·부록 Figure/Table 64개 output registry
- source schema audit와 외부입력 gate
- active type의 class-level daily-to-monthly streaming panel
- Table 1, Table 2, Figure 3, Table B.1 generator
- prior 36개월 Carhart beta와 Eq. (2) abnormal-return 산식
- `F_ST_Rev`, `F_r2_1`, `F_r12_2` 시점 정렬
- 대표수익률과 전월 TNA 가중 클래스 수익률 비교 및 그룹별 consolidation gate
- share-class TNA 일치율, 수익률 차이, consolidation 판정 진단 Figure 3종

## 전체 class-month 중간 패널

- 원천: 19,927,019 fund-day
- 선택된 active-type 원행: 15,974,873
- 산출: 778,877 class-month, 8,482 fund codes, 367 months
- 기간: 1996-01~2026-07
- `(month, fund_code)` 중복: 0
- 설정 placeholder 제거: 7,158행
- 숫자로 변환되지 않거나 0 이하인 return factor: 0행
- 0.5 미만 또는 1.5 초과 return factor: 219행, 124개 fund code
- 오염된 fund-month: 193개; monthly return과 flow를 결측 처리

이 파일은 share-class 통합 전 중간 산출물이다. 최종 fund-month 표본으로
사용하지 않는다.

## 현재 blocker

1. 한국 Carhart 4요인과 무위험수익률
2. 한국형 investor sentiment와 CFNAI 대체변수
3. 대표 TNA는 class 합계로 검증됐지만 대표수익률은 class 가중수익률보다
   중앙값 월 10.78bp 높음; gross/net 의미 확인 필요
4. `실현수익률`의 gross/net 및 분배금 처리에 대한 vendor 정의
5. 극단 return factor가 분할·병합·청산 조정인지 데이터 오류인지 확인
6. 역사적 fee와 turnover
7. survivorship-bias-free full holdings와 46개 stock characteristics

현재 자료만으로는 parsimonious `flow + F_r12_2 + sentiment` replication을
우선 진행할 수 있다. fee·turnover·holdings 관련 결과는 proxy로 채우지 않고
registry에서 blocked로 유지한다.
