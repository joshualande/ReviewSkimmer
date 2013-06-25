#!/usr/bin/env python
import os
import argparse

from flask import Flask
from flask import render_template
from flask import request

from reviewskimmer.analysis.summarize import ReviewSummarizer

from helpers import get_poster_thumbnail,get_top_grossing_dict


app = Flask(__name__)
app.config.from_envvar('REVIEWSKIMMER_CONFIG')


from reviewskimmer.database.dbconnect import IMDBDatabaseConnector
db = app.config['DB']
connector=IMDBDatabaseConnector(db)

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('local',default=False, action='store_true')
parser.add_argument('debug',default=False, action='store_true')
args = parser.parse_args()


app.debug=True

@app.route('/')
def index():
    top_grossing = get_top_grossing_dict(connector,
            years=range(2013,1999,-1),
            movies_per_year=4)
    return render_template('index.html', top_grossing=top_grossing)

@app.route('/search.html')
def search():
    movie_name = request.args.get('q', None)

    imdb_movie_id=connector.get_newest_imdb_movie_id(movie_name)

    if imdb_movie_id is not None:
        thumbnail_url_html=get_poster_thumbnail(imdb_movie_id,connector)

        summarizer=ReviewSummarizer(connector=connector,
            imdb_movie_id=imdb_movie_id, num_occurances=5)

        return render_template('search.html', 
                top_quotes=summarizer.get_top_quotes(),
                top_occurances=summarizer.get_top_occurances(),
                debug=args.debug,
                movie_name=movie_name,
                number_reviews=len(summarizer.all_reviews),
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
    top=top.tolist()[:30]
    bottom=connector.get_bottom_100_all_time()['rs_imdb_movie_id']
    bottom=bottom.tolist()[:30]

    top=[get_poster_thumbnail(i,connector) for i in top]
    bottom=[get_poster_thumbnail(i,connector) for i in bottom]

    print 'top',top
    print 'bottom',bottom

    return render_template('charts.html',
            top=top,
            bottom=bottom)


@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/contact.html')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':

    import argparse


    if args.local:
        app.run() 
    else:
        # works remotely
        app.run(host='0.0.0.0',port=80)
