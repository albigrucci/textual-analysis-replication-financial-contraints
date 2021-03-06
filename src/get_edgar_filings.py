# -*- coding: utf-8 -*-
"""
Created on Tue Feb 12 11:03:00 2019

@author: alber
"""


import os, urllib, tempfile, zipfile
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from pathlib import Path
from tqdm import tqdm

path = Path(__file__).parents[1]
os.chdir(path)


#%%

def _url_get(url):
    
    content = None
    content = urllib.request.urlopen(url).read()
    return content

def _fix_url(s):
    """
    
    Fixes  Edgar master file URLs as they miss one part
    Parameters
    ----------
    s : string URL from Edgar masterfile.

    Returns
    -------
    npx_url : string
        Adjusted URL.

    """
    edgar_url = r'https://www.sec.gov/Archives/'
    url = "/".join([s.split("/")[0], s.split("/")[1], s.split("/")[2], ''.join(x for x in s.split("/")[3].split("-"))[:-6], s.split("/")[3]])
    npx_url = urllib.parse.urljoin(edgar_url, url).strip()
    return npx_url


def _get_url2(s):
        
    try:
        soup = BeautifulSoup(urllib.request.urlopen(s), 'html.parser')
        url2 = urllib.parse.urljoin( "/".join(s.split("/")[:-1])+"/", soup.filename.contents[0])
        return url2

    except UnboundLocalError:
        print('catched!')
        return np.nan
    
    except TypeError:
        print('catched!')
        return np.nan
    
    except urllib.error.URLError:
        print('catched URLError!')
        return np.nan
    
    
def get_edgar_filing_urls(filing_type='N-PX', start_date='2018-1-1', end_date='Jan 2019', get_clean_filing=False):
    
    """
    Search the Edgar archive for the all the filing types requested between the dates passed.
    Returns a Pandas Dataframe with Company Names, Filing dates and Urls.
    
    Parameters
    ----------
    filing_type : String, optional
        Type of filing you want to get the url of. The default is 'N-PX'.
    start_date : String, optional
        Starting date for the search, must be parsable by Pandas.to_datetime(). The default is Jan 2018.
    end_date : TYPE, optional
        End date for the search, must be parsable by Pandas.to_datetime(). The default is Jan 2019.
    get_clean_filing : Bool, optional
        Get the html or the clean file if True
    Returns
    -------
    Pandas Dataframe including Company Names, Filing dates and Urls pointing to the filing requested.

    """
    
    edgar_url = r'https://www.sec.gov/Archives/edgar/'
    grep = f'|{filing_type}|'.encode('ASCII')
    quarter_list = (pd.date_range(pd.to_datetime(start_date), 
                   pd.to_datetime(end_date) + pd.offsets.QuarterEnd(1), freq='Q')).tolist()
    quarter_list = [[d.year, d.quarter] for d in quarter_list]   
    matched_lines = []       
    
    
    # Retrieve filing locations from Edgar masterfile
    for y, q in quarter_list:
        complete_url = urllib.parse.urljoin(edgar_url, "full-index/{}/QTR{}/master.zip".format(y, q))
        print(complete_url)
        with tempfile.NamedTemporaryFile(mode='w+b') as tmp:
                    tmp.write(_url_get(complete_url))        
                    with zipfile.ZipFile(tmp).open("master.idx") as f:
                        for line in f: # read file line by line
                            if grep in line: # search for string in each line
                                matched_lines.append(line) # keep a list of matched lines

    # Create dataframe and URL locations
    df_index = pd.DataFrame([sub.decode().split("|") for sub in matched_lines],
                            columns=['CIK', 'Company Name', 'Form Type', 'Date Filed', 'Filename'])
    df_index['URL'] = df_index['Filename'].apply(_fix_url)
    df_index['Date Filed'] = pd.to_datetime(df_index['Date Filed'])
    
    if get_clean_filing:
        print('Warning: this might take long.. multithreading to be implemented')
        df_index['Clean URL'] = df_index['URL'].apply(_get_url2)
        
    mask = (pd.to_datetime(start_date) <= df_index['Date Filed']) & (df_index['Date Filed'] <= pd.to_datetime(end_date))

    return df_index[mask]    
    
def download_filings(df, path_files='edgar_filings'): 
    """
    Given the Dataframe from get_edgar_filing_urls(), downloads the filings in path_files
    Parameters
    ----------
    df : Pandas Dataframe
        Output Dataframe from get_edgar_filing_urls().
    path_files : string, optional
        Path to download the files to. The default is 'edgar_filings'.

    Returns
    -------
    None.

    """
    
    
    for i, row in tqdm(df.iterrows()):
        filename = "_".join([row['CIK'], row['Form Type'], row['Date Filed'].strftime(format="%Y%m%d")])
        filename += Path(row.URL.strip()).suffix
        path_filename = Path(path_files) / filename
        urllib.request.urlretrieve(row['URL'], path_filename)
    return None




#%%

if __name__ == '__main__':
    
    df = get_edgar_filing_urls(filing_type='10-K')
    download_filings(df, path_files='edgar_filings')

        
