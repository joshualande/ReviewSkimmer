
import BeautifulSoup
import urllib2
import re


def get_soup(url):
    # from here: http://www.markbartlett.org/web-engineering/web-engineering-1/page-scraping-with-urllib2-beautifulsoup
    user_agent='Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.142 Safari/535.19',
    headers = { 'User-Agent' : user_agent }

    temp = urllib2.Request(url, '', headers)
    temp = urllib2.urlopen(temp)
    soup = BeautifulSoup.BeautifulSoup(temp)
    return soup


def scrape(movie):

    url = 'http://www.imdb.com/title/tt1980209/'

    req = urllib2.Request(url, '', headers)
    urlopen = urllib2.urlopen(url)
