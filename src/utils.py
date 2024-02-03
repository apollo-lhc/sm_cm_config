# FILEPATH: utils.py
"""
This file contains utility functions used in both the XML generate and the MCU generate files.
"""
import argparse

# register class
class reg:
    """create an object with a name, and a start and a size"""
    def __init__(self, name, start, end, sz):
        self.name = name
        self.start = start
        self.end = end
        self.size = sz

    def __str__(self):
        return "name: " + self.name + " start: " + str(self.start) + \
            " end: " + str(self.end) + " size: " + str(self.size)
    def __eq__(self, other):
        if isinstance(other, reg):
            return self.name == other.name and self.start == other.start and \
                self.end == other.end and self.size == other.size
        return False

# custom file type for yaml file, to be used with argparse
def yaml_file(filename):
    """custom file type for yaml file, to be used with argparse"""
    if not filename.endswith('.yml'):
        raise argparse.ArgumentTypeError('File must have a .yml extension')
    return filename
