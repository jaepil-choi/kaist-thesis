# tnic_dl 전처리 문제 진단 및 수정 계획

## 1. 프로젝트 맥락

### 목표
Hoberg & Phillips (2018) "Text-Based Industry Momentum" 논문을 한국 시장 데이터로 복제하는 KAIST 석사 논문.

**핵심 가설**: 텍스트 기반 산업 피어(TNIC 또는 Autoencoder cluster)에 대한 충격이 전통적 산업분류(FnGuide) 피어 충격보다 더 강하고 지속적인 momentum을 유발한다. 이는 투자자의 비가시성(inattention)으로 인한 것이다.

### 사용 데이터
- **텍스트**: MongoDB에 저장된 한국 DART 사업보고서 (`section_code=020100`, 사업의 개요)
- **주가/거래**: FnGuide DataGuide (`data/fnguide/processed/`)
- **산업분류**: FnGuide Industry (한국판 SIC 역할)

### 주요 파일 구조
```
KAIST_thesis/
├── tnic/                          # H&P 2016 방법론 (전통적 TNIC)
│   └── korean_text_processor.py  # Kiwi 기반 한국어 전처리
├── tnic_dl/                       # Kim et al. 2020 방법론 (Deep Autoencoder)
│   ├── preprocessing/
│   │   ├── vocab_builder.py       # 어휘 선택
│   │   └── vectorizer.py          # Binary 벡터화
│   ├── models/
│   │   ├── autoencoder.py         # 모델 아키텍처
│   │   └── trainer.py             # 학습
│   └── similarity/
│       └── spherical_kmeans.py    # 클러스터링
├── scripts/
│   ├── build_korean_corpus_by_year.py      # H&P TNIC 코퍼스 구축
│   ├── build_binary_matrices_by_year.py    # Binary matrix
│   ├── compute_similarity_matrices_by_year.py  # Cosine similarity
│   └── build_tnic_peer_groups.py           # TNIC peer group 정의
├── text-based-industry-momentum-korea.ipynb  # 메인 분석 노트북
├── text-based-industry-momentum-korea-2.py   # Table 2 (TNIC 버전)
└── text-based-industry-momentum-korea-autoencoder-2.py  # Table 2 (Autoencoder 버전)
```

### 현재 문제 의식
`visualize-tnic.py`로 t-SNE 시각화를 수행했을 때, **Autoencoder cluster가 FnGuide 전통 산업분류를 제대로 capture하지 못함**이 확인됨. 이것이 이 문서에서 다루는 핵심 문제.

---

## 2. Kim et al. (2020) 방법론 요약

### 논문 참조
"An artificial intelligence-enabled industry classification and its interpretation"

### 전처리 파이프라인
```
사업보고서 텍스트
    → 명사/고유명사 추출 (POS tagging)
    → 어휘 필터링
        - 전체 문서의 >20%에 등장하는 단어 제외 (너무 일반적)
        - <2개 문서에만 등장하는 단어 제외 (너무 희소)
        - 지리어(국가명, 도시명) 제외
        - 20개 미만 고유 단어 문서 제외
    → 빈도순 상위 2,000 단어 선택
    → 2,000차원 Binary 벡터 (단어 존재 여부 1/0)
```

### 아키텍처
```
Encoder: 2000 → 500 (ReLU) → 125 (ReLU) → 10 (Linear)
Decoder: 10 → 125 (ReLU) → 500 (ReLU) → 2000 (Sigmoid)
```

### 학습
- Loss: Binary Cross-Entropy
- **Pre-training: RBM (Restricted Boltzmann Machine) greedy layer-wise**
- Fine-tuning: Backpropagation

### 클러스터링
- Spherical K-means (cosine similarity 기반)
- K=300 (US 시장 ~4,000개 기업 기준, TNIC-300 granularity 매칭)

### 피어 정의
- **10차원 embedding 간 pairwise cosine similarity** 계산
- threshold 이상인 기업쌍을 피어로 정의

---

## 3. 현재 구현 상태 진단

### 3.1 아키텍처/벡터화 — 대부분 정확 ✓

| 항목 | 논문 | 구현 | 상태 |
|------|------|------|------|
| Vocabulary size | 2,000 | 2,000 | ✓ |
| Max doc frequency | >20% 제외 | 20% | ✓ |
| Min unique words | 20 | 20 | ✓ |
| Input vector | 2,000-dim binary | 동일 | ✓ |
| Architecture | 2000→500→125→10→125→500→2000 | 동일 | ✓ |
| Activations | ReLU/Linear/Sigmoid | 동일 | ✓ |
| Loss | Binary cross-entropy | BCE | ✓ |
| Clustering | Spherical K-means | 동일 | ✓ |
| Geographic 제외 | 명시 | 부분 구현 | △ |
| Pre-training | RBM | **Xavier init만** | ❌ |
| Peer 정의 | Cosine sim on embeddings | **Cluster 멤버십** | ❌ |

---

## 4. 수정이 필요한 문제 목록

### [P0-A] RBM Pre-training 완전 누락 — 가장 치명적

**위치**: `tnic_dl/models/trainer.py`

**현재 코드**:
```python
class AutoencoderTrainer:
    def __init__(self, ...):
        # Initialize weights (Xavier initialization)
        self.apply(self._init_weights)   # ← RBM 없이 Xavier만
        self.optimizer = optim.Adam(...)
```

**논문 명세**:
> "Pre-train using a greedy layer-wise approach (**Restricted Boltzmann Machine**) for initialization [recommended based on Hinton & Salakhutdinov, 2006]. Fine-tune the full network using backpropagation."

**왜 치명적인가**:
- 2,000차원 sparse binary 벡터는 원소의 ~99%가 0
- Random initialization에서 backprop만 수행하면 초반 레이어로의 gradient가 매우 약함
- 희소한 입력에서 많은 ReLU 뉴런이 비활성화(dead ReLU)
- Kim et al.이 RBM을 선택한 핵심 이유가 바로 sparse binary input 문제를 해결하기 위함
- RBM 없이는 autoencoder가 임의의 local optima에 수렴 → 10차원 embedding이 산업 구조를 반영하지 못함

**수정 방향**:

옵션 A (정통 방법): Torch-RBM 구현 후 레이어별 pre-train
```python
class RBMPretrainer:
    """Restricted Boltzmann Machine for greedy layer-wise pre-training."""
    def __init__(self, n_visible, n_hidden, lr=0.01, n_epochs=10):
        ...
    def train(self, X):  # Contrastive Divergence
        ...
    def get_weights(self):
        return self.W, self.h_bias, self.v_bias

def pretrain_autoencoder(model, X, layer_sizes):
    """Greedy layer-wise RBM pre-training."""
    current_input = X
    for i, (n_vis, n_hid) in enumerate(zip(layer_sizes[:-1], layer_sizes[1:])):
        rbm = RBMPretrainer(n_vis, n_hid)
        rbm.train(current_input)
        # Transfer weights to encoder layer
        model.encoder[i*2].weight.data = rbm.W
        model.encoder[i*2].bias.data = rbm.h_bias
        # Get hidden activations as input for next layer
        current_input = sigmoid(current_input @ rbm.W.T + rbm.h_bias)
```

옵션 B (실용적 대안): SVD 기반 초기화
```python
from sklearn.decomposition import TruncatedSVD

def svd_initialize_autoencoder(model, X_sparse, latent_dim=10):
    """Initialize autoencoder with SVD decomposition."""
    svd = TruncatedSVD(n_components=latent_dim, random_state=42)
    svd.fit(X_sparse)
    # Initialize encoder weights using SVD components
    # This gives a meaningful starting point for the latent space
    ...
```

옵션 B가 구현이 훨씬 간단하며, 실무적으로 RBM과 유사한 효과를 낼 수 있음.

---

### [P0-B] Cluster 멤버십 기반 피어 → Cosine Similarity 기반 피어로 전환

**위치**: `checkpoints_autoencoder/` 생성 파이프라인, `text-based-industry-momentum-korea-autoencoder-2.py`

**현재 방식**:
```python
# Autoencoder cluster를 FnGuide처럼 고정 그룹으로 사용
autoencoder_ret = pd.read_parquet('checkpoint_03_autoencoder_peer_returns.parquet')
# → K-means cluster 멤버십 기반 equal-weighted peer return
```

**논문 의도**:
> "Compute **pairwise cosine similarity** scores between firms using the **10-dimensional reduced feature vectors**"

K-means cluster 기반은 FnGuide 산업분류와 구조적으로 동일한 "fixed partition" 문제 발생:
- Binary 멤버십 (같은 클러스터 = 피어, 다른 클러스터 = 비피어)
- TNIC의 핵심 이점인 **비대칭 peer relationship** 소실
- 클러스터 경계에 있는 기업의 "근접 피어"가 누락됨

**수정 방향**:
```python
# 10-dim embedding 로드
embeddings = np.load('embeddings_autoencoder_{year}.npy')  # (N, 10)
firm_info = pd.read_csv('firm_info_{year}.csv')

# Pairwise cosine similarity 계산
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize

# L2-normalize before cosine similarity
emb_normalized = normalize(embeddings, norm='l2', axis=1)
sim_matrix = emb_normalized @ emb_normalized.T  # (N, N)

# Threshold 기반 피어 정의 (FnGuide membership fraction에 맞게 calibrate)
# → scripts/build_tnic_peer_groups.py의 calibrate_threshold_raw() 참고
threshold = calibrate_threshold(sim_matrix, target_fraction)
peer_matrix = sim_matrix > threshold  # Boolean (N, N)

# 각 기업의 피어 return 계산 (focal firm 제외한 equal-weighted)
for firm_i in firms:
    peers_i = peer_matrix[i, :]  # Boolean mask
    peers_i[i] = False           # Self 제외
    peer_return_i = monthly_returns[peers_i].mean()
```

---

### [P1-A] NNB 품사 태그 포함 — 업스트림 어휘 오염

**위치**: `tnic/korean_text_processor.py`

**현재 코드**:
```python
self.pos_tags = set(['NNG', 'NNP', 'NNB'])
```

**문제**: `NNB`(의존명사)는 '것', '수', '등', '개', '가지', '분', '때', '이상', '이하' 등 문법적 단어. 업종 구분력이 전혀 없음에도 vocabulary를 오염시킴.

**수정**:
```python
# NNB 제외 → NNG (일반명사), NNP (고유명사)만 유지
self.pos_tags = set(['NNG', 'NNP'])
```

H&P 2016 원문: "nouns and proper nouns" — 의존명사는 여기 해당하지 않음.

---

### [P1-B] 지리어 목록 불완전

**위치**: `tnic_dl/preprocessing/vocab_builder.py`

**현재 geographic_terms (31개만)**:
```python
self.geographic_terms = {
    '서울', '부산', '인천', '대구', '대전', '광주', '울산', '세종',
    '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
    '한국', '미국', '중국', '일본', '유럽', '아시아', '베트남', '독일', '프랑스',
    '국내', '해외', '글로벌', '아태',
}
```

**누락 항목**:
```python
# 추가 필요
추가_geographic_terms = {
    # 한국 주요 도시 (business description에 자주 등장)
    '수원', '성남', '화성', '용인', '안산', '안양', '고양', '창원', '청주',
    '전주', '포항', '천안', '원주', '춘천', '강릉', '목포', '여수', '순천',
    '제천', '충주', '군산', '익산', '구미', '경주', '진주', '통영', '거제',
    # 추가 국가명
    '영국', '캐나다', '호주', '싱가포르', '인도', '브라질', '멕시코', '태국',
    '인도네시아', '말레이시아', '필리핀', '대만', '홍콩', '러시아', '터키',
    '사우디', '두바이', '이란', '이스라엘', '남아공',
    # 광역 지역
    '동남아', '중동', '북미', '남미', '동유럽', '서유럽', '오세아니아',
    # 방향형 지역 (지리적 의미로 사용 시)
    '동부', '서부', '남부', '북부',
}
```

**왜 중요한가**: 수출/수입 비즈니스를 하는 기업들은 사업보고서에 진출 국가명을 빈번히 언급. 이 단어들이 vocabulary에 포함되면 **모든 수출기업이 서로 유사해 보이는** 왜곡 발생.

---

### [P1-C] H&P TNIC 파이프라인의 threshold 보정 순서 역전

**위치**: `scripts/build_tnic_peer_groups.py`

**현재 코드** (잘못된 순서):
```python
# 1. Raw score에서 threshold 보정
threshold = calibrate_threshold_raw(M_raw, target_fraction)

# 2. 그 다음 median adjustment
M_adjusted = apply_median_adjustment(M_raw)

# 3. adjusted score에 raw-based threshold 적용 → 완전히 다른 값 범위에 적용됨
build_tnic_peer_groups(M_adjusted, threshold, ...)
```

**H&P 2016 명세**:
> "We subtract these median scores from the raw scores to obtain our **final scores** used for each firm. If this **final score** is above the **calibrated minimum similarity threshold**..."

올바른 순서:
```python
# 1. Median adjustment FIRST
M_adjusted = apply_median_adjustment(M_raw)

# 2. Adjusted score에서 threshold 보정
threshold = calibrate_threshold_adjusted(M_adjusted, target_fraction)

# 3. 동일한 adjusted score에 threshold 적용
build_tnic_peer_groups(M_adjusted, threshold, ...)
```

Raw score와 median-adjusted score의 값 범위가 다름:
- Raw: [0, 1]
- Adjusted: median이 약 0에 가까우므로 [-0.1, +0.4] 정도

Raw에서 보정된 threshold (예: 0.10)를 adjusted score에 적용하면 의도한 membership fraction과 전혀 다른 비율이 산출됨. **이것이 전통적 TNIC가 FnGuide를 capture하지 못하는 직접적 원인**.

---

### [P2-A] K=300 — 한국 시장 크기 부적합

**현재**: K=300 (미국 시장 ~4,000개 기업 기준)
- 한국 시장: ~2,000개 기업
- 평균 클러스터 크기: 2000/300 ≈ **6.7개 기업** → 피어 return 분산이 매우 큼

**Kim et al. 근거**: K=300은 TNIC-300 (US)과 granularity 맞추기 위한 선택.
- FnGuide 산업분류: 약 62개 그룹 (상위) / 약 150개 그룹 (세부)
- 한국 시장에서는 **K=50~100** 범위가 적합할 가능성 높음

**수정 접근**:
1. Elbow method로 최적 K 탐색: `find_optimal_k(embeddings, k_range=range(30, 201, 10))`
2. FnGuide membership fraction과 matching: 비교 benchmark로 사용
3. Silhouette score 기반 K 선택

---

### [P2-B] 25% 필터 후 20-word 재필터 누락 (TNIC 파이프라인)

**위치**: `scripts/build_korean_corpus_by_year.py`

**현재 코드**:
```python
firm_words = filter_by_min_words(firm_words, 20)    # 1차: 20 단어 미만 제거
firm_words = filter_by_frequency(firm_words, 0.25)  # 2차: 흔한 단어 제거
# → 2차 후 일부 기업이 20 미만으로 떨어졌지만 재필터링 없음
```

**올바른 순서**:
```python
firm_words = filter_by_min_words(firm_words, 20)    # 1차
firm_words = filter_by_frequency(firm_words, 0.25)  # 2차
firm_words = filter_by_min_words(firm_words, 20)    # 3차 (재필터)
```

---

## 5. 수정 작업 범위 및 파일 목록

### 즉시 수정 (P0)

| 파일 | 수정 내용 |
|------|----------|
| `tnic_dl/models/trainer.py` | RBM pre-training 또는 SVD 기반 초기화 추가 |
| `tnic_dl/pipeline.py` 또는 새 스크립트 | Cluster 기반 → Cosine similarity 기반 peer group 변경 |
| `checkpoints_autoencoder/` 재생성 | P0 수정 후 전체 pipeline 재실행 |

### 단기 수정 (P1)

| 파일 | 수정 내용 |
|------|----------|
| `tnic/korean_text_processor.py` | `pos_tags`에서 `NNB` 제거 |
| `tnic_dl/preprocessing/vocab_builder.py` | `geographic_terms` 확장 |
| `scripts/build_tnic_peer_groups.py` | threshold 보정 순서 수정 (raw → adjusted 후 보정) |

### 중기 수정 (P2)

| 파일 | 수정 내용 |
|------|----------|
| `tnic_dl/config.py` | K 값 재보정 (K=50~100 실험) |
| `scripts/build_korean_corpus_by_year.py` | 25% 필터 후 20-word 재필터 추가 |

---

## 6. 수정 후 검증 방법

### Autoencoder 품질 검증
```python
# 1. t-SNE 시각화로 FnGuide 산업 capture 여부 확인
python visualize-tnic.py --year 2010 --color-by both --interactive

# 기대: 같은 FnGuide 산업 내 기업들이 t-SNE 공간에서 클러스터 형성
# 현재: FnGuide 산업과 autoencoder cluster가 무관하게 분산됨
```

### TNIC 피어 그룹 품질 검증
```python
# FnGuide membership fraction과 TNIC membership fraction 비교
# 논문: 비슷한 수준의 granularity를 가져야 함
from scripts.build_tnic_peer_groups import calculate_fnguide_membership_fraction

fnguide_frac = calculate_fnguide_membership_fraction(df_year, 'FnGuide Industry')
tnic_frac = calculate_fnguide_membership_fraction(df_year, 'tnic_cluster')
# 두 값이 비슷해야 올바른 calibration

# Overlap 분석 (TNIC vs FnGuide)
# H&P 2018에서는 두 분류가 ~50% 이상 overlap해야 의미있음
```

### Figure 1 패턴 검증
```python
# 올바른 패턴 (H&P 2018 Figure 1):
# - t=0에서 turnover spike
# - SIC 피어: 빠른 decay (1~2개월)
# - TNIC 피어: 느린 decay (6~12개월)
# 현재: 전 구간에서 turnover 감소 (잘못된 패턴)
```

---

## 7. 추가 참고 사항

### Turnover 계산 오류 (별도 수정 필요)

**현재 노트북 코드**:
```python
share_turnover_df = monthly_trading_value / monthly_market_cap  # 잘못됨
```

**H&P 2018 정의**: `Share turnover = trading volume / shares outstanding`

거래대금(trading value)을 시가총액(market cap)으로 나누는 것은 **거래대금 비율**이지 share turnover가 아님. 주가 상승 시 market cap이 커져 분모가 커지므로 과소 추정됨.

**올바른 계산**:
```python
# FnGuide 데이터에서 trading_volume과 float_shares 사용
monthly_trading_volume = fd('fnguide_trading_volume').resample('ME').sum()
monthly_float_shares = fd('fnguide_float_shares').resample('ME').mean()
share_turnover_df = monthly_trading_volume / monthly_float_shares
```

### Figure 1 정규화 방식 불일치

**현재**: t=-3을 1.0으로 정규화
```python
# normalize_and_aggregate: normalizes at t=-WINDOW_BEFORE (t=-3)
avg_turnover = turnover_windows_array.mean(axis=0)
normalized = avg_turnover / avg_turnover[0]  # t=-3 기준
```

**H&P 논문**: "Event month 0's turnover scaled to 1.0"  
각 window를 t=0 값으로 나눈 뒤 평균.

```python
# 올바른 정규화
event_month_idx = WINDOW_BEFORE  # t=0의 index
normalized_windows = turnover_windows_array / turnover_windows_array[:, event_month_idx:event_month_idx+1]
avg_normalized = normalized_windows.mean(axis=0)
```

이 두 가지 오류의 결합으로 인해 Figure 1이 t=0에서 spike 대신 감소하는 패턴이 나옴.

---

## 8. 작업 시작점 권장

### 새 chat에서 작업 순서

1. **먼저 읽을 파일**:
   - `tnic_dl/preprocessing/vocab_builder.py`
   - `tnic_dl/preprocessing/vectorizer.py`
   - `tnic_dl/models/autoencoder.py`
   - `tnic_dl/models/trainer.py`
   - `tnic_dl/similarity/spherical_kmeans.py`
   - `tnic/korean_text_processor.py`
   - `scripts/build_tnic_peer_groups.py`

2. **P1-A 먼저 수정** (`NNB` 제거): 가장 간단하고 upstream 영향이 큼

3. **P1-B 수정** (지리어 확장): `vocab_builder.py`에 지리어 추가

4. **P0-A 수정** (RBM/SVD 초기화): `trainer.py`에 SVD 기반 초기화 구현

5. **P0-B 수정** (Cosine sim 기반 peer): 새 스크립트 작성 또는 `pipeline.py` 수정

6. **P1-C 수정** (TNIC threshold 순서): `build_tnic_peer_groups.py` 수정

7. **전체 pipeline 재실행** 후 t-SNE 시각화로 검증

### 핵심 질문 (작업 전 확인 필요)
- 현재 `checkpoints_autoencoder/` 파일들은 어떤 K 값으로 만들어졌는가?
- MongoDB에서 추출된 텍스트는 `data/korean_texts/business_descriptions_clean.parquet`에 저장되어 있는가?
- `tnic_dl/` pipeline의 진입점은 `tnic_dl/pipeline.py`인가, 아니면 `scripts/run_tnic_dl_pipeline.py`인가?
