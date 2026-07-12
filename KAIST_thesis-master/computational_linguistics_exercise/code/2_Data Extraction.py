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
# # Data Extraction
# Aug 16, 2022

# %% [markdown]
# Yuhan Ye

# %% [markdown]
# References: 
# https://marcosammon.com/teaching/
# https://sraf.nd.edu/textual-analysis/

# %% [markdown]
# ## Basic tools: Regular Expressions

# %%
#Import Python Packages
import numpy as np
import pandas as pd
import os
import re
from bs4 import BeautifulSoup
import codecs
import csv
import string
import nltk

# %%
nltk.download('punkt') #Now updated for Python 3.X

# %%
test="101000000000100"
#* is greedy, match 0 or more
#*? is reluctant, match zero or 1 (and no more)

# %%
t2=re.findall("1.*1",test)
print(t2)

# %%
t3=re.findall("1.*?1",test) #stops at the 3rd digit and no more
print(t3)

# %%
# using finditer to count words
string="better ingredients, better pizza, papa john's pizza"
nummatch = sum(1 for _ in re.finditer(r'\bpizza\b',
                                      string, flags=re.IGNORECASE))
print(nummatch)

# %% [markdown]
# ## Basic tools:  Wordstems

# %%
# Create p_stemmer of class PorterStemmer
from nltk.stem.porter import PorterStemmer
from nltk.tokenize import RegexpTokenizer

# %%
wordtest="regulation regulatory regulations"
p_stemmer = PorterStemmer()
tokenizer = RegexpTokenizer(r'\w+')

# %%
print("string: ", wordtest)

# %%
tokens = tokenizer.tokenize(wordtest)
print("tokens: ",tokens)

# %%
stemmed_tokens = [p_stemmer.stem(i) for i in tokens]
stemmedcorp = " ".join(stemmed_tokens)
print("stemmed tokens:", stemmedcorp)

# %% [markdown]
# ## Basic tools:  Section Extracts

# %%
#String
ftext="item1a. section to extract item1b section to ignore"

# %%
#What to find
regexTxt = 'item[^a-zA-Z\n]*1a\..*?item[^a-zA-Z\n]*1b'

# %%
#Note, this will include both "bookends"
section = re.findall(regexTxt, ftext, re.IGNORECASE | re.DOTALL)

# %%
section

# %%
#re.findall returns a list -- this converts it to a string
section=section[0]

# %%
section

# %%
#Remove the bookends with re.sub
section = re.sub('item[^a-zA-Z\n]*1a\.',"",section,flags=re.IGNORECASE)
section = re.sub('item[^a-zA-Z\n]*1b',"",section,flags=re.IGNORECASE)
print(section)

# %% [markdown]
# ## Now, let's look into a single 10-K file as an example

# %%
#Regular expressions we will use to identify the business description section
#The rbusiness description section is item 1, so we want to identify the section
#between item 1 and item 1a, or item 1 and item 1b
regexTxt = 'item[^a-zA-Z\n]*1\..*?item[^a-zA-Z\n]*1a'
regexTxt2 = 'item[^a-zA-Z\n]*1\..*?item[^a-zA^Z\n]*1b'
regexTxtEx = 'item[^a-zA-Z\n]*1.*?item[^a-zA^Z\n]*1a'
regexTxtEx2 = 'item[^a-zA-Z\n]*1.*?item[^a-zA^Z\n]*1b'

# %%
#Set parset for beautiful soup
paser = 'html.parser'
#paser = 'html5lib'

# %%
os.chdir('/Users/f0034w9/Dropbox (Dartmouth College)/Exercise Computational Linguistics/data/')

# %%
#Read the Access Power Inc 2021 Q1 10K file
with codecs.open('AccessPower10K.txt', 'r', encoding='utf8', errors='replace') as myfile:
    ftext = myfile.read().replace('\n', ' ')

# %%
#Use beautiful soup to clean the file if it is html
if '<html>' in ftext.lower():
  try:
      ftext = BeautifulSoup(ftext,paser).get_text()
  except Exception as e:
      print(str(e))

# %%
#first pass at identifying the business description section
section = re.findall('item[^a-zA-Z\n]*1.*item[^a-zA-Z\n]*1a',ftext, re.IGNORECASE | re.DOTALL)

# %%
section

# %%
#If that fails, try alternative 1
if len(section) ==0 :   
  section = re.findall(regexTxtEx,ftext, re.IGNORECASE | re.DOTALL)
  #If alternative 1 fails, try alternative 2
  if len(section) ==0 :
      section = re.findall(regexTxtEx2,ftext, re.IGNORECASE | re.DOTALL)
#If it succeeds, extract the business description section
else:
  section = re.findall(regexTxt,ftext, re.IGNORECASE | re.DOTALL)
  if len(section) ==0:
      section = re.findall(regexTxt2,ftext, re.IGNORECASE | re.DOTALL)

# %%
#Sometimes there will be multiple matches
#A common case is one match in the table of contents, and one match
#in the body of the document.
#Taking the longer section avoids the mistaken match to the
#table of contents.
#print('find ' + str(len(section)) + ' instance(s) of item 1A')

result = max(section,key=len)   #take the longer section 
### try to take the 2nd section?

# %%
result #now we see full text of the business description section in 10-K

# %%
#Remove extra spaces and string "table of contents", which may appear
#on every page
result = re.sub(r'table of contents', ' ', result, flags=re.IGNORECASE)
result = result.strip()
result = re.sub('\s+', ' ', result).strip()
# \S+ means “a string of non-whitespace characters” 
# \s+ means “a string of whitespace characters”

# %%
result

# %%
#Write business description section to a text file
with codecs.open('AccessPower10K2.txt', 'w', 'utf-8') as g:
    g.write(result)
    g.close()

# %%

# %% [markdown]
# Now we can see the difference of the two .txt files in the directory

# %%
#\b - word boundary (a word is a sequence of word characters)
#\w - word characters, usually [a-zA-Z0-9_]
# * - match 0 or more of the preceding expression
# This finds any word containing "market"
marketwords = re.findall(r'\b\w*market\w*\b', result, flags=re.IGNORECASE)

# %%
marketwords

# %%
print("Unique Words Containing \"market\"")
print(set(marketwords))

# %%
print("Number of Words Containing \"market\": ",len(marketwords))

# %%
wordcount = len(result.split())
print("Total Number of Words: ",wordcount)

# %% [markdown]
# ## Next, we clean multiple 10-K files at a time

# %%
#Regular expressions we will use to identify the business description section
#The rbusiness description section is item 1, so we want to identify the section
#between item 1 and item 1a, or item 1 and item 1b
regexTxt = 'item[^a-zA-Z\n]*1\..*?item[^a-zA-Z\n]*1a'
regexTxt2 = 'item[^a-zA-Z\n]*1\..*?item[^a-zA^Z\n]*1b'
regexTxtEx = 'item[^a-zA-Z\n]*1.*?item[^a-zA^Z\n]*1a'
regexTxtEx2 = 'item[^a-zA-Z\n]*1.*?item[^a-zA^Z\n]*1b'


# %%
paser = 'html.parser'
# paser = 'html5lib'
max_attempt = 3

# %%
pwd

# %%
os.chdir('./rantexts')

# %%
pwd

# %%
path_of_the_directory='/Users/yuhanye/Desktop/rantexts'

# %%
# print("Files and directories in a specified path:")
# for filename in os.listdir(path_of_the_directory):
#     f = os.path.join(path_of_the_directory,filename)
#     if os.path.isfile(f):
#         print(f)   ##check the file names in the folder to make sure

# %%
path_of_the_directory ='/Users/f0034w9/Dropbox (Dartmouth College)/Exercise Computational Linguistics/data/rantexts'

# %%
######%%%%%%%still need to solve: how to remove tables ########%%%%%%%%%%%
# ######%%%sometimes the code extracts from item10 in tables and end at item 1a in body#%%%%

#load the 10-K files saved in local drive and clean the data
for filename in os.listdir(path_of_the_directory): ###need to set directory 
#     filename ='/Users/yuhanye/Desktop/subtexts/2018\QTR1\20180227_10-K_edgar_data_1196501_0001171843-18-001503_1.txt'                                               ###to the data to run this
    with codecs.open(filename, 'r', encoding='utf8', errors='replace') as myfile:
        ftext = myfile.read().replace('\n', ' ')
    
    
    ####%%%%%%%%%%% remove html part  ####%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    #Use beautiful soup to clean the file if it is html
    if '<html>' in ftext.lower(): 
        try:
            ftext = BeautifulSoup(ftext,paser).get_text()
            #print(ftext)
        except Exception as e:
            print(str(e))
            
    ####%%%%%%% extract business description item 1 ####%%%%%%%%%%%%%%
    
    #first pass at identifying the business description section
    section = re.findall('item[^a-zA-Z\n]*1.*item[^a-zA-Z\n]*1a',ftext, re.IGNORECASE | re.DOTALL)
    #print(section)   
    
    #If that fails, try alternative 1
    if len(section) ==0:
        section = re.findall(regexTxtEx,ftext, re.IGNORECASE | re.DOTALL)
        #If alternative 1 fails, try alternative 2
        if len(section) ==0 :
            section = re.findall(regexTxtEx2,ftext, re.IGNORECASE | re.DOTALL)
    
    #If it succeeds, extract the business description section
    else:
        section = re.findall(regexTxt,ftext, re.IGNORECASE | re.DOTALL)
        if len(section) ==0:
            section = re.findall(regexTxt2,ftext, re.IGNORECASE | re.DOTALL)
    #print(section)
    
    #Sometimes there will be multiple matches
    #A common case is one match in the table of contents, and one match
    #in the body of the document.
    #Taking the longer section avoids the mistaken match to the
    #table of contents.
    
    #print('find ' + str(len(section)) + ' instance(s) of item 1')
    
    result = max(section,key=len, default=None) #Taking the longer section
    #print(result)  #display the content of item 1 business descriptions
    
    #Write business description section to a text file
    # save the extracted item 1 information in the "subtextsout" folder
   
    try:
        if len(result.encode('utf-8')) > 2000:  #only save string that is longer than 2kb
            #show example of .txt that start from item 11 outline
            with codecs.open('./temp_out/'+ filename, 'w', 'utf-8') as g:
                g.write(result)
                g.close()
    except:
        pass 

# %%
# you can see: out of 61 sample files, only 56 are saved and 5 are deleted 
## as they are smaller than 2kb

# %%
