# Replication checklist

완료 기준은 원 논문의 본문·부록 Figure/Table 총 45개다. 개별 산출물의 상태는
`config/output-registry.yml`이 source of truth다.

## 공통 데이터 gate

- [x] 수정수익률 정의 검증: 권리·분할 조정 decimal price return, 현금배당 제외
- [ ] 전월 말 시가총액의 주식수 기준 검증
- [ ] 상장·상장폐지·종목코드 변경·corporate action을 포함한 PIT universe
- [ ] 일별 무위험수익률
- [ ] 한국 일별 Fama–French 1/3/5 factor와 MOM·STREV·LTREV
- [ ] PCA 252일 covariance·60일 loading window의 결측/상장폐지 처리
- [ ] IPCA용 최소 240개월 월별 return·46개 characteristic
- [ ] 재무 characteristic의 실제 공시일 또는 정당화된 PIT availability rule
- [ ] bid-ask spread, shortability, borrow fee 및 거래세
- [ ] seed, validation period, rolling retraining과 hyperparameter 고정

## 구현 단계

- [x] 식 (1) `Phi = I - beta W_F.T` residual composition
- [x] IPCA-style OLS residual-maker
- [x] 일별 asset return에서 residual return 생성
- [x] 식 (3) residual allocation을 stock weight로 상계·L1 정규화
- [x] 4종목 합성 회귀 테스트
- [x] 2018년 이후 Kimchi 5-factor+MOM VW/EW·일간/월간 strict builder
- [ ] canonical stock-daily schema audit
- [ ] PIT monthly universe와 0.01% market-cap filter
- [ ] rolling Fama–French residuals
- [ ] rolling PCA residuals
- [ ] 46개 characteristic builder와 IPCA residuals
- [ ] OU+Threshold benchmark
- [ ] Fourier+FFN benchmark
- [ ] CNN+Transformer 및 Sharpe/mean-variance objective
- [ ] transaction/short holding cost objective
- [ ] output registry와 실행 manifest 연결

## 산출물

- [ ] Main Figure 1–19
- [ ] Main Table 1–9
- [ ] Appendix Figure A.1–A.7
- [ ] Appendix Table A.I–A.X

현재 구현된 core math는 논문 번호가 붙은 empirical output을 아직 생성하지
않는다. 이를 완료 산출물로 잘못 집계하지 않는다.
