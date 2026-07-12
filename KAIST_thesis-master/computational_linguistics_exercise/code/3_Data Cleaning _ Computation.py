# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Data Cleaning & Computation
# Aug 18, 2022

# %% [markdown]
# Yuhan Ye

# %% [markdown]
# ## Import all the necessary packages first

# %%
import os
import numpy as np
import pandas as pd
import spacy
import nltk
import re
import unicodedata
import string
import csv
import matplotlib.pyplot as plt
import seaborn as sns
import random
import xlrd

# %% [markdown]
# ## Lower casing

# %% [markdown]
# - Convert everything to the lower case 

# %%
os.chdir("/Users/f0034w9/Dropbox (Dartmouth College)/Exercise Computational Linguistics/data/")

# %%
## start with a single file as example
##lower casing
with open('AccessPower10K2.txt', 'r') as file:
    string = file.read().replace('\n', '')
#string

# %%
stringlow=string.lower()  ## a built-in method used for string handling in Python
#stringlow

# %%

# %% [markdown]
# ## Punctuation removal

# %% [markdown]
# - remove all the punctuation in the dataset (also remove @,%,#, and other special characters

# %%
string=stringlow
## punctuation removal
#string.punctuation contains !”#$%&\’()*+,-./:;<=>?@[\\]^_`{|}~
string_no_punct=re.sub(r'[^\w\s]','',string)
#string_no_punct

# %%

# %% [markdown]
# ## Remove stop words

# %% [markdown]
# - The intuition behind using stop words is that, by removing low information words from the text, we can focus on the important words instead.
# - We can also remove all short words (length < 2).
# - We can also append other unnecessary words to stopwords list.

# %%
## As my sample of 44 firms is too small, if applying 5% rule to exclude buzz words, 
## the error can be relatively big
## thus I use a stopwords list

# %%
from nltk.corpus import stopwords
stopwords_list=stopwords.words('english')   ## 'english' is actually a list of buzz words
#stopwords_list

# %%
string = string_no_punct

string_no_stopwords = [word for word in string.split() if (word not in stopwords_list) and len(word) > 2]
string_no_stopwords=" ".join(string_no_stopwords)
#string_no_stopwords

# %%

# %% [markdown]
# ## Word tokenization

# %%
from nltk.tokenize import word_tokenize

string_inp=string_no_stopwords
words = word_tokenize(string_inp)
tokens=string_inp.split()
#tokens

# %%

# %% [markdown]
# ## Keep only nouns 

# %%
text=' '.join(tokens).lower()
tokens2 = nltk.word_tokenize(text)
tags = nltk.pos_tag(tokens2)
nouns = [word for word,pos in tags if (pos == 'NN' or pos == 'NNP' or pos == 'NNS' or pos == 'NNPS')
]
nouns=sorted(nouns)  #sort it alphabetically 
#nouns

# %%

# %% [markdown]
# ## Return unique values from a list

# %%
myset = set(nouns)
#myset

# %%

# %% [markdown]
# # Next work on multiple files with for loop

# %%
# preparation for multiple files loop

# %%
## change the .txt file name 
# now the file names follow this pattern: 
### old:   2018\QTR1\20180103_10-K_edgar_data_1158420_0001144204-18-000327_1
### new name: 1158420_0001144204-18-000327_1 (contains CIK code： 1158420)

# %%
def get_numbers_from_filename(filename):
    #a=re.search('000.*18', filename).group(0)
    #b = a[:-3]
    print(filename)
    return '_'.join(filename.split('_')[-3:]).split('.')[0]
    #return b


# %%
#extract the CIK code for indexing
newname_example=get_numbers_from_filename('2018\QTR1\20180103_10-K_edgar_data_1158420_0001144204-18-000327_1')

# %%
newname_example

# %%
pwd

# %%
os.chdir('./rantextsout')
path_of_the_directory='/Users/f0034w9/Dropbox (Dartmouth College)/Exercise Computational Linguistics/data/rantextsout'

# %%
dicts = {}  #use a dictionary to store all the word lists of firms
names = []

#load the 10-K files saved in local drive 'subtextsout' and clean the data
for filename in os.listdir(path_of_the_directory): ###need to set directory 
#     filename ='/Users/yuhanye/Desktop/subtextsout/2018\QTR1\20180227_10-K_edgar_data_1196501_0001171843-18-001503_1.txt'                                               ###to the data to run this
    if filename.endswith('.txt'):         #skip the .DS file in the folder
        ####%%%%%%%%%%% lower casing      ####%%%%%%%%%%%%%%%%%%%%%%%%%%%%    
        with open(filename, 'r') as file:
            string = file.read().replace('\n', '')
        #print(string)

        stringlow=string.lower()  ## a built-in method used for string handling in Python
        #print(stringlow)


        ####%%%%%%%%%%% punctuation removal  ####%%%%%%%%%%%%%%%%%%%%%%%%%%%
        string=stringlow
        ## punctuation removal
        #string.punctuation contains !”#$%&\’()*+,-./:;<=>?@[\\]^_`{|}~
        string_no_punct=re.sub(r'[^\w\s]','',string)
        #print(string_no_punct)


        ####%%%%%%%%%%%%%%% Remove stop words ####%%%%%%%%%%%%%%%%%%%%%%%%%%
        stopwords_list=stopwords.words('english')   ## 'english' is actually a list of buzz words
        #stopwords_list
        string = string_no_punct

        string_no_stopwords = [word for word in string.split() if (word not in stopwords_list) and len(word) > 2]
        string_no_stopwords=" ".join(string_no_stopwords)
        #string_no_stopwords
        
        
        ####%%%%%%%%%%%%%%% word tokenization ####%%%%%%%%%%%%%%%%%%%%%%%%%%
        from nltk.tokenize import word_tokenize
        string_inp=string_no_stopwords
        words = word_tokenize(string_inp)
        tokens=string_inp.split()
        #print(tokens)
        
        
        ####%%%%%%%%%%%%%%%   keep only nouns    ####%%%%%%%%%%%%%%%%%%%%%%%%%%
        text=' '.join(tokens).lower()
        tokens2 = nltk.word_tokenize(text)
        tags = nltk.pos_tag(tokens2)
        nouns = [word for word,pos in tags if (pos == 'NN' or pos == 'NNP' or pos == 'NNS' or pos == 'NNPS')
        ]
        nouns=sorted(nouns)  #sort it alphabetically 
        #print(nouns)
        
        ####%%%%%%%%%%%%%%%   Return unique values from list  ####%%%%%%%%%%%%%
        myset = set(nouns)   # set format
        
        
        ####%%%%%%%%%%%%%%%   rename the .txt file ####%%%%%%%%%%%%%
        newname=get_numbers_from_filename(filename)
        names.append(newname)
        
        dicts[newname] = myset
        
        

# %%
#print(dicts)   

# %%
len(dicts.keys())      #equal to number of firms in the sample 

# %%
len(names)         #equal to number of firms in the sample 

# %%
#dicts

# %% [markdown]
# ## Generate corpus

# %%
#generate our specific corpus by merging word lists of all firms 
total_tokens = []
for key in dicts.keys():
    total_tokens += list(dicts[key])
total_tokens = set(total_tokens)
total_tokens=sorted(total_tokens)  #sort it alphabetically 
#total_tokens      #see our corpus 

# %%
len(total_tokens)       #we extracted this number of unique words from our sample data

# %%

# %% [markdown]
# ## Word presence: 0 or 1, saved in matrix 

# %%
# write a matrix collecting all the presence of each word for each company
one_hot_matrix = np.zeros((len(dicts.keys()),len(total_tokens)))
for j, token in enumerate(total_tokens):
    for i, key in enumerate(dicts.keys()):
        if token in dicts[key]:
            one_hot_matrix[i,j] = 1       

# %%
one_hot_matrix

# %%
pwd

# %%
# os.chdir('/Users/yuhanye/Desktop')
# path_of_the_directory='/Users/yuhanye/Desktop'
binary=pd.DataFrame(one_hot_matrix,columns=list(total_tokens),index=dicts.keys()).transpose()
binary.to_csv('../binary.csv')

binary

# %%

# %% [markdown]
# # Show word distribution

# %%
#Make new column in dataframe "binary" by adding values from all other columns
binary['words'] = binary.sum(axis=1)  
#pay attention, when you run this multiple times, 
#the sum will also add up multiple times
#binary

# %%
distribution = binary['words'].to_frame()   #convert the extracted series to dataframe
distribution = distribution.sort_values(['words'], ascending=[False])
top10=distribution.head(10)  #we can see the top 10 words used in our sample
top10

# %%
top10.transpose()

# %%
top10
top10.index.name = 'counts'
top10.reset_index(inplace=True) #convert index to column 

# %%
top10

# %%
plotdata = pd.DataFrame(
    top10)
# Plot a bar chart
plotdata.plot(kind="bar", ylim=[50, 58], x='counts')
plt.savefig('top10.png', transparent=True)

# %%

# %% [markdown]
#
# # Words summary statistics

# %%
distribution

# %%
distribution.describe().transpose()

# %%

# %% [markdown]
# ## Compute pairwise cosine similarity score

# %%
# it will be a n*n matrix
# n is number of companies

# %%
from sklearn.metrics.pairwise import cosine_similarity
similarity = cosine_similarity(one_hot_matrix)

# %%
df=pd.DataFrame(similarity,columns=dicts.keys(),index=dicts.keys())
#print(df)
df.to_csv('../similarity.csv')       

# %% [markdown]
#

# %%

# %% [markdown]
# ### Change matrix format to same format 
# ### as TNIC score on Hoberg-Philips Library

# %%
dicts_cik = {}  #use a dictionary to store all the word lists of firms 
names_cik = []

#extract CIK code of firms
for key in dicts.keys():
    CIK_code=key.split('_')[0].split('-')[0].lstrip("0")
    #print(CIK_code)
    newname=CIK_code
    names_cik.append(newname) 
    dicts_cik[newname] = myset

# %%
dicts   # check if the renaming is good

# %%
#dicts_cik

# %%
len_keys = len(dicts_cik.keys())
list_keys = list(dicts_cik.keys())
list_company1 = []
list_company2 = []
list_similarity = []
for i in range(len_keys):
    for j in range(i+1,len_keys):
        list_company1.append(list_keys[i])
        list_company2.append(list_keys[j])
        list_similarity.append(similarity[i,j])
pairwise_similarity = {'company1': list_company1, \
                       'company2': list_company2,\
                       'similarity': list_similarity}
pairwise_similarity = pd.DataFrame(pairwise_similarity)

# %%
pairwise_similarity #cik code

# %% [markdown]
# # Map the CIK code with GVKEY

# %%
pwd

# %%
#load the universe mappings of CIK and gvkey codes
columns = ["gvkey", "cik"]
df = pd.read_excel("../Map_gvkey_cik.xlsm", usecols=columns)

#sort dataframe by index in ascending order

# df=df.set_index('cik')
df = df.sort_index(ascending=False)
df.to_csv('../match.csv')  
# map_dict=df.T.to_dict('list')
# map_dict
mapping=df
mapping

# %%
pairwise_similarity1 = pairwise_similarity.rename(columns={'company1': 'cik'})
pairwise_similarity1

# %%
pairwise_similarity1['cik']=pairwise_similarity1['cik'].astype(str).astype(int)

# %%
pairwise_similarity2=pairwise_similarity1.merge(mapping, on='cik', how='inner')
pairwise_similarity2

# %%
pairwise_similarity3 = pairwise_similarity2.rename(columns={'gvkey': 'gvkey1'})
pairwise_similarity3

# %%
pairwise_similarity4 = pairwise_similarity3.drop('cik', axis=1)
pairwise_similarity4

# %%
pairwise_similarity5 = pairwise_similarity4.rename(columns={'company2': 'cik'})
pairwise_similarity5

# %%
pairwise_similarity5['cik']=pairwise_similarity5['cik'].astype(str).astype(int)
pairwise_similarity6=pairwise_similarity5.merge(mapping, on='cik', how='inner')
pairwise_similarity6

# %%
pairwise_similarity7 = pairwise_similarity6.rename(columns={'gvkey': 'gvkey2'})
pairwise_similarity7

# %%
pairwise_similarity8 = pairwise_similarity7.drop('cik', axis=1)
pairwise_similarity8

# %% [markdown]
# ### Compare scores based on sample corpus and total corpus

# %%
df = pd.read_csv("tnic3_data.txt", sep="\t")
#filter, only keep year 2018
df2018=df.loc[df['year'] == 2018]

# %%
df2018.to_csv('df2018.csv') 
df2018

# %%
pairwise_similarity9=pairwise_similarity8.merge(df2018, on=['gvkey1','gvkey2'], how='inner')
pairwise_similarity9.to_csv('pairwise_similarity9.csv') 
pairwise_similarity9

# %%
new_cols = ["year","gvkey1","gvkey2","similarity",'score']
pairwise_similarity10=pairwise_similarity9[new_cols]
pairwise_similarity10

# %%
pairwise_similarity11 = pairwise_similarity10.rename(columns={'similarity': 'score_sample'})
pairwise_similarity11

# %%
pairwise_similarity12 = pairwise_similarity11.rename(columns={'score': 'score_total'})
pairwise_similarity12.to_csv('score_compare.csv') 
pairwise_similarity12

# %%
pairwise_similarity12.describe()

# %%
