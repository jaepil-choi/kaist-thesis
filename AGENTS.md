# Repository Instructions

## 프로젝트 목적

이 저장소는 KAIST MFE 졸업논문의 key paper를 선정하고, 해당 논문의 연구를
한국 데이터로 재현(replication)하고 필요한 경우 확장(extension)하기 위한
연구 저장소다.

- 학교의 기본 방향은 권위 있는 금융 학술지의 실증논문을 key paper로 정한 뒤
  한국 시장 데이터로 재현·확장하는 것이다.
- 후보 논문, 선정 근거, 데이터 실행가능성 및 현재 우선순위의 source of truth는
  `docs/key-paper-selection.md`다. 연구 방향을 판단하거나 큰 작업을 시작하기
  전에 반드시 이 문서를 읽는다.
- key paper는 아직 최종 확정되지 않았을 수 있다. 문서의 최신 판정과 사용자의
  명시적 지시를 과거 코드나 오래된 문서보다 우선한다.
- `KAIST_thesis-master/`는 과거 작업과 참고자료가 포함된 디렉터리다. 그 안의
  오래된 `CLAUDE.md`나 과거 논문 주제를 현재 프로젝트 지침으로 간주하지 않는다.

## Replication 원칙

- key paper의 일부 결과만 선택적으로 구현하지 않는다. 원 논문의 모든 핵심
  figure와 table을 그대로 재현하는 것을 기본 완료 기준으로 삼는다.
- 확장 분석에 앞서 원 논문의 표본 구성, 변수 정의, 시점 정렬, 전처리,
  포트폴리오 구성, 추정식, 표준오차, 검정 및 출력 형식을 가능한 한 충실히
  구현한다.
- 구현을 시작하기 전에 원 논문의 핵심 figure/table 목록과 각각에 필요한
  입력 데이터, 방법론, 예상 산출물을 명시적인 replication checklist로 만든다.
- 한국 데이터 때문에 원문과 동일하게 구현할 수 없는 항목은 조용히 생략하거나
  임의로 대체하지 않는다. 원 정의, 한국 데이터의 제약, 사용한 proxy 또는
  방법론 변경, 결과 해석에 미치는 영향을 문서화한다.
- exact replication과 한국 시장에 맞춘 extension을 코드, 결과 및 논문에서
  명확히 구분한다.
- look-ahead bias, survivorship bias, stale/current-snapshot 변수의 과거 적용,
  share-class 중복, 상장폐지 표본 누락, 공시일과 기준일의 혼동을 우선적으로
  점검한다.
- 사전 계산된 vendor 지표는 검산에 활용할 수 있지만, 핵심 결과는 가능한 한
  raw data에서 직접 재계산하여 재현 가능한 계보를 남긴다.

## 데이터 확보와 취급

- 한국 데이터로 핵심 분석을 재현할 수 있는지가 논문 선정과 구현의 최우선
  gate다. 코드 작성 전에 필요한 변수, 단위, grain, 기간, 식별자, point-in-time
  가용성 및 결측률을 먼저 조사한다.
- 사용자는 자산운용사 fund manager로서 국내 주식, 재무 및 펀드 데이터에
  비교적 폭넓게 접근할 수 있다. 데이터가 저장소에 없다는 이유로 즉시
  불가능하다고 결론 내리지 말고, 필요한 원천·테이블·필드·기간을 구체적으로
  정리해 사용자에게 확인한다.
- 회사 데이터와 외부 vendor 데이터의 정의 및 단위를 표본으로 검증한다.
  특히 수익률의 decimal/percent 구분, gross/net 기준, 가격 조정, AUM/flow
  계산식, 날짜 유효시점과 식별자 매핑을 추측하지 않는다.
- 자격증명, `.env`, 원시 회사 데이터, vendor 계약상 비공개 데이터는 커밋하지
  않는다. 문서와 테스트에는 스키마, 집계 통계, 비식별 예시 또는 합성 fixture를
  사용한다.
- 원천 데이터는 불변으로 취급하고, 전처리와 분석 산출물은 코드로 다시 만들 수
  있게 한다. 로컬 절대경로를 코드에 박지 말고 설정 또는 환경변수로 주입한다.

## Python 환경과 실행

- 이 프로젝트의 Python 환경과 의존성 관리는 `uv`를 사용한다.
- Python 명령은 가상환경을 직접 활성화하거나 시스템 Python을 호출하지 말고
  저장소 루트에서 `uv run ...` 형태로 실행한다.

```bash
uv run python path/to/script.py
uv run pytest
uv run ruff check .
```

- 의존성은 임의의 `pip install` 대신 `uv add <package>` 또는
  `uv add --dev <package>`로 `pyproject.toml`과 `uv.lock`에 반영한다.
- 분석 스크립트에는 재현 가능한 random seed, 명시적인 입력·출력 경로,
  주요 파라미터와 실행 진입점을 둔다. notebook에만 핵심 로직을 남기지 말고
  재사용되는 로직은 모듈이나 CLI script로 옮긴다.
- 최소한 작은 표본에 대한 schema·단위·정렬 검증과 주요 산식의 sanity check를
  수행한 뒤 전체 표본을 실행한다.

## Windows `apply_patch` known obstacle

- Corporate PC의 Windows 사용자명이 한글 등 non-ASCII 문자를 포함하면,
  Codex가 기본으로 제공하는 `apply_patch`가 사용자 프로필 아래의 실행 경로나
  sandbox wrapper를 제대로 처리하지 못해 `Access is denied` 또는 sandbox
  준비 오류로 실패할 수 있다.
- 이 문제가 발생하면 Python, `Set-Content`, `git apply` 같은 다른 쓰기 방식으로
  우회하지 않는다. `C:\tmp`에 미리 복사된 알려진 Codex
  `codex-apply-patch*.exe`를 찾아 `apply_patch` 용도로 사용한다.
- 여러 agent가 같은 실행 파일을 동시에 사용하면서 생기는 racing condition을
  피하기 위해 shared 원본 exe를 직접 실행하거나 이름을 바꾸지 않는다. 먼저
  `C:\tmp` 안에서 repo·agent·task/thread를 식별할 수 있는 고유한 파일명으로
  사본을 만들고, 그 전용 사본만 사용한다. 대상 파일명이 이미 존재하면
  덮어쓰지 말고 새 고유 이름을 선택한다.
- 다른 agent가 만든 사본을 수정·삭제·덮어쓰지 않는다. 실행 전 source와 copy의
  크기 또는 SHA-256 hash가 같은지 확인하고, patch는 저장소 루트에서 적용한다.
  sandbox 밖 실행 승인이 필요하면 그 전용 사본에 한정해 요청한다.

```powershell
$source = 'C:\tmp\codex-apply-patch.exe'
$copy = 'C:\tmp\codex-apply-patch-<repo>-<agent>-<task>.exe'
Copy-Item -LiteralPath $source -Destination $copy
$patch = @'
*** Begin Patch
*** Update File: path/to/file
@@
-old
+new
*** End Patch
'@
& $copy --codex-run-as-apply-patch $patch
```

## 논문 작성과 Typst

- 학위논문은 Typst로 작성한다. 템플릿과 한국어 예시는
  `thesis/paper/typst/`에 있다.
- 기존 `kaist-thesis.typ` 템플릿을 유지하고, 논문 source와 bibliography도
  해당 디렉터리의 구조와 예시를 따른다. 사용자가 요청하지 않는 한 LaTeX나
  다른 문서 시스템으로 전환하지 않는다.
- Typst source를 수정한 뒤에는 실제 PDF를 compile하여 오류, 넘침, 표·그림
  배치, 인용 및 bibliography를 확인한다.

```bash
typst compile thesis/paper/typst/example-korean.typ
```

- 최종 figure와 table은 분석 코드가 생성한 결과에서 추적 가능해야 하며,
  논문에 수동으로 숫자를 복사해 서로 다른 결과가 생기지 않게 한다.

## `scratch-pad-for-ai/` 사용 규칙

- `scratch-pad-for-ai/`는 사용자가 요청한 작업을 수행하는 동안 AI가 자유롭게
  사용할 수 있는 임시 작업공간이다. 탐색용 query, 일회성 실험, 중간 파일과
  진단 결과는 이곳에 둔다.
- 작업을 마칠 때 임시 파일, 캐시, 중복 산출물 및 더 이상 필요 없는 실험 코드는
  삭제한다.
- 이후에도 반복 사용할 가치가 있는 작업은 입력·출력과 옵션이 명확하고
  하드코딩이 적은 간결한 script로 정리해 남긴다. 파일명과 짧은 docstring만
  보아도 목적과 실행법을 알 수 있게 한다.
- 큰 검색 결과나 재생성 가능한 output은 `scratch-pad-for-ai/outputs/`에 두고
  기본적으로 커밋하지 않는다. 중요한 결론은 output 파일에만 남기지 말고
  `docs/`의 적절한 연구 문서에 간결하게 반영한다.

## 작업 및 검증 관례

- 작업 전 관련 문서, 코드, 설정과 `git status`를 확인하고 사용자의 기존 변경을
  보존한다.
- 이 저장소에서는 변경 검증에 `git diff`를 사용하지 않는다. 수정한 구간은
  `Get-Content`, `rg`, 전용 formatter/linter/test 등 비변경 비교 방식으로
  확인한다.
- 연구 결과를 생성하는 변경은 데이터 계보와 실행 순서를 남기고, 실행 명령과
  생성 파일을 재현할 수 있게 한다.
- 결과가 원 논문과 다르면 먼저 구현 오류, 표본·시점·단위·가중 방식 및
  데이터 정의 차이를 점검한다. 원하는 결론에 맞추기 위해 사후적으로 표본이나
  사양을 바꾸지 않는다.
- 완료 보고에는 변경한 내용, 실행한 검증, 생성된 결과, 남은 데이터 또는
  방법론상의 제약을 구분해 적는다.
