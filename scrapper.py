import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

nbaBoxUrl = 'https://www.basketball-reference.com/boxscores/'

boxScoreClass = 'stats_table'

def getBoxScoreLinks():
    page = requests.get(nbaBoxUrl)
    soup = BeautifulSoup(page.content, 'html.parser')
    gameLinks = []
    data = soup.findAll('td', {'class': 'right gamelink'})
    for div in data:
        links = div.findAll('a')
        for a in links:
            gameLinks.append(a['href'])
    return gameLinks

def getBoxScoreTeams(soup):
    data = soup.find('div', {'class': 'scorebox'})
    substring = 'teams'
    teams = []
    team = {'name':'', 'abrv':'', 'table' : '', 'opponent' : ''}
    for a in data.find_all('a', href=True):
        if substring in a['href']:
            new = team.copy()
            new['name'] = a.getText()
            new['abrv'] = a['href'].split('/')[2]
            teams.append(new)
    #set opponent
    for team in teams:
        for opponent in teams:
            if team['name'] != opponent['name']:
                team['opponent'] = opponent['name']
    return teams

def getGameDate(soup):
    for div in soup.find_all('div', {'class': 'scorebox_meta'}):
        childdiv = div.find('div')
        #format date
        datetime_object = datetime.strptime(childdiv.string, '%I:%M %p, %B %d, %Y')
        return datetime_object.strftime("%m/%d/%Y")

def getHomeTeam(url):
    homeTeam = url.split('/')[4]
    homeTeam = re.findall("[a-zA-Z]+", homeTeam)[0]
    return homeTeam

def getGameId(url):
    gameId = url.split('/')[4]
    gameId = re.findall("\d+", gameId)[0]
    return gameId

def getFileName(url):
    fileName = url.split('/')[4]
    fileName = fileName.rsplit( ".", 1 )[ 0 ]
    return fileName

def removeSummaryRows(df):
    df = df[df.Starters != 'Team Totals']
    df = df[df.Starters != 'Reserves']
    return df

def updateColumns(df):
    df = df.drop('FG%', 1)
    #rename
    df = df.rename({'Starters': 'Players'}, axis=1)  
    return df

def replaceDNP(df):
    df = df.replace('Did Not Play', 0)
    return df

def orderColumns(df):
    df = df[['Players', 'Team', 'Opponent', 'GameID', 'Date', 'Court', 'MP', 'FG', 'FGA', '3P', '3PA', 'FT', 'FTA', 'ORB', 'DRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']]
    return df

def getGameBoxScore():
    url = 'https://www.basketball-reference.com/boxscores/202110250LAC.html'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    #get teams
    teams = getBoxScoreTeams(soup)
    gameDate = getGameDate(soup)
    homeTeam = getHomeTeam(url)
    gameId = getGameId(url)
    fileName = getFileName(url)

    #Remove extra header
    for div in soup.find_all("tr", {'class':'over_header'}): 
        div.decompose()

    masterDf = pd.DataFrame()
    for team in teams:
        team['table'] = soup.find_all("table", {'id':'box-'+ team['abrv'] +'-game-basic'})
        #format dataframe
        df = pd.read_html(str(team['table']))[0]

        #constants
        df['Team'] = team['name']
        df['Opponent'] = team['opponent']
        df['Date'] = gameDate
        df['GameID'] = gameId


        if team['abrv'] == homeTeam:
            df['Court'] = 'Home'
        else:
            df['Court'] = 'Away'

        masterDf = pd.concat([masterDf, df], ignore_index=True)
        #master_df = master_df.append(df,ignore_index=True)

    #format dataframe
    masterDf = removeSummaryRows(masterDf)
    masterDf = replaceDNP(masterDf)
    masterDf = updateColumns(masterDf)
    masterDf = orderColumns(masterDf)
    print(masterDf.head(2))
    masterDf.to_csv(fileName + '.csv', index=False, sep='\t', encoding='utf-8')

    #add footer row
    with open(fileName + '.csv','a') as fd:
        fd.write('\n')
        fd.write('Sample Link:' + '\t' + url)
    

#gameLinks = getBoxScoreLinks()
getGameBoxScore()
