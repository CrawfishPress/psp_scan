#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright © 2016 John Crawford
MIT License - see LICENSE.txt for verbiage

Program is for reading PaintShop Pro files (.pspimage), and converting to bitmaps or PNGs,
including transparency layers. PNGs will have one Alpha channel mask save also.

Currently supports:
 - Files saved in PSP X format (file-format version 8)
 - Layers of type Raster/Mask/Group (adjustment-layers, etc, are silently ignored)
 - Layers saved in Uncompressed format (RLE/LZ77 formats not yet supported, code will raise exception)
 - Layer Groups, max of two layers in group (raster + mask)
 - One Alpha-channel mask (only first one is saved in PNGs)

# Requirements:
 - Pillow 3.3
 - Python 2.7

# Source:
ftp://ftp.corel.com/pub/documentation/PSP/PSP%20File%20Format%20Specification%208.pdf.zip
 - September, 2005
 - Paint Shop Pro (PSP) File Format Version 8.0
 - Paint Shop Pro Application Version 10.0 (or PSP X)
 - File Format Documentation Version 8.0

Note: in order to run this as a module, on the command-line, I had
to name this file `__main__.py` (instead of `psp_scan.py`). Still working
on the whole Python packaging thing...
"""

# TODO - allow CLI to select mask-layers for input-directories, not just single files
# TODO - allow CLI to save formats other than BMP/PNG
# TODO - check visibility flag on layers
# TODO - add decompression code for RLE/LZ77 compressed channels
# TODO - handle more than two grouped layers - currently only layer + mask is parsed
# TODO - mask_to_alpha() - add 'use_raster' flag, convert RGB layers to greyscale
# TODO - refactor various layer/mask saving functions

# TODO - add info-chunk/header for other non-used blocks?
# TODO - add Channels to API?
# TODO - test import/api?

# TODO - logging
# TODO - fix fubar.background channel file-dump error
# TODO - refactor DEBUG output
# TODO - update to Python 3+
# TODO - convert tests to use fileIO objects, not write files
# TODO - determine the difference between the image.putalpha() and PaintShop Pro's PNG.save with alpha

from cli import *
from local_dev import *


if __name__ == '__main__':

    good_args = run_command_line()

    if good_args.test:
        for k, v in vars(good_args).items():
            print ("\t%s: %s" % (k, v))
        with time_this('Total time'):
            main_demo()
