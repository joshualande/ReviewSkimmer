from os.path import expandvars, join, exists
import os
import urllib

def scrape_movie_poster(imdb_movie_id, connector, poster_dir, poster_thumbnail_dir, force=False):


    poster_dir = expandvars(poster_dir)
    poster_thumbnail_dir = expandvars(poster_thumbnail_dir)

    movie = connector.get_movie(imdb_movie_id)


    imdb_poster_thumbnail_url = movie['rs_imdb_poster_thumbnail_url']
    local_poster_thumbnail_filename=join(poster_thumbnail_dir,'poster_thumbnail_%s.jpg' % imdb_movie_id)

    if imdb_poster_thumbnail_url is None:
        print ' * Skipping thumbnail poster for movie %s b/c it is not on IMDB' % imdb_movie_id
    elif not exists(local_poster_thumbnail_filename) or force:
        print ' * downloading thumbnail poster %s' % imdb_poster_thumbnail_url
        urllib.urlretrieve(imdb_poster_thumbnail_url,local_poster_thumbnail_filename)
        assert os.stat(local_poster_thumbnail_filename).st_size>0
    else:
        print ' * skipping thumbnail poster %s' % imdb_poster_thumbnail_url

    imdb_poster_url = movie['rs_imdb_poster_url']
    local_poster_filename=join(poster_dir,'poster_%s.jpg' % imdb_movie_id)
    if imdb_poster_url is None:
        print ' * Skipping poster for movie %s b/c it is not on IMDB' % imdb_movie_id
    elif not exists(local_poster_filename) or force:
        print ' * downloading poster %s' % imdb_poster_url
        urllib.urlretrieve(imdb_poster_url, local_poster_filename)
        assert os.stat(local_poster_filename).st_size>0
    else:
        print ' * skipping poster %s' % imdb_poster_url

def scrape_all_movie_posters(connector, poster_dir, poster_thumbnail_dir):

    all_movies=connector.get_all_movies()

    all_imdb_movie_ids=all_movies['rs_imdb_movie_id'].tolist()

    for imdb_movie_id in all_imdb_movie_ids:
        scrape_movie_poster(imdb_movie_id, connector, poster_dir, poster_thumbnail_dir)
