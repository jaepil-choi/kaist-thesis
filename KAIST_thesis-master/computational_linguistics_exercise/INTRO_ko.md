## 컴퓨테이셔널 링귀스틱스 파이썬 실습 안내 (연구–실무 세미나)

### 개요

- **목표**: 10-K 사업설명(Item 1) 텍스트를 다운로드–정제–표현–유사도 계산까지 재현하고, Hoberg–Phillips(2016) 방법론을 소규모 샘플에 적용합니다.
- **구성 문서**: `computational_linguistics_exercise_slides.md`, `exercise_session_instructions.md`, `README.txt`의 흐름을 따릅니다.

### 핵심 학습 범위와 흐름

- **전체 흐름**: Data Access → Data Extraction → Data Cleaning → Computation → Different Sampling
  - 직접 인용: “Data Access; Data Extraction; Data Cleaning; Computation; Different Sampling” (slides)
- **Part I**: EDGAR에서 10-K 원문을 수집하고, 각 문서의 사업설명(Item 1)만 추출하여 소형 말뭉치를 만듭니다.
  - 직접 인용: “1st Part – Access 10-K files via EDGAR … Extract Business Descriptions section from 10-K files” (slides)
- **Part II**: 소문자화, 구두점/불용어 제거, 토큰화, 품사 태깅(명사만 유지) 후, 문서–단어 매트릭스와 코사인 유사도를 계산합니다.
  - 직접 인용: “Compute similarity scores in pairs step-by-step (Hoberg and Phillips, 2016)” (slides)

### 사전 준비 및 참고 자료

- **Python 기초 복습**: 아나콘다 설치, 가상환경, 주피터 기본, 리스트/넘파이/판다스 자료구조 복습 영상.
  - 직접 인용: “Download, install Anaconda; set up virtual environment … Jupyter notebook basics; Data structure in Python …” (`exercise_session_instructions.md`)
- **참고 링크**:
  - Hoberg–Phillips Data Library, FHP Vertical Relatedness, Notre Dame Textual Analysis Repository
  - 직접 인용: “TNIC data is the richest form of the textual network project … The baseline version above is the ‘standard version’ meant for most research projects.” (`exercise_session_instructions.md`)

### 데이터 접근과 다운로드

- **EDGAR 대량 다운로드 시간 준수**: 서버 오프타임에 요청.
  - 직접 인용: “Only download from the SEC server in ‘off’ hours (between 9PM EST and 6AM EST)” (slides)
- **다운로드 방식**:
  - (1) Notre Dame 저장소에서 일괄 수집본, (2) 파이썬 스크립트로 `master.idx` 기반 수집, (3) WRDS 라이브러리 사용(구독 필요)
  - 직접 인용: “3 ways to download all 10-K files … Python script to download all the files (.txt format) … A Master Index provided by SEC” (slides)

### 추출(Extraction)과 전처리(Cleaning)

- **HTML 및 비텍스트 제거**: BeautifulSoup 사용
  - 직접 인용: “We use Beautiful Soup to pull data out of HTML and XML” (slides)
- **사업설명(Item 1) 구간 추출**: 정규표현식으로 Item 1 ~ Item 1A(또는 1B) 구간을 탐지
  - 직접 인용: “Extract Business Description section of 10-K – We use Regular Expression operations to extract from Item 1 to Item 1a” (slides)
- **텍스트 정리**: 소문자화, 구두점 제거, 불용어 제거, 토큰화, 명사만 유지
  - 직접 인용: “Clean up words – Lower casing … Punctuation removal … Stopwords removal … Tokenization … Keep only nouns” (slides)

### 계산(Computation)과 산출물

- **문서–단어 표현**: 말뭉치 생성 후 단어 존재(0/1) 매트릭스 구성(`binary.csv`)
- **유사도 계산**: 코사인 유사도 행렬(`similarity.csv`)
- **TNIC3와 비교**: CIK–GVKEY 매핑 후 샘플 점수와 전체(TNIC3) 점수를 `score_compare.csv`로 비교
  - 직접 인용: “Output: DataFrame saved in binary.csv, similarity.csv, & score_compare.csv” (slides)
  - 직접 인용: “Compare the scores based on our sample corpus and total corpus” (`exercise_session_instructions.md`)

### 파일 및 노트북 개요

- `code/1_EDGAR_DownloadForms.ipynb`: `master.idx`를 분기별로 내려받아 10-K 텍스트를 로컬에 저장. 파일명에는 접수일, 폼, CIK 등이 포함됩니다.
- `code/2_Data Extraction.ipynb`: 샘플 폴더(`rantexts`)의 10-K에서 사업설명(Item 1)만 정규표현식으로 추출. HTML 본문은 BeautifulSoup로 제거 후 저장(`rantextsout`).
- `code/3_Data Cleaning _ Computation.ipynb`: 정제(소문자/구두점/불용어/명사) → 말뭉치/원핫 매트릭스 → 상위 단어 분포(`top10.png`) → 코사인 유사도(`similarity.csv`) → CIK–GVKEY 매핑 → TNIC3 비교(`score_compare.csv`).
- `code/MOD_Download_Utilities.py`: HTTP 다운로드 유틸(파일/문자열/리스트), 재시도, SEC 헤더, 오프타임 대기 로직.
- `code/MOD_EDGAR_Forms.py`: 10-K/10-Q 등 SEC 폼 묶음 상수 정의.

### 실행 전 필수 수정 사항

- 각 노트북의 경로 상수를 본인 환경에 맞게 수정하십시오(예: 출력 디렉터리, 로그 파일, 입력 데이터 폴더).
  - `1_EDGAR_DownloadForms.ipynb`: `PARM_PATH`, `PARM_LOGFILE`를 본인 경로로 교체.
  - `2_Data Extraction.ipynb`: `rantexts` 입력과 `temp_out`/`rantextsout` 출력 경로 확인.
  - `3_Data Cleaning _ Computation.ipynb`: `rantextsout` 입력 경로, `Map_gvkey_cik.xlsm`/`tnic3_data.txt` 위치 확인.

### 주의 사항 및 트러블슈팅

- **Windows 인코딩**: 텍스트 파일 읽기 시 `encoding='utf-8'` 지정 권장.
  - 직접 인용: “if you are Windows user, … add encoding='utf-8' … with open(filename, 'r', encoding='utf-8') as file:” (`README.txt`)
- **대용량 TNIC3**: 전체 유사도 파일은 약 1GB로, 별도 다운로드 필요.
  - 직접 인용: “As the TNIC3 similarity score is around 1GB … download from … tnic3_data.zip” (`README.txt`)
- **엑셀 매핑 파일 이슈**: `Map_gvkey_cik.xlsm`이 동작하지 않으면 CSV로 저장 후 `pd.read_csv`로 대체.
  - 직접 인용: “manually save the file in csv format, and use the alternative code to import data: df = pd.read_csv("Map_gvkey_cik.csv", usecols=columns)” (`README.txt`)

### 추가 인용(슬라이드의 핵심 문구)

- “Filter out HTML part – 10-K are .txt files with the embedded HTML … That’s why we need to remove them part to proceed the analysis” (slides)
- “We use Beautiful Soup … We use Regular Expression …” (slides)
- “Show difference of similarity scores based on – total corpus (TNIC3 database) – limited corpus (our sample data)” (slides)

### 참고 문헌

- Hoberg, Gerard, and Gordon Phillips (2016), “Text-Based Network Industries and Endogenous Product Differentiation,” JPE.
- 실습 자료의 모든 링크는 `exercise_session_instructions.md` 상단 “Useful links”를 참조하십시오.
