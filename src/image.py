""" Originally I had this code in psp_scan.py, but due to circular imports, needed a relative-import
inside a function in cli.py, which is disallowed in Python 3. So moved the code here.

This is more or less the entry-point for non-CLI code.

Note the self.gia attribute (for General Image Attributes, the PSP file's data block). This contains
variables that can be considered "global" (originally they were global, then I refactored them out) to
the image. For some reason, PSP has blocks that need information from other blocks, mostly from the GIA
block. Also, self.gia gets any command-line arguments that might be relevant (for instance, --verbose).
"""

from layers import *

default_options = {
    'VERBOSE': False,
    'DEBUG': False,
    'API_FORMAT': True,
}

used_blocks = {blks.PSP_IMAGE_BLOCK:            {'format': general_image_attributes_chunk,    'func': GeneralImage},
               blks.PSP_LAYER_BANK_BLOCK:       {'format': None,                              'func': LayerBank},
               blks.PSP_LAYER_BLOCK:            {'format': None,                              'func': Block},
               blks.PSP_GROUP_EXTENSION_BLOCK:  {'format': group_layer_info_chunk,            'func': Block},
               blks.PSP_MASK_EXTENSION_BLOCK:   {'format': mask_layer_info_chunk,             'func': Block},
               blks.PSP_ALPHA_BANK_BLOCK:       {'format': alpha_bank_info_chunk_header,      'func': AlphaBank},
               }


class PSPImage(object):
    """ A PSPImage object can be created with either a file string, or open file pointer. """

    def __init__(self, file_thing, cmd_options=None):

        # Don't really need to copy the default dict, but it's remotely possible the code
        # might someday support having multiple Images open at once, so...
        full_options = default_options.copy()
        if cmd_options:
            full_options.update(cmd_options)

        self.gia = full_options
        self._blocks = []
        self.file_name = None

        # Check if we were passed a valid filename string, and one that is a .pspimage file
        if isinstance(file_thing, str) and os.path.isfile(file_thing):
            if not file_thing.endswith('.pspimage'):
                err_msg = "File [{0}] must end in .pspimage".format(file_thing)
                raise TypeError(err_msg)
            with open(file_thing, 'rb') as fp:
                self.file_name = file_thing
                self._open(fp)
                return

        # Check if we were passed a valid file pointer
        if hasattr(file_thing, 'read'):
            self._open(file_thing)
            return

        # Well, darn...
        err_msg = 'Not a file pointer or valid filename string - what *is* this thing: [{0}]'.format(str(file_thing))
        raise TypeError(err_msg)

    def _open(self, file_fp):

        # Quick check that file is correct type, similar to what Pillow does
        if not accept(file_fp.read(len(valid_file_marker))):
            raise TypeError('Not a PSP file')

        # Get file size and version numbers
        file_fp.seek(0, os.SEEK_END)
        self.file_size = file_fp.tell()
        file_fp.seek(0, os.SEEK_SET)

        file_header = read_chunk(file_fp, PSP_file_header, self.gia['DEBUG'])
        self.major_version = file_header['major_version']
        self.minor_version = file_header['minor_version']

        if self.major_version not in supported_versions:
            err_msg = "Wups. Version [{0}] not supported. Only versions [{1}] currently supported".format(
                self.major_version, ",".join([str(x) for x in supported_versions]))
            raise ValueError(err_msg)

        self.gia['major_version'] = self.major_version
        self.gia['minor_version'] = self.minor_version  # Currently always zero, per the specs...
        self.gia['used_blocks'] = used_blocks

        try:
            self.load_blocks(file_fp)
        except Exception as e:
            err_msg = "File loading error: [{0}]".format(e)
            raise SyntaxError(err_msg)

    def load_blocks(self, file_fp):
        """ Reads the top-level blocks only - note that blocks with sub-blocks (such as LayerBank), are
            responsible for reading their own sub-blocks.
        """

        cur_block = 0
        while more_blocks(file_fp, self.file_size):
            new_block_header = read_header(file_fp, generic_header, self.gia['DEBUG'])
            new_block_id = new_block_header['block_id']
            block_dict = self.gia['used_blocks'].get(new_block_id)
            create_block_func = block_dict['func'] if block_dict else Block
            new_block = create_block_func(file_fp, self.gia, new_block_header)
            new_block.block_number = cur_block
            self._blocks.append(new_block)
            cur_block += 1

            if self.gia['DEBUG']:
                print ("Appended block %s: %s bytes" % (PSP_Block_ID[new_block.block_id], new_block.block_length))

    def get_block(self, block_id):

        foo = [blk for blk in self._blocks if blk.block_id == block_id]
        foo = foo[0] if foo else None
        return foo

    def list_blocks(self):

        print ("\nImage File [{0}]: {1:,} bytes.".format(self.file_name, self.file_size))
        print ("File Version = [{0}.{1}]\n".format(self.major_version, self.minor_version))
        for b in self._blocks:
            print (b)

    def mask_to_alpha(self, layer_num):
        """ Returns a Pillow.Image object that has a bitmap of the entire image, and an Alpha Channel
            of the selected layer-mask. Layer must be of type Mask (greyscale), unless:
            TBD: add flag to use a Raster layer, in which case the RGB will be converted to a greyscale mask.
        """

        layer = self.layers[layer_num]
        if layer.layer_type != layer_types.keGLTMask:
            err_msg = "Layer must be of type Mask. Layer[{0}] = {1}".format(layer_num, layer.layer_str)
            raise TypeError(err_msg)

        new_img = self.as_PIL
        new_img.putalpha(layer.as_XL)

        return new_img

    def save_as_bitmap(self, out_file, mask_num=None):

        pic_width = self.gia['width']
        pic_height = self.gia['height']

        layer_bank = self.get_block(blks.PSP_LAYER_BANK_BLOCK)
        save_bitmap(out_file, layer_bank.bitmap, Rect(0, 0, pic_width, pic_height))

    def save_as_PNG(self, out_file, mask_num=None):

        layer_bank = self.get_block(blks.PSP_LAYER_BANK_BLOCK)
        alpha_bank = self.get_block(blks.PSP_ALPHA_BANK_BLOCK)
        layer_count = self.gia['layer_count']
        mask = None
        img_rect = None

        if mask_num:
            if mask_num >= layer_count:
                raise ValueError("Layer [{0}] greater than max layer [{1}]".format(mask_num, layer_count - 1))
            maybe_mask = layer_bank.sub_blocks[mask_num]
            if maybe_mask.layer_type not in [layer_types.keGLTRaster, layer_types.keGLTMask]:
                raise TypeError("Layer [{0}] is of type {1}".format(mask_num, maybe_mask.layer_str))
            mask = maybe_mask.as_mask
            img_rect = maybe_mask.rect
        else:
            # TODO - currently just grabs first channel, could be others - make a parameter?
            if alpha_bank:
                first_alpha = alpha_bank.sub_blocks[0]
                if first_alpha.channel:
                    mask = first_alpha.channel.uncompressed_data
                    img_rect = first_alpha.saved_alpha_rect

        png_file = out_file.replace('.bmp', '.png')

        save_PNG(self.gia, png_file, layer_bank.bitmap, mask, img_rect)

    def save_layers_to_file(self, tmp_dir=None, full_size=True):
        """ Write out all layer bitmap data as an actual file bitmap, for debugging. Either tmp_dir must be
            supplied, or the original image must have come from a file-string (and a tmp_dir will be
            placed there). If full_size is requested (the default), will expand the layers to full-image size.
        """

        new_dir = get_or_create_dir(tmp_dir, self.file_name, 'layers')

        visible_layers = [layer for layer in self.layers if layer.layer_type in [layer_types.keGLTRaster, layer_types.keGLTMask]]
        for layer in visible_layers:
            l_name = layer.layer_name + '.bmp'
            full_name = os.path.join(new_dir, l_name)
            img = layer.as_XL if full_size else layer.as_PIL
            img.save(full_name)
            img.close()

    def save_blocks_to_file(self, tmp_dir=None):
        """ Write out all block bitmap data as an actual file bitmap, for debugging. Either tmp_dir must be
            supplied, or the original image must have come from a file-string (and a tmp_dir will be
            placed there). (block-data = bitmaps/channels/masks)
        """

        new_dir = get_or_create_dir(tmp_dir, self.file_name, 'blocks')

        for b in self._blocks:
            b.save_block_to_file(new_dir)

    @property
    def doc(self):
        gia_doc = "API properties/functions:\n" + \
                  "    .doc\n" + \
                  "    .header\n" + \
                  "    .header_full\n" + \
                  "    .filename\n" + \
                  "    .width\n" + \
                  "    .height\n" + \
                  "    .blocks\n" + \
                  "    .layers" + \
                  "    .as_PIL" + \
                  "    .save_layers_to_file(tmp_dir)" + \
                  "    .save_blocks_to_file(tmp_dir)" + \
                  "    .mask_to_alpha(layer_num)"

        return gia_doc

    @property
    def header(self):
        """ header: dict of selected data from the general_image_attributes block """
        gia = self.get_block(blks.PSP_IMAGE_BLOCK)
        short_dict = {k: v for k, v in gia.info_chunk.items() if k in gia_wanted_fields}

        return short_dict

    @property
    def header_full(self):
        """ header: dict of all data from the general_image_attributes block """
        gia = self.get_block(blks.PSP_IMAGE_BLOCK)

        return gia.info_chunk

    @property
    def filename(self):
        return self.file_name

    @property
    def width(self):
        return self.gia['width']

    @property
    def height(self):
        return self.gia['height']

    @property
    def blocks(self):
        return self._blocks

    @property
    def layers(self):
        bank = self.get_block(blks.PSP_LAYER_BANK_BLOCK)

        return bank.sub_blocks

    @property
    def as_PIL(self):
        """ Returns a Pillow.Image object, using the file's combined bitmap and width/height.  """

        bank = self.get_block(blks.PSP_LAYER_BANK_BLOCK)
        bitmap_bytes = string_to_bytes(flatten_RGB(bank.bitmap))
        img = Image.frombytes('RGB', (self.gia['width'], self.gia['height']), bitmap_bytes)

        return img
