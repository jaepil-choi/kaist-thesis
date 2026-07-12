# NLP Exercise Session using Python

## Learning outcomes

- Students will be familiar with the text-based methods after the course and can apply the methods in his/her future research paper for the course.
- We will demonstrate the step-by-step implementation of the theory discussed in the RTP class sessions.

## Useful links

- [Hoberg-Phillips Data Library](http://hobergphillips.tuck.dartmouth.edu)
- [Fresard-Hoberg-Phillips Vertical Relatedness Data Library](http://faculty.marshall.usc.edu/Gerard-Hoberg/FresardHobergPhillipsDataSite/index.html)
- [Notre Dame Textual Analysis Repository](https://sraf.nd.edu/textual-analysis/)
- Additional data needed for the Python exercise is `tnic3_data.txt`, which is downloaded as a zip file as `tnic3_data.zip`. Here it is.
- Download baseline TNIC Database (calibrated to be as granular as three-digit SIC codes) [Recommended for most research projects]

> TNIC data is the richest form of the textual network project (an unrestricted network). The benefits are outlined in the readme file on the website, and in the Hoberg and Phillips (2010 RFS, 2016 JPE) papers noted below. The baseline version above is the "standard version" meant for most research projects.

## Online videos

- Conducted by student from the Swiss Finance Institute
- Videos and Data on Dropbox with link to be provided.

## Outline

### Python Refresher

- Guidance on Python installation and basic coding examples would be provided via pre-recorded video and Jupyter Notebooks. If you are a Python beginner or want to refresh your memory on the language, feel free to check it out.
- Videos:
  1. Download, install Anaconda; set up virtual environment
  2. Jupyter notebook basics; Data structure in Python (List, Numpy Array)
  3. Data structure in Python (Pandas Series, DataFrame)
  4. How to use Jupyter Notebook with a simple example

### Exercise Session (Part I)

- Main reference paper is Hoberg, Gerard, and Gordon Phillips. "Text-based network industries and endogenous product differentiation." Journal of Political Economy 124, no. 5 (2016): 1423-1465.
- Data: 10-K, a comprehensive report filed annually by publicly-traded companies covering company financial and operating performance and is required by the U.S. Securities and Exchange Commission (SEC). In particular, the business description section of the 10-K is mandated by SEC regulations requiring firms to describe the significant products they offer to their customers.
- We will do a partial replication of the main reference paper by working with a subset of firms, 1 year of data. We start with the download and storage of 10-K data. Particularly, we extract the business description section of the data so that the text file gets smaller in size and easier for later analysis.

### Exercise Session (Part II)

- Clean up words by:
  - Lower casing
  - Punctuation removal
  - Eliminate broad or buzzwords
  - Tokenization
  - Keep only nouns
- We continue by computing the textual similarity score of each firm to every other firm by calculating firm-by-firm pairwise word similarity scores using the processed and cleaned up 10-K product words.
  - Generate a corpus with our sample
  - Document all firms’ word presence (0,1) in a matrix
  - Show the distribution of words
  - Summary stats of words
  - Compute pairwise cosine similarity scores for each of the firms with each other
  - Compare the scores based on our sample corpus and total corpus
