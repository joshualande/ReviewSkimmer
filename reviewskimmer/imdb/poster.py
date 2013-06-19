from os.path import expandvars, join, exists
import os
import urllib

def scrape_movie_poster_thumbnail(imdb_movie_id, connector, poster_thumbnail_dir):

    poster_thumbnail_dir = expandvars(poster_thumbnail_dir)
    movie = connector.get_movie(imdb_movie_id)

    imdb_poster_thumbnail_url = movie['rs_imdb_poster_thumbnail_url']
    local_poster_thumbnail_filename=join(poster_thumbnail_dir,'poster_thumbnail_%s.jpg' % imdb_movie_id)

    if imdb_poster_thumbnail_url is None:
        print ' * Skipping thumbnail poster for movie %s b/c it is not on IMDB' % imdb_movie_id
        return None
    else:
        if not exists(local_poster_thumbnail_filename):
            print ' * downloading thumbnail poster %s' % imdb_poster_thumbnail_url
            urllib.urlretrieve(imdb_poster_thumbnail_url,local_poster_thumbnail_filename)
            assert os.stat(local_poster_thumbnail_filename).st_size>0
        else:
            print ' * skipping thumbnail poster %s' % imdb_poster_thumbnail_url
        return local_poster_thumbnail_filename

def injest_movie_poster_into_s3(local_poster_thumbnail_filename,s3):
    basename=os.path.basename(local_poster_thumbnail_filename)

    bucket = s3.get_bucket('reviewskimmer')
    if bucket.lookup(basename) is not None:
        print ' * skipping putting poster in S3 b/c it is already there'
    else:
        print ' * adding movie poster in S3'
        k=bucket.new_key(basename)
        k.set_contents_from_filename(local_poster_thumbnail_filename)
        k.set_acl('public-read')

def scrape_all_movie_posters(connector, s3, poster_thumbnail_dir):

    all_movies=connector.get_all_movies()

    all_imdb_movie_ids=all_movies['rs_imdb_movie_id'].tolist()

    for i,imdb_movie_id in enumerate(all_imdb_movie_ids):
        print '%s: %s/%s' % (imdb_movie_id,i,len(all_imdb_movie_ids))
        local_poster_thumbnail_filename=scrape_movie_poster_thumbnail(imdb_movie_id, connector, poster_thumbnail_dir)
        if local_poster_thumbnail_filename is not None:
            injest_movie_poster_into_s3(local_poster_thumbnail_filename,s3)
        print
