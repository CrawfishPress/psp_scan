# General Code Notes

See blocks.md and structs.py for detailed description of blocks.

## Reading a Block
Note there are two different ways this code reads a block. First case, it's a new block with unknown ID, so
the (fixed-length) header has to be read first - then the ID determines what kind of block to create,
and the new block object is responsible for reading its own data. Second case, it's an _expected_ sub-block
(for example, the Layer Bank has a known number of layer sub-blocks, so it creates a new sub-block and lets
that block read both its own header and data.

## Example of Rectangle-mask and Layer-mask

  - docs/masks/sample_square_coords.png

Note the layer called "L2_blue_square" does not fill the entire image, so it has a rectangle-mask. There is
a layer-mask also grouped with the raster-layer. So the visible bitmap is a combination of two masks,
resulting in the smaller blue rectangle that the `Group` layer shows as a summary.

## Layers and bitmap-rectangles
A given layer will not necessarily contain a bitmap that matches the entire width/height of the full image.
For instance, if half of the layer is transparent, and the other half has pixels, only the pixels will be stored.
There are two different rectangles defining the location where the stored-pixels come from.
The first is an outer border ("Image Rectangle"), which in some cases will be smaller than the entire bitmap.
The second contains only actual bitmap data ("Saved image rectangle") - but, the coordinates are *relative*
to the containing outer border rectangle.
In addition, each layer has a rectangle-mask (greyscale channel), indicating pixels that are "transparent",
and have to be read from the layer below. Note that this mask is only the size of the "Saved Image Rectangle" (?)

### Example:

              full bitmap                    layer 2 inner rect - dots are live pixels, the rest are transparent
    +-----------------+---------------+      +----------------+
    |                 |  layer 2      |      |................|
    |                 |  outer rect   |      |.............   |
    |                 |               |      |...........     |
    |                 |               |      |.........       |
    |                 |               |      |.......         |
    |                 |               |      |.....           |
    |                 |               |      |....            |
    |                 |               |      |...             |
    |                 |               |      |.               |
    +-----------------+---------------+      +----------------+

Note that "transparent" pixels still have an RGB value (0, 0, 0), which is a valid color.
The bitmap-array for the inner rect will be a full rectangular shape. Therefore the *rectangle-mask* also has
to be used, to determine which of those pixels are not displayed (and the underlying pixels shown).

    Layer 2 mask bitmap values - 00 is transparent, FF will show pixel in inner-rect, and partial otherwise:
    FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:
    FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:00:00:00:
    FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:00:00:00:00:00:
    FF:FF:FF:FF:FF:FF:FF:FF:FF:00:00:00:00:00:00:00:
    FF:FF:FF:FF:FF:FF:FF:00:00:00:00:00:00:00:00:00:
    FF:FF:FF:FF:FF:00:00:00:00:00:00:00:00:00:00:00:
    FF:FF:FF:FF:00:00:00:00:00:00:00:00:00:00:00:00:
    FF:FF:FF:00:00:00:00:00:00:00:00:00:00:00:00:00:
    FF:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:

And that's just the rectangle-mask. Then there could be a full-layer mask, grouped with the layer.
The grouped layer-mask, can have dimensions that are larger, smaller, or intersecting with the rectangle-mask.
When I first started, I thought one would be strictly larger than the other, but testing with some simple masks
ruled that out.

So basically, computing the final mask that applies to the visible bits in a layer, is a bit tricky.

## Rectangle List
 - Image rectangle - Rectangle defining image border.
    - May be either entire image-size, or just a sub-rectangle
 - Saved Image rectangle - Rectangle within Image rectangle that contains "significant" data (only the contents saved)
    - Note the coordinates are relative to the Image rectangle

 - Mask rectangle - Rectangle defining user mask border.
    - In V4, may be either entire image-size or sub-rectangle
    - In V8, for Raster-layer, it appears to be same as Image rectangle (Mask rectangle is not used in Rasters)
    - In V8, for Mask-layer, it appears to be a sub-rectangle
      - Note that a Mask-layer may be *larger* than the Image rectangle, in which case the extra space has no
      effect on that layer's display (but it *might* be used in an Alpha channel, which affects the entire image).
 - Saved Mask rectangle - Rectangle within Mask rectangle that contains "significant" data (only the contents saved)
    - Note the coordinates are relative to the Mask rectangle

## Alpha Compositing
 - https://en.wikipedia.org/wiki/Alpha_compositing

Sadly, I have not been able to replicate the PSP alpha compositing. When I combine masks/layers, there
are slight variations in the generated bytes. Just off-by-one, but in some cases higher, and some lower,
so I can't correct for it. Means that a file saved by the code as a Bitmap, won't be identical to one saved
by PSP as a Bitmap, alas. Visually identical (at least I can't see a difference without the dropper-tool), but
not bitwise-identical.

## Kludge
I have found a situation in one PSP file, that I don't know if it counts as a "bug" or not, but it's definitely
a problem. One image I created, had a Background bitmap that is larger than the listed Image bitmap dimensions.
(I'm not sure how I created it, I haven't been able to reproduce it). The Image is 1024x1024, but the
Background is 1040x1024. Also, one of the Rectangle coordinates (img_rect_tl_x) has a value of 4,294,967,280,
which is close to the maximum value for a variable of type unsigned long: 4,294,967,295 (0xffffffff).
Shockingly, when I tried to use that value, I got an exception:

    "Python int too large to convert to C long"

So the fix I'm using, is to set any too-large Rectangle coordinates to the max-width/height, and to trim
the Background size (and bitmap) down to those dimensions also. Kinda messy, but then again, so
is most software...

Note: There's no way (that I can tell), to determine which *direction* the Background bitmap is off-screen.
If it's at the bottom or right, truncating the bitmap will give the correct image. If it's to the top or left,
then truncating the bitmap will give the wrong image. (Naturally, that's how my broken test-image has it).

## Kludge Manual Fix
If that becomes an issue, there's also a manual fix, inside PSP:
- Rectangle-select the entire Background
- Crop To Selection
This trims the external bitmap bits, and sets the rectangle coordinates correctly.

## Documentation Kludges
I did all the documentation in Markdown _.md_ format. Naturally, when I go to upload to PyPi, I find out
that they don't support Markdown, only ReST _.rst_. I used `pandoc` to convert the README.md, but it only mostly
worked, and I had to do some manual tweaks.

    pandoc --from=markdown --to=rst --output=README.rst README.md
    pandoc --from=markdown --to=rst --output=CHANGES.rst CHANGES.md

## Testing
    python -m unittest tests
