import nltk
import re
import random
from itertools import chain
from collections import Counter
from nltk.corpus import stopwords

def analyze_reviews(reviews):
    """ Assume reviews is a pandas dataframe. """

    good_reviews=reviews[reviews['rs_review_movie_score']>=9]
    bad_reviews=reviews[reviews['rs_review_movie_score']<=2]

    print 'len(good_reviews)=%s' % len(good_reviews)
    print 'len(bad_reviews)=%s' % len(bad_reviews)

    m = re.compile('\d')

    english_stop_words=stopwords.words('english')


    def tokenize(text):
        tokens=nltk.word_tokenize(text)
        # strip out trailing puncutation
        tokens = [ token[:-1] if token[-1] in ['.',',','!','?'] else token for token in tokens]

        # lower case
        tokens = [token.lower() for token in tokens]

        # Take only relativly long characters
        toeksn = [token for token in tokens if len(token)>=3]

        # remove words with numbers/digits
        tokens = [token for token in tokens if m.search(token) is None]

        # Remove stop words: http://nltk.googlecode.com/svn/trunk/doc/book/ch02.html
        tokens = [token for token in tokens if token not in english_stop_words]
        return tokens

    good_tokens_list = []
    for i,review in good_reviews.iterrows():
        text=review['rs_review_text']
        good_tokens_list.append(tokenize(text))

    bad_tokens_list = []
    for i,review in bad_reviews.iterrows():
        text=review['rs_review_text']
        bad_tokens_list.append(tokenize(text))

    all_words=Counter()
    for tokens in good_tokens_list + bad_tokens_list:
        for token in tokens:
            all_words[token]+=1

    most_common=all_words.most_common(1000)
    most_common=zip(*most_common)[0]

    print 'most_common_words = ',most_common[-20:]

    def document_features(tokens):
        return {word:word in tokens for word in most_common}

    good_set=[(document_features(tokens), True) for tokens in good_tokens_list]
    bad_set=[(document_features(tokens), False) for tokens in bad_tokens_list]

    train_set = good_set + bad_set
    random.shuffle(train_set) # dunno if this is necessary

    classifier = nltk.NaiveBayesClassifier.train(train_set)

    print 'accuracy',nltk.classify.accuracy(classifier, train_set)

    classifier.show_most_informative_features(100)

    return classifier
