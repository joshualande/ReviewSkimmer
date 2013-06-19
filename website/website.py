#!/usr/bin/env python
import os
from os.path import join

from flask import Flask
from flask import render_template
from flask import request
from reviewskimmer.analysis.summarize import summarize_reviews


app = Flask(__name__)
app.config.from_envvar('REVIEWSKIMMER_CONFIG')


from reviewskimmer.database.dbconnect import IMDBDatabaseConnector
db = app.config['DB']
connector=IMDBDatabaseConnector(db)

most_informative_words = app.config['MOST_INFORMATIVE_WORDS']

app.debug=True

def get_poster_thumbnail(imdb_movie_id):
    path='https://s3-us-west-2.amazonaws.com/reviewskimmer/poster_thumbnail_%d.jpg' % imdb_movie_id
    return '<img src="%s">' % path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search.html')
def search():
    movie_name = request.args.get('q', None)

    imdb_movie_id=connector.get_newest_imdb_movie_id(movie_name)

    if imdb_movie_id is not None:
        thumbnail_url_html=get_poster_thumbnail(imdb_movie_id)

        summary=summarize_reviews(connector=connector,
                imdb_movie_id=imdb_movie_id,
                most_informative_words=most_informative_words)
        print summary

        return render_template('search.html', 
                summary=summary,
                movie_name=movie_name,
                imdb_movie_id=imdb_movie_id,
                thumbnail_url_html=thumbnail_url_html)

    else:
        return render_template('search.html', 
                movie_name=movie_name,
                imdb_movie_id=imdb_movie_id,
                )

@app.route('/charts.html')
def about():
    return render_template('charts.html')


@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/contact.html')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run()
