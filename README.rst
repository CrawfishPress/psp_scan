PSP\_Scan
---------

This is a library for reading Paintshop Pro files (.pspimage), and
converting to BMPs or PNGs. Any PNG files saved, will have a
transparency-layer mask stored in the Alpha channel. This enables the
PNG files to be used in websites, or in game-development, etc.

You can access the blocks comprising a PSP file, either
programmatically, using a Python API, or via command-line arguments, and
manipulate or save them to files. They can also be converted to
Pillow.Image objects, which lets you use any Pillow function on them,
including saving in formats other than BMP/PNG.

Paintshop Pro is a full-featured graphics-editing (raster and vector)
program for Windows (only).

Pillow is a Python-package for manipulating graphics (which this library
makes use of).

Supported
---------

-  Files saved in PSP X format (file-format version 8)

   -  this is an older version than the latest commercial software sold,
      so you need to use File->Save-As
   -  (note this is the last release I can find specification-documents
      for)

-  Layers saved in Uncompressed format

   -  Use File->Save-As, and select ``Uncompressed`` format
   -  RLE/LZ77 formats not yet supported, code will raise exception -
      fixing this is high on my TODO list

-  Layers of type Raster/Mask/Group

   -  Adjustment-layers, etc, are silently ignored, no exceptions raised

-  Two layers maximum in a group (raster + mask) - adding more is also
   on my TODO list
-  PNG files saved, will have a transparency-layer (Alpha channel)
   grabbed from the PSP file's Alpha channel.
-  CLI (Command-Line Interface), for file manipulation/conversion,
   individually, or by directory
-  API commands for file manipulation/conversion
-  Python 2.7
-  Tested on Windows 7 (Powershell), should work on later versions

Pip Requirements
----------------

-  pillow>=3.3.0
-  virtualenv (optional, but highly recommended - also
   virtualenvwrapper)

Installation for Windows
------------------------

See
`windows-install <https://github.com/CrawfishPress/psp_scan/wiki/Windows-Install>`__
for full instructions on installing the program locally.

Note: if you don't care about virtual environments, installing from PyPi
is simple:

::

    pip install psp_scan

If it worked, **and** your Python site-packages directory is in either PATH
or PYTHONPATH, then do:

::

    python -m psp_scan -h

If it *didn't* work, then see
`windows-install <https://github.com/CrawfishPress/psp_scan/wiki/Windows-Install>`__
for more information about setting paths.

CLI and API
-----------

There are two ways you can use the package, either by a command-line
interface, or Python API.

The CLI is simpler - you run the ``psp_scan`` package, and give it
various arguments, such as what file to convert, and to which format,
and it performs that action. However, the CLI arguments available are
only a subset of the API commands.

The API is more complex - you need to write a Python program that
imports the ``psp_scan`` package, and write functions that manipulate
the Image as wanted, and other functions that save the resulting Image.
However, there are more features in the API, which might not be
available in the CLI - so if you wanted them, you'd have to use the API.
Especially, Pillow functions are available - for instance, you could
rotate an image by 90 degrees, or scale it, etc.

CLI Usage
---------

See
`cli-docs <https://github.com/CrawfishPress/psp_scan/wiki/CLI-Usage>`__
for details

Example of CLI usage and output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Examples <https://github.com/CrawfishPress/psp_scan/wiki/CLI-Usage#example-of-cli-usage-and-output>`__

CLI Commands-list
~~~~~~~~~~~~~~~~~

::

    usage: psp_scan.py [-h] [-f {png,bmp}] [-m MASK] [-i DIR] [-o DIR] [-n] [-x] [-l] [-v] [-t] [file_in]

           psp_scan some_file.pspimage            # converts a single file to .png (default)
           psp_scan some_file.pspimage -m 3       # converts a single file to .png, and uses layer 3 mask in Alpha channel
           psp_scan some_file.pspimage -f bmp     # converts a single file to .bmp

           psp_scan -i some_dir -v                # converts all files (recursively) inside directory, prints output
           psp_scan -i some_dir -o new_dir        # converts all files (recursively) to new directory

           psp_scan -l some_file.pspimage         # lists basic block information for file (add -v for more detail)
           psp_scan -x some_file.pspimage         # expands file into blocks/layers, saves to new directory

    positional arguments:
      file_in                           single file to convert (optional)

    optional arguments:
      -h, --help                        show this help message and exit
      -f {png,bmp}, --format {png,bmp}  format to convert file into (optional, default=png)
      -m MASK, --mask MASK              mask-layer to use for PNG Alpha channel, for single file
      -i DIR, --input-dir DIR           directory to read files from (optional)
      -o DIR, --output-dir DIR          directory to save converted files (optional)
      -n, --non-recursive               read directories non-recursively (default is recursive)
      -x, --expand                      expand file into layers/blocks, save into directory
      -l, --list                        list basic block info (no file conversion) - add -v for more detail
      -v, --verbose                     extra output when processing files

API Usage
---------

See
`api-docs <https://github.com/CrawfishPress/psp_scan/wiki/API-Usage>`__
for details

API Properties-list
~~~~~~~~~~~~~~~~~~~

::

    - pic.doc
    - pic.header            # returns a dict with selected data fields in PSP.info_chunk
    - pic.header_full       # returns a dict with all data fields in PSP.info_chunk
    - pic.filename          # returns the file used (as a string), or None if a file-pointer was passed in
    - pic.width             # width/height for the entire image
    - pic.height
    - pic.blocks            # returns a list of blocks - the most important block, layers, has its own property
    - pic.layers            # returns a list of layers
    - pic.as_PIL            # returns a Pillow.Image object using the image's full bitmap (all layers combined)

    - pic.layers[0].doc
    - pic.layers[0].header  # returns a dict with all data fields in PSP.Layer.info_chunk
    - pic.layers[0].name    # returns name of layer
    - pic.layers[0].width   # width/height of the visible bitmap-rectangle in the Layer - note this
    - pic.layers[0].height  # could be smaller than the image's width/height
    - pic.layers[0].rect    # returns the rectangle (or bounding-box) that contains all the visible pixels for this layer
    - pic.layers[0].as_PIL  # returns a Pillow.Image object using the layer's bitmap and width/height,
                            # or None if the layer doesn't have a bitmap (like a Group-layer) - check the return
    - pic.layers[0].as_XL   # same as .as_PIL, but expands the layer to full image-size

API functions
~~~~~~~~~~~~~

::

    pic.save_layers_to_file(tmp_dir)  # Saves Raster/Mask layers to separate bitmap files
    pic.save_blocks_to_file(tmp_dir)  # Saves everything in all layers (channels, masks, etc) to bitmap files
    pic.mask_to_alpha(7)              # returns a Pillow.Image object with an Alpha channel, from the selected mask

Pillow functions
~~~~~~~~~~~~~~~~

Because the ``.as_PIL/.as_XL`` property returns a Pillow.Image object,
you can use any of the Pillow functions that work on one. For example:

::

    >>> foo = pic.layers[2].as_PIL
    >>> foo.save('layer_three.bmp')
    >>> flipped = foo.transpose(Image.ROTATE_90)
    >>> flipped.save('layer_three_rot90.bmp')

This includes saving in other formats - for instance:

::

    >>> foo.save('layer_three.tiff', format='tiff')

Additional Random Documentation
-------------------------------

-  `Blocks Overview <https://github.com/CrawfishPress/psp_scan/wiki/Blocks-Overview>`__
-  `General Code Notes <https://github.com/CrawfishPress/psp_scan/wiki/Code-Notes>`__
-  `Project Origin <https://github.com/CrawfishPress/psp_scan/wiki/Origin>`__

Some Credits
~~~~~~~~~~~~

Thanks to
`LeviFiction <http://forum.corel.com/EN/memberlist.php?mode=viewprofile&u=65072>`__
for helping me with some file-format questions.
