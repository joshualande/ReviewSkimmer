#!/usr/bin/env python
import os
from os.path import join

from flask import Flask
from flask import render_template
from flask import request


app = Flask(__name__)
app.config.from_envvar('REVIEWSKIM_SETTINGS')


from reviewskim.database.dbconnect import IMDBDatabaseConnector
db = app.config['DB']
connector=IMDBDatabaseConnector(db)

app.debug=True

reviewskim_media_dir=app.config['REVIEWSKIM_MEDIA_DIR']

def get_poster_thumbnail(imdb_movie_id):
    path='https://s3-us-west-2.amazonaws.com/reviewskimmer/poster_thumbnail_%d.jpg' % imdb_movie_id
    return path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search.html')
def search():
    movie_name = request.args.get('q', None)

    imdb_movie_id=connector.get_imdb_movie_id(movie_name)
    if imdb_movie_id is not None:
        thumbnail_url=get_poster_thumbnail(imdb_movie_id)
    else:
        thumbnail_url=None

    return render_template('search.html', 
            movie_name=movie_name,
            imdb_movie_id=imdb_movie_id,
            thumbnail_url=thumbnail_url)

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/contact.html')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run()
