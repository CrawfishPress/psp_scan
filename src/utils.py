from __future__ import print_function

import contextlib
import os
import string
import struct
import sys
import time

from structs import *


def accept(prefix):
    """ Used by Pillow to quickly verify file type (Pillow only used first 16 bytes, however) """
    return prefix == valid_file_marker


def string_to_hex(data_string):
    """ Converts a series of characters into a printable hex string. For debugging output """

    hb = ":".join(string.upper(x.encode('hex')) for x in data_string)
    return hb


def string_to_bytes(data_string):
    """ Converts a series of characters into bytes. """

    sb = ''.join([chr(x) for x in data_string])
    return sb


def flatten_RGB(pixel_triples):
    """ Converts a list of triples [(0, 255,0), ...] into flat list [0, 255, 0, ...] """

    # TODO - this is a kinda kludgy way of flattening lists, itertools.chain might be better
    flattened = []
    _ = [flattened.extend([x[0], x[1], x[2]]) for x in pixel_triples]

    return flattened


def transmute_struct(block_struct):

    block_format = '<' + "".join([val for val in block_struct.values()])
    block_length = struct.calcsize(block_format)

    return block_format, block_length


def read_header(file_fp, block_struct, DEBUG=False):

    header = read_chunk(file_fp, block_struct, DEBUG)
    if header['header_id'] != valid_header_identifier:
        raise SyntaxError("Invalid block-header")

    return header


def read_name(file_fp, name_len, DEBUG=False):

    name_fmt = {'some_name': '{0}s'.format(name_len)}
    name = read_chunk(file_fp, name_fmt, DEBUG)['some_name']

    return name


def read_chunk(file_fp, block_struct, DEBUG=False):
    """ For a given chunk, mash together all the data-fields, with their unpacked values, into a dict.
        For fixed-length objects like headers, the length can be computed from the format string.
    """

    if DEBUG:
        potential_struct = [str(k) for k, v in globals().items() if v == block_struct]
        some_struct = potential_struct if potential_struct else block_struct
        msg = "struct = [{0}]".format(some_struct)
        print (msg)

    block_format, block_length = transmute_struct(block_struct)

    raw_data = file_fp.read(block_length)
    parsed_data = struct.unpack(block_format, raw_data)

    block_field_names = [val for val in block_struct.keys()]
    block_headers = dict(zip(block_field_names, parsed_data))

    return block_headers


def skip_block(file_fp, block_length):
    file_fp.read(block_length)


def more_blocks(file_fp, file_length):
    if file_fp.tell() < file_length:
        return True
    return False


class Rect(object):
    def __init__(self, a, b, c, d):
        """ top_left_x/y value, bottom_right_x/y value... """
        self.tl_x = a
        self.tl_y = b
        self.br_x = c
        self.br_y = d

    @property
    def width(self):
        return self.br_x - self.tl_x

    @property
    def height(self):
        return self.br_y - self.tl_y

    @property
    def coords_api(self):
        foo = {'tl_x': self.tl_x, 'tl_y': self.tl_y, 'br_x': self.br_x, 'br_y': self.br_y}
        return foo

    # TODO fix this, now that coords_api() isn't used
    def __repr__(self):
        return "{0}/{1} - {2}/{3}".format(self.tl_x, self.tl_y, self.br_x, self.br_y)


# TODO - much refactoring, that expand-flag is kludgy
def get_or_create_dir(tmp_dir, file_name, prefix, expand=False):

    if not tmp_dir and not file_name:
        raise ValueError('Must supply a temporary directory parameter (or use a filename instead of file pointer)')

    if not tmp_dir:
        short_name = os.path.splitext(os.path.basename(file_name))[0]
        tmp_dir = os.path.join(os.path.dirname(file_name), prefix + '.' + short_name)
    elif expand:
        short_name = os.path.splitext(os.path.basename(file_name))[0]
        tmp_dir = os.path.join(tmp_dir, prefix + '.' + short_name)

    # http://stackoverflow.com/questions/273192/how-to-check-if-a-directory-exists-and-create-it-if-necessary
    # Interestingly, they prefer doing a try/except block, because of a possible race condition.
    # So - don't manually create the directory at the *exact millisecond* this code is running, or it's borked...
    if not os.path.exists(tmp_dir):
        try:
            os.makedirs(tmp_dir)
        except Exception as e:
            print (e)
            sys.exit(1)

    return tmp_dir


@contextlib.contextmanager
def time_this(section_name):
    """ According to the docs I've seen, returning True eats the Exception,
        returning False (None) re-raises any Exception - but you *can't* return False
        in a generator in Python 2.7? Then it turns out, I'd just as soon trap the Exception,
        so the other lines in main_demo() run...
    """
    start_time = time.time()
    try:
        yield
    except Exception as e:
        print (e)
        # return False
        # pass
    finally:
        time_msg = "{0} = {1:.2f}s".format(section_name, time.time() - start_time)
        print ("\n{0}\n".format(time_msg))
