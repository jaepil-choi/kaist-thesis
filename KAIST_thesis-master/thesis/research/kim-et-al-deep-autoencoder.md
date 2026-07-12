[cite_start]Based on the paper "An artificial intelligence-enabled industry classification and its interpretation"[cite: 2155], here is the detailed methodology for constructing the text-based industry network using a deep autoencoder.

### 1. Data Collection and Preprocessing

* [cite_start]**Data Source:** 10-K annual reports filed with the US Securities and Exchange Commission (SEC) from 2013 to 2016[cite: 2289].
* [cite_start]**Text Extraction:** Extract the "business description" section (Item 101 of Regulation S-K) from each 10-K report[cite: 2290].
* **Sample Filtering:**
  * [cite_start]Use the Compustat historical segment database to obtain primary SIC codes[cite: 2291].
  * [cite_start]Keep only the latest year for each report to avoid redundancies [e.g., if a 2015 report contains data for 2013-2015, keep only 2015 data](cite: 2294, 2295).
  * [cite_start]Remove observations missing a primary SIC code[cite: 2296].
  * [cite_start]Final sample size in the paper: 14,560 firm-year observations[cite: 2298].

### 2. Bag-of-Words Construction (Vectorization)

[cite_start]Convert the business descriptions into numerical vectors using the "bag-of-words" model[cite: 2300].

* **Vocabulary Selection:**
  * [cite_start]Focus on **nouns and proper nouns** only[cite: 2332].
  * **Exclusion Criteria:**
    * [cite_start]Exclude words that appear in **more than 20%** of all business descriptions [to remove common words](cite: 2332).
    * [cite_start]Exclude geographical words [country names, popular city names](cite: 2335).
    * [cite_start]Exclude documents containing fewer than **20 unique words**[cite: 2336].
  * [cite_start]**Top Words:** Select the **2,000 most frequently used unique words** across all documents to form the final vocabulary vector $W$[cite: 2338].
* **Vector Encoding:**
  * [cite_start]Represent each firm $i$'s business description as a **2,000-dimensional binary vector** $V_i$[cite: 2339, 2340].
  * **Encoding Rule:** Each element $v_{ij}$ of vector $V_i$ is:
    * $1$ if the word $w_j$ from the vocabulary $W$ appears in the document.
    * [cite_start]$0$ otherwise[cite: 2340, 2354].

[Image of Autoencoder architecture diagram]

### 3. Deep Autoencoder Architecture

[cite_start]Use a deep autoencoder to reduce the dimensionality of the input vector ($V_i$) from 2,000 to a lower-dimensional feature vector[cite: 2443, 2450].

* [cite_start]**Overall Structure:** A symmetric "butterfly" architecture with an encoder and a decoder[cite: 2254, 2451].
* **Layer Sizes (Nodes):**
  * [cite_start]**Input Layer:** 2,000 nodes [matches the vocabulary size](cite: 2451).
  * [cite_start]**Encoder Hidden Layer 1:** 500 nodes[cite: 2451].
  * [cite_start]**Encoder Hidden Layer 2:** 125 nodes[cite: 2451].
  * [cite_start]**Coded Layer (Bottleneck):** **10 nodes** [This is the reduced feature vector used for clustering](cite: 2450, 2451).
    * [cite_start]*Note:* For 2D visualization, this can be set to 2 nodes[cite: 2524].
  * [cite_start]**Decoder Hidden Layer 1:** 125 nodes[cite: 2451].
  * [cite_start]**Decoder Hidden Layer 2:** 500 nodes[cite: 2451].
  * [cite_start]**Output Layer:** 2,000 nodes[cite: 2451].
* **Activation Functions:**
  * [cite_start]**Hidden Layers:** **ReLU (Rectified Linear Unit)** is used for all encoding and decoding hidden layers[cite: 2451].
  * [cite_start]**Coded Layer (Bottleneck):** **Linear** function [to unbind values](cite: 2452).
  * [cite_start]**Output Layer:** **Sigmoid** function [to output probabilities between 0 and 1, suitable for the binary input reconstruction](cite: 2509).

### 4. Model Training

* [cite_start]**Goal:** Minimize the difference between the input vector $V_i$ and the reconstructed output vector[cite: 2258, 2447].
* [cite_start]**Loss Function:** **Binary Cross-Entropy**[cite: 2508].
* **Training Procedure:**
  * [cite_start]Pre-train using a greedy layer-wise approach (Restricted Boltzmann Machine) for initialization [recommended based on Hinton & Salakhutdinov, 2006](cite: 2259).
  * [cite_start]Fine-tune the full network using backpropagation[cite: 2260, 2445].

### 5. Clustering (Industry Construction)

Once the model is trained, extract the **10-dimensional vector** from the Coded Layer for each firm. [cite_start]Use this reduced feature vector for clustering[cite: 2450, 2518].

* [cite_start]**Algorithm:** **Spherical K-means Clustering**[cite: 2514].
  * *Reasoning:* Standard K-means uses Euclidean distance, which is less effective for high-dimensional text data. [cite_start]Spherical K-means uses **cosine similarity**, focusing on the direction of the vectors rather than magnitude[cite: 2512, 2514].
* [cite_start]**Number of Clusters (K):** Set $K=300$ to match the granularity of the Hoberg and Phillips (2016) TNIC-300 classification for comparison[cite: 2519].
* [cite_start]**Output:** Firms are assigned to one of the 300 industry clusters based on the cosine similarity of their 10-dimensional autoencoded features[cite: 2518].

### 6. Similarity Measurement (Network Construction)

To build the firm-to-firm network (TNIC analog):

* [cite_start]Compute **pairwise cosine similarity** scores between firms using the **10-dimensional reduced feature vectors** obtained from the autoencoder[cite: 2520].
* [cite_start]This results in a distribution of similarity scores that is more normally distributed and distinguishable compared to the skewed distribution from raw high-dimensional vectors[cite: 2735, 2736].
