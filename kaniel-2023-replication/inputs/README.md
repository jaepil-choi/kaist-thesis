# 외부 입력 계약

모든 파일은 UTF-8 CSV이고, `month`는 해당 월의 말일을 나타내는
`YYYY-MM-DD` 형식이어야 한다. 수익률과 factor는 percent가 아니라 decimal이다.

## `external/korea_carhart_monthly.csv`

```text
month,mkt_rf,smb,hml,mom,rf
```

- `mkt_rf`: 시장 초과수익률
- `smb`: size factor
- `hml`: value factor
- `mom`: momentum factor
- `rf`: 월 무위험수익률

factor는 한국 주식 raw data에서 point-in-time 방식으로 직접 구축하거나,
정의·표본·단위가 확인된 외부 시계열을 사용한다. 미래 상장종목을 과거
universe에 포함하면 안 된다.

## sentiment 입력

```text
month,sentiment
```

기본 설정은 ECOS derived의 `korea_sentiment_proxy_monthly.csv`를 읽는다.
2005~2014 고정 calibration PCA와
1개월 availability lag를 적용한 ECOS-only proxy다. 원 논문의 Baker–Wurgler
sentiment와 동일하지 않으며 exact 결과로 해석하지 않는다.

## ECOS에서 확보한 기본 입력

기본 설정은 다음 세 파일을 직접 읽는다.

- `data/kaist_pilot/canonical/kaniel_2023/ecos/derived/risk_free_monthly.csv`
  (`month,rf`): 통안증권 91일 연%를 월 decimal 수익률로 변환
- `data/kaist_pilot/canonical/kaniel_2023/ecos/derived/korea_activity_monthly.csv`
  (`month,activity`): ESI 순환변동치에서 100을 차감한 robustness proxy
- `data/kaist_pilot/canonical/kaniel_2023/ecos/derived/korea_sentiment_proxy_monthly.csv`
  (`month,sentiment`): 고정 calibration PCA와 1개월 lag를 적용한 불완전 proxy

ESI는 CFNAI와 동일한 실물활동 지표가 아니며 발표일/vintage도 포함하지 않는다.
예측에 사용할 때는 최소 1개월 lag 또는 별도 발표일 정렬이 필요하다. 상세
계보와 한계는 `docs/kaniel-ecos-inputs.md`에 기록했다.

## 아직 없는 입력

- 한국 Carhart 4요인 완성본
- Baker–Wurgler 정의에 가까운 exact-definition 한국형 sentiment
- 역사적 fund expense ratio
- turnover ratio
- 분기별 survivorship-bias-free full holdings
- holdings 기반 46개 주식 characteristic

이 자료가 없는 산출물은 `config/output-registry.yml`에서 `blocked`로 남긴다.
