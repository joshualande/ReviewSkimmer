import unicodedata

def clean_unicode(string):
    """ Convert unicode to string.
        Note, replace unicode dash with regular dash. """
    string=string.replace(u'\x96','-')
    string=string.replace(u'\x97','-')
    return string.encode('utf8').strip()

def strip_unicode(string):
    # from http://stackoverflow.com/questions/1342000/how-to-replace-non-ascii-characters-in-string
    return "".join(i for i in string if ord(i)<128)

