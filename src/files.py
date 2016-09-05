"""
I'll take, "things that write out to a file", for $500, Alex...
"""

from PIL import Image

from utils import *


def save_rect_mask_debug(out_file, bitmap_data, img_rect):
    """ Save pixel data as bitmap - convert greyscale pixels into byte-string, then create new bitmap image.
    When writing the mask/transparency code, I found it very helpful to be able to generate a bitmap-image file
    of the mask, rather than staring at hex-code, to see what was going on. Mainly for debugging.
    """

    bitmap_bytes = string_to_bytes(bitmap_data)
    img = Image.frombytes('L', (img_rect.width, img_rect.height), bitmap_bytes)
    img.save(out_file, 'bmp')
    img.close()


def save_layer_mask_debug(gia, out_file, bitmap_data, img_rect):
    """ Similar to save_rect_mask(), but for an entire layer. Since layer-mask might be a rectangle smaller
        than the full image, expand to full size. Also for debugging (in case the function names aren't a clue...)
    """

    pic_width = gia['width']
    pic_height = gia['height']

    bitmap_bytes = string_to_bytes(bitmap_data)
    img_back = Image.new('L', (pic_width, pic_height))
    img_mask = Image.frombytes('L', (img_rect.width, img_rect.height), bitmap_bytes)
    img_back.paste(img_mask, (img_rect.tl_x, img_rect.tl_y))
    img_back.save(out_file, 'bmp')
    img_back.close()
    img_mask.close()


def save_layer_merge_debug(gia, out_file, bitmap_data, img_rect, rect_mask_bits):
    """ Saves an entire merged layer, both with and without the rectangle-mask applied.
        Uses a cool checkerboard effect for background of transparent section. Mainly for debugging.
    """

    pic_width = gia['width']
    pic_height = gia['height']

    def is_checkered(x, y):
        x_foo = (((x / 16) % 2) == 0)
        y_foo = (((y / 16) % 2) == 0)
        final = (x_foo == y_foo)
        return final

    mask_width = img_rect.width
    mask_height = img_rect.height

    bitmap_bytes = string_to_bytes(flatten_RGB(bitmap_data))
    img_black = Image.new('RGB', (pic_width, pic_height), (0, 0, 0))
    img_rect_bitmap = Image.frombytes('RGB', (mask_width, mask_height), bitmap_bytes)
    img_black.paste(img_rect_bitmap, (img_rect.tl_x, img_rect.tl_y))

    img_black.save(out_file, 'bmp')

    # Expand rect_mask, if any, to image-size - apply with cool checkerboard effect.
    if rect_mask_bits:
        img_greyscale = Image.new('L', (pic_width, pic_height))
        mask = Image.frombytes('L', (mask_width, mask_height), string_to_bytes(rect_mask_bits))
        img_greyscale.paste(mask, (img_rect.tl_x, img_rect.tl_y))

        checkers = []
        for height in range(pic_height):
            for width in range(pic_width):
                color = 192 if is_checkered(width, height) else 255
                checkers.append(color)
        check_bytes = string_to_bytes(checkers)
        checker_gray = Image.frombytes('L', (pic_width, pic_height), check_bytes)
        checker_rgb = checker_gray.convert(mode='RGB')
        checker_rgb.paste(img_black, img_greyscale)

        # Rename file from 'layer-' to 'layer-trans'
        out_dir, base = os.path.split(out_file)
        base = base.replace('layer', 'layer-trans')
        layer_file = os.path.join(out_dir, base)
        checker_rgb.save(layer_file, 'bmp')

        mask.close()
        checker_gray.close()
        checker_rgb.close()

    img_black.close()
    img_rect_bitmap.close()


def save_bitmap(out_file, bitmap_data, img_rect):
    """ Save pixel data as bitmap - flatten pixel RGB triplets into byte-string, then create new bitmap image. """

    bitmap_bytes = string_to_bytes(flatten_RGB(bitmap_data))
    img = Image.frombytes('RGB', (img_rect.width, img_rect.height), bitmap_bytes)
    img.save(out_file, 'bmp')
    img.close()


def save_stuff_to_file(out_file, bitmap_img, extension='bmp'):

    bitmap_img.save(out_file, extension)
    bitmap_img.close()


def save_PNG(gia, out_file, bitmap_data, mask=None, img_rect=None):
    """ Same as save_bitmap(), but with a mask - if the mask exists, it's saved to the PNG's Alpha channel. """

    pic_width = gia['width']
    pic_height = gia['height']

    bitmap_bytes = string_to_bytes(flatten_RGB(bitmap_data))
    img_main = Image.frombytes('RGB', (pic_width, pic_height), bitmap_bytes)

    if mask:
        mask_bits = ''.join([chr(x) for x in mask])
        new_mask = Image.frombytes('L', (img_rect.width, img_rect.height), mask_bits)
        img_back = Image.new('L', (pic_width, pic_height))
        img_back.paste(new_mask, (img_rect.tl_x, img_rect.tl_y))
        img_main.putalpha(img_back)
        new_mask.close()
        img_back.close()

    img_main.save(out_file, 'png')
    img_main.close()
