# Generated outputs

이 디렉터리는 `run.py`가 생성하는 결과용이다. 재생성 가능한 파일은 Git에
커밋하지 않는다. 각 실행은 `manifests/`에 입력 경로, 설정, 행 수, 실행시각과
산출물 SHA-256을 기록한다.

2026-08-07의 parsimonious sensitivity 산출물은 다음과 같다.

- `intermediate/korea_carhart_monthly_non_pit.csv`: 3개월 reporting-lag factor
- `intermediate/parsimonious_proxy_cross_oos_predictions.parquet`: 136,641 predictions
- `tables/table_07_parsimonious_proxy_portfolios.csv`: 45개월 portfolio
- `manifests/parsimonious_proxy.json`: 입력 해시와 proxy/non-PIT/dropout 한계

파일명에 `proxy` 또는 `non_pit`가 없는 exact Table 7로 재명명하지 않는다.
