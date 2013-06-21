from collections import OrderedDict
from operator import itemgetter
import nltk.data
import nltk


class ReviewSummarizer(object):

    def __init__(self, connector, imdb_movie_id, num_occurances=5):

        self.connector=connector
        self.imdb_movie_id=imdb_movie_id
        self.num_occurances=num_occurances

        self._summarize()

    def _summarize(self):
        reviews_df=self.connector.get_reviews(self.imdb_movie_id)
        all_reviews=reviews_df['rs_review_text'].tolist()
        all_tokenized_reviews = [nltk.word_tokenize(i) for i in all_reviews]

        temp = self.connector.get_most_informative_features()
        most_informative_words = temp['rs_feature_name'].tolist()

        # Find highest-occurance words in reviews
        occurances = dict()
        for word in most_informative_words:
            occurances[word]=sum(word in i for i in all_tokenized_reviews)

        sorted_occurances=sorted(occurances.items(), key=itemgetter(1), reverse=True)
        self._top_occurances=OrderedDict(sorted_occurances[:self.num_occurances])

        # Now, find representative quotes
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

        self._top_quotes=[]
        for word in self._top_occurances:
            # find top review where word occurs
            first_occurance = next(i for i in all_reviews if word in i)
            
            sentences = tokenizer.tokenize(first_occurance)
            first_quote = next(i for i in sentences if word in i)

            first_quote=first_quote.replace(word,'<b>%s</b>' % word)
            self._top_quotes.append(first_quote)

    def get_top_occurances(self):
        return self._top_occurances
    def get_top_quotes(self):
        return self._top_quotes
