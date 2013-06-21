import traceback
import sys
from . import scrape

def ingest_movies(imdb_movie_ids, connector, 
        nreview_limit=None, force=False, **kwargs):
    """ ingest multiple movies,
        skipping movies which are already in teh
        database, unless nreview_limit is sufficinetly
        large (or None) that more reviews need to be pulled in. """
    def _scrape(imdb_movie_id,force=False):
        try:
            print ' -> loading ',
            movie=scrape.scrape_movie(
                imdb_movie_id=imdb_movie_id,
                nreview_limit=nreview_limit,
                **kwargs)
            print '%s :)' % movie['movie_name']
            connector.add_movie(movie,force=force)
            return movie
        except:
            print 'Error Reading Movie %s, moving on...' % imdb_movie_id
            traceback.print_exc(sys.stdout)

    for i,imdb_movie_id in enumerate(imdb_movie_ids):

        print imdb_movie_id,'%s/%s' % (i,len(imdb_movie_ids))

        if force:
            _scrape(imdb_movie_id,force=True)
        else:
            if not connector.in_database(imdb_movie_id):
                movie=_scrape(imdb_movie_id)
            else:
                nreviews_in_db=connector.get_nreviews(imdb_movie_id)

                if nreview_limit is None:
                    # Default to read all reviews
                    nreviews_in_imdb=scrape.nreviews_on_page(imdb_movie_id, debug=False)
                    if nreviews_in_db < nreviews_in_imdb:
                       _scrape(imdb_movie_id,force=True)
                    else:
                       print ' -> skipping %s :(' % connector.get_movie_name(imdb_movie_id)
                else: # specify # of reviews to read
                    if nreview_limit <= nreviews_in_db:
                        # if enough reviews already in database
                        print ' -> skipping %s :(' % connector.get_movie_name(imdb_movie_id)
                    else:
                        nreviews_in_imdb=scrape.nreviews_on_page(imdb_movie_id, debug=False)
                        if nreviews_in_imdb <= nreviews_in_db:
                            # or the required # of reviews is small
                            print ' -> skipping %s :(' % connector.get_movie_name(imdb_movie_id)
                        else:
                            _scrape(imdb_movie_id,force=True)
        print
