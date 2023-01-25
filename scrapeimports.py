# -*- coding: utf-8 -*-
"""
Created on Sun Jan  1 14:35:29 2023

@author: finnr
"""
import random
from bs4 import BeautifulSoup
import lxml
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fake_useragent import UserAgent
import fake_useragent

ua = UserAgent()

def get_rot_prox():
    
    #Get Proxies
    full_url = 'https://free-proxy-list.net/'
    
    #Access Page
    headers = {"User-Agent": ua.random,
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
               "Accept-Language": "en-US,en;q=0.7",
               "Accept-Encoding": "gzip, deflate",
               "Referer": "https://www.google.com/",
               "DNT": "1", "Connection": "close", "Upgrade-Insecure-Requests": "1"}

    page = requests.get(full_url, headers=headers)
    time.sleep(5)
    
    #Get Page Text
    soup = BeautifulSoup(page.text, 'lxml') 
    
    global ip_ads
    ip_ads = list()

    for item in soup.find_all("tr"):
        
        it = str(item.find('td')).replace('<td>','').replace('</td>','').replace("None",'')
    
        if it == '':
            continue
        if '-' in it:
            continue
        if 'class' in it:
            continue
        if 'title' in it:
            continue
        else:
            ip_ads.append(it)
            
    return ip_ads
            
            
get_rot_prox()