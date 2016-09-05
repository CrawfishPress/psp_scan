import collections

from blocks import *
from masks import *


class Layer(object):
    def __init__(self, img_fp, gia):

        self.gia = gia
        header = read_header(img_fp, generic_header)

        self.block_id = header['block_id']
        self.block_length = header['block_length']
        self.block_type = PSP_Block_ID[self.block_id]
        self.layer_number = 0  # set by parent LayerBank block for debugging - the layer doesn't know its own position.
        self.channels = []

        # This is kludgy, there are certain things I don't understand about how PSP computes rectangle coords.
        # We start with the rectangles in the raw data, then figure out which is used how.
        self.img_rect = None
        self.saved_img_rect = None
        self.mask_rect = None
        self.saved_mask_rect = None

        # This is the minimum rectangle that contains all rect-mask bits, relative to entire image.
        self.abs_rect = None
        self.rect_mask_bits = None  # bitmap-list (RGB) for rectangle mask

        self.layer_mask_bits = None  # bitmap-list (greyscale) for entire layer
        self.layer_scaled_bits = None  # the visible-rectangle portion of the layer-mask (which can be larger)
        self.layer_mask_rect = None  # rectangle from the grouped layer-mask, if any

        self.omega_mask = []  # Both rect-mask and layer-mask (if any) combined.
        self.omega_rect = None

        self.bitmap = None

        self.group_extension = None
        self.mask_extension = None
        self.grouped = []
        self.kludge_coords = None

        # This is my Information Chunk
        chunk_start = read_chunk(img_fp, layer_info_chunk_start)

        # Read rest of Information Chunk (which is variable-length, due to layer_name)
        self.layer_name = read_name(img_fp, chunk_start['name_length'])
        self.info_chunk = read_chunk(img_fp, layer_info_chunk_rest)
        self.unused_chunk = read_chunk(img_fp, layer_info_chunk_unused)
        self.layer_type = self.info_chunk['layer_type']
        self.layer_str = PSPLayerType[self.layer_type]

        if self.gia['DEBUG']:
            print ("working on layer [{0}], type = {1}".format(self.layer_name, self.layer_str))
            for k, v in sorted(self.info_chunk.items()):
                print ("%s: %s" % (k, v))

        # To skip a partially-read block, I need the remaining bytes
        if self.layer_type not in supported_layers:
            block_bytes_read = chunk_start['name_length']
            _, lic_length = transmute_struct(layer_info_chunk_start)
            _, lir_length = transmute_struct(layer_info_chunk_rest)
            _, liu_length = transmute_struct(layer_info_chunk_unused)
            block_bytes_read += (lic_length + lir_length + liu_length)
            if self.gia['VERBOSE'] or self.gia['DEBUG']:
                print ("INFO: skipping layer [{0}], type = {1}".format(self.layer_name, self.layer_str))
            skip_block(img_fp, self.block_length - block_bytes_read)
            return

        if self.layer_type == layer_types.keGLTGroup:
            self.group_extension = Block(img_fp, self.gia)
        elif self.layer_type == layer_types.keGLTMask:
            self.mask_extension = Block(img_fp, self.gia)

        # This is my other Information Chunk (okay, it's called a Bitmap Chunk)
        layer_bitmap_chunk_data = read_chunk(img_fp, layer_bitmap_chunk)
        self.bitmap_count = layer_bitmap_chunk_data['bitmap_count']
        self.channel_count = layer_bitmap_chunk_data['channel_count']

        if self.layer_type not in [layer_types.keGLTRaster, layer_types.keGLTMask]:
            return

        self.kludge_fix_info_chunk()
        self.parse_rect_coords()
        self.compute_rectangles()
        self.process_channels(img_fp)
        self.kludge_fix_bitmap()

    def kludge_fix_info_chunk(self):

        pic_width = self.gia['width']
        pic_height = self.gia['height']

        rects = [(k, v) for k, v in self.info_chunk.items() if 'rect' in k]
        for k, v in rects:
            if v > 100000:
                fix = "WARNING: layer [{0}], rectangle coordinate [{1}] has an invalid value: [{2:,}]. " \
                      "Setting coordinate to zero."
                print (fix.format(self.layer_name, k, v))
                self.info_chunk[k] = 0

        # TODO - I *think* Background will only have one set of screwed up coordinates, but possibly more? Check later
        tmp_width, tmp_height = pic_width, pic_height
        widths = [(k, v) for k, v in self.info_chunk.items() if 'br_x' in k]
        for k, v in widths:
            if v > pic_width:
                fix = "WARNING: layer [{0}], rectangle coordinate [{1}] has an invalid value: [{2:,}]. " \
                      "Setting coordinate to maximum image-width of [{3}]."
                print (fix.format(self.layer_name, k, v, pic_width))
                self.info_chunk[k] = pic_width
                tmp_width = v

        heights = [(k, v) for k, v in self.info_chunk.items() if 'br_y' in k]
        for k, v in heights:
            if v > pic_height:
                fix = "WARNING: layer [{0}], rectangle coordinate [{1}] has an invalid value: [{2:,}]. " \
                      "Setting coordinate to maximum image-height of [{3}]."
                print (fix.format(self.layer_name, k, v, pic_height))
                self.info_chunk[k] = pic_height
                tmp_height = v

        KludgeVals = collections.namedtuple('KludgeVals', ['width', 'height'])
        self.kludge_coords = KludgeVals(tmp_width, tmp_height)

    def parse_rect_coords(self):

        # Get bitmap/mask rectangle coordinates
        new_rect = Rect(self.info_chunk['img_rect_tl_x'], self.info_chunk['img_rect_tl_y'],
                        self.info_chunk['img_rect_br_x'], self.info_chunk['img_rect_br_y'])
        self.img_rect = new_rect

        new_rect = Rect(self.info_chunk['saved_img_rect_tl_x'], self.info_chunk['saved_img_rect_tl_y'],
                        self.info_chunk['saved_img_rect_br_x'], self.info_chunk['saved_img_rect_br_y'])
        self.saved_img_rect = new_rect

        new_rect = Rect(self.info_chunk['mask_rect_tl_x'], self.info_chunk['mask_rect_tl_y'],
                        self.info_chunk['mask_rect_br_x'], self.info_chunk['mask_rect_br_y'])
        self.mask_rect = new_rect

        new_rect = Rect(self.info_chunk['saved_mask_rect_tl_x'], self.info_chunk['saved_mask_rect_tl_y'],
                        self.info_chunk['saved_mask_rect_br_x'], self.info_chunk['saved_mask_rect_br_y'])
        self.saved_mask_rect = new_rect

    def compute_rectangles(self):
        """
        Determine rectangle coordinate relationship. For reasons that I have yet to determine, sometimes:
            - the first (outer) rectangle will equal the entire image (say (0, 0) to (256, 256))
            - the second (inner) rectangle will contain the visible bits (and is relative to the outer rectangle,
            so it might start at, say (16, 16))
        At other times:
            - the first (outer) rectangle will be smaller than the entire image
            - the second (inner) rectangle will be the same size as the outer rectangle (still relative to it,
            so it starts at (0, 0))
        So this function determines the rectangle that actually contains the visible bits, and is relative
        to the entire image size.
        """
        pic_width = self.gia['width']
        pic_height = self.gia['height']

        if self.layer_type == layer_types.keGLTRaster:
            outer_rect = self.img_rect
            inner_rect = self.saved_img_rect
        else:  # self.layer_type == layer_types.keGLTMask:
            outer_rect = self.mask_rect
            inner_rect = self.saved_mask_rect

        self.abs_rect = outer_rect
        if outer_rect.tl_x == 0 and outer_rect.tl_y == 0 and \
                outer_rect.br_x == pic_width and outer_rect.br_y == pic_height:
            self.abs_rect = inner_rect

    def process_channels(self, img_fp):
        """ For Version 8, a Layer should have either 4 (3 RGB + 1 rectangle-mask) channels,
            or 1 one greyscale channel. Read in the channels, combine RGB into a single bitmap.
            Get Rectangle-mask from greyscale channel. Get layer-mask (Mask-layer only).
        """

        for x in range(0, self.channel_count):
            new_channel = Channel(img_fp, self.gia)
            new_channel.channel_number = x
            self.channels.append(new_channel)
            if self.gia['DEBUG']:
                print ("appended channel %s: %s bytes" % (PSPChannelType[new_channel.channel_type], new_channel.channel_length))

        if self.layer_type == layer_types.keGLTRaster and self.channel_count > 2:
            combined = zip(self.channels[0].uncompressed_data,
                           self.channels[1].uncompressed_data,
                           self.channels[2].uncompressed_data)

            self.bitmap = combined

        # Both versions 4.0 and 8.0 have a rectangle-mask in the raster-layer, after the three RGB channels
        if len(self.channels) > 3 and self.channels[3].bitmap_type == dibs.PSP_DIB_TRANS_MASK:
            self.rect_mask_bits = self.channels[3].uncompressed_data

        if self.layer_type == layer_types.keGLTMask:
            self.bitmap = self.channels[0].uncompressed_data

    def kludge_fix_bitmap(self):

        if not self.kludge_coords:
            return

        pic_width = self.gia['width']
        pic_height = self.gia['height']

        outer_rect = Rect(0, 0, self.kludge_coords.width, self.kludge_coords.height)
        inner_rect = Rect(0, 0, pic_width, pic_height)
        trunc_bitmap = compute_sub_mask(self.bitmap, outer_rect, inner_rect)
        self.bitmap = trunc_bitmap

    def generate_layer_mask(self):
        """ There are two different masks that a raster layer might need - a rectangle-mask, and a layer-mask.
            The rectangle-mask is already in the layer. The layer-mask is also in the layer for version 4.0,
            but grouped with another layer (of type Mask) for version 8.0. Note this has to run after all layers
            are read, because that layer-mask is in the following layer.
            Also note that either mask can be larger than the other - the layer could be full-sized, whereas
            the mask is only a subset of the image, or vice-versa. Or the layer might not be larger/smaller,
            but just partially overlapping. So I need to compute the intersection of the rectangle-mask
            and layer-mask.
        """

        if self.layer_type != layer_types.keGLTRaster:
            return

        # Get layer-mask, either from same layer (V4), or a grouped layer
        if self.grouped:
            self.layer_mask_bits = self.grouped[0].bitmap
            self.layer_mask_rect = self.grouped[0].abs_rect

        # Combine both the rectangle-mask and layer-mask into a single, Ultimate MASK!
        # See docs/masks/sample_square_coords.png for visual example of mask-interaction

        if not self.layer_mask_bits or not self.rect_mask_bits:
            self.omega_mask = self.rect_mask_bits
            self.omega_rect = self.abs_rect
            return

        self.omega_rect = find_intersection_rect(self.layer_mask_rect, self.abs_rect)

        self.layer_scaled_bits = compute_sub_mask(self.layer_mask_bits, self.layer_mask_rect, self.omega_rect)
        rect_mask_subset = compute_sub_mask(self.rect_mask_bits, self.abs_rect, self.omega_rect)

        for y in range(self.omega_rect.height):
            for x in range(self.omega_rect.width):
                pixel_loc = x + y * self.omega_rect.width
                greyscale_pixel = apply_rect_mask_to_layer(rect_mask_subset[pixel_loc], self.layer_scaled_bits[pixel_loc])
                self.omega_mask.append(greyscale_pixel)

    @property
    def doc(self):
        lyr_doc = "API properties/functions:\n" + \
                  "    .doc\n" + \
                  "    .header\n" + \
                  "    .name\n" + \
                  "    .width\n" + \
                  "    .height\n" + \
                  "    .rect\n" + \
                  "    .as_PIL\n" + \
                  "    .as_XL"

        return lyr_doc

    @property
    def header(self):
        return self.info_chunk

    @property
    def name(self):
        return self.layer_name

    @property
    def width(self):
        return self.abs_rect.width

    @property
    def height(self):
        return self.abs_rect.height

    @property
    def rect(self):
        return self.abs_rect
        # return self.abs_rect.coords_api

    @property
    def as_mask(self):
        """ Converts Raster RGB layers to greyscale mask, and Mask layers are... left alone.
        """

        if self.layer_type not in [layer_types.keGLTRaster, layer_types.keGLTMask]:
            return None

        if self.layer_type == layer_types.keGLTMask:
            return self.bitmap

        # So we have a bitmap consisting of RGB triples [(0, 0, 0), (1, 1, 1),] to compress (not flatten)
        # Just converting mask into on/off areas, no actual grey
        new_mask = [0 if max(trip) == 0 else 255 for trip in self.bitmap]

        return new_mask

    @property
    def as_PIL(self):
        """ Returns a Pillow.Image object, using the layer's bitmap and width/height - if the layer *has*
            a bitmap - Group-layers are skipped.
        """

        if self.layer_type not in [layer_types.keGLTRaster, layer_types.keGLTMask]:
            return None

        if self.layer_type == layer_types.keGLTMask:
            bitmap_bytes = string_to_bytes(self.bitmap)
            img = Image.frombytes('L', (self.abs_rect.width, self.abs_rect.height), bitmap_bytes)
        else:
            bitmap_bytes = string_to_bytes(flatten_RGB(self.bitmap))
            img = Image.frombytes('RGB', (self.abs_rect.width, self.abs_rect.height), bitmap_bytes)

        return img

    @property
    def as_XL(self):
        """ Returns a Pillow.Image object, using the layer's bitmap, but expanded to the image's width/height -
        if the layer *has* a bitmap - Group-layers are skipped.
        """

        if self.layer_type not in [layer_types.keGLTRaster, layer_types.keGLTMask]:
            return None

        m_type = 'L' if self.layer_type == layer_types.keGLTMask else 'RGB'
        mask_background = Image.new(m_type, (self.gia['width'], self.gia['height']))
        mask_background.paste(self.as_PIL, (self.abs_rect.tl_x, self.abs_rect.tl_y))

        return mask_background

    def __repr__(self):
        if self.gia['API_FORMAT']:
            return self.api_repr()

        return self.non_api_repr()

    def api_repr(self):

        layer_count = ''
        if self.layer_type == layer_types.keGLTGroup:
            grouped_names = [layer.layer_name for layer in self.grouped]
            layer_count = ", layers = [{0}], names = {1}".format(
                self.group_extension.info_chunk['layer_count'], grouped_names)
        block_str = "{0}.{1}[{2}]: {3:,} bytes, channels = [{4}], name = [{5}]{6}"
        block_str = block_str.format(self.block_type, self.layer_str, self.layer_number,
                                     self.block_length, self.channel_count, self.layer_name, layer_count)

        return block_str

    def non_api_repr(self):

        block_str = "\nLayer[{0}]: {1:,} bytes, type = [{2}], channels = [{3}], name = [{4}]"
        block_str = block_str.format(self.layer_number, self.block_length, self.layer_str, self.channel_count, self.layer_name)

        if self.layer_type == layer_types.keGLTGroup:
            groups = [layer.layer_name for layer in self.grouped]
            block_str += "\n\tGrouped layers: {0}".format(groups)
            return block_str

        if self.gia['VERBOSE']:
            if self.bitmap:
                block_str += "\n\tBitmap[{0} pixels]: {1}".format(len(self.bitmap), str(self.bitmap[:5]))
            if self.rect_mask_bits:
                block_str += "\n\tMask Rect[{0} pixels]: {1}".format(len(self.rect_mask_bits), str(self.rect_mask_bits[:20]))

            if self.grouped:
                block_str += "\n\tGrouped with:       [{0}]".format(self.grouped[0].layer_name)

            rect_str = "\n\t{0:20}topleft = ({1}, {2}), bottomright = ({3}, {4}), width/height = {5}/{6}"

            block_str += rect_str.format("Image Rect:",
                                         self.img_rect.tl_x, self.img_rect.tl_y,
                                         self.img_rect.br_x, self.img_rect.br_y,
                                         self.img_rect.width, self.img_rect.height)
            block_str += rect_str.format("SavedImage Rect:",
                                         self.saved_img_rect.tl_x, self.saved_img_rect.tl_y,
                                         self.saved_img_rect.br_x, self.saved_img_rect.br_y,
                                         self.saved_img_rect.width, self.saved_img_rect.height)

            block_str += rect_str.format("Mask Rect",
                                         self.mask_rect.tl_x, self.mask_rect.tl_y,
                                         self.mask_rect.br_x, self.mask_rect.br_y,
                                         self.mask_rect.width, self.mask_rect.height)
            block_str += rect_str.format("SavedMask Rect",
                                         self.saved_mask_rect.tl_x, self.saved_mask_rect.tl_y,
                                         self.saved_mask_rect.br_x, self.saved_mask_rect.br_y,
                                         self.saved_mask_rect.width, self.saved_mask_rect.height)

        if self.gia['VERBOSE']and self.channels:
            for sb in self.channels:
                block_str += str(sb)

        return block_str

    def save_block_to_file(self, tmp_dir):
        """ Mainly for debugging, saves all the intermediate layer/mask/bitmaps to a temp dir. """

        if self.layer_type != layer_types.keGLTRaster:
            return

        pic_width = self.gia['width']
        pic_height = self.gia['height']

        out_file = os.path.join(tmp_dir, self.layer_name + '--dbitmap_raw.bmp')
        # save_bitmap(out_file, self.bitmap, self.saved_img_rect)
        save_stuff_to_file(out_file, self.as_PIL, 'bmp')

        if self.rect_mask_bits:
            expanded_rect_mask_bits = expand_rect_mask_debug(self.gia, self.rect_mask_bits, self.abs_rect)
            out_file = os.path.join(tmp_dir, self.layer_name + '--expanded_rect_mask.bmp')
            save_rect_mask_debug(out_file, expanded_rect_mask_bits, Rect(0, 0, pic_width, pic_height))

        if self.layer_mask_bits:
            out_file = os.path.join(tmp_dir, self.layer_name + '-group_layer_mask.bmp')
            full_mask = expand_rect_mask_debug(self.gia, self.layer_mask_bits, self.layer_mask_rect)
            save_rect_mask_debug(out_file, full_mask, Rect(0, 0, pic_width, pic_height))
            out_file = os.path.join(tmp_dir, self.layer_name + '-group_layer_rect.bmp')
            save_rect_mask_debug(out_file, self.layer_mask_bits, self.layer_mask_rect)
            out_file = os.path.join(tmp_dir, self.layer_name + '-layer_scaled.bmp')
            save_rect_mask_debug(out_file, self.layer_scaled_bits, self.omega_rect)
            out_file = os.path.join(tmp_dir, self.layer_name + '-layer_final.bmp')
            save_rect_mask_debug(out_file, self.omega_mask, self.omega_rect)

        out_file = os.path.join(tmp_dir, self.layer_name + '--merge_layer.bmp')
        save_layer_merge_debug(self.gia, out_file, self.bitmap, self.omega_rect, self.omega_mask)

        for b in self.channels:
            func = getattr(b, 'save_block_to_file', None)
            if func:
                func(tmp_dir, self.layer_name, self.width, self.height)


class LayerBank(Block):
    def read_any_info_chunks(self, _):
        pass

    def read_any_sub_blocks(self, img_fp):
        layer_count = self.gia['layer_count']

        for x in range(0, layer_count):
            sub_block = Layer(img_fp, self.gia)
            if sub_block.layer_type not in supported_layers:
                if self.gia['VERBOSE']:
                    print ("WARNING: layer type {0} not supported".format(sub_block.layer_str))
                continue
            self.sub_blocks.append(sub_block)

            if self.gia['DEBUG']:
                print ("appended block [{0}]: {1} bytes, name = [{2}]".format(
                    PSP_Block_ID[sub_block.block_id], sub_block.block_length, sub_block.layer_name))

        self.info_chunk = {'layer_count': layer_count}
        self.group_layers_and_gen_masks()
        self.combine_layers()

    def group_layers_and_gen_masks(self):
        """ File format 4 stores a full-layer mask (not rect-mask) in the same layer, as a channel, whereas
            File format 8 stores the layer-mask as an entirely separate layer, but grouped. As a result,
            all of the layers have to be read, before a raster-layer can determine its layer-mask.
        """

        if self.gia['DEBUG']:
            print ("beginning layer and mask-processing. Layer blocks:")
            for block in self.sub_blocks:
                print ("\t{0}".format(block.layer_name))
        for x, block in enumerate(self.sub_blocks):
            block.layer_number = x
            if block.layer_type == layer_types.keGLTGroup:
                group_count = block.group_extension.info_chunk['layer_count']
                if group_count != 2:  # For now, only handling case of raster+mask grouped layers, no sub-groups
                    continue

                bitmap = self.sub_blocks[x + 1]
                mask = self.sub_blocks[x + 2]
                bitmap.grouped.append(mask)
                mask.grouped.append(bitmap)

                block.grouped.append(bitmap)
                block.grouped.append(mask)

        for block in self.sub_blocks:
            if self.gia['DEBUG']:
                print ("generating layer-mask for [{0}]".format(block.layer_name))
            block.generate_layer_mask()

    def combine_layers(self):
        """ Builds up a bitmap from all layers, one at a time, starting with the bottom layer. So transparency masks
        are applied to the lowest level that is visible.
        """

        pic_width = self.gia['width']

        # TODO - going to assume the first layer is the bottom layer, *and* it covered the full width/height - fix later
        self.bitmap = self.sub_blocks[0].bitmap[:]

        for layer in self.sub_blocks[1:]:
            if layer.layer_type != layer_types.keGLTRaster:
                continue

            tl_x = layer.omega_rect.tl_x
            tl_y = layer.omega_rect.tl_y
            for y in range(layer.omega_rect.height):
                for x in range(layer.omega_rect.width):
                    lower_pixel = x + tl_x + (y + tl_y) * pic_width
                    higher_pixel = x + y * layer.omega_rect.width
                    transparent_pixel = apply_mask_to_layer(self.bitmap[lower_pixel], layer.bitmap[higher_pixel], layer.omega_mask[higher_pixel])
                    self.bitmap[lower_pixel] = transparent_pixel
