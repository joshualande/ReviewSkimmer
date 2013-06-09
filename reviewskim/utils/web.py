import re

import urlparse
from bs4 import BeautifulSoup
import urllib2

from . strings import clean_unicode



def url_join(path, *args):     
    return '/'.join([path.rstrip('/')] + list(args)) 

def get_soup(url, no_user_agent=False):
    """ Code inspired by:
            http://www.markbartlett.org/web-engineering/web-engineering-1/page-scraping-with-urllib2-beautifulsoup
    """

    if no_user_agent:
        temp = urllib2.Request(url)
    else:
        # taken from http://www.whatsmyuseragent.com/
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36'


        headers = { 'User-Agent' : user_agent }

        temp = urllib2.Request(url, '', headers)

    try:
        temp = urllib2.urlopen(temp)
    except urllib2.HTTPError, error:
        contents = error.read()
        print contents
        raise error

    soup = BeautifulSoup(temp)

    return soup

def get_html_text(review_text):
    """ This function takes in a (part of an)
        HTML document, extracts the text out of it

        The review has a bunch of text + html formatting.
        Clean the review up by pulling out all the text,
        adding missing periods, and 
    """
    text=review_text.findAll(text=True)

    # remove garbage (new lines, etc ...) from beginning and end of text
    text=[i.strip() for i in text]

    # add in missing exclamations
    text=[i if i[-1] in ['.','!','?'] else i+'.' for i in text]

    # join all the text with spaces
    text=' '.join(text)

    # remove new lines
    text=text.replace('\n', ' ')

    # convert multiple spaces to single spaces
    text=re.sub('\s+',' ',text)
    return clean_unicode(text)

