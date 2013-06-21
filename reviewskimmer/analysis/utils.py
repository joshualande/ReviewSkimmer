
from collections import OrderedDict
from pandas import DataFrame

def get_most_informative_features(classifier, n=10, column_prefix=''): 
    """ Classifier is of type nltk.classify.naivebayes.NaiveBayesClassifier
    """

    feature_name=column_prefix+'feature_name'
    informative_ranking=column_prefix+'informative_ranking'
    classification=column_prefix+'classification'
    classification_bool=column_prefix+'classification_bool'
    odds_ratio=column_prefix+'odds_ratio'



    cpdist = classifier._feature_probdist 
    results=OrderedDict([[feature_name,[]],
                         [informative_ranking,[]],
                         [classification,[]],
                         [classification_bool,[]],
                         [odds_ratio,[]],
                         ])
    for i,(fname, fval) in enumerate(classifier.most_informative_features(n)): 
        def labelprob(l): 
            return cpdist[l,fname].prob(fval) 
        labels = sorted([l for l in classifier._labels 
                         if fval in cpdist[l,fname].samples()], 
                        key=labelprob) 
        if len(labels) == 1: continue 
        l0 = labels[0] 
        l1 = labels[-1] 
        if cpdist[l0,fname].prob(fval) == 0: 
            ratio = 'INF' 
        else: 
            ratio = '%8.1f' % (cpdist[l1,fname].prob(fval) / 
                              cpdist[l0,fname].prob(fval)) 
        results[feature_name].append(fname)
        results[classification].append(l1)
        results[classification_bool].append(l1==classifier._labels[0])
        results[odds_ratio].append(ratio)
        results[informative_ranking].append(i)
        
    df=DataFrame(results)
    return df
