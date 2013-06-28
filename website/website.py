#!/usr/bin/env python
from os.path import expandvars
import sys
import traceback
import os
import argparse

from flask import Flask
from flask import render_template
from flask import request

from reviewskimmer.analysis.summarize import ReviewSummarizer,CachedReviewSummarizer
from reviewskimmer.imdb import scrape 
from reviewskimmer.imdb.poster import scrape_movie_poster_thumbnail,injest_movie_poster_into_s3

from helpers import get_poster_thumbnail,get_top_grossing_dict



app = Flask(__name__)
app.config.from_envvar('REVIEWSKIMMER_CONFIG')


from reviewskimmer.database.dbconnect import IMDBDatabaseConnector
db = app.config['DB']
connector=IMDBDatabaseConnector(db)

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--amazon',default=False, action='store_true')
parser.add_argument('--debug',default=False, action='store_true')
parser.add_argument('--nocache',default=False, action='store_true')
args = parser.parse_args()

app.debug=True

@app.route('/')
def index():
    top_grossing = get_top_grossing_dict(connector,
            years=range(2013,2005,-1),
            movies_per_year=4)
    return render_template('index.html', top_grossing=top_grossing)

@app.route('/search.html')
def search():
    movie_name = request.args.get('q', None)

    imdb_movie_id=connector.get_newest_imdb_movie_id(movie_name)

    if imdb_movie_id is not None:
        thumbnail_url_html=get_poster_thumbnail(imdb_movie_id,connector)

        ob=ReviewSummarizer if args.nocache else CachedReviewSummarizer
        summarizer=ob(connector=connector,
            imdb_movie_id=imdb_movie_id, num_occurances=5)

        top_quotes=summarizer.get_top_quotes()
        for quote in top_quotes:
            word=quote['word']

            if quote == top_quotes[0]:
                print quote

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
            quote['first_quote_html'] = first_quote_html


        return render_template('search.html', 
                top_quotes=top_quotes,
                top_word_occurances=summarizer.get_top_word_occurances(),
                debug=args.debug,
                movie_name=movie_name,
                number_reviews=summarizer.get_nreviews(),
                imdb_movie_id=imdb_movie_id,
                thumbnail_url_html=thumbnail_url_html)

    else:
        return render_template('search.html', 
                movie_name=movie_name,
                imdb_movie_id=imdb_movie_id,
                )

@app.route('/charts.html')
def charts():

    top=connector.get_top_100_all_time()['rs_imdb_movie_id']
    top=top.tolist()[:10]
    bottom=connector.get_bottom_100_all_time()['rs_imdb_movie_id']
    bottom=bottom.tolist()[:10]

    top=[get_poster_thumbnail(i,connector) for i in top]
    bottom=[get_poster_thumbnail(i,connector) for i in bottom]

    return render_template('charts.html', top=top, bottom=bottom)


@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/presentation.html')
def presentation():
    return render_template('presentation.html')

@app.route('/secret.html')
def secret():
    user_request = request.args.get('q', None)
    
    if user_request == 'cachepopular':

        message='<div class="alert alert-success">The popular movies were cached!</div>'
    elif user_request == 'clearcache':

        connector.delete_quotes_cache()

        message='<div class="alert alert-success">The cache was cleared!<div>'
    elif user_request == 'injestmovie':
        try:
            imdb_movie_id=int(request.args.get('imdb_movie_id', None))

            if connector.in_database(imdb_movie_id):
                raise Exception("Movie already in the database")
            movie=scrape.scrape_movie(imdb_movie_id=imdb_movie_id)
            message='<div class="alert alert-success">The movie "%s" was injested!</div>' % movie['movie_name']
            connector.add_movie(movie)
        except Exception, ex:
            traceback.print_exc(sys.stdout)
            message='<div class="alert alert-error">Unable to injest movie! %s</div>' % ex
    elif user_request == 'getposter':
        try:
            import boto
            s3 = boto.connect_s3()
            imdb_movie_id=int(request.args.get('imdb_movie_id', None))
            poster_thumbnail_dir=expandvars('$REVIEWSKIMMER_MEDIA_DIR/posters_thumbnails')
            local_poster_thumbnail_filename=scrape_movie_poster_thumbnail(imdb_movie_id, connector, poster_thumbnail_dir)
            if local_poster_thumbnail_filename is not None:
                injest_movie_poster_into_s3(local_poster_thumbnail_filename,s3)
            message='<div class="alert alert-success">Injested poster for movie "%s"</div>' % imdb_movie_id
        except Exception, ex:
            traceback.print_exc(sys.stdout)
            message='<div class="alert alert-error">Unable to injest poster! %s</div>' % ex

    elif user_request is None:

        message=None
    else:
        raise Exception('Unrecognized request "%s"' % user_request)

    return render_template('secret.html',message=message)


if __name__ == '__main__':

    import argparse


    if args.amazon:
        app.run(host='0.0.0.0',port=80)
    else:
        app.run() 
