"""
Test command-line interface functions

Need to use os.path.join() on directories, if I want to keep it OS-neutral. Which is somewhat funny,
given that Paintshop Pro only runs on Windows. :) (But I did a lot of dev/testing on Linux, and
tend to join() reflexively...)

Originally I used namedtuples, but had to constantly do join() on the attributes, it was cleaner to
just make a new Class to do all the joining.
"""

import os
import unittest

from src.cli import *


# Data for test_warp_dir():

# Gets converted with DirData() class
# So for instance, ['pics', 'hexes'] converts to directory path 'pics\hexes' (on Windows anyway)
dirs_to_read = [(['pics'], ['pics', 'hexes'], ['bar'], ['bar', 'hexes']),

                (['pics'], ['pics', 'hexes', 'delta'], ['bar'], ['bar', 'hexes', 'delta']),
                (['pics'], ['pics', 'hexes'], ['bar', 'delta'], ['bar', 'delta', 'hexes']),
                (['pics'], ['pics', 'hexes', 'delta'], ['bar', 'beta'], ['bar', 'beta', 'hexes', 'delta']),

                (['pics', 'hexes'], ['pics', 'hexes', 'alpha'], ['bar'], ['bar', 'alpha']),
                (['pics', 'hexes'], ['pics', 'hexes', 'alpha', 'beta'], ['bar'], ['bar', 'alpha', 'beta']),

                # this case should never happen, top-dir should not equal full-dir, but never know...
                (['pics', 'hexes'], ['pics', 'hexes'], ['bar'], ['bar']),
                ]

# Data for test_dir_walker():

# Gets converted in walker() generator function
dirs_to_walk = [(['pics'], ['Image3.pspimage', 'layers_06.pspimage', 'multi_shapes.psimage', 'ship.pspimage']),
                (['pics', 'warped'], ['fubar.pspimage', 'fubar_red.pspimage', 'randomness.pspimage']),
                (['pics', 'hexes'], ['hexagons.pspimage', 'hex_mask.pspimage']),
                (['pics', 'shapes', 'squares'], ['red_square.pspimage', 'blue_square.pspimage']),
                ]

# Gets converted with FileData() class
files_to_fubar = [(['pics', 'Image3.pspimage'], ['fubar', 'Image3.png'], ['fubar']),
                  (['pics', 'layers_06.pspimage'], ['fubar', 'layers_06.png'], ['fubar']),
                  (['pics', 'ship.pspimage'], ['fubar', 'ship.png'], ['fubar']),
                  (['pics', 'warped', 'fubar.pspimage'], ['fubar', 'fubar.png'], ['fubar']),
                  (['pics', 'warped', 'fubar_red.pspimage'], ['fubar', 'fubar_red.png'], ['fubar']),
                  (['pics', 'warped', 'randomness.pspimage'], ['fubar', 'randomness.png'], ['fubar']),
                  (['pics', 'hexes', 'hexagons.pspimage'], ['fubar', 'hexagons.png'], ['fubar']),
                  (['pics', 'hexes', 'hex_mask.pspimage'], ['fubar', 'hex_mask.png'], ['fubar']),
                  (['pics', 'shapes', 'squares', 'red_square.pspimage'], ['fubar', 'squares', 'red_square.png'], ['fubar', 'squares']),
                  (['pics', 'shapes', 'squares', 'blue_square.pspimage'], ['fubar', 'squares', 'blue_square.png'], ['fubar', 'squares']),
                  ]

# Gets converted with FileData() class
files_to_alpha = [(['pics', 'Image3.pspimage'], ['alpha', 'beta', 'Image3.png'], ['alpha', 'beta']),
                  (['pics', 'layers_06.pspimage'], ['alpha', 'beta', 'layers_06.png'], ['alpha', 'beta']),
                  (['pics', 'ship.pspimage'], ['alpha', 'beta', 'ship.png'], ['alpha', 'beta']),
                  (['pics', 'warped', 'fubar.pspimage'], ['alpha', 'beta', 'fubar.png'], ['alpha', 'beta']),
                  (['pics', 'warped', 'fubar_red.pspimage'], ['alpha', 'beta', 'fubar_red.png'], ['alpha', 'beta']),
                  (['pics', 'warped', 'randomness.pspimage'], ['alpha', 'beta', 'randomness.png'], ['alpha', 'beta']),
                  (['pics', 'hexes', 'hexagons.pspimage'], ['alpha', 'beta', 'hexagons.png'], ['alpha', 'beta']),
                  (['pics', 'hexes', 'hex_mask.pspimage'], ['alpha', 'beta', 'hex_mask.png'], ['alpha', 'beta']),
                  (['pics', 'shapes', 'squares', 'red_square.pspimage'], ['alpha', 'beta', 'squares', 'red_square.png'], ['alpha', 'beta', 'squares']),
                  (['pics', 'shapes', 'squares', 'blue_square.pspimage'], ['alpha', 'beta', 'squares', 'blue_square.png'], ['alpha', 'beta', 'squares']),
                  ]


# I love the Mock library, but didn't really want to install it for something as trivial as these.
def walker(_):
    """ Mocking the os.walk() function, which returns a triple of (cur_dir, [sub_dirs], [files]) """
    for a, b in dirs_to_walk:
        yield (os.path.join(*a), [], b)


class MockArgs(object):
    """ Mocking the argparse() output of command-line arguments"""
    def __init__(self, in_dir, fmt, no_recurse):
        self.input_dir = in_dir
        self.format = fmt
        self.non_recursive = no_recurse


class DirData(object):
    def __init__(self, top, full, out, res):
        self.top_dir = os.path.join(*top)
        self.full_dir = os.path.join(*full)
        self.out_dir = os.path.join(*out)
        self.results = os.path.join(*res)

    @property
    def dir_args(self):
        return self.top_dir, self.full_dir, self.out_dir


class FileData(object):
    def __init__(self, src, out_f, out_d):
        self.src_file = os.path.join(*src)
        self.out_file = os.path.join(*out_f)
        self.out_dir = os.path.join(*out_d)

    @property
    def files_out(self):
        return self.src_file, self.out_file, self.out_dir


class CLI_Tester(unittest.TestCase):
    def test_warp_dir(self):

        dirs_to_warp = [DirData(*d) for d in dirs_to_read]
        for a_dir in dirs_to_warp:
            expected = a_dir.results
            new_dir = warp_dirs(*a_dir.dir_args)
            self.assertEqual(new_dir, expected)

    def test_dir_walker(self):
        """ Walk a faked directory, check that output files are correct. """

        top_dir = '/pics'
        fmt = 'pmg'
        foo = MockArgs(top_dir, fmt, False)

        # Test with output directory only one level = 'fubar'
        files_returned = walk_dir(foo, 'fubar', walker)
        files_expected = [FileData(*f).files_out for f in files_to_fubar]

        self.assertListEqual(files_returned, files_expected)

        # Test with output directory equal multiple levels = 'alpha/beta'
        files_returned = walk_dir(foo, os.path.join('alpha', 'beta'), walker)
        files_expected = [FileData(*f).files_out for f in files_to_alpha]

        self.assertListEqual(files_returned, files_expected)
