
from . import scrape

def ingest_movies(imdb_movie_ids, connector, 
        nreview_limit=None, force=False, **kwargs):
    """ ingest multiple movies,
        skipping movies which are already in teh
        database, unless nreview_limit is sufficinetly
        large (or None) that more reviews need to be pulled in. """
    def _scrape(force=False):
        print ' -> loading ',
        movie=scrape.scrape_movie(
            imdb_movie_id=imdb_movie_id,
            nreview_limit=nreview_limit,
            **kwargs)
        print '%s :)' % movie['movie_name']
        connector.add_movie(movie,force=force)
        return movie


    for i,imdb_movie_id in enumerate(imdb_movie_ids):

        print imdb_movie_id,'%s/%s' % (i,len(imdb_movie_ids))

        if force:
            _scrape(force=True)
        else:
            if not connector.in_database(imdb_movie_id):
                movie=_scrape()
            else:
                nreviews_in_db=connector.get_nreviews(imdb_movie_id)
                nreviews_in_imdb=scrape.nreviews_on_page(imdb_movie_id, debug=False)

                if nreview_limit is None:
                    # Default to read all reviews
                    if nreviews_in_db < nreviews_in_imdb:
                       _scrape(force=True)
                    else:
                       print ' -> skipping %s :(' % connector.get_movie_name(imdb_movie_id)
                else: # specify # of reviews to read
                    if (nreviews_in_imdb <= nreviews_in_db) or \
                        (nreview_limit <= nreviews_in_db):
                        # if enough reviews already in database
                        # or the required # of reviews is small
                        print ' -> skipping %s :(' % connector.get_movie_name(imdb_movie_id)
                    else:
                        _scrape(force=True)
        print
