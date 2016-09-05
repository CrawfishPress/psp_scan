""" Handle command-line functions
Able to convert single files, or full directories
"""

import argparse
from argparse import RawTextHelpFormatter

from image import *


BASE_DIR = os.getcwd()


def run_command_line():
    usage = """
       psp_scan some_file.pspimage            # converts a single file to .png (default)
       psp_scan some_file.pspimage -m 3       # converts a single file to .png, and uses layer 3 mask in Alpha channel
       psp_scan some_file.pspimage -f bmp     # converts a single file to .bmp

       psp_scan -i some_dir -v                # converts all files (recursively) inside directory, prints output
       psp_scan -i some_dir -o new_dir        # converts all files (recursively) to new directory

       psp_scan -l some_file.pspimage         # lists basic block information for file (add -v for more detail)
       psp_scan -x some_file.pspimage         # expands file into blocks/layers, saves to new directory """

    def hp(**kwargs):
        return RawTextHelpFormatter(max_help_position=50, width=120, **kwargs)

    parser = argparse.ArgumentParser(description=usage, formatter_class=hp)

    parser.add_argument('file_in', nargs='?', help='single file to convert (optional)')

    parser.add_argument('-f', '--format', choices=['png', 'bmp'], default='png', help='format to convert file into (optional, default=png)')
    parser.add_argument('-m', '--mask', type=int, help='mask-layer to use for PNG Alpha channel, for single file')
    parser.add_argument('-i', '--input-dir', metavar='DIR', default=BASE_DIR, help='directory to read files from (optional)')
    parser.add_argument('-o', '--output-dir', metavar='DIR', default=None, help='directory to save converted files (optional)')
    parser.add_argument('-n', '--non-recursive', action="store_true", help='read directories non-recursively (default is recursive)')
    parser.add_argument('-x', '--expand', action="store_true", help='expand file into layers/blocks, save into directory')
    parser.add_argument('-l', '--list', action="store_true", help='list basic block info (no file conversion) - add -v for more detail')
    parser.add_argument('-v', '--verbose', action="store_true", help='extra output when processing files')
    parser.add_argument('-t', '--test', action="store_true", help=argparse.SUPPRESS)

    # You would think an empty argument list would *default* to printing help, but no...
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.input_dir and not args.output_dir:
        args.output_dir = args.input_dir

    if not args.test:
        handle_cli(args)

    return args


def cli_expand_file(cli_args):

    in_file = cli_args.file_in
    if not in_file:
        raise ValueError("filename required to expand")

    out_dir = cli_args.output_dir
    layer_dir = get_or_create_dir(out_dir, in_file, 'layers', expand=True)
    block_dir = get_or_create_dir(out_dir, in_file, 'blocks', expand=True)

    p = PSPImage(in_file)
    p.save_layers_to_file(layer_dir)
    p.save_blocks_to_file(block_dir)


def cli_list_file(cli_args):

    cli_options = {'VERBOSE': False, 'API_FORMAT': False}
    cli_options['VERBOSE'] = True if cli_args.verbose else False

    in_file = cli_args.file_in
    p = PSPImage(in_file, cmd_options=cli_options)
    p.list_blocks()


def cli_single_file(cli_args):
    """ Saves a single file, to specified output directory (possibly created), in a specified format. """

    in_file = cli_args.file_in
    _, base_file = os.path.split(in_file)
    format_str = '.bmp' if cli_args.format == 'bmp' else '.png'
    base_file = base_file.replace('.pspimage', format_str)
    out_dir = get_or_create_dir(cli_args.output_dir, None, None)
    out_file = os.path.join(out_dir, base_file)
    mask_num = cli_args.mask

    if cli_args.verbose:
        print ("converting: {0}{1}=> {2}".format(in_file, ' ' * (70 - len(in_file)), out_file))

    p = PSPImage(in_file)
    func = p.save_as_bitmap if cli_args.format == 'bmp' else p.save_as_PNG
    func(out_file, mask_num)


def cli_many_files(cli_args):
    """ Saves all files, from specified directory, to specified directory, in a specified format.
        Recurses down the input directory, unless specified otherwise.
    """

    in_dir = cli_args.input_dir
    out_dir = get_or_create_dir(cli_args.output_dir, None, None)
    is_verbose = cli_args.verbose

    files = walk_dir(cli_args, out_dir, os.walk)

    if not len(files):
        if is_verbose:
            print ("no files found in directory [{0}]".format(in_dir))
        return

    # I got tired of PyCharm telling me "'file' is overshadowing another variable" - so fyle, it is...
    FileData = collections.namedtuple('FileData', ['in_file', 'out_file', 'out_dir'])
    fyles = [FileData(*fyle) for fyle in files]
    max_size = max([len(fyle.in_file) for fyle in fyles]) + 5

    for fd in fyles:
        if is_verbose:
            print ("converting: {0}{1}=> {2}".format(fd.in_file, ' ' * (max_size - len(fd.in_file)), fd.out_file))
        try:
            p = PSPImage(fd.in_file)
            get_or_create_dir(fd.out_dir, None, None)
            func = p.save_as_bitmap if cli_args.format == 'bmp' else p.save_as_PNG
            func(fd.out_file)
        except Exception as e:
            print ("skipping file [{0}]:".format(fd.in_file))
            print ("\t", e)


def warp_dirs(top_dir, full_dir, new_dir):
    """ Given one top directory, and a full-directory-path starting in that directory (possibly multiple levels),
        and a desired new top-level directory, replace the entire top-level component in the "full" directory
        with the new directory: Example:
        /pics/alpha           # top
        /pics/alpha/hexes     # full dir
        foo                   # given new dir-string
        /foo/hexes            # desired output

        foo/bar               # could also be multi-level new dir
        /foo/bar/hexes        # would be output
        Basically, copy the existing directory structure, but to a new name. Any directory can have multiple levels.
        Note: should only be called when full-dir is a superset of top-dir (never called on the top-level dir).
    """

    # Windows allows for 'foo/bar\alpha'
    top_dir = os.path.normpath(top_dir)
    full_dir = os.path.normpath(full_dir)
    new_dir = os.path.normpath(new_dir)

    top_pieces = top_dir.split(os.sep)
    full_pieces = full_dir.split(os.sep)
    new_pieces = new_dir.split(os.sep)

    top_split = len(top_pieces)
    full_trunc = full_pieces[top_split:]
    new_combined = new_pieces + full_trunc
    new_dir = os.path.join(*new_combined)

    return new_dir


def walk_dir(cli_args, out_dir, walker):
    """ Generates a list of triples - [(input_file, output_file, output_dir)] for files in the directory,
        that are of type '.pspimage', recursively (or not, per the flag). Also replaces the 'pspimage' with
        the correct format type (bmp/png).
    """

    in_dir = cli_args.input_dir
    format_str = '.bmp' if cli_args.format == 'bmp' else '.png'
    no_recurse = cli_args.non_recursive

    files = []
    for some_dir, sub_dirs, file_list in walker(in_dir):
        if some_dir == in_dir:  # Then this is the top-level dir
            tmp_files = [(os.path.join(some_dir, fyle), os.path.join(out_dir, fyle), out_dir)
                         for fyle in file_list if fyle.endswith('.pspimage')]
            files.extend(tmp_files)
        else:
            if no_recurse:
                break
            # Replace top-level dir with output dir
            dir_minus = warp_dirs(in_dir, some_dir, out_dir)
            tmp_files = [(os.path.join(some_dir, fyle), os.path.join(dir_minus, fyle), dir_minus)
                         for fyle in file_list if fyle.endswith('.pspimage')]
            files.extend(tmp_files)

    new_files = [(fyle[0], fyle[1].replace('.pspimage', format_str), fyle[2]) for fyle in files]

    return new_files


def handle_cli(cli_args):

    if cli_args.expand:
        cli_expand_file(cli_args)
    elif cli_args.list:
        cli_list_file(cli_args)
    elif cli_args.file_in:
        cli_single_file(cli_args)
    else:
        cli_many_files(cli_args)
