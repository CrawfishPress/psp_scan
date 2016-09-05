"""
Mask computations
"""

from utils import Rect


def find_intersection_rect(rect_one, rect_two):
    """ Given two rectangles, find the common section. """

    new_tl_x = max(rect_one.tl_x, rect_two.tl_x)
    new_tl_y = max(rect_one.tl_y, rect_two.tl_y)
    new_br_x = min(rect_one.br_x, rect_two.br_x)
    new_br_y = min(rect_one.br_y, rect_two.br_y)

    new_rect = Rect(new_tl_x, new_tl_y, new_br_x, new_br_y)

    return new_rect


def apply_mask_to_layer(dest, source, alpha):
    """
    :param dest: a set of RGB triples (50, 100, 150), the lower bitmap layer that shows through the transparency
    :param source: a set of RGB triples (123, 100, 50), to have the transparency-mask applied to
    :param alpha: a single hex value (FF) that represents the transparency:
     - 0 is fully transparent, the dest layer shows through completely
     - FF is fully opaque, the source layer is all that's visible
     - other values are computed
    :return: a set of RGB triples (50, 60, 70)

    https://en.wikipedia.org/wiki/Alpha_compositing
    out_rgb = src_rgb * alpha + dst_rgb (1 - alpha)
    """

    # Handle the easy cases first:
    if alpha == 0:
        return dest

    if alpha == 255:
        return source

    alpha_pct = alpha / 255.0
    new_rgb = (int(source[0] * alpha_pct + dest[0] * (1 - alpha_pct)),
               int(source[1] * alpha_pct + dest[1] * (1 - alpha_pct)),
               int(source[2] * alpha_pct + dest[2] * (1 - alpha_pct)))

    return new_rgb


def apply_rect_mask_to_layer(source, alpha):
    """ Same as apply_mask_to_layer(), but for single pixels. Also always uses black background,
        since it's for greyscale masks.
    """

    dest = 0
    # Handle the easy cases first:
    if alpha == 0:
        return dest

    if alpha == 255:
        return source

    alpha_pct = alpha / 255.0
    new_rgb = int(source * alpha_pct + dest * (1 - alpha_pct))

    return new_rgb


def compute_sub_mask(outer_mask, outer_rect, inner_rect):
    """ Given a mask and sub-mask coordinates, extracts the sub-mask. No doubt numpy could do this in one line. :)
        outer_rect is the coords for the mask, and inner_rect is the sub-coordinates - contained entirely
        inside the outer_rect, nothing outside.
    """

    tl_x = inner_rect.tl_x - outer_rect.tl_x
    tl_y = inner_rect.tl_y - outer_rect.tl_y
    outer_width = outer_rect.width
    outer_height = outer_rect.height
    width = inner_rect.width
    height = inner_rect.height

    # If they're the same size, we're done. This is too easy...
    if width == outer_width and height == outer_height:
        return outer_mask

    inner_mask = []
    for y in range(height):
        for x in range(width):
            new_x = x + tl_x
            new_y = y + tl_y
            pixel_loc = new_x + new_y * outer_width
            new_pixel = outer_mask[pixel_loc]
            inner_mask.append(new_pixel)

    return inner_mask


def expand_rect_mask_debug(gia, bits, abs_rect):
    """ Take a rectangle-mask that is smaller than full-size (probably),
        and expand it to size of the entire image. Purely for debugging output.
    :param gia: general-image attributes - originally a global, contains height/width, etc
    :param bits: greyscale bitmap (0, 0, 0, 0, 250, 255, ...)
    :param abs_rect: outer-border coordinates of rectangle-mask
    :return: greyscale bitmap, with dimensions matching the entire image (0, 0, 0, 0, 250, 255, ...)
    """

    pic_width = gia['width']
    pic_height = gia['height']

    black_bitmap = [0 for _ in range(pic_width * pic_height)]
    tl_x = abs_rect.tl_x
    tl_y = abs_rect.tl_y
    rect_width = abs_rect.width
    rect_height = abs_rect.height

    for y in range(rect_height):
        for x in range(rect_width):
            pixel_loc = x + y * rect_width
            new_pixel_loc = x + tl_x + (y + tl_y) * pic_width
            black_bitmap[new_pixel_loc] = bits[pixel_loc]

    return black_bitmap
