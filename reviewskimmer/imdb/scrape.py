import re
import os
from collections import OrderedDict
import datetime
from os.path import expandvars,join
import traceback

from reviewskimmer.utils.web import url_join, get_html_text, get_soup
from reviewskimmer.utils.strings import clean_unicode

def scrape_movie(**kwargs):
    """ Convenience function  which scrapes one movie. """
    s=IMDBScraper(**kwargs)
    s.scrape_movie()
    return s.get_results()

def nreviews_on_page(imdb_movie_id, debug=False):
    """ This static function is necessary for caching. """
    main_page_url=IMDBScraper.get_main_page_url(imdb_movie_id)
    main_page_soup = get_soup(main_page_url)
    return IMDBScraper._scrape_nreviews(main_page_soup,imdb_movie_id,debug)


class IMDBScraper(object):
    def __init__(self, 
            imdb_movie_id,
            debug=False, 
            nreview_limit=None):
        self.imdb_movie_id = imdb_movie_id
        self.debug=debug
        self.nreview_limit=nreview_limit

        assert self.nreview_limit is None or self.nreview_limit % 10 == 0

    @staticmethod
    def format_imdb_date(date):
        """ Most IMDB movies are of the format: "24 May 2013".
            For example: http://www.imdb.com/title/tt1905041/
            Some movies release dates are of the form "April 1957".
            For example: http://www.imdb.com/title/tt0050083/
            
        """
        try:
            return datetime.datetime.strptime(date,'%d %B %Y')
        except:
            return datetime.datetime.strptime(date,'%B %Y')


    def scrape_title(self):
        _title=self.main_page_soup.findAll('title')
        assert len(_title)==1
        _title=_title[0]
        _title=clean_unicode(_title.next)
        f=re.match('(.+) \((\d+)\) - IMDb',_title)
        groups=f.groups()
        assert len(groups)==2
        self.movie_name,release_year=groups

    def scrape_release_date(self):
        try:
            temp=self.main_page_soup.findAll("h4",**{"text":"Release Date:"})
            assert len(temp)==1
            _release_date=temp[0].next.next
            _release_date=str(_release_date)
            g=re.match('\s*(.+) \(.+\)',_release_date)
            groups=g.groups()
            assert len(groups)==1
            self.release_date=groups[0]
            self.release_date=self.format_imdb_date(self.release_date)
        except:
            print 'Error scraping release date for movie %s' % self.movie_name
            if self.debug: traceback.print_exc()
            self.release_date= None 

    def scrape_nreviews(self):
        self.nreviews=self._scrape_nreviews(self.main_page_soup,self.imdb_movie_id,self.debug)

    @staticmethod
    def _scrape_nreviews(main_page_soup,imdb_movie_id,debug):
        """ find the 'See all XXX user reviews' text on the webpage.
            Pull out of that the number of reviews.
        """
        pattern=re.compile('([\d,]+) user')
        reviews=main_page_soup.findAll(itemprop="reviewCount",text=pattern)
        try:
            assert len(reviews)==1
            reviews_text=str(reviews[0].text)

            # find number of reviews in the string
            groups=pattern.match(str(reviews_text)).groups()
            assert len(groups)==1
            nreviews=int(groups[0].replace(',',''))
            assert nreviews > 0
            return nreviews
        except:
            print 'No movie reviews for movie %s' % imdb_movie_id
            if debug: traceback.print_exc()
            return 0


    def scrape_budget(self):
        try:
            val=self.main_page_soup.findAll('h4',**{"class":"inline","text":"Budget:"})
            assert len(val)==1
            val=val[0]
            val=val.next.next.strip()
            assert val[0]=='$'
            val=val[1:].replace(',','')
            self.budget = float(val)
        except:
            print 'Error reading in budget for movie: %s' % self.movie_name
            if self.debug: traceback.print_exc()
            self.budget = None 

    def scrape_description(self):
        try:
            self.description=self.main_page_soup.findAll('div', itemprop="description")
            assert len(self.description)==1
            self.description=self.description[0]
            self.description=self.description.next.next.get_text()
            self.description=re.sub('\s+',' ',self.description)
        except:
            print 'Error reading description for movie %s' % self.movie_name
            if self.debug: traceback.print_exc()
            self.description= None 

    def scrape_gross(self):
        val=self.main_page_soup.findAll('h4',**{"class":"inline","text":'Gross:'})
        assert len(val)<=1
        if len(val)==0:
            self.gross=None
            print 'No gross for movie %s' % self.imdb_movie_id
        else:
            val=val[0]
            val=val.next.next.strip()
            if val[0]=='$':
                val=val[1:].replace(',','')
                self.gross = float(val)
            else:
                self.gross = None

    @staticmethod
    def get_main_page_url(imdb_movie_id):
        return url_join('http://www.imdb.com/title/','tt%07d' % imdb_movie_id)
    
    def scrape_main_page(self):

        self.main_page_url = self.get_main_page_url(self.imdb_movie_id)
        self.main_page_soup = get_soup(self.main_page_url)

        self.scrape_title()
        self.scrape_nreviews()
        self.scrape_release_date()
        self.scrape_budget()
        self.scrape_gross()
        self.scrape_description()
        self.get_posters()

    def scrape_movie(self):

        imdb_movie_id = self.imdb_movie_id

        self.scrape_main_page()


        # load in all review pages
        n=0

        self.reviews = []
        self.imdb_review_ranking_counter=0

        while n < self.nreviews:
            imdb_review_url=url_join(self.main_page_url,'reviews?start=%s' % n)

            if n % 50 ==0 and self.debug:
                print ' * n=%d/%d' % (n, self.nreviews)


            self.reviews += self.get_reviews_from_page(imdb_review_url)

            n+=10 # imdb pages increment in steps of 10

            if self.nreview_limit is not None and n == self.nreview_limit:
                break


    def get_reviews_from_page(self,imdb_review_url):

        soup = get_soup(imdb_review_url)

        # find all reviews on the page
        # The easiest way si to match on user avatars:
        all_reviews_html = soup.findAll('img',**{'class':"avatar"})

        all_reviews = []
        for i in all_reviews_html:
            try:
                all_reviews.append(self.get_review_from_page(i,imdb_review_url))
            except:
                print 'Error Reading in review on page %s' % imdb_review_url
                if self.debug: traceback.print_exc()
        return all_reviews

    def get_results(self):
        return dict(
                imdb_movie_id=self.imdb_movie_id,
                imdb_movie_url=self.main_page_url,
                nreviews=self.nreviews, 
                budget=self.budget,
                gross=self.gross,
                imdb_description=self.description,
                imdb_poster_url=self.imdb_poster_url,
                imdb_poster_thumbnail_url=self.imdb_poster_thumbnail_url,
                movie_name=self.movie_name,
                release_date=self.release_date,
                reviews=self.reviews)

    def get_posters(self):
        """ Read in the movie posters from a page.
        """

        try:
            imdb_movie_id = self.imdb_movie_id

            # read the poster
            poster=self.main_page_soup.findAll("img",itemprop="image",  title=re.compile('Poster'))
            assert len(poster)==1
            self.imdb_poster_thumbnail_url=poster[0]['src']
            self.imdb_poster_url=self.imdb_poster_thumbnail_url.split('._V')[0]+'.jpg'
        except:
            print 'Error scraping poster url for movie %s' % self.movie_name
            if self.debug: traceback.print_exc()
            self.imdb_poster_thumbnail_url=None
            self.imdb_poster_url=None

    def get_review_from_page(self,review_soup,imdb_review_url):
        """ Pull out a single review form an IMDB
            movie review page.

            review is a soup object anchored on a reviewer's avatar.
        """
        # Most reviews begin with the text 
        #   > "XXX out of XXX found the following review useful:"
        # we have to back up to find it, but sometimes it doesn't exist
        _quality_of_review = review_soup.previous.previous.previous.previous
        m=re.match('(\d+) out of (\d+) people found the following review useful:', str(_quality_of_review))
        if m is not None and len(m.groups())==2:
            groups=m.groups()
            num_likes = int(groups[0])
            num_dislikes = int(groups[1])-int(groups[0])
        else:
            num_likes = num_dislikes = None

        _title=review_soup.next.next.next
        review_title=clean_unicode(_title)

        # the next thing to look for is the review score.
        # Note that this doesn't not always exist:
        review_image = _title.next.next
        if review_image.name == 'img':
            _review_score=_title.next.next.attrs['alt']
            review_score=_review_score.split('/')
            assert review_score[0].isdigit() and review_score[1].isdigit()
            review_score=[int(review_score[0]),int(review_score[1])]
            assert review_score[0] in range(1,11)
            assert review_score[1]==10
            review_score=review_score[0]

            _reviewer=_title.next.next.next.contents[3].next
        else:
            # No user review, jump to reviewer
            review_score=None
            _reviewer=_title.next.next.next.next.next.next

        reviewer_url=_reviewer.previous['href']
        m=re.match('/user/ur(\d+)/',reviewer_url)
        groups=m.groups()
        assert len(groups)==1
        imdb_reviewer_id = int(groups[0])

        if _reviewer == ' ':
            # for some reason, I think some reviewers don't have
            # a reviewer name. I found this problem here:
            #   http://www.imdb.com/title/tt1408101/reviews?start=120
            reviewer=None
            _review_place=_reviewer.next.next
        elif hasattr(_reviewer,'name') and _reviewer.name == 'br':
            # this happens when there is no reviewer and no place!
            # This happend at: http://www.imdb.com/title/tt1392170/reviews?start=1340
            # If so, move the '_place' up the "<small>8 April 2012</small>"
            # html so that it will get caught at the next condition
            reviewer=None
            _review_place=_reviewer.next.next 
        else:
            reviewer=clean_unicode(_reviewer)
            _review_place=_reviewer.next.next.next

        if hasattr(_review_place,'name') and _review_place.name == 'small':
            # this happens when there is no place.
            # If so, skip on to date
            # For an example of this ...
            review_place = None
            _date = _review_place.next
        else:
            m = re.match('from (.+)', _review_place)
            groups=m.groups()
            assert len(groups)==1
            review_place = groups[0]
            review_place=review_place

            _date=_review_place.next.contents[1].next

        date=str(_date)
        date=datetime.datetime.strptime(date,'%d %B %Y')


        _review_text=_date.next.next.next.next
        imdb_review_text=get_html_text(_review_text)
        if imdb_review_text=='*** This review may contain spoilers ***.':
            spoilers=True
            _review_text=_review_text.next.next.next.next
            imdb_review_text=get_html_text(_review_text)
        else:
            spoilers=False

        d=dict(review_title=review_title,
                date=date,
                review_score=review_score,
                reviewer=reviewer,
                review_place=review_place,
                imdb_review_text=imdb_review_text,
                spoilers=spoilers,
                num_likes = num_likes,
                num_dislikes = num_dislikes,
                imdb_movie_id=self.imdb_movie_id,
                imdb_reviewer_id=imdb_reviewer_id,
                imdb_review_ranking=self.imdb_review_ranking_counter,
                imdb_review_url=imdb_review_url)

        self.imdb_review_ranking_counter+=1
        return d

