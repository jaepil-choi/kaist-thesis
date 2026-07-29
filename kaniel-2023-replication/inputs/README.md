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

## `external/korea_sentiment_monthly.csv`

```text
month,sentiment
```

원 논문의 Baker–Wurgler sentiment와 한국 대체변수의 구성 차이를 문서화한다.
현재 시점의 지표를 과거에 소급 적용하지 않는다.

## `external/korea_activity_monthly.csv`

```text
month,activity
```

CFNAI 대체변수를 사용할 경우 구성 지표, 발표시차, 실시간 vintage 사용 여부를
기록한다. 사후 개정된 macro series를 사용할 때는 결과 해석의 한계로 표시한다.

## 아직 없는 입력

- 역사적 fund expense ratio
- turnover ratio
- 분기별 survivorship-bias-free full holdings
- holdings 기반 46개 주식 characteristic

이 자료가 없는 산출물은 `config/output-registry.yml`에서 `blocked`로 남긴다.
