# Replication checklist

완료 기준은 원 논문의 본문·부록 Figure/Table 총 45개다. 개별 산출물의 상태는
`config/output-registry.yml`이 source of truth다.

## 공통 데이터 gate

- [x] 수정수익률 정의 검증: 권리·분할 조정 decimal price return, 현금배당 제외
- [ ] 전월 말 시가총액의 주식수 기준 검증
- [ ] 상장·상장폐지·종목코드 변경·corporate action을 포함한 PIT universe
- [x] 일별 무위험수익률: ECOS 91일 CD 연율을 252일 복리 환산
- [x] 한국 일별 Fama–French 1/3/5 factor와 MOM
- [ ] exact STREV·LTREV: 제공된 Kimchi 방법론에 정의가 없어 FF8은 차단
- [x] PCA 252일 covariance·60일 loading window의 공개 코드 결측 규칙
- [ ] IPCA용 최소 240개월 월별 return·46개 characteristic
- [ ] 재무 characteristic의 실제 공시일 또는 정당화된 PIT availability rule
- [ ] bid-ask spread, shortability, borrow fee 및 거래세
- [x] seed 0, 1000일 training, 125일 retraining/batch, 100 epochs 계약 고정

## 구현 단계

- [x] 식 (1) `Phi = I - beta W_F.T` residual composition
- [x] IPCA-style OLS residual-maker
- [x] 일별 asset return에서 residual return 생성
- [x] 식 (3) residual allocation을 stock weight로 상계·L1 정규화
- [x] 4종목 합성 회귀 테스트
- [x] 2018년 이후 Kimchi 5-factor+MOM VW/EW·일간/월간 strict builder
- [x] canonical stock-daily schema·decimal return·중복키 audit
- [x] PIT monthly universe와 0.01% market-cap filter
- [x] rolling Korean FF1/FF3/FF5 residuals와 synthetic factor composition
- [x] K=5 rolling PCA residuals, 252일 covariance·60일 loading, 2020-2026
- [x] 46개 characteristic builder와 IPCA ALS/residual core
- [x] 전체 한국 패널 characteristic 산출 및 coverage audit 고정
- [x] IPCA `initial_months`/rolling window 분리와 ALS convergence gate
- [ ] K=5 60개월 short-history IPCA: 논문 사양(46개 instrument, penalty 없음)에서 여전히 비수렴 (0/7 window, final_delta 3.36e23)
- [x] coverage>=0.90 instrument 축소(8개)와 Gamma ridge 옵션 구현 및 수렴 grid
- [x] 연결/별도 account code 체계(4001/1001) 대응과 separate fallback; 회계 characteristic coverage +0.079~+0.100
- [x] 우선주 등 비보통주 153개 유니버스 제외
- [x] coverage 측정 기준 3종(raw / 추정 유니버스 / 기간 제한) 분리 및 audit 기록
- [x] 회계 characteristic 13개를 포함한 28-instrument IPCA 잔차 생성(ridge 0.01)
- [ ] 금융업 재무제표 테이블 확보 또는 금융업 명시적 제외 결정
- [ ] FY 2011~2015 연결·별도 재무제표 확보
- [x] K=5, 8-instrument IPCA 잔차 2종 생성: ridge 0과 ridge 0.01, 각 1,330,517행
- [ ] ridge 없는 축소 사양은 1e-3 gate만 통과하고 1e-6에서는 0/7 비수렴이므로
      residual 사용 전 tolerance 근거를 논문에 명시
- [ ] 240개월 exact IPCA history 확보; 그 전 결과는 short-history sensitivity
- [x] OU+Threshold benchmark 구현 및 full Korean PCA5 실행
- [x] Fourier+FFN benchmark 구현 및 100-epoch Korean PCA5 실행
- [x] CNN+Transformer 및 Sharpe/mean-variance objective 구현
- [x] 누적 residual/Fourier t-1 신호 정렬 검증
- [x] PCA low-rank composition underlying gross exposure 정규화
- [x] epoch/subperiod checkpoint와 중단 후 재개
- [x] transaction/short holding cost objective와 lagged-weight CNN
- [x] 1일·다기간 holding objective
- [x] direct FFN 및 OU-feature FFN ablation
- [x] 16개 validation grid와 5개 대안 CNN experiment runner
- [x] output registry와 실행 manifest 연결

## 산출물

- [ ] Main Figure 1–19: 한국 variant 생성 여부와 exact blocker는 registry 참조
- [ ] Main Table 1–9: 장시간 CNN variant 실행 중; exact 미국 표본은 차단
- [ ] Appendix Figure A.1–A.7: 한국 variant 생성 여부와 exact blocker는 registry 참조
- [ ] Appendix Table A.I–A.X: validation/대안-network 장시간 실행 상태는 registry 참조

번호가 붙은 한국 결과는 원문 수치의 exact replication이 아니다. 특히 IPCA,
현금배당 포함 total return, 실제 공시시점 재무, 상장폐지수익률 및 실현 거래비용
결과는 입력이 확보되기 전까지 완료로 집계하지 않는다.
