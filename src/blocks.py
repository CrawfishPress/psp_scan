"""
Contains all the blocks except for Layer, which is in a class by itself...
"""

from files import *

supported_versions = [8]
supported_layers = [layer_types.keGLTGroup, layer_types.keGLTMask, layer_types.keGLTRaster]
supported_compression = [comps.PSP_COMP_NONE]
gia_wanted_fields = ['image_width', 'image_height', 'total_image_size', 'layer_count', 'color_count', 'bit_depth']


class Block(object):
    def __init__(self, img_fp, gia, header=None):

        if not header:
            header = read_header(img_fp, generic_header, gia['DEBUG'])

        self.block_id = header['block_id']
        self.block_length = header['block_length']
        self.block_type = PSP_Block_ID[self.block_id] if self.block_id < len(PSP_Block_ID) else 'unknown'
        self.block_number = 0  # set by parent PSPImage block for debugging - the block doesn't know its own position.
        self.info_chunk = None
        self.sub_blocks = []
        self.gia = gia

        # Note: block-length does not include length of header itself, just the following data-length,
        # thus making it easy to skip blocks.
        if self.block_id not in self.gia['used_blocks']:
            skip_block(img_fp, self.block_length)
            return

        self.read_any_info_chunks(img_fp)
        self.read_any_sub_blocks(img_fp)

    def read_any_info_chunks(self, img_fp):

        chunk_format = self.gia['used_blocks'][self.block_id]['format']
        self.info_chunk = read_chunk(img_fp, chunk_format, self.gia['DEBUG'])

    def read_any_sub_blocks(self, img_fp):
        pass

    def save_block_to_file(self, tmp_dir):

        for b in self.sub_blocks:
            func = getattr(b, 'save_block_to_file', None)
            if func:
                func(tmp_dir)

    @property
    def header(self):
        return self.info_chunk

    def __repr__(self):

        if self.gia['API_FORMAT']:
            return self.api_repr()

        return self.non_api_repr()

    def api_repr(self):

        block_str = "Block[{0}][{1}]: {2:,} bytes".format(self.block_number, self.block_type, self.block_length)

        return block_str

    def non_api_repr(self):

        block_str = "Block[{0}][{1}]: {2:,} bytes".format(self.block_number, self.block_type, self.block_length)
        if self.info_chunk:
            for k, v in self.info_chunk.items():
                block_str += "\n\t{0}: {1}".format(k, v)
        if self.sub_blocks:
            for sb in self.sub_blocks:
                block_str += "\n{0}".format(sb)

        return block_str


class GeneralImage(Block):
    """ Not to be confused with KernelImage.
        Only reason this is not a generic block, is to pass up some global variables to another block.
    """
    def __init__(self, img_fp, gia, header=None):
        self.gia = gia

        super(GeneralImage, self).__init__(img_fp, gia, header)
        gia['layer_count'] = self.info_chunk['layer_count']
        compression_type = self.info_chunk['compression_type']
        gia['compression_type'] = compression_type
        gia['width'] = self.info_chunk['image_width']
        gia['height'] = self.info_chunk['image_height']

        if compression_type not in supported_compression:
            mal_comp = PSPCompression[compression_type] if compression_type < len(PSPCompression) else 'unknown'
            err_msg = "Compression type [{0}] not currently supported".format(mal_comp)
            raise TypeError(err_msg)

    def non_api_repr(self):

        block_str = "Block[{0}][{1}]: {2} bytes".format(self.block_number, self.block_type, self.block_length)
        if self.info_chunk:
            for k, v in self.info_chunk.items():
                if k in gia_wanted_fields:
                    block_str += "\n\t{0}: {1:,}".format(k, v)

        return block_str


class Channel(object):
    """ Reads a single channel containing either bitmap color information (one of R|G|B),
        or a grayscale bitmap mask. Decompresses the channel from either uncompressed, or TBD: RLE or LZ77.
    """
    def __init__(self, fp, gia):

        self.gia = gia
        header = read_header(fp, generic_header)
        channel_info = read_chunk(fp, channel_info_chunk, gia['DEBUG'])

        self.block_id = header['block_id']
        self.channel_length = channel_info['comp_channel_len']
        self.channel_type = channel_info['channel_type']
        self.bitmap_type = channel_info['bitmap_type']
        self.block_type = PSP_Block_ID[self.block_id]

        self.compression_type = gia['compression_type']
        self.uncompressed_data = None
        self.channel_number = 0  # set by parent Layer block for debugging - the channel doesn't know its own position.

        self.content_chunk = fp.read(self.channel_length)

        self.decompress()

    def decompress(self):

        self.uncompressed_data = [ord(x) for x in self.content_chunk]  # for format=uncompressed - other formats TBD

    def __repr__(self):

        color = PSPChannelType[self.channel_type]
        dib = PSPDIBType[self.bitmap_type]
        comp_type = ""
        if self.compression_type > 0:
            comp_type = ", Compression type = {0}".format(PSPCompression[self.compression_type])

        block_str = "\n\tBlock[{0}:{1}]: {2:,} bytes, type = {3}, Bitmap type = {4}{5}"
        block_str = block_str.format(self.block_type, self.channel_number, self.channel_length, color, dib, comp_type)

        if self.gia['DEBUG']:
            bar = string_to_hex(self.content_chunk)[:100]
            foo = self.uncompressed_data[:20]
            block_str += "\n\t\t{0}\n\t\t{1}".format(foo, bar)

        return block_str

    def save_block_to_file(self, tmp_dir, layer_name, width, height):

        short_channel_desc = {
            'PSP_CHANNEL_COMPOSITE': 'rect_mask',
            'PSP_CHANNEL_RED': 'red',
            'PSP_CHANNEL_GREEN': 'green',
            'PSP_CHANNEL_BLUE': 'blue'}

        # Note - mask isn't applied at the channel level, so the debug-output file for merged channels won't be transparent.
        channel_type = short_channel_desc[PSPChannelType[self.channel_type]]
        channel_name = "{0}--chan_{1}--{2}".format(layer_name, self.channel_number, channel_type)
        out_file = os.path.join(tmp_dir, channel_name + '.bmp')
        save_rect_mask_debug(out_file, self.uncompressed_data, Rect(0, 0, width, height))


class AlphaChannel(object):
    def __init__(self, img_fp, gia):

        self.gia = gia

        header = read_header(img_fp, generic_header, gia['DEBUG'])
        self.block_id = header['block_id']
        self.block_type = PSP_Block_ID[self.block_id]
        self.block_length = header['block_length']
        self.alpha_rect = {}
        self.saved_alpha_rect = {}

        # Read start of Information Chunk
        chunk_start = read_chunk(img_fp, alpha_channel_info_chunk_start, gia['DEBUG'])

        # Read rest of Information Chunk (which is variable-length, due to layer_name)
        self.alpha_name = read_name(img_fp, chunk_start['name_length'], gia['DEBUG'])
        self.info_chunk = read_chunk(img_fp, alpha_channel_info_chunk_rest, gia['DEBUG'])
        self.channel_chunk = read_chunk(img_fp, alpha_channel_chunk, gia['DEBUG'])
        self.channel_size = self.channel_chunk['chunk_size']

        # Read Channel - currently spec says only one possible.
        # (However, testing shows that *zero* is also a possibility - wups.)
        if self.channel_chunk['channel_count'] == 1:
            self.channel = Channel(img_fp, self.gia)
        else:
            self.channel = None

        # Get bitmap/mask rectangle coordinates
        new_rect = Rect(self.info_chunk['alpha_rect_a'], self.info_chunk['alpha_rect_b'],
                        self.info_chunk['alpha_rect_c'], self.info_chunk['alpha_rect_d'])
        self.alpha_rect = new_rect

        new_rect = Rect(self.info_chunk['saved_alpha_rect_a'], self.info_chunk['saved_alpha_rect_b'],
                        self.info_chunk['saved_alpha_rect_c'], self.info_chunk['saved_alpha_rect_d'])
        self.saved_alpha_rect = new_rect

        self.alpha_width = self.alpha_rect.width
        self.alpha_height = self.alpha_rect.height

        self.saved_alpha_width = self.saved_alpha_rect.width
        self.saved_alpha_height = self.saved_alpha_rect.height

    def __repr__(self):

        block_str = "\nBlock[{0}]: name =[{1}]: bytes = [{2:,}]"
        block_str = block_str.format(self.block_type, self.alpha_name, self.block_length)

        if self.gia['VERBOSE']:
            block_str += "\n\t\tAlpha Rect:\t\t\ttopleft = ({0}, {1}), bottomright = ({2}, {3})".format(
                self.alpha_rect.tl_x, self.alpha_rect.tl_y,
                self.alpha_rect.br_x, self.alpha_rect.br_y)
            block_str += "\n\t\tAlpha Rect\t\t\twidth/height = {0}/{1}".format(self.alpha_width, self.alpha_height)
            block_str += "\n\t\tSavedAlpha Rect:\ttopleft = ({0}, {1}), bottomright = ({2}, {3})".format(
                self.saved_alpha_rect.tl_x, self.saved_alpha_rect.tl_y,
                self.saved_alpha_rect.br_x, self.saved_alpha_rect.br_y)
            block_str += "\n\t\tSavedAlpha Rect\t\twidth/height = {0}/{1}".format(self.saved_alpha_width, self.saved_alpha_height)

            block_str += str(self.channel)

        return block_str

    def save_block_to_file(self, tmp_dir):

        channel_name = "Alpha--{0}".format(self.alpha_name)
        out_file = os.path.join(tmp_dir, channel_name + '.bmp')
        save_layer_mask_debug(self.gia, out_file, self.channel.uncompressed_data, self.saved_alpha_rect)


class AlphaBank(Block):
    def read_any_sub_blocks(self, img_fp):

        channel_count = self.info_chunk['alpha_channel_count']
        for x in range(0, channel_count):
            sub_block = AlphaChannel(img_fp, self.gia)
            self.sub_blocks.append(sub_block)
