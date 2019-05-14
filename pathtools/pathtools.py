import argparse
import os

class FullPath(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, fullpath(value))

def fullpath(value):
    return os.path.abspath(os.path.expanduser(value))
