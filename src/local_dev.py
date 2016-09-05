from image import *


def read_version_08(cur_pic):
    """ Only used for initial development of the code (the 'pics' directory
        isn't included in the Pypi distribution, although it's on Github)
    """

    # Go up a level from current file:
    PIC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sample_pics = ['ship',          # 0
                   'layers_06',     # 1
                   'hexagons',      # 2
                   'hex_mask',      # 3
                   'multi_shapes',  # 4
                   # TODO - fix this:
                   os.path.join('warped', 'randomness'),    # 5
                   os.path.join('warped', 'fubar'),         # 6
                   ]

    cur_pic = 0 if cur_pic >= len(sample_pics) else cur_pic
    pic_in_dir = os.path.join(PIC_DIR, 'pics')
    pic_out_dir = get_or_create_dir(os.path.join(pic_in_dir, 'out'), None, None)

    in_file = os.path.join(pic_in_dir, sample_pics[cur_pic]) + '.pspimage'
    out_file = os.path.join(pic_out_dir, sample_pics[cur_pic]) + '_out.bmp'

    return in_file, out_file


def main_demo(pic_num=0):
    """ Just for local code-testing, pick a random, ah, pic, and put it through its paces... """

    in_file, out_file = read_version_08(pic_num)

    with time_this('Image scanning time'):
        p = PSPImage(in_file)

    with time_this('Bitmap save-time'):
        p.save_as_bitmap(out_file)

    with time_this('PNG save-time'):
        p.save_as_PNG(out_file)

    with time_this('Blocks save-time'):
        p.save_blocks_to_file()

    with time_this('Layers save-time'):
        p.save_layers_to_file()

    p.list_blocks()
