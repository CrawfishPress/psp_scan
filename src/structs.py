"""
Basic method of reading a PSP file, is to use a format string and the struct module,
to convert the file binary data into Python data structures.

http://docs.python.org/2/library/struct.html:
B:  one byte (unsigned char)
H:  two bytes (unsigned short)
I:  four bytes (unsigned int)
L:  four bytes (unsigned long)
Q:  eight bytes (unsigned long long - no, really, that's what the page says)
s:  string, variable-length

Note that format strings will be prefixed with a '<'. This tells struct.unpack() to use little-endian byte order,
which PSP uses, and also to not pad bytes (PSP doesn't align objects).
"""

from collections import OrderedDict

# Valid PSP file must start with "Paint Shop Pro Image File\n\x1a" padded with zeros to 32 bytes.
valid_file_marker = 'Paint Shop Pro Image File' + '\n\x1a' + ('\x00' * 5)

PSP_file_header = OrderedDict([
    ('file_marker', '32s'),
    ('major_version', 'H'),
    ('minor_version', 'H'),
])

# Valid Block Headers must start with "~BK\x00" (the fourth char is a zero byte).
valid_header_identifier = '~BK\x00'

generic_header = OrderedDict([
    ('header_id', '4s'),
    ('block_id', 'H'),
    ('block_length', 'I')  # Does not include length of header itself, just the following data-length
])

# General Image Attributes Block
general_image_attributes_chunk = OrderedDict([
    ('chunk_size', 'I'),
    ('image_width', 'I'),
    ('image_height', 'I'),
    ('resolution_val', 'Q'),  # TODO - figure out why this value is weird.
    ('resolution_metric', 'B'),
    ('compression_type', 'H'),
    ('bit_depth', 'H'),
    ('plane_count', 'H'),
    ('color_count', 'I'),
    ('greyscale_flag', 'B'),
    ('total_image_size', 'I'),
    ('active_layer', 'I'),
    ('layer_count', 'H'),
    ('graphics_content', 'I'),
])

# Layer Bank Block
# Layer Sub-Block Information Chunk (two pieces, since one is variable-length):
layer_info_chunk_start = OrderedDict([
    ('chunk_size', 'I'),
    ('name_length', 'H'),
])

layer_info_chunk_rest = OrderedDict([
    ('layer_type', 'B'),
    ('img_rect_tl_x', 'L'),
    ('img_rect_tl_y', 'L'),
    ('img_rect_br_x', 'L'),
    ('img_rect_br_y', 'L'),
    ('saved_img_rect_tl_x', 'L'),
    ('saved_img_rect_tl_y', 'L'),
    ('saved_img_rect_br_x', 'L'),
    ('saved_img_rect_br_y', 'L'),
    ('layer_opacity', 'B'),
    ('blending_mode', 'B'),
    ('layer_flags', 'B'),
    ('transparency_protected', 'B'),
    ('link_group', 'B'),
    ('mask_rect_tl_x', 'L'),
    ('mask_rect_tl_y', 'L'),
    ('mask_rect_br_x', 'L'),
    ('mask_rect_br_y', 'L'),
    ('saved_mask_rect_tl_x', 'L'),
    ('saved_mask_rect_tl_y', 'L'),
    ('saved_mask_rect_br_x', 'L'),
    ('saved_mask_rect_br_y', 'L'),
    ('mask_linked', 'B'),
    ('mask_disabled', 'B'),
    ('invert_mask', 'B'),
    ('blend_range', 'H'),
])

# This chunk is technically part of the previous one, but the debugging code prints out the "info_chunk"
# for each block, and I got tired of looking at all these useless fields in the output...
layer_info_chunk_unused = OrderedDict([
    ('source_blend_1', 'I'),
    ('dest_blend_1', 'I'),
    ('source_blend_2', 'I'),
    ('dest_blend_2', 'I'),
    ('source_blend_3', 'I'),
    ('dest_blend_3', 'I'),
    ('source_blend_4', 'I'),
    ('dest_blend_4', 'I'),
    ('source_blend_5', 'I'),
    ('dest_blend_5', 'I'),
    ('use_highlight_color', 'B'),
    ('highlight_color', 'I'),
])

# Extension blocks for layers
group_layer_info_chunk = OrderedDict([
    ('chunk_size', 'I'),
    ('layer_count', 'I'),
    ('linked', 'B'),
])

mask_layer_info_chunk = OrderedDict([
    ('chunk_size', 'I'),
    ('overlay_color', 'I'),
    ('opacity', 'B'),
])

layer_bitmap_chunk = OrderedDict([
    ('chunk_size', 'I'),
    ('bitmap_count', 'H'),
    ('channel_count', 'H'),
])

# Alpha Bank Block
alpha_bank_info_chunk_header = OrderedDict([
    ('chunk_length', 'I'),
    ('alpha_channel_count', 'H'),
])

# Alpha Channel Information Chunk (two pieces, since one is variable-length):
alpha_channel_info_chunk_start = OrderedDict([
    ('chunk_length', 'I'),
    ('name_length', 'H'),
])

# TODO - change the coordinates to tl_x/br_y, like the rest
alpha_channel_info_chunk_rest = OrderedDict([
    ('alpha_rect_a', 'L'),
    ('alpha_rect_b', 'L'),
    ('alpha_rect_c', 'L'),
    ('alpha_rect_d', 'L'),
    ('saved_alpha_rect_a', 'L'),
    ('saved_alpha_rect_b', 'L'),
    ('saved_alpha_rect_c', 'L'),
    ('saved_alpha_rect_d', 'L'),
])

alpha_channel_chunk = OrderedDict([
    ('chunk_size', 'I'),
    ('alpha_channel_bitmap_count', 'H'),
    ('channel_count', 'H'),
])

# Channel Block
channel_info_chunk = OrderedDict([
    ('chunk_size', 'I'),
    ('comp_channel_len', 'I'),
    ('uncomp_channel_len', 'I'),
    ('bitmap_type', 'H'),
    ('channel_type', 'H'),
])

PSP_Block_ID = [
    'PSP_IMAGE_BLOCK',
    'PSP_CREATOR_BLOCK',
    'PSP_COLOR_BLOCK',
    # I renamed this next one, from PSP_LAYER_START_BLOCK - although that's what is in the spec,
    # it's inconsistent with all the other block names, which are BANK_XXX.
    'PSP_LAYER_BANK_BLOCK',
    'PSP_LAYER_BLOCK',
    'PSP_CHANNEL_BLOCK',
    'PSP_SELECTION_BLOCK',
    'PSP_ALPHA_BANK_BLOCK',
    'PSP_ALPHA_CHANNEL_BLOCK',
    'PSP_COMPOSITE_IMAGE_BLOCK',
    'PSP_EXTENDED_DATA_BLOCK',
    'PSP_TUBE_BLOCK',
    'PSP_ADJUSTMENT_EXTENSION_BLOCK',
    'PSP_VECTOR_EXTENSION_BLOCK',
    'PSP_SHAPE_BLOCK',
    'PSP_PAINTSTYLE_BLOCK',
    'PSP_COMPOSITE_IMAGE_BANK',
    'PSP_COMPOSITE_ATTRIBUTES',
    'PSP_JPEG_BLOCK',
    'PSP_LINESTYLE_BLOCK',
    'PSP_TABLE_BANK_BLOCK',
    'PSP_TABLE_BLOCK',
    'PSP_PAPER_BLOCK',
    'PSP_PATTERN_BLOCK',
    'PSP_GRADIENT_BLOCK',
    'PSP_GROUP_EXTENSION_BLOCK',
    'PSP_MASK_EXTENSION_BLOCK',
    'PSP_BRUSH_BLOCK',
    'PSP_ART_MEDIA_BLOCK',
    'PSP_ART_MEDIA_MAP_BLOCK',
    'PSP_ART_MEDIA_TILE_BLOCK',
    'PSP_ART_MEDIA_TEXTURE_BLOCK',
    'PSP_COLORPROFILE_BLOCK',
]

PSPDIBType = [
    'PSP_DIB_IMAGE',
    'PSP_DIB_TRANS_MASK',
    'PSP_DIB_USER_MASK',
    'PSP_DIB_SELECTION',
    'PSP_DIB_ALPHA_MASK',
    'PSP_DIB_THUMBNAIL',
    'PSP_DIB_THUMBNAIL_TRANS_MASK',
    'PSP_DIB_ADJUSTMENT_LAYER',
    'PSP_DIB_COMPOSITE',
    'PSP_DIB_COMPOSITE_TRANS_MASK',
    'PSP_DIB_PAPER',
    'PSP_DIB_PATTERN',
    'PSP_DIB_PATTERN_TRANS_MASK',
]

PSPLayerType = [
    'keGLTUndefined',
    'keGLTRaster',
    'keGLTFloatingRasterSelection',
    'keGLTVector',
    'keGLTAdjustment',
    'keGLTGroup',
    'keGLTMask',
    'keGLTArtMedia',
]

PSPCompression = [
    'PSP_COMP_NONE',
    'PSP_COMP_RLE',
    'PSP_COMP_LZ77',
    'PSP_COMP_JPEG',
]

PSPChannelType = [
    'PSP_CHANNEL_COMPOSITE',
    'PSP_CHANNEL_RED',
    'PSP_CHANNEL_GREEN',
    'PSP_CHANNEL_BLUE',
]


"""
http://stackoverflow.com/questions/36932/how-can-i-represent-an-enum-in-python
https://pypi.python.org/pypi/enum34
I thought the built-in enums would be nicer, but they're surprisingly painful to use. They start at 1, not zero,
which can only be changed by passing in a dict instead of string. And accessing them is a long string:

    from enum import Enum
    PSP_Block = Enum('PSP_Block', " ".join(PSP_Block_ID))
test_psp.py:
    img_block = pi.get_block(PSP_Block.PSP_IMAGE_BLOCK.value - 1)

So... plan B...
"""


def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)


blks = enum(*PSP_Block_ID)
layer_types = enum(*PSPLayerType)
dibs = enum(*PSPDIBType)
comps = enum(*PSPCompression)
