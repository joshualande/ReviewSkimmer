import re
import os
import urllib
from collections import OrderedDict
import datetime
from os.path import expandvars,join

from reviewskim.utils.web import url_join, get_html_text, get_soup
from reviewskim.utils.strings import clean_unicode


def get_review_from_page(review,imdb_movie_id):
    """ Pull out a single review form an IMDB
        movie review page.

        review is a soup object anchored on a reviewer's avatar.
    """
    # Most reviews begin with the text 
    #   > "XXX out of XXX found the following review useful:"
    # we have to back up to find it, but sometimes it doesn't exist
    _quality_of_review = review.previous.previous.previous.previous
    m=re.match('(\d+) out of (\d+) people found the following review useful:', str(_quality_of_review))
    if m is not None and len(m.groups())==2:
        groups=m.groups()
        num_likes = int(groups[0])
        num_dislikes = int(groups[1])-int(groups[0])
    else:
        num_likes = num_dislikes = None

    _title=review.next.next.next
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

    d=dict(
            review_title=review_title,
            date=date,
            review_score=review_score,
            reviewer=reviewer,
            review_place=review_place,
            imdb_review_text=imdb_review_text,
            spoilers=spoilers,
            num_likes = num_likes,
            num_dislikes = num_dislikes,
            imdb_movie_id=imdb_movie_id,
            imdb_reviewer_id=imdb_reviewer_id,
    )
    return d


def get_reviews_from_page(imdb_review_webpage, imdb_movie_id, debug=False):

    soup = get_soup(imdb_review_webpage)

    # find all reviews on the page
    # The easiest way si to match on user avatars:
    all_reviews_html = soup.findAll('img',**{'class':"avatar"})

    reviews = [get_review_from_page(i,imdb_movie_id) for i in all_reviews_html]
    for review in reviews:
        review['imdb_review_url']=imdb_review_webpage
    return reviews




def scrape_movie(imdb_movie_id, poster_dir, poster_thumbnail_dir,
                 debug=False, fast=False):
    """ If fast, only scrape first page

        imdb_movie_id should be of the form tt1980209
    """

    main_page_url = url_join('http://www.imdb.com/title/','tt%07d' % imdb_movie_id)

    soup = get_soup(main_page_url)

    # find the 'See all XXX user reviews' text on the webpage
    pattern=re.compile('See all ([\d,]+) user reviews')
    reviews=soup.findAll('a', text=pattern)

    # This should only show up once on a webpage, but good to be paranoid
    assert len(reviews)==1
    reviews_text=str(reviews[0].text)

    # find number of reviews in the string
    groups=pattern.match(str(reviews_text)).groups()
    assert len(groups)==1
    nreviews=int(groups[0].replace(',',''))

    # there should alwasy be a review
    assert nreviews > 0

    # load in all review pages
    n=0

    reviews = []

    # read in title
    _title=soup.findAll('title')
    assert len(_title)==1
    _title=_title[0]
    _title=clean_unicode(_title.next)
    f=re.match('(.+) \((\d+)\) - IMDb',_title)
    groups=f.groups()
    assert len(groups)==2
    movie_name,release_year=groups
    release_year=int(release_year)

    # read the poster
    poster=soup.findAll("img",itemprop="image",  title=re.compile('Poster'))
    assert len(poster)==1
    imdb_poster_thumbnail_url=poster[0]['src']
    imdb_poster_url=imdb_poster_thumbnail_url.split('._V')[0]+'.jpg'

    print ' * downloading thumbnail poster %s' % imdb_poster_thumbnail_url

    local_poster_thumbnail_filename=expandvars(join(poster_thumbnail_dir,'poster_thumbnail_%s.jpg' % imdb_movie_id))
    # download the poster
    urllib.urlretrieve(imdb_poster_thumbnail_url,local_poster_thumbnail_filename)
    assert os.stat(local_poster_thumbnail_filename).st_size>0

    print ' * downloading poster %s' % imdb_poster_url

    local_poster_filename=expandvars(join(poster_dir,'poster_%s.jpg' % imdb_movie_id))
    urllib.urlretrieve(imdb_poster_url, local_poster_filename)
    assert os.stat(local_poster_filename).st_size>0

    # read in release date
    temp=soup.findAll("h4",**{"text":"Release Date:"})
    assert len(temp)==1
    _release_date=temp[0].next.next
    _release_date=str(_release_date)
    g=re.match('\s+(.+) \(\w+\)',_release_date)
    groups=g.groups()
    assert len(groups)==1
    release_date=groups[0]
    release_date=datetime.datetime.strptime(release_date,'%d %B %Y')

    assert release_date.year == release_year

    # get out the box office 
    val=soup.findAll('h4',**{"class":"inline","text":"Budget:"})
    assert len(val)==1
    val=val[0]
    val=val.next.next.strip()
    if val[0]=='$':
        val=val[1:].replace(',','')
        budget = float(val)
    else:
        # This happens when budgets are in other currencies.
        # For example, http://www.imdb.com/title/tt0211915/
        budget = None 

    # get the gross
    val=soup.findAll('h4',**{"class":"inline","text":'Gross:'})
    assert len(val)==1
    val=val[0]
    val=val.next.next.strip()
    assert val[0]=='$'
    val=val[1:].replace(',','')
    gross = float(val)

    description=soup.findAll('div', itemprop="description")
    assert len(description)==1
    description=description[0]
    description=description.next.next.get_text()
    description=re.sub('\s+',' ',description)

    while n < nreviews:
        imdb_review_webpage=url_join(main_page_url,'reviews?start=%s' % n)


        if n % 50 ==0 and debug:
            print ' * n=%d/%d' % (n, nreviews)


        reviews += get_reviews_from_page(imdb_review_webpage, imdb_movie_id, debug)

        n+=10 # imdb pages increment in steps of 10
        if fast: break

    for i,review in enumerate(reviews):
        review['imdb_review_ranking'] = i

    if not fast:
        assert len(reviews) == nreviews,'reviews=%s, nreviews=%s' % (len(reviews),nreviews)

    return dict(
            imdb_movie_id=imdb_movie_id,
            imdb_movie_url=main_page_url,
            nreviews=nreviews, 
            budget=budget,
            gross=gross,
            imdb_description=description,
            imdb_poster_url=imdb_poster_url,
            imdb_poster_thumbnail_url=imdb_poster_thumbnail_url,
            movie_name=movie_name,
            release_date=release_date,
            reviews=reviews)

def get_top_movies(year, number, debug=False):
    """ Pull out the 'number' highest-grosing
        movies of the year.
    """
    NUM_MOVIES_PER_PAGE=50

    def get_website(start,year):
        website='http://www.imdb.com/search/title?at=0&sort=boxoffice_gross_us&start=%s&title_type=feature&year=%s,%s' % (start,year,year)
        return website

    n=1

    ret_list=OrderedDict()

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

            movie_name=clean_unicode(title_part.next)

            link=str(title_part['href'])
            m=re.match('/title/tt(\d+)/',link)
            groups=m.groups()
            assert len(groups)==1
            imdb_movie_id=int(groups[0])

            _year=title_part.next.next.next.next
            m=re.match(r'\((\d+)\)',_year)
            groups=m.groups()
            assert len(groups)==1
            year=int(groups[0])

            ret_list[imdb_movie_id]=dict(movie_name=movie_name,year=year)

            # if only a few movies are requested
            if len(ret_list) == number:
                return ret_list

    return ret_list

