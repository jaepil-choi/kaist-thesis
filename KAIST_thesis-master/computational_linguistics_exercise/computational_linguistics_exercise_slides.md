Natural Language Processing (NLP), Machine 
Learning and AI in Finance
Research to Practice Seminar
Python Exercise
Fall, 2024

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Outline
Prior to class: preparation at home
- Videos available - click on the green links below.
Coverage: Videos for each of these 4 steps
- Download, install Anaconda; Set up virtual environment
- Jupyter notebook basics; Data structure in Python (List, Numpy Array)
- Data structure in Python (Pandas Series, DataFrame)
- How to use Jupyter Notebook with a simple example
Python Exercise
Gordon Phillips
2 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Outline
Reminder: Please bring your laptop to the classroom in case you have questions.
1st Part
- Access 10-K files via EDGAR and store the files
- Extract a subsample: ≈60 firms, 1 year
- Extract Business Descriptions section from 10-K files
2nd Part
- Clean up words
- Compute similarity scores in pairs step-by-step (Hoberg and Phillips, 2016)
- with sample data
Python Exercise
Gordon Phillips
3 / 31

Data Access

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Access
How to access 10-K files via EDGAR?
1) Go to Security and Exchange Commission (SEC) website
Python Exercise
Gordon Phillips
5 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Access
How to access 10-K files via EDGAR?
2) Search for EDGAR database
Python Exercise
Gordon Phillips
6 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Access
How to access 10-K files via EDGAR?
3) Example: search for Apple
Python Exercise
Gordon Phillips
7 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Access
How to access 10-K files via EDGAR?
4) Check Apple’s product description in last 10-K
Python Exercise
Gordon Phillips
8 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Access
How to access 10-K files via EDGAR?
4) Check Apple’s product description in last 10-K
Python Exercise
Gordon Phillips
9 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Access
How to access 10-K files via EDGAR?
4) Check Apple’s product description in last 10-K (Item 1)
Python Exercise
Gordon Phillips
10 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Access
How to access 10-K files via EDGAR?
4) Check Apple’s product description in last 10-K (Item 1)
Python Exercise
Gordon Phillips
11 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
3 ways to download all 10-K files
Method 1:
Directly download cleaned and Raw 10-X Files for 1993-2021, by Notre Dame
- All cleaned (e.g., post Stage One parse) files (44 GB)
- All raw files (367 GB)
Python Exercise
Gordon Phillips
12 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
3 ways to download all 10-K files
Method 1:
Directly download cleaned and Raw 10-X Files for 1993-2021, by Notre Dame Repo
- All cleaned (e.g., post Stage One parse) files (44 GB)
- All raw files (367 GB) (we will explain why the difference is so big later)
- Possible to download by every 5 years (not to occupy too much computer storage)
- Show an example of downloaded .txt file
Python Exercise
Gordon Phillips
13 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
3 ways to download all 10-K files
Method 2:
Python script to download all the files (.txt format)
- We adopt this method in class (coding details on later slides)
- A Master Index provided by SEC (CIK, filing date, form type and firm name)
Python Exercise
Gordon Phillips
14 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
3 ways to download all 10-K files
Method 2:
Python script to download all the files (.txt format)
- Example master index (2022, Q2)
- Only download from the SEC server in “off” hours (between 9PM EST and 6AM
EST)
Python Exercise
Gordon Phillips
15 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
3 ways to download all 10-K files
Method 3:
A 3rd way is to directly read the text by WRDS library in Python
- If you have related Compustat (COMP) and Capital IQ (CIQ) subscriptions
- Sample code is here
Python Exercise
Gordon Phillips
16 / 31

Data Extraction

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Extraction
Download 10-K files from EDGAR by Master Index
Relevant files:
Code: 1_EDGAR_DownloadForms.ipynb
Supporting codes: 1) MOD_Download_Utilities.py, 2) MOD_EDGAR_Forms.py
Output: many firms’ 10-K raw files saved in folder "texts"
Sampling
- From folder "texts", randomly select a sample of 61 firms
- Save in folder "rantexts"
Python Exercise
Gordon Phillips
18 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Extraction
Filter out HTML part
- 10-K are .txt files with the embedded HTML, XBRL, exhibits, and the
ASCII-encoded graphics ( taking up 90% of the document)
- For example, IBM’s 10-K filing on 20120228:
- 48,253,491 characters contained in the file
- only about 7.6% account for the 10-K text including the exhibits and tables
- HTML coding: 55%, XBRL tables 33%, ASCII-encoded graphics 27%
- That’s why we need to remove them part to proceed the analysis
Python Exercise
Gordon Phillips
19 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Extraction
Filter out HTML part
- Many tags on the page <word></word>
Python Exercise
Gordon Phillips
20 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Extraction
Key packages
Filter out HTML part
- We use Beautiful Soup to pull data out of HTML and XML
Extract Business Description section of 10-K
- We use Regular Expression operations to extract from Item 1 to Item 1a
Python Exercise
Gordon Phillips
21 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Extraction
Extract Item 1 from sample data
- First show AccessPower10K.txt for a simple example
- Then loop over the sample 10-K files
- Filter out HTML part
- Extract the Business Description section
- 5 raw files of poor quality, thus skipped (empty or few random signs)
- Save the extracted section
Relevant files:
Input: 61 firms’ 10-K .txt files in folder "rantexts"
Code: 2_Data Extraction.ipynb
Supporting codes: 1) MOD_Download_Utilities.py, 2) MOD_EDGAR_Forms.py
Output: 56 firms’ extracted texts saved in folder "rantextsout"
Python Exercise
Gordon Phillips
22 / 31

Data Cleaning

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Data Cleaning
Clean up words
- Lower casing by Python built-in method
- Punctuation removal by re
- Eliminate broad or buzz words by Stopwords removal
- Word tokenization by NLTK Tokenizer Package
- Keep only nouns
Relevant files:
Input: 10-K .txt files saved in folder "rantextsout"
Code: 3_Data Cleaning & Computation.ipynb
Output: Results to be used in next step
Python Exercise
Gordon Phillips
24 / 31

Computation

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Computation
Compute similarity scores in pairs step-by-step (Hoberg and Philips, 2016)
sample 61 firms, 1 year
- Generate a corpus with our sample
- Document all firms’ word presence 0,1 in a matrix
- Show distribution of words
- Summary stats of words
- Compute pairwise cosine similarity score
Relevant files:
Input: Results obtained in last step
Code: 3_Data Cleaning & Computation.ipynb
Output: DataFrame saved in binary.csv, similarity.csv, & score_compare.csv
Python Exercise
Gordon Phillips
26 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Computation
Show distribution of words
- Top 10 popular words
Out of 56 firms:
Python Exercise
Gordon Phillips
27 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Computation
Show distribution of words
- Summary stats of words
Out of 56 firms:
Python Exercise
Gordon Phillips
28 / 31

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Computation
Pairwise cosine similarity score
- Summary stats of words
Out of 56 firms (cik code):
Python Exercise
Gordon Phillips
29 / 31

Different Sampling

Data Access
Data Extraction
Data Cleaning
Computation
Different Sampling
Different Sampling
Show difference of similarity scores based on
- total corpus (TNIC3 database)
- limited corpus (our sample data)
Python Exercise
Gordon Phillips
31 / 31
