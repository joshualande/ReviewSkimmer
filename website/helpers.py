import urllib
from collections import OrderedDict

def get_search_url(imdb_movie_id,connector):
    movie_name=connector.get_movie_name(imdb_movie_id)
    url='/search.html?q='+urllib.quote(movie_name)
    return url

def get_poster_thumbnail(imdb_movie_id,connector):
    path='https://s3-us-west-2.amazonaws.com/reviewskimmer/poster_thumbnail_%d.jpg' % imdb_movie_id
    url=get_search_url(imdb_movie_id,connector)
    return '<a href="%s"><img class="img-polaroid" src="%s"></a>' % (url,path)

def get_top_grossing_dict(connector, years, movies_per_year):
    top_grossing=connector.get_top_grossing()
    movies=OrderedDict()
    for year in years:
        temp=top_grossing[top_grossing['rs_year']==year]
        temp.sort('rs_ranking')
        m=temp['rs_imdb_movie_id'][:4].tolist()
        movies[year]=[get_poster_thumbnail(i,connector) for i in m]
    return movies
