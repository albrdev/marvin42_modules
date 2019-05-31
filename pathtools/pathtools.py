"""
@author: albrdev
@date: 2019-05-14
"""

import argparse
import os

class FullPath(argparse.Action):
    """
    Helper class mainly for use with 'argparse' class. Auto. expands paths for arguemnt options
    """
    def __call__(self, parser, namespace, value, option_string=None):
        setattr(namespace, self.dest, fullpath(value))

def fullpath(value):
    """
    Standalone path string expander
    e.g: Will expand '~' to the absolute path for the home directory of the user
    """
    return os.path.abspath(os.path.expanduser(value))
