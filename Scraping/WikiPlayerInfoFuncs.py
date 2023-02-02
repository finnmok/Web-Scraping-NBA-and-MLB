#!/usr/bin/env python
# coding: utf-8

# # Imports

# In[15]:


import numpy as np
import pandas as pd
import random
from bs4 import BeautifulSoup
import seaborn as sns
import matplotlib.pyplot as plt
import lxml
import requests
import re
import time
from lxml import etree
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from re import match
from fake_useragent import UserAgent
import fake_useragent


# In[16]:


ua = UserAgent()


# In[17]:


import scrapeimports
from scrapeimports import get_rot_prox


# In[18]:


ip_ads = get_rot_prox()


# # Functions for Grabbing

# ### Grab Players and URLS from basketball-reference.com and Wikipedia

# In[19]:


def getPlayers(season_yr):
    
    """
    GRABS ALL PLAYERS IN AN NBA SEASON
    
    input: int season_yr (basketball season year. eg 2021 represents 2020-2021 NBA season)
    output: list[str] of NBA Players (format: 'Lastname,Firstname')
    """
    
    
    #URL for all players in the season
    url = f'https://www.basketball-reference.com/leagues/NBA_{season_yr}_totals.html#totals_stats'
    page = requests.get(url, proxies={'http':random.choice(ip_ads)})
    
    #Grab the list from the website
    soup = BeautifulSoup(page.text, 'lxml')
    all_people = soup.find_all('tr',class_='full_table')
    
    #Go through list and collect each player
    nba_players = []
    for person in all_people:
        nba_players.append(person.find('td')['csk'])
        
    return nba_players


# In[20]:


def getWikiPage(player_list,index):
    
    """
    GET WIKI PAGE FOR PLAYER BASED ON LIST NAME AND INDEX
    
    input: list[str] getPlayers(), int index
    
    output: str Wikipedia URL
    """
    
    #Create Search Using First/Last Name
    global player_first
    player_first = player_list[index].split(',')[1]
    
    global player_last
    player_last = player_list[index].split(',')[0]
    
    search_url = f'https://en.wikipedia.org/w/index.php?search=nba+{player_first}+{player_last}&title=Special:Search&profile=advanced&fulltext=1&ns0=1'
    
    search_page = requests.get(search_url, proxies={'http':random.choice(ip_ads)})
    soup = BeautifulSoup(search_page.text, 'lxml')
    
    for item in soup.find_all('div',class_ = 'mw-search-result-heading'):
        if player_last.lower() in item.find('a')['title'].lower():
            if player_first.lower() in item.find('a')['title'].lower():
                return 'https://en.wikipedia.org/wiki/' + item.find('a')['title'].replace(' ','_')
    
    return 'https://en.wikipedia.org/wiki/' + soup.find_all('div',class_ = 'mw-search-result-heading')[0].find('a')['title'].replace(' ','_')


# ### Collect Personal, Career, History, and Highlight Information

# In[21]:


def getPersonalInfo(url):

    """
    GET INFORMATION FOR A PLAYER
    
    input:  str url (Player URL to scrape)
    
    output: list born, str nationality, str height, str weight
    
    """
    
    #Go to Wiki Page
    wiki_page = requests.get(url, proxies={'http':random.choice(ip_ads)})
    soup = BeautifulSoup(wiki_page.text, 'lxml')
    
    #Go to Wiki Player information box
    #Example box here: 
    infobox = soup.find('table',class_='infobox vcard')
    if infobox == None:
        infobox = soup.find('table',class_='infobox ib-baseball-bio vcard')
    if infobox == None:
        return None, None, None, None
    all_facts = infobox.find_all('tr')
    

    born,nationality,height,weight = None,None,None,None
    
    for item in all_facts:

        #Get Birthday and Birthplace
        if 'Born' in item.get_text():
            txt = item.get_text().replace('\xa0',' ').replace('Born ','')
            pattern = re.compile(r"\(age \d\d\)", re.IGNORECASE)
            born = re.split(pattern,txt)

        #Get Nationality
        if 'Nationality' in item.get_text():
            nationality = item.get_text().replace('\xa0',' ').replace("Nationality",'')

        #Get Listed Height    
        if 'height' in item.get_text():
            height = item.get_text().replace('\xa0',' ').replace('Listed height','')

        #Get Current Weight
        if 'weight' in item.get_text():
            weight = item.get_text().replace('\xa0',' ').replace('Listed weight','')

    return born, nationality, height, weight


# In[22]:


def getCareer(url):
    
    """
    GET INFORMATION FOR A PLAYER
    
    input:  str url (Player URL to scrape)
    
    output: str highschool, str college, str draft, str careeryrs
    
    """
    
    #Go to Wiki Page
    wiki_page = requests.get(url, proxies={'http':random.choice(ip_ads)})
    soup = BeautifulSoup(wiki_page.text, 'lxml')
    
    #Go to Wiki Player information box
    #Example box here: 
    global infobox
    infobox = soup.find('table',class_='infobox vcard')
    if infobox == None:
        infobox = soup.find('table',class_='infobox ib-baseball-bio vcard')
    if infobox == None:
        return None, None, None, None
    all_facts = infobox.find_all('tr')
    
    highschool,college,draft,careeryrs = None,None,None,None
    executed=False
    
    for item in all_facts:

        #Get High School
        if 'High school' in item.get_text():
            highschool = item.get_text().replace('High school','').split('\n')
            highschool = list(filter(lambda x: x!='',highschool))

            if len(highschool) == 1:
                highschool = highschool[0]

        #Get College
        if 'College' in item.get_text() and executed != True:
            college = item.get_text().replace('College','').split('\n')
            college = list(filter(lambda x: x!='',college))
            executed = True
            
            if len(college) == 1:
                college = college[0]

        #Get Draft Information (Year, Round, Pick Overall)        
        if 'NBA draft' in item.get_text():
            draft = item.get_text().replace('NBA draft','').split(' / ')[0]

        #Get Years for their Career
        if 'Playing career' in item.get_text():
            careeryrs = item.get_text().replace("Playing career",'')

    return highschool, college, draft, careeryrs


# In[23]:


def getHistory(url):
   
    """
    GET INFORMATION FOR A PLAYER
    
    input:  str url (Player URL to scrape)
    
    output: list careerhistory
    
    """
    
    #Go to Wiki Page
    wiki_page = requests.get(url, proxies={'http':random.choice(ip_ads)})
    soup = BeautifulSoup(wiki_page.text, 'lxml')
    
    #Go to Wiki Player information box
    #Example box here: 
    infobox = soup.find('table',class_='infobox vcard')
    if infobox == None:
        infobox = soup.find('table',class_='infobox ib-baseball-bio vcard')
    if infobox == None:
        return None, None, None, None
    all_facts = infobox.find_all('tr')
    
    careerhistory = None
    atag,btag = None,None
    
    for item in all_facts:
        

        #Find Indexes to Get Their Career Years
        if "Career history" in item.get_text():
            atag = item

        if "Career highlights and awards" in item.get_text():
            btag = item
        elif "Career NBA  statistics" in item.get_text():
            btag = item

        if (atag != None) and (btag != None):
            a = all_facts.index(atag) + 1
            b = all_facts.index(btag)
            careerhistory = []

            for team in all_facts[a:b]:
                careerhistory.append(team.get_text())
            careerhistory = list(filter(lambda x: x!='\n',careerhistory))

    return careerhistory


# In[24]:


def getHighlights(url):
      

    """
    GET INFORMATION FOR A PLAYER
    
    input:  str url (Player URL to scrape)
    
    output: list highlights
    
    """
    
    #Go to Wiki Page
    wiki_page = requests.get(url, proxies={'http':random.choice(ip_ads)})
    soup = BeautifulSoup(wiki_page.text, 'lxml')
    
    #Go to Wiki Player information box
    #Example box here: 
    infobox = soup.find('table',class_='infobox vcard')
    if infobox == None:
        infobox = soup.find('table',class_='infobox ib-baseball-bio vcard')
    if infobox == None:
        return None, None, None, None
    all_facts = infobox.find_all('tr')
    
    careerhighlights = None
    ctag,dtag,etag = None,None,None
    
    for item in all_facts:

        #Get Information on Career Highlights and Awards
        if "Career highlights and awards" in item.get_text():
            ctag = item
        
        if "Career NBA  statistics" in item.get_text():
            dtag = item
        elif 'at NBA.com' in item.get_text():
            dtag = item
        
        if (ctag != None) and (dtag != None):    
            c = all_facts.index(ctag) + 1
            d = all_facts.index(dtag)
            careerhighlights = []

            for award in all_facts[c:d]:
                careerhighlights.append(award.get_text())
            #highlights = list(filter(lambda x: x!='',careerhighlights[0].split('\n')))
    
    #return highlights      
    return careerhighlights


# # Grabbing Seasons 1999-2023

# In[25]:


#Dataframe to store all information

nba_stats_wiki = pd.DataFrame(columns=["Year","Name","Born","Nationality","Height","Weight",
                                       "Highschool","College","Draft","CareerYears",
                                       "History","Awards"])


# In[26]:


#Grab All Information Using Functions Created Earlier (eg. getPersonalInfo and getHighlights)

import time

def getSeasonData(year):
    startTime = time.time()

    nba_yr = getPlayers(year)
    
    for n in range(len(nba_yr)):
        if n % 10 == 0:
            print(year,": ", n+1, " out of ",len(nba_yr) )
        url = getWikiPage(nba_yr,n)

        born, nationality, height, weight = getPersonalInfo(url)
        highschool, college, draft, careeryrs = getCareer(url)
        careerhistory = getHistory(url)
        highlights = getHighlights(url)

        global nba_stats_wiki
        nba_stats_wiki = nba_stats_wiki.append({"Year":year,"Name":nba_yr[n],"Born":born,"Nationality":nationality,
                                                "Height":height,"Weight":weight,"Highschool":highschool,
                                                "College":college,"Draft":draft,"CareerYears":careeryrs,
                                                "History":careerhistory,"Awards":highlights},ignore_index=True)
    executionTime = (time.time() - startTime)
    print(f'Execution time in seconds for {year} season: ' + str(executionTime))

