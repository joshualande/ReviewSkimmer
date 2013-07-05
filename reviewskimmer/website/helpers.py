try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict
import traceback
import sys
from os.path import expandvars
import urllib
from reviewskimmer.imdb.poster import scrape_movie_poster_thumbnail,injest_movie_poster_into_s3
from reviewskimmer.imdb import scrape

def get_search_url(imdb_movie_id,connector):
    movie_name=connector.get_movie_name(imdb_movie_id)
    url='/search.html?q='+urllib.quote(movie_name)
    return url

def get_poster_thumbnail(imdb_movie_id,connector):
    path='https://s3-us-west-2.amazonaws.com/reviewskimmer/poster_thumbnail_%d.jpg' % imdb_movie_id
    url=get_search_url(imdb_movie_id,connector)
    return '<a href="%s"><img class="img-polaroid" src="%s"></a>' % (url,path)

def get_top_grossing_imdb_movie_ids(connector, years, movies_per_year):
    top_grossing=connector.get_top_grossing()
    movies=OrderedDict()
    for year in years:
        temp=top_grossing[top_grossing['rs_year']==year]
        temp.sort('rs_ranking')
        movies[year]=temp['rs_imdb_movie_id'][:4].tolist()
    return movies

def get_top_grossing_thumbnails(connector, years, movies_per_year):
    movies=get_top_grossing_imdb_movie_ids(connector, years, movies_per_year)
    for year in movies.keys():
        movies[year]=[get_poster_thumbnail(i,connector) for i in movies[year]]
    return movies

def format_quotes(top_quotes):

    formatted_quotes=[]

    for quote in top_quotes:
        word=quote['word']

        formatted_more_quotes = ['&quot%s&quot &#8212; <a href=&quot%s&quot>%s</a>' % \
                (i['text'].replace(word,'<a><b>%s</b></a>' % word).replace('"','&quot'),
                    i['reviewer_url'],
                    i['reviewer']) \
                for i in quote['more_quotes']]

        content = '<br><br>'.join(formatted_more_quotes)

        first_quote = quote['first_quote']
        first_quote_html = first_quote['text']
        first_quote_html = '<span style="font-size:24px">"%s"</span>&#8212;<a href="%s">%s</a>' % (first_quote_html,first_quote['reviewer_url'],first_quote['reviewer'])
        first_quote_html = first_quote_html.replace(word,
                """<a id="hover" 
                     rel="popover" 
                     data-content="%s" 
                     data-original-title="More <b>%s</b> Reviews">
                     <b>%s</b></a>""" % (content,word,word))
        formatted_quotes.append(first_quote_html)
    return formatted_quotes

def try_load_poster(imdb_movie_id,connector):
    try:
        import boto
        s3 = boto.connect_s3()
        poster_thumbnail_dir=expandvars('$REVIEWSKIMMER_MEDIA_DIR/posters_thumbnails')
        local_poster_thumbnail_filename=scrape_movie_poster_thumbnail(imdb_movie_id, connector, poster_thumbnail_dir)
        if local_poster_thumbnail_filename is not None:
            injest_movie_poster_into_s3(local_poster_thumbnail_filename,s3)
        message='<div class="alert alert-success">Injested poster for movie "%s"</div>' % imdb_movie_id
    except Exception, ex:
        traceback.print_exc(sys.stdout)
        message='<div class="alert alert-error">Unable to injest poster! %s</div>' % ex
    return message


def try_injest_movie(imdb_movie_id,connector):
    try:
        if connector.in_database(imdb_movie_id):
            raise Exception("Movie already in the database")
        movie=scrape.scrape_movie(imdb_movie_id=imdb_movie_id)
        connector.add_movie(movie)
        message='<div class="alert alert-success">The movie "%s" was injested!</div>' % movie['movie_name']
    except Exception, ex:
        traceback.print_exc(sys.stdout)
        message='<div class="alert alert-error">Unable to injest poster! %s</div>' % ex
    return message

def get_top_for_website(connector):
    top=connector.get_top_100_all_time()['rs_imdb_movie_id']
    top=top.tolist()[:10]
    return top

def get_bottom_for_website(connector):
    bottom=connector.get_bottom_100_all_time()['rs_imdb_movie_id']
    bottom=bottom.tolist()[:10]
    return bottom
