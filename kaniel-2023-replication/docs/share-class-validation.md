# Share-class validation and consolidation rule

검증일: 2026-07-29

## 검증식

대표펀드 `g`의 월 `t` 클래스 가중수익률은 다음과 같이 계산한다.

```text
class_weighted_return[g,t]
  = sum(TNA[i,t-1] * return[i,t]) / sum(TNA[i,t-1])
```

가중치에는 당월말 TNA가 아니라 전월말 TNA를 사용한다. 대표 TNA는 같은 월에
관측된 하위 클래스의 당월말 TNA 합계와 비교한다. `펀드구분=1`이며
`설정구분=0`인 관계만 사용하고, 모자펀드 관계인 `펀드구분=2`는 제외한다.

## Gate

- 최소 비교기간: 24개월
- 수익률 일치: 절대차 5bp 이내인 월이 90% 이상
- TNA 일치: 대표 TNA와 클래스 합계 차이가 2% 이내인 월이 80% 이상
- 대표 이력 완전: 클래스 관측월 중 대표코드 coverage 95% 이상
- fee-like 차이: 대표수익률이 더 높은 월 90% 이상이며 대표 프리미엄 중앙값이
  0~25bp

## 전체 결과

- share-class 관계: 42,680개
- 클래스 이력이 있는 대표그룹: 970개
- 비교 group-month: 103,560개
- 대표 TNA / 클래스 TNA 합계 중앙값: 1.001833
- TNA 2% 이내 일치율: 76.06%
- 대표수익률 - 클래스 가중수익률 중앙값: +10.78bp/월
- 대표수익률이 더 높은 월: 94.80%
- 수익률 절대차 5bp 이내 일치율: 11.43%

TNA가 2% 이내로 일치하는 월만 보아도 대표수익률은 96.36%의 월에서 더 높고
중앙값 차이는 +11.13bp/월이다. 따라서 대표코드는 TNA aggregate라는 증거는
강하지만, 대표수익률은 클래스 가중수익률과 동일하지 않다. 차이의 크기와
방향은 클래스 보수 차이와 유사하지만 vendor 정의 확인 전에는 대표수익률을
gross return이라고 단정하지 않는다.

## 확정 규칙

1. 대표코드와 하위 클래스를 동시에 표본에 넣지 않는다.
2. TNA gate를 통과하면 대표 TNA를 사용한다. 대표행이 빠진 월만 클래스 TNA
   합계를 fallback으로 사용한다.
3. TNA와 수익률 gate를 모두 통과한 `representative_row_preferred` 그룹만
   대표 행 전체를 그대로 사용한다.
4. TNA는 검증됐지만 수익률에 fee-like 차이가 있는 그룹은
   `separate_return_basis_required`로 둔다. 대표수익률과 클래스 가중수익률을
   별도 후보로 보존하고 하나를 임의 선택하지 않는다.
5. 대표행이 전혀 없는 그룹은 클래스 전월 TNA 가중수익률과 클래스 TNA 합계를
   사용한다.
6. 증거기간 부족 또는 TNA/수익률 불일치 그룹은 최종 연구표본에서 제외하고
   수동검토 대상으로 남긴다.

## 그룹 판정

| 판정 | 그룹 수 | 처리 |
|---|---:|---|
| `representative_row_preferred` | 39 | 대표 TNA와 대표수익률 사용 |
| `separate_return_basis_required` | 447 | 대표 TNA 사용, 두 수익률 후보 분리 |
| `class_aggregate_only` | 7 | 클래스 TNA 합계와 전월 TNA 가중수익률 사용 |
| `insufficient_evidence` | 178 | 최종 표본 제외 |
| `manual_review` | 299 | 최종 표본 제외·원인 조사 |

TNA 자체의 판정은 대표 우선 524개, 대표 결측월 class fallback 3개,
class-only 7개, 증거부족 175개, 수동검토 261개다.

## 남은 확인

`실현수익률`이 대표코드와 클래스코드에서 각각 gross/net 중 무엇을 뜻하는지,
분배금과 보수가 어떻게 반영되는지 vendor 정의가 필요하다. 이 확인 전에는
`separate_return_basis_required` 447개 그룹의 ML target return을 확정하지
않는다.
