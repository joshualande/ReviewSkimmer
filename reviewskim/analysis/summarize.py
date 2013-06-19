from collections import OrderedDict
from operator import itemgetter
import nltk.data

def summarize_reviews(connector, imdb_movie_id, most_informative_words, num_occurances=5):
    reviews_df=connector.get_reviews(imdb_movie_id)
    all_reviews=reviews_df['rs_review_text'].tolist()

    # Find highest-occurance words in reviews
    occurances = dict()
    for word in most_informative_words:
        occurances[word]=sum(word in i for i in all_reviews)

    sorted_occurances=sorted(occurances.items(), key=itemgetter(1), reverse=True)
    top_occurances=OrderedDict(sorted_occurances[:num_occurances])

    # Now, find representative quotes
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    top_quotes=[]
    for word in top_occurances:
        # find top review where word occurs
        first_occurance = next(i for i in all_reviews if word in i)
        
        sentences = tokenizer.tokenize(first_occurance)
        first_quote = next(i for i in sentences if word in i)
        top_quotes.append(first_quote)


    d = dict(
        top_occurances=top_occurances,
        top_quotes=top_quotes,
    )
    return d
