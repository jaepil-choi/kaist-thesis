# External inputs

원시 회사·vendor 데이터와 자격증명은 이 디렉터리에 커밋하지 않는다.

현재 코드는 저장소의 불변 canonical 입력인
`data/kaist_pilot/canonical/common/korean_equity/`를 참조한다. 새 데이터는 기존
canonical 파일을 덮어쓰지 말고 별도 staging 경로에서 schema, 기간, key,
SHA-256을 검증한 뒤 manifest와 함께 승격한다.

필요한 외부 입력과 gate는 `../docs/data-requirements.md`를 따른다.
