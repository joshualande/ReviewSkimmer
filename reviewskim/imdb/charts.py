from collections import OrderedDict
import re

from reviewskim.utils.strings import clean_unicode
from reviewskim.utils.web import get_soup

def _get_movie_list(url):

    soup = get_soup(url)
    votes=soup.find(text='Votes')
    current_movie=votes.next.next.next.next.next.next.next.next.next.next.next

    movies=[current_movie]
    for i in range(99):
        current_movie=current_movie.next.next.next.next.next.next.next.next.next.next.next.next.next.next.next.next
        movies.append(current_movie)

    ret=OrderedDict()
    for movie in movies:
        m=re.match('/title/tt(\d+)/',movie['href'])
        imdb_movie_id=int(m.groups()[0])
        movie_title=clean_unicode(movie.next)
        ret[imdb_movie_id]=movie_title

    return ret

def get_top_100():
    return _get_movie_list(url='http://www.imdb.com/chart/top')

def get_bottom_100():
    return _get_movie_list(url='http://www.imdb.com/chart/bottom')
