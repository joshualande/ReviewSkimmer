from collections import OrderedDict
import math
from operator import itemgetter
import nltk.data
import nltk
import itertools


class ReviewSummarizer(object):

    def __init__(self, connector, imdb_movie_id, num_occurances=5):

        self.connector=connector
        self.imdb_movie_id=imdb_movie_id
        self.num_occurances=num_occurances

        self._summarize()

    def _summarize(self):
        all_reviews=self._get_reviews()
        top_word_occurances=self._find_top_occuranges(all_reviews)
        top_quotes=self._find_top_quotes(top_word_occurances,all_reviews)

        self._data = dict(nreviews=len(all_reviews),
                top_word_occurances=top_word_occurances,
                top_quotes=top_quotes)

    def _get_reviews(self):

        # Now, find representative quotes
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

        reviews_df=self.connector.get_reviews(self.imdb_movie_id)

        all_reviews=[]
        for i,review in reviews_df.iterrows():
            score=review['rs_review_movie_score']
            if score>=6 or score <=5:
                if score>=6: classification='pos'
                if score <=5: classification='neg'
                r=dict(text=dict(
                    raw=review['rs_review_text'],
                    raw_tokenized=nltk.word_tokenize(review['rs_review_text'])
                    )
                    )
                r['classification']=classification
                
                sentences =  tokenizer.tokenize(r['text']['raw'])

                good_sentences = [i for i in sentences if len(i.split())<20]

                r['good_sentences'] = []
                for s in good_sentences:
                    r['good_sentences'].append(
                            dict(raw=s, tokenized=nltk.word_tokenize(s)))

                # combine only tokens from good 'short' sentences
                r['text']['good_tokens'] = list(itertools.chain(*[i['tokenized'] for i in r['good_sentences']]))

                all_reviews.append(r)                   
        return all_reviews

    def _find_top_occuranges(self,all_reviews):
        most_informative_words = self.connector.get_most_informative_features()

        occurances = dict()

        for i,j in most_informative_words.iterrows():
            word = j['rs_feature_name']
            classification = j['rs_classification']
            odds_ratio = j['rs_odds_ratio']

            num_found=sum(word in i['text']['good_tokens'] for i in all_reviews if i['classification'] == classification)
            occurances[word]=dict(
                num_found=num_found,
                odds_ratio=float(odds_ratio),
                weighted_num=num_found*math.log(float(odds_ratio)),
                classification=classification)

        sorted_occurances=sorted(occurances.items(), 
                key=lambda x: x[1]['weighted_num'], 
                reverse=True)

        top_word_occurances=OrderedDict(sorted_occurances[:self.num_occurances])
        return top_word_occurances

    def _find_top_quotes(self,top_word_occurances,all_reviews):
        top_quotes=[]
        raw_top_quotes=[]
        for word,v in top_word_occurances.items():
            # find top review where word occurs

            classification = v['classification']

            def find(word,classification,all_reviews):
                for r in all_reviews:
                    for s in r['good_sentences']:
                        if word in s['tokenized'] and classification==r['classification'] \
                            and s['raw'] not in raw_top_quotes:
                            return s['raw']
                return None
        
            first_quote=find(word,classification,all_reviews)
            if first_quote is None: continue

            raw_top_quotes.append(first_quote)
            first_quote=first_quote.replace(word,'<b>%s</b>' % word)
            top_quotes.append(first_quote)
        return top_quotes

    def get_top_word_occurances(self):
        return self._data['top_word_occurances']
    def get_top_quotes(self):
        return self._data['top_quotes']
    def get_nreviews(self):
        return self._data['nreviews']


class CachedReviewSummarizer(ReviewSummarizer):
    """ Cache the reviews for fast lookup. """
    def __init__(self, connector, imdb_movie_id, num_occurances=5):
        self.connector=connector
        self.imdb_movie_id=imdb_movie_id
        self.num_occurances=num_occurances

        if connector.are_quotes_cached(imdb_movie_id):
            self._data  = connector.get_cached_quotes(imdb_movie_id)
        else:
            self._summarize()
            connector.set_cached_quotes(imdb_movie_id, self._data)

