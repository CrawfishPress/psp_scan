## API Usage

Requires installing the package with pip (see 
[windows-install](https://github.com/CrawfishPress/psp_scan/blob/master/docs/windows.md) 
for details)

### API Properties-list
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

### API functions

Note that while you _can_ save individual layers, there are also functions on the main image
object to save _all_ layers individually, to files with computed names (for general debugging), as a `.bmp`:

    - pic.save_layers_to_file(tmp_dir)  # Saves Raster/Mask layers to separate bitmap files, expanded to image-size
    - pic.save_layers_to_file(tmp_dir, full_size=False)  # Saves Raster/Mask layers to separate bitmap files
    - pic.save_blocks_to_file(tmp_dir)  # Saves everything in all layers (channels, masks, etc) to bitmap files

    Either tmp_dir must be supplied, or the original image must have come from a file-string 
    (and a directory will be placed there). If directory doesn't exist, it will be created with
    a default name of `masks.pic_name`. Also:

    - foo = pic.mask_to_alpha(7)        # returns a Pillow.Image object with an Alpha channel, from the
    - foo.save('some_file.png')         # selected mask (which you can save as a .png file + Alpha channel).

### Pillow functions

Because the `.as_PIL/.as_XL` property returns a Pillow.Image object, you can use any of the Pillow functions that
work on one. For example:

    >>> foo = pic.layers[2].as_PIL
    >>> foo.save('layer_three.bmp')
    >>> flipped = foo.transpose(Image.ROTATE_90)
    >>> flipped.save('layer_three_rot90.bmp')

This includes saving in other formats - for instance:

    >>> foo.save('layer_three.tiff', format='tiff')

### Other Properties

Although the API provides a number of features directly, you are not limited to those.
Your code can access any of the attributes and functions on any of the created objects.
And since this is an open-source tool, it's easily readable (and being in Python also helps) to find attributes
that aren't exposed in the API. For instance, if you wanted to look at one of RGB channels in a layer:

    >>> print pic.layers[2].channels[0]
        Block[PSP_CHANNEL_BLOCK:0]: 10,400 bytes, type = PSP_CHANNEL_RED, Bitmap type = PSP_DIB_IMAGE

    >>> print pic.layers[2].channels[0].info_chunk
        Traceback (most recent call last):
          File "api_test.py", line 32, in <module>
            print pic.layers[2].channels[0].info_chunk
        AttributeError: 'Channel' object has no attribute 'info_chunk'

Okay, so apparently Channels don't have info_chunks - I should read my own code. :) In any case, all of the
object capabilities are accessible, whether they are directly accessible via API or not. (Of course, the
standard disclaimer for these things is that they could change, whereas the API, hopefully not so much.)

### Image Loading

    laptop:> python
        Python 2.7.3 (default, Aug  1 2012, 05:14:39) 
    >>> from psp_scan import PSPImage, layer_types
    >>> pic = PSPImage("some_file.pspimage") # can also pass in a file pointer opened for reading

### Image Save/Conversion

    >>> foo = pic.as_PIL            # Returns a Pillow.Image object
    >>> foo = pic.layers[2].as_PIL  # Or you can grab individual layers
    >>> foo.save('layer_three.bmp')
    >>> foo.save('layer_three.tiff', format='tiff')

Pillow determines the file-type to save, based on the extension - unless you override that with the `format`
option. The `format` option is mainly for when using file-objects instead of file-names, however. I suppose
you could save a file with one extension, and a different format, but that could wreak havoc with the Internet -
don't do that. :)

http://pillow.readthedocs.io/en/3.3.x/reference/Image.html#PIL.Image.Image.save


### General Data Display

    >>> print pic.doc
        API properties/functions:
            .doc
            .header
            .header_full
            .filename
            .width
            .height
            .blocks
            .layers
            .as_PIL
            .save_layers_to_file(tmp_dir)
            .save_blocks_to_file(tmp_dir)
            .mask_to_alpha(layer_num)

    >>> pic.header
        {'total_image_size': 1966080, 'color_count': 16777216, 'image_width': 256, 'bit_depth': 24, 
        'image_height': 256, 'layer_count': 3}

    >>> from pprint import pprint as pp
    >>> pp(pic.header)
        {'bit_depth': 24,
         'color_count': 16777216,
         'image_height': 256,
         'image_width': 256,
         'layer_count': 3,
         'total_image_size': 1966080}

    >>> pp(pic.blocks)
        [Block[0][PSP_IMAGE_BLOCK]: 46 bytes,
         Block[1][PSP_EXTENDED_DATA_BLOCK]: 24 bytes,
         Block[2][PSP_CREATOR_BLOCK]: 56 bytes,
         Block[3][PSP_COMPOSITE_IMAGE_BANK]: 208,966 bytes,
         Block[4][PSP_LAYER_BANK_BLOCK]: 461,657 bytes,
         Block[5][PSP_ALPHA_BANK_BLOCK]: 65,637 bytes]

    >>> print pic.blocks[5].header
    	{'chunk_length': 6, 'alpha_channel_count': 1}

### Layer Handling

    >>> print pic.layers[0].doc
        API properties/functions:
            .doc
            .header     # returns a dict with all data fields in PSP.Layer.info_chunk
            .name       # returns name of layer
            .width
            .height
            .rect       # returns the rectangle (or bounding-box) that contains all the visible pixels for this layer
            .as_PIL     # returns a Pillow.Image object using the layer's bitmap and width/height
            .as_XL      # same as .as_PIL, but expands the layer to full image-size (useful for masks, say)

    >>> from pprint import pprint as pp
    >>> pp(pic.layers)
        [PSP_LAYER_BLOCK.keGLTRaster[0]: 196,830 bytes, channels = [3], name = [Background],
         PSP_LAYER_BLOCK.keGLTRaster[1]: 46,329 bytes, channels = [4], name = [Layer_1_red],
         PSP_LAYER_BLOCK.keGLTRaster[2]: 41,851 bytes, channels = [4], name = [Layer_2_green]]

    >>> for layer in pic.layers:  # Same general output as above
    >>>     print layer 
    >>>
    >>> L3 = pic.layers[2]
    >>> print L3
        PSP_LAYER_BLOCK.keGLTRaster[2]: 41,851 bytes, channels = [4], name = [Layer_2_green]
    >>> print pic.layers[4].rect
        {'tl_y': 0, 'tl_x': 0, 'br_y': 256, 'br_x': 256}

    >>> print pic.layers[0].as_PIL
        <PIL.Image.Image image mode=RGB size=256x256 at 0x203AC90>

#### Supported Layer Types
    layer_types.keGLTRaster
    layer_types.keGLTGroup
    layer_types.keGLTMask

#### Saving a single layer
    >>> foo = pic.layers[2].as_PIL  # Layer will be normal-sized, which might be smaller than the full image
    >>> foo = pic.layers[2].as_XL   # Layer will be expanded to full image-size
    >>> foo.save('layer_three.bmp')
    >>> pic.layers[2].as_PIL.save('layer_three.bmp')  # Also works

#### Saving a group of layers
    >>> masks = [layer for layer in pic.layers if layer.layer_type == layer_types.keGLTMask]
    >>> print masks
        [PSP_LAYER_BLOCK.keGLTMask[5]: 10,580 bytes, channels = [1], name = [Mask - Layer_3_blue],
         PSP_LAYER_BLOCK.keGLTMask[9]: 15,497 bytes, channels = [1], name = [Mask - Layer_5_triangle]]
    >>> for layer in masks:
    >>>     l_name = layer.layer_name + '.bmp'
    >>>     layer.as_PIL.save(l_name)
    >>>     # layer.as_XL.save(l_name)  # If you want the layer full-sized

Output will be two files, named `Mask - Layer_3_blue.bmp` and `Mask - Layer_5_triangle.bmp`

#### Saving all layers/masks/channels at once

    pic.save_layers_to_file('tmp_dir')  # Saves Raster/Mask layers to separate bitmap files, expanded to full-size
    pic.save_layers_to_file('tmp_dir', full_size=False)  # same as previous, but layers are actual-size
    pic.save_blocks_to_file('tmp_dir')  # Saves everything in all layers (channels, masks, etc) to bitmap files

Either `tmp_dir` must be supplied, or the image must have originally been opened with a file-string (not
an open file-pointer). The file-string will be used as the destination to which a tmp_dir location will be added.

The directory will be created if it doesn't exist. The default name (if no tmp_dir is supplied) is `layers.pic_name`
or `blocks.pic_name`.

Result will be a directory containing a .BMP file for every (raster) layer and mask in the file.

#### Example: Saving a PNG file with mask saved in the Alpha channel

Note: this code is only for demonstrating the general use, of both the API and Pillow to do things.
There is both an API function and a command-line function that do the same thing (below):

    >>> # Pick a mask layer, which might be smaller than the entire image:
    >>> mask = pic.layers[9]
    >>> # make a mask-background, that is the size of the entire image:
    >>> mask_back = Image.new('L', (pic.width, pic.height))
    >>> # paste the mask into the background, at the coordinates that the mask was created at:
    >>> mask_back.paste(mask.as_PIL, (mask.rect.tl_x, mask.rect.tl_y))
    >>> pic_bmp = pic.as_PIL
    >>> pic_bmp.putalpha(mask_back)
    >>> pic_bmp.save('out_file.png')

The correct way to do this is:

    >>> foo = pic.mask_to_alpha(9)  # Returns a Pillow.Image object with the layer-9 mask in an Alpha channel
    >>> foo.save('out_file.png')
