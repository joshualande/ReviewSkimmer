
from . import scrape

def ingest_movies(movies, connector, force=False, **kwargs):
    """ Simple function to ingest multiple movies,
        assuming movies is a list of imdb_movie_ids.
    """
    def _scrape():
        movie=scrape.scrape_movie(
            imdb_movie_id=imdb_movie_id,
            **kwargs)        
        return movie


    for i,imdb_movie_id in enumerate(movies):

        print imdb_movie_id,'%s/%s' % (i,len(movies))

        if force:
            print ' -> loading :)'
            movie=_scrape()
            connector.add_movie(movie, force=True)
        else:
            if not connector.in_database(imdb_movie_id):
                print ' -> loading :)'
                movie=_scrape()
                connector.add_movie(movie)
            else:
                print ' -> skipping :('
