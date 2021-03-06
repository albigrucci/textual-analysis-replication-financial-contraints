# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""


import os, sys, urllib, re, string, nltk
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from html.parser import HTMLParser
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import CountVectorizer


path = Path(__file__).parents[1]
os.chdir(path)

sys.path.append((path / 'src').as_posix())

import get_edgar_filings as gef


#%%

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)
    def handle_entityref(self, name):
         self.fed.append('&[^\s]*;' % name)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def cleanhtml(raw_html):
    cleanr =re.compile('<.*?>')
    cleanr1 = re.compile('&[^\s]*;')
    cleantext = re.sub(cleanr,'', raw_html)
    clean = re.sub(cleanr1,'',cleantext)
    return clean

# This method removes regular and broken html tags e.g. single tags with no corresponding 
# closing tags as well as html entities e.g. expressions of the from &****; 

def process_line(html):
    b = strip_tags(html)
    if b!='' and not b.isspace():
        return b
    else:
        return cleanhtml(html)
    
def get_mda_output(url):
    html = False
    mda_output = ''
    with urllib.request.urlopen(url) as f1:
        for num, line in enumerate(f1, 0):
                if num < 300:
                    if b'<html>' in line.lower():
                        html = True
                        #print('it is html')
                else:
                    if html:
                        m = re.search(b'>Liquidity',line)
                        #print(num)
                        if m:
                            while True:
                                try:
                                    a = next(f1)
                                except StopIteration:
                                    break
                                if re.search(b'>item',a.lower()):
                                    break
                                b = process_line(a.decode("utf-8"))
                                if not b.isspace():
                                    mda_output += b
                                      
                            break   
                    else:
                        #This code is for non-html
                        m = re.match(b'^(\s*)liquidity and capital resources(\s*)$',line.lower())
                        if m:
                            while True:
                                try:
                                    a = next(f1)
                                except StopIteration:
                                    break
                                if re.search(b'^(\s*)item(\s*)[7-8]',a.lower()):
                                    break
                                mda_output += cleanhtml(a.decode("utf-8"))
                            break
    return mda_output
    
def stem_text(text):
    stemmer = SnowballStemmer('english')
    j = text.split()
    stemmed = [stemmer.stem(word) for word in j]
    return ' '.join(stemmed)

def get_dictionary(path):
    texts = pd.read_csv(path, header=None)[0].to_list()  
    dictionary = {}
    for text in texts:
        text = stem_text(text)
        if text not in dictionary:
            dictionary[text] = len(dictionary)
    return dictionary


def extract_bow_feature_vector(text, dictionary):

    feature_vector = np.zeros(len(dictionary))
    for relevant_text in dictionary:
        feature_vector[dictionary[relevant_text]] = text.count(relevant_text)
    return feature_vector 

def filings_from_CIKs(path, filing_type, start_date, end_date):
    ciks = pd.read_csv(path).CIK.astype(str).to_list()
    index = gef.get_edgar_filing_urls(filing_type=filing_type, start_date=start_date, end_date=end_date)
    return index[index.CIK.isin(ciks)]

#%%

if __name__ == '__main__':
     
    index = filings_from_CIKs('inputs/CIKs.csv', '10-K', '2000-1-1', 'Jan 2020')
    stemmed_english_words = set(stem_text(
                                " ".join(nltk.corpus.words.words()).lower()
                                ).split())


    
    equity_focused = get_dictionary('inputs/equity_focused_list.csv')
    debt_focused = get_dictionary('inputs/debt_focused_list.csv')
    delay = get_dictionary('inputs/delay.csv')

    cols_equity = [f'equity_feature_{i}' for i in range(len(equity_focused))]
    cols_debt = [f'debt_feature_{i}' for i in range(len(debt_focused))]
    cols_delay = [f'delay_feature_{i}' for i in range(len(delay))]


    rows = []
    for i, row in tqdm(index.iterrows()):
        try:
            mda = get_mda_output(row['URL']).lower()
        except:
            print('Unreadable: Skipped')
            continue
        if mda == '':
            print('Unreadable: Skipped')
            continue
        mda = stem_text(" ".join(w for w in nltk.wordpunct_tokenize(mda)))  
        
        row_dict = row.to_dict()
        row_dict.update(dict(zip(cols_equity, extract_bow_feature_vector(mda, equity_focused))))
        row_dict.update(dict(zip(cols_debt, extract_bow_feature_vector(mda, debt_focused))))
        row_dict.update(dict(zip(cols_delay, extract_bow_feature_vector(mda, delay))))
        rows.append(row_dict)


    df = pd.DataFrame(rows)
    df.to_pickle('edgar_data.pkl')  

#%%

  