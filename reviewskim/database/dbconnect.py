from datetime import datetime 
import urllib
import getpass
import MySQLdb

class IMDBDatabaseConnector(object):
    """ Class to interface with the movie database. """

    def __init__(self, db):
        self.db=db
        self.cursor=self.db.cursor()

    def delete_db(self):
        """ Delete all tables from the IMDB databse. """
        db=self.db
        db.query("DROP TABLE rs_movies")
        db.query("DROP TABLE rs_reviews")

    def create_movie_schema(self):
        """ Create the schema for the IMDB reviews databse.
        """
        db=self.db
        db.query("""
            CREATE TABLE rs_movies (
            rs_imdb_movie_id INT NOT NULL PRIMARY KEY,
            rs_movie_name TEXT NOT NULL CHARACTER SET utf8,
            rs_budget INT,
            rs_gross INT,
            rs_imdb_movie_url TEXT NOT NULL,
            rs_imdb_poster_url TEXT NOT NULL,
            rs_imdb_poster_thumbnail_url TEXT NOT NULL,
            rs_db_insert_time DATETIME NOT NULL,
            rs_release_date DATE NOT NULL,
            rs_imdb_description TEXT NOT NULL
            );
        """);


        db.query("""
            CREATE TABLE rs_reviews (
            rs_imdb_movie_id INT NOT NULL,
            rs_reviwer TEXT,
            rs_review_movie_score INT,
            rs_review_date DATE NOT NULL,
            rs_num_likes INT,
            rs_num_dislikes INT,
            rs_review_spoilers BOOL NOT NULL,
            rs_imdb_review_ranking INT,
            rs_review_place TEXT,
            rs_review_url TEXT NOT NULL,
            rs_review_text TEXT CHARACTER SET utf8
            );
        """)

    def _add_movie_description(self,movie):
        """ Add in the IMDB descriptions of the movie. """
        c=self.cursor

        rs_imdb_movie_id=movie['imdb_movie_id']
        rs_movie_name=movie['movie_name']
        rs_db_insert_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rs_budget=movie['budget']
        rs_gross=movie['gross']
        rs_release_date=movie['release_date'].strftime('%Y-%m-%d')
        rs_imdb_movie_url=urllib.unquote(movie['imdb_movie_url'])
        rs_imdb_poster_url=urllib.unquote(movie['imdb_poster_url'])
        rs_imdb_poster_thumbnail_url=urllib.unquote(movie['imdb_poster_thumbnail_url'])
        rs_imdb_description=movie['imdb_description']

        c.execute("""
            INSERT INTO rs_movies
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", 
            (rs_imdb_movie_id, rs_movie_name, rs_budget,
            rs_gross,  rs_imdb_movie_url, rs_imdb_poster_url, rs_imdb_poster_thumbnail_url,

            rs_db_insert_time,
            rs_release_date, rs_imdb_description,)
        )

        pass

    def add_movie(self,movie):
	""" Take in a movie dictionary skimmed from
	    reviewskim.imdb.scrape.scrape_movie and put the review
	    into the database. """
        self._add_movie_description(movie)
        self._add_all_reviews(movie['reviews'])

    def _add_review(self,review):
	""" Add a review dictionary to the database.  This dict
        comes from reviewskim.imdb.scrape.scrape_movie to the
        database. """

        c=self.cursor

        rs_imdb_movie_id=review['imdb_movie_id']
        reviwer=review['reviewer']
        review_movie_score=review['review_score']
        review_date=review['date'].strftime('%Y-%m-%d')
        review_num_likes=review['num_likes']
        review_num_dislikes=review['num_dislikes']
        review_spoilers=review['spoilers']
        imdb_review_ranking=review['imdb_review_ranking']
        review_place=review['review_place']
        review_url=urllib.unquote(review['review_url'])
        review_text=review['review_text']

        c.execute("""
            INSERT INTO rs_reviews 
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", 
            (rs_imdb_movie_id,reviwer,review_movie_score, 
                review_date,review_num_likes, review_num_dislikes, 
                review_spoilers, imdb_review_ranking,review_place, 
                review_url, review_text)
        )

        # This is necessary: http://mysql-python.sourceforge.net/MySQLdb.html
        self.db.commit()

    def _add_all_reviews(self,reviews):
        for review in reviews:
            self._add_review(review)

    def del_movie(self,imdb_movie_id):

        if not self.in_database(imdb_movie_id):
            raise Exception("Movie %s not in database" % imdb_movie_id)

        self._del_all_reviews_for_movie(imdb_movie_id)
        self._del_movie_description(imdb_movie_id)

    def _del_movie_description(self,imdb_movie_id):
        c=self.cursor

        c.execute("""
            DELETE FROM rs_movies
            WHERE rs_imdb_movie_id=%s""",
            (imdb_movie_id,)
        )
        self.db.commit()

    def _del_all_reviews_for_movie(self,imdb_movie_id):
	""" Remove every review for a movie specified by imdb_movie_id.
	"""
        c=self.cursor

        c.execute("""
            DELETE FROM rs_reviews
            WHERE rs_imdb_movie_id=%s""",
            (imdb_movie_id,)
        )
        self.db.commit()

    def get_reviews(self,imdb_movie_id):
        """ Read all revies for the movie with a given imdb movie id.
        """
        c=self.cursor

        ex=c.execute("""
            select * FROM rs_reviews WHERE rs_imdb_movie_id=%s""",
            (imdb_movie_id,)
        )
        reviews=c.fetchall()
        return reviews

    def has_movie(self,imdb_movie_id):
        """ Test if a movie with a given imdb movie id is in the database. """
        c=self.cursor

        ex=c.execute("""
            select * FROM rs_movies WHERE rs_imdb_movie_id=%s""",
            (imdb_movie_id,)
        )
        l=len(c.fetchall())
        assert l<=1
        return l==1

    def get_imdb_movie_id(self,movie_name):
        """ Test if a movie with a given imdb movie id is in the database. """
        c=self.cursor

        ex=c.execute("""
            select rs_imdb_movie_id FROM rs_movies WHERE rs_movie_name=%s""",
            (movie_name,)
        )
        l=c.fetchall()
        assert len(l)<=1
        if len(l)==1:
            print 'l=',l,'x'*100
            return l[0][0]
        else:
            return None
    
    def rs_imdb_poster_thumbnail_url(self,imdb_movie_id):
        assert self.has_movie(imdb_movie_id)
        c=self.cursor

        ex=c.execute("""
            select rs_imdb_poster_thumbnail_url FROM rs_movies WHERE rs_imdb_movie_id=%s""",
            (imdb_movie_id,)
        )
        l=c.fetchall()
        assert len(l)==1
        return l[0][0]
