# Source:
ftp://ftp.corel.com/pub/documentation/PSP/PSP%20File%20Format%20Specification%208.pdf.zip
 - September, 2005
 - Paint Shop Pro (PSP) File Format Version 8.0
 - Paint Shop Pro Application Version 10.0 (or PSP X)
 - File Format Documentation Version 8.0

# General Block Information

A PSP file is Block-oriented, and consists of a File Header, followed by assorted Blocks (up to ten main types)
Blocks are hierarchical, with some blocks (usually called xxxBank), having sub-blocks.

## Blocks
The term "block" refers to a part of a PSP file that consists of a Block Header
and *all* the data following the header that is contained in the block. Since the Block Header
indicates the size of the data, it is easy to determine how much of the data immediately following
the block header is associated with it. Most blocks also have a data/info "chunk" immediately following the
header - the chunk-length varies between block-types - the original devs wanted to keep the block header a
fixed-length for all blocks, so you could skip unwanted blocks quickly.

## Sub-blocks
A sub-block is a block that is fully contained within another block. It has the full structure of a block,
including header/info chunks, etc. Whereas a chunk is described as: "an 'interesting' piece of data within
a PSP file that does not have a block header". (Since it's the header that describes the length of data,
a chunk's length has to be determined from its structure.)

# Top-level blocks
- File Header (required)
- General Image Attributes Block (required)
- Extended Data Block
- Tube Data Block
- Creator Data Block
- Composite Image Bank Block (contains merged-layers final image, and possibly thumbnails)
- Color Palette Block (paletted image documents only)
- Layer Bank Block (required - source of actual bitmap data)
- Selection Block
- Alpha Bank Block (may contain transparency-masks)

## Block
- Block Header
  - fixed-length
  - identical across blocks
  - has length of entire data-portion of block (so everything except 10-byte header)
- Block Info Chunk
  - most are fixed-length, a few are variable-length (name-fields vary)
  - different for each block type
  - describes the following content chunk
- Content Chunk
  - optional
  - variable-length
  - may contain sub-blocks

# Specific Main Blocks

## File Header (required)
Valid PSP Header must start with "Paint Shop Pro Image File\n\x1a" padded with zeros to 32 bytes.

## General Image Attributes Block (required)
- Block Header
- General Image Attributes Chunk
  - contains image width/height, layer count, etc

## Layer Bank Block (required)
- Block Header
- no info-chunk here? Weird - the count of following layer blocks has to come from the GIA block
- Array of: Layer Sub-Blocks
  - Layer Sub-Block 1
  - ...
  - Layer Sub-Block N

### Layer Sub-Block
- Block Header
- Layer Information Chunk (variable-length)
- Layer Extension Sub-Block (optional, only in Mask/Group/Adjustment/Vector/etc layers)
- Layer Bitmap Chunk (this is really just another Information Chunk, contains channel-count)
- Array of: Layer Channel Blocks
  - Channel Block 1
  - ...
  - Channel Block N

### Layer Extension Blocks (Supported):

#### Group Layer Sub-Block
- Block Header
- Group Layer Information Chunk

#### Mask Layer Sub-Block
- Block Header
- Mask Layer Information Chunk

## Alpha Bank Block (optional)
- Block Header
- Alpha Bank Information Chunk
- Array of: Alpha Channel Blocks
  - Alpha Channel 1
  - ...
  - Alpha Channel N

### Alpha Channel Block
- Block Header
- Alpha Channel Information Chunk (variable-length)
- Alpha Channel Chunk
- Channel Block

## Channel Block
- Block Header
- Channel Information Chunk
- Channel Content Chunk (variable-length, compression=none|rle|lz77)
