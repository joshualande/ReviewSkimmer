def url_join(path, *args):     
    return '/'.join([path.rstrip('/')] + list(args)) 
