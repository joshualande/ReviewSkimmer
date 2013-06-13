def clean_unicode(string):
    """ Convert unicode to string.
        Note, replace unicode dash with regular dash. """
    string=string.replace(u'\x96','-')
    string=string.replace(u'\x97','-')
    return string.encode('utf8')
