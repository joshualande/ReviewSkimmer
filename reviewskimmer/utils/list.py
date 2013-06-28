import itertools
def flatten_dict(d):
    """ Flatten a dictionary of lists into one lont list of items.
    """
    return list(itertools.chain(*zip(*d.items())[1]))

