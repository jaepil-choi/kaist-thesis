# ECOS Open API reference

This reference is a text reconstruction of the six supplied ECOS API
specification workbooks, verified against live JSON responses on 2026-07-28.
It is self-contained; the original XLS/XLSX files are not required.

## Contents

1. [Common request contract](#common-request-contract)
2. [Response envelope](#response-envelope)
3. [Services](#services)
4. [Cycles and dates](#cycles-and-dates)
5. [Errors](#errors)
6. [Validated CPI example](#validated-cpi-example)
7. [Operational rules](#operational-rules)

## Common request contract

Base URL:

```text
https://ecos.bok.or.kr/api/
```

Common path prefix:

```text
{SERVICE}/{API_KEY}/{FORMAT}/{LANG}/{START_ROW}/{END_ROW}
```

| Segment | Required | Values / meaning |
|---|---:|---|
| `SERVICE` | yes | One of the six service names below |
| `API_KEY` | yes | ECOS-issued key |
| `FORMAT` | yes | `json` or `xml`; use `json` for automation |
| `LANG` | yes | `kr` or `en` |
| `START_ROW` | yes | 1-based first result row |
| `END_ROW` | yes | 1-based last result row |

URL-encode each path segment. In `StatisticSearch`, represent an unused
optional item-code position with `?` encoded as `%3F`.

## Response envelope

Successful JSON:

```json
{
  "StatisticSearch": {
    "list_total_count": 1,
    "row": [
      {}
    ]
  }
}
```

The top-level key equals the requested service. `list_total_count` is the
total matching count, not necessarily the number returned in the requested
row window. `row` is the returned slice.

Informational or error JSON:

```json
{
  "RESULT": {
    "CODE": "INFO-200",
    "MESSAGE": "해당하는 데이터가 없습니다."
  }
}
```

Check `RESULT` before accessing the service object.

## Services

### `KeyStatisticList`

Return headline indicators.

```text
KeyStatisticList/{key}/json/kr/{start_row}/{end_row}/
```

No service-specific input.

| Output field | Meaning |
|---|---|
| `CLASS_NAME` | statistic group |
| `KEYSTAT_NAME` | statistic name |
| `DATA_VALUE` | value |
| `CYCLE` | latest recorded time |
| `UNIT_NAME` | unit |

### `StatisticTableList`

Discover statistic tables. `STAT_CODE` is optional.

```text
StatisticTableList/{key}/json/kr/{start_row}/{end_row}/{stat_code?}/
```

| Output field | Meaning |
|---|---|
| `P_STAT_CODE` | parent table code |
| `STAT_CODE` | table code |
| `STAT_NAME` | table name |
| `CYCLE` | cycle |
| `SRCH_YN` | searchable flag |
| `ORG_NAME` | source organization |

Filter to `SRCH_YN=Y` before selecting a table.

### `StatisticItemList`

Discover item codes, hierarchy, coverage, unit, and weight for a table.
`STAT_CODE` is required.

```text
StatisticItemList/{key}/json/kr/{start_row}/{end_row}/{stat_code}/
```

| Output field | Meaning |
|---|---|
| `STAT_CODE` | table code |
| `STAT_NAME` | table name |
| `GRP_CODE` | item group code |
| `GRP_NAME` | item group name |
| `ITEM_CODE` | item code |
| `ITEM_NAME` | item name |
| `P_ITEM_CODE` | parent item code |
| `P_ITEM_NAME` | parent item name |
| `CYCLE` | cycle |
| `START_TIME` | first available time |
| `END_TIME` | last available time |
| `DATA_CNT` | data count |
| `UNIT_NAME` | unit |
| `WEIGHT` | weight |

The same item code can appear once per cycle. Always filter by the intended
cycle before taking `START_TIME` or `END_TIME`.

### `StatisticSearch`

Retrieve observations. Table code, cycle, start time, and end time are
required. Item-code groups 1 through 4 are optional but positional.

```text
StatisticSearch/{key}/json/kr/{start_row}/{end_row}/
{stat_code}/{cycle}/{start_time}/{end_time}/
{item_code1?}/{item_code2?}/{item_code3?}/{item_code4?}/
```

| Output field | Meaning |
|---|---|
| `STAT_CODE` | table code |
| `STAT_NAME` | table name |
| `ITEM_CODE1` ... `ITEM_CODE4` | item codes |
| `ITEM_NAME1` ... `ITEM_NAME4` | item names |
| `UNIT_NAME` | unit |
| `WGT` | weight |
| `TIME` | observation time |
| `DATA_VALUE` | observation value |

Use `StatisticItemList` first. Do not infer which item-code position a code
belongs to. Preserve `DATA_VALUE` as received until the consumer explicitly
converts it.

### `StatisticWord`

Read a statistical term and its explanation. `WORD` is required.

```text
StatisticWord/{key}/json/kr/{start_row}/{end_row}/{word}/
```

| Output field | Meaning |
|---|---|
| `WORD` | term |
| `CONTENT` | explanation |

### `StatisticMeta`

Search statistical metadata by data name. `DATA_NAME` is required.

```text
StatisticMeta/{key}/json/kr/{start_row}/{end_row}/{data_name}/
```

| Output field | Meaning |
|---|---|
| `LVL` | hierarchy level |
| `P_CONT_CODE` | parent content code |
| `CONT_CODE` | content code |
| `CONT_NAME` | content name |
| `META_DATA` | metadata text |

## Cycles and dates

| Cycle | Meaning | Date format | Example |
|---|---|---|---|
| `A` | annual | `YYYY` | `2025` |
| `S` | semiannual | `YYYYS1` or `YYYYS2` | `2025S1` |
| `Q` | quarterly | `YYYYQ1` ... `YYYYQ4` | `2025Q4` |
| `M` | monthly | `YYYYMM` | `202512` |
| `SM` | semimonthly | `YYYYMMS1` or `YYYYMMS2` | `202512S2` |
| `D` | daily | `YYYYMMDD` | `20251231` |

Start and end formats must match the requested cycle. Confirm requested dates
fall within the selected item's `START_TIME` and `END_TIME`.

## Errors

ECOS may prefix these numeric codes with `INFO-` or `ERROR-`.

| Numeric code | Meaning | Action |
|---:|---|---|
| `100` (info) | invalid API key | verify `BOK_ECOS_API_KEY`; do not print it |
| `200` (info) | no matching data | revise table/item/date filters |
| `100` (error) | required value missing | compare request with service contract |
| `101` | date format does not match cycle | correct the date format |
| `200` (error) | invalid or missing file type | use `json` or `xml` |
| `300` | missing start/end row | supply both integer row bounds |
| `301` | invalid row-count type | use integers |
| `400` | range too large; 60-second timeout | split the request |
| `500` | server/service error | verify service, then retry later |
| `600` | database connection error | stop and retry later |
| `601` | SQL error | stop and report the request parameters |
| `602` | excessive API calls | stop, back off, and reduce call frequency |

Never retry `400` or `602` in a tight loop.

## Validated CPI example

Discovery on 2026-07-28 identified:

| Table | Meaning |
|---|---|
| `901Y009` | `4.2.1. 소비자물가지수` |
| `901Y010` | `4.2.2. 소비자물가지수(특수분류)` |
| `902Y008` | `9.1.2.2. 국제 주요국 소비자물가지수` |

Top commodity-class items in monthly table `901Y010`:

| Item code | Item name | Unit |
|---|---|---|
| `00` | 총지수 | `2020=100` |
| `211` | 농축수산물 | `2020=100` |
| `212` | 공업제품 | `2020=100` |
| `213` | 전기 · 가스 · 수도 | `2020=100` |
| `22` | 서비스 | `2020=100` |

Example for total CPI:

```text
StatisticSearch/{key}/json/kr/1/1000/
901Y010/M/202501/202512/00/%3F/%3F/%3F/
```

Re-run discovery for current coverage rather than assuming the listed
`END_TIME` remains current.

## Operational rules

- Prefer `StatisticTableList` → `StatisticItemList` → `StatisticSearch`.
- Use the smallest row range and time range that satisfies the task.
- Split long daily or high-dimensional requests into date chunks.
- Deduplicate on the complete item-code tuple plus `TIME`.
- Treat units as series metadata; never merge unlike units silently.
- Record the source organization from `StatisticTableList`.
- Redact `{key}` in provenance URLs and logs.