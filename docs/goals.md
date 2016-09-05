## Origin
I first started this project when I was attempting some game-development (ahem). 
Many game-engines use PNG files, with an Alpha channel containing a transparency-mask,
so shapes _other_ than rectangles can be shown on the screen (computers do like their rectangles).
I used (and still use) PaintShop Pro - an excellent piece of software, IMHO, not to mention cheaper
than Adobe Photoshop (which the rest of the world seems to use).

I found myself editing a lot of .psp files, with one main bitmap, and one mask-layer 
(separated for editing), which I would then save the mask-layer to the Alpha channel and save
the entire file as a PNG. This worked fine, but involved a lot of manual steps. So I looked around
to see if there was a way of automating it. PIL is another excellent package, but it doesn't
handle .psp files (yet - adding this code to it, is on my TODO list). I couldn't find anything,
so started researching/writing some code. I've been working on-and-off for years, not sure
how long it's taken, but probably months total. Which brings up:

## Relevant XKCD cartoon:
https://xkcd.com/1319/

## General Goal
Simplify converting .psp files into .png files that had Alpha-channels with transparency-masks.

Granted, the time saved manually converting files, will probably never equal the development-time of this code,
but xkcd notwithstanding, not only can I do what I originally tried to automate, but a lot of other things.
Once you've parsed a .psp file enough to convert it, you can do a lot with the data,
and it's a lot faster to code new functions. 

Plus, other people can also use the library - 
I like to think I'm not the _only_ person using Paintshop Pro, rather than Adobe Photoshop. :)
