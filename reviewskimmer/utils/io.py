from os.path import expandvars, splitext
import yaml

def loaddict(filename):
    filename = expandvars(filename)

    extension = splitext(filename)[-1]

    if extension == '.yaml':
        return yaml.load(open(filename,'r'))
    else:
        raise Exception("Unrecognized extension %s" % extension)

def savedict(results, filename, yaml_kwargs=dict()):
    is_results = lambda x: isinstance(x,dict) or isinstance(x,list)

    filename = expandvars(filename)

    extension = splitext(filename)[-1]

    if extension == '.yaml':
        open(filename, 'w').write(yaml.dump(results, **yaml_kwargs))
    else:
        raise Exception("Unrecognized extension %s" % extension)

