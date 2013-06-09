import re
from reviewskim.utils.web import url_join, get_html_text, get_soup
from reviewskim.utils.strings import clean_unicode



def scrape_movie(imdb_movie_key, fast=False, debug=False):
    """ If fast, only scrape first page

        imdb_movie_key should be of the form tt1980209
    """

    main_page_url = url_join('http://www.imdb.com/title/',imdb_movie_key)
    if debug:
        print main_page_url

    soup = get_soup(main_page_url)

    # find the 'See all XXX user reviews' text on the webpage

    pattern=re.compile('See all (.+) user reviews')
    reviews=soup.findAll('a', text=pattern)

    # This should only show up once on a webpage, but good to be paranoid
    assert len(reviews)==1
    reviews_text=str(reviews[0].text)

    # find number of reviews in the string
    groups=pattern.match(str(reviews_text)).groups()
    assert len(groups)==1
    nreviews=int(groups[0])

    # there should alwasy be a review
    assert nreviews > 0

    # load in all review pages
    n=0

    reviews = []

    scrape_movie.imdb_review_ranking=0

    while n < nreviews:
        review_page_url=url_join(main_page_url,'reviews?start=%s' % n)
        soup = get_soup(review_page_url)

        # find all reviews on the page
        # The easiest way si to match on user avatars:
        all_reviews_html = soup.findAll('img',**{'class':"avatar"})

        if debug:
            print 'url=',review_page_url,'nreview=',len(all_reviews_html)


        def get_review(review):

            # Most reviews begin with the text 
            #   > "XXX out of XXX found the following review useful:"
            # we have to back up to find it, but sometimes it doesn't exist
            _quality_of_review = review.previous.previous.previous.previous
            m=re.match('(\d+) out of (\d+) people found the following review useful:', str(_quality_of_review))
            if m is not None and len(m.groups())==2:
                groups=m.groups()
                quality_of_review = [int(groups[0]), int(groups[1])]
            else:
                quality_of_review = None

            _title=review.next.next.next
            title=clean_unicode(_title)

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

                _reviewer=_title.next.next.next.contents[3].next
            else:
                # No user review, jump to reviewer
                review_score=None
                _reviewer=_title.next.next.next.next.next.next

            reviewer=clean_unicode(_reviewer)

            _place=_reviewer.next.next.next

            if hasattr(_place,'name') and _place.name == 'small':
                # this hppaens when there is no place
                place = None
                _date = _place.next
            else:
                m = re.match('from (.+)', _place)
                groups=m.groups()
                assert len(groups)==1
                place = groups[0]
                place=place

                _date=_place.next.contents[1].next

            date=str(_date)


            _review_text=_date.next.next.next.next
            review_text=get_html_text(_review_text)
            if review_text=='*** This review may contain spoilers ***.':
                spoilers=True
                _review_text=_review_text.next.next.next.next
                review_text=get_html_text(_review_text)
            else:
                spoilers=False

            d=dict(
                    title=title,
                    date=date,
                    review_score=review_score,
                    reviewer=reviewer,
                    place=place,
                    review_text=review_text,
                    spoilers=spoilers,
                    quality_of_review = quality_of_review,
                    imdb_review_ranking=scrape_movie.imdb_review_ranking,
            )
            scrape_movie.imdb_review_ranking+=1
            return d

        for review_html in all_reviews_html:
            reviews.append(get_review(review_html))

        if fast:
            break 

        n+=10 # imdb pages increment in steps of 10

    if not fast:    
        assert len(reviews) == nreviews

    return dict(nreviews=nreviews, reviews=reviews)

def get_top_movies(year, number, debug=False):
    """ Pull out the 'number' highest-grosing
        movies of the year.
    """
    NUM_MOVIES_PER_PAGE=50

    # Note, the webpage gives 50 movies at a time
    assert number % NUM_MOVIES_PER_PAGE==0

    def get_website(start,year):
        website='http://www.imdb.com/search/title?at=0&sort=boxoffice_gross_us&start=%s&title_type=feature&year=%s,%s' % (start,year,year)
        return website

    n=1

    ret_list=[]

    while n<number:
        print 'n=%s/%s' % (n,number)
        url_page = get_website(start=n,year=year)

        print url_page
        n+=NUM_MOVIES_PER_PAGE

        # I don't get why, but IMDB barfs when I specify a user agent???
        soup=get_soup(url_page,no_user_agent=True)

        # Match on <td class="number">, which refers to the ranking of the movie
        all_movies=soup.findAll('td',**{'class':"number"})

        for movie in all_movies:
            title_part=movie.next.next.next.next.next.next.next.next.next.next.next.next.next

            title=title_part.next

            link=str(title_part['href'])
            m=re.match('/title/(tt\d+)/',link)
            groups=m.groups()
            assert len(groups)==1
            imdb_id=groups[0]

            _year=title_part.next.next.next.next
            m=re.match(r'\((\d+)\)',_year)
            groups=m.groups()
            assert len(groups)==1
            year=groups[0]

            ret_list.append(dict(title=title,imdb_id=imdb_id,year=year))

    return ret_list

