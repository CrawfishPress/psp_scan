## CLI Usage
See [windows-install](https://github.com/CrawfishPress/psp_scan/blob/master/docs/windows.md)
for complete information on setting up virtual environments, paths, etc. The docs
below assume you're running Powershell with the paths correctly set.

### Run program in Windows
Currently the only method is to run as listed below, giving a _module_ path in a
command to Python. (I don't list all that in the docs below, however.):

    python -m psp_scan -h
      or
    python -m psp_scan pics\ship.pspimage -v

If everything is installed correctly, you should see this (or help, if you did `-h`):

    converting: .\pics\ship.pspimage                => C:\repo_dir\psp_scan\ship.png

### CLI Commands-list
Note - as mentioned above, you need to type `python -m psp_scan` to execute the program.
I left it out below just for simplicity. (Also, this is just cut/paste from program's help-output.)

    usage: psp_scan.py [-h] [-f {png,bmp}] [-m MASK] [-i DIR] [-o DIR] [-n] [-x] [-l] [-v] [-t] [file_in]

           psp_scan some_file.pspimage            # converts a single file to .png (default)
           psp_scan some_file.pspimage -m 3       # converts a single file to .png, and uses layer 3 mask in Alpha channel
           psp_scan some_file.pspimage -f bmp     # converts a single file to .bmp

           psp_scan -i some_dir -v                # converts all files (recursively) inside directory, prints output
           psp_scan -i some_dir -o new_dir        # converts all files (recursively) to new directory

           psp_scan -l some_file.pspimage         # lists basic block information for file (add -v for more detail)
           psp_scan -x some_file.pspimage         # expands file into blocks/layers, saves to new directory

    positional arguments:
      file_in                           single file to convert (optional)

    optional arguments:
      -h, --help                        show this help message and exit
      -f {png,bmp}, --format {png,bmp}  format to convert file into (optional, default=png)
      -m MASK, --mask MASK              mask-layer to use for PNG Alpha channel, for single file
      -i DIR, --input-dir DIR           directory to read files from (optional)
      -o DIR, --output-dir DIR          directory to save converted files (optional)
      -n, --non-recursive               read directories non-recursively (default is recursive)
      -x, --expand                      expand file into layers/blocks, save into directory
      -l, --list                        list basic block info (no file conversion) - add -v for more detail
      -v, --verbose                     extra output when processing files

### Operations Summary

  - convert a single file, to one of two formats
  - convert a single file to a PNG file, and specify any layer to use as an Alpha channel mask
  - expand a single file, to its individual layers, or all components (channels/masks), to output files
  - convert an entire directory of files also to a single format (recursively, unless turned off)
  - specify the output directory for converted files for either input-file option 
    - will match the recursive structure of the input directory, if given

If you specify an input directory but not an output directory, it will default to the output directory (so
files will be converted in-place in the directory.)

Output directory will be created if it is specified, but doesn't exist.

Adding additional formats is on my TODO list - it can be done through the API if necessary.

Note: for PNG files, if you specify a single file, you can specify any layer (type raster/mask) by number,
to use as the mask saved to the PNG's Alpha channel. If you specify a directory, or no mask-number,
it will default to the first mask inside the PSP file's Alpha channel. (I have a TODO to apply this
to the input-directory option.)

Also note: if you do use a raster-layer (and not a mask-layer), it gets converted from RGB to
greyscale in a binary manner - pixels are either 0 or 255, totally transparent, or not. I tried
to find a good conversion to greyscale, but with three RGB channels to process, never really got
satisfactory results - so I just punted, and went with an on/off mask, depending on if any pixels were lit.

This doesn't apply to mask-layers, of course, which are already greyscale (or masks saved to the Alpha channel).

### Example of CLI usage and output

[Examples](https://github.com/CrawfishPress/psp_scan/blob/master/docs/examples.png)
