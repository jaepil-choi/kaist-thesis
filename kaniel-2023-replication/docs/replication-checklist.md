# Replication checklist

원 논문의 완료 기준은 본문과 부록의 Figure/Table 총 64개다. 상세 제목,
구현 stage와 현재 blocker의 source of truth는
`config/output-registry.yml`이다.

## 공통 선행조건

- [ ] point-in-time 국내 active equity universe 확정
- [ ] 설정 첫 행 placeholder 제거와 일별 return-factor 단위 검증
- [ ] 해지펀드의 전체 이력 보존 검증
- [ ] share-class 대표펀드 합산식과 이중집계 부재 검증
- [ ] 한국 Carhart factor를 raw 주식자료에서 재구축
- [ ] 한국 investor sentiment 정의와 발표시차 확정
- [ ] CFNAI 대체변수와 실시간 vintage 처리 확정
- [ ] random, chronological, expanding-window 표본외 split 고정
- [ ] 예측 portfolio weighting과 decile breakpoints 고정
- [ ] seed, tuning grid, ensemble 규칙 고정

## 본문 산출물

- [ ] Figure 1–14
- [ ] Table 1–9

현재 정적 정의 산출물인 Figure 3, Table 1, Table 2는 구현했다. 나머지는
empirical panel과 외부 입력을 연결한 뒤 생성한다.

## Appendix A

- [ ] Figure A.1–A.26
- [ ] Table A.1–A.14

역사적 fee·turnover 또는 full holdings가 필요한 항목은 자료를 확보할 때까지
`blocked`로 둔다. top-10 holdings나 현재 fee snapshot으로 대체하지 않는다.

## Appendix B

- [x] Table B.1 tuning grid generator

## 결과 판정

각 산출물은 다음 상태 중 하나여야 한다.

- `implemented`: 실행 코드와 검증된 결과가 있음
- `planned`: 현재 데이터로 구현 가능하나 아직 코드가 없음
- `planned_partial`: 한국 핵심모형은 가능하지만 원 논문의 전체 정보집합은 불가
- `blocked_external`: factor·sentiment·macro 외부 입력이 없음
- `blocked_fee_history` / `blocked_fee_turnover`: 역사적 fee/turnover가 없음
- `blocked_holdings`: survivorship-bias-free full holdings가 없음

“한국 데이터에서는 중요하지 않을 것”이라는 이유로 산출물을 생략하지 않는다.
정확히 재현할 수 없으면 원 정의, 한국 데이터 제약, proxy 사용 여부와 결과
해석에 미치는 영향을 최종 논문에 남긴다.
