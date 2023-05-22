# grouped_file_renamer

Usage: `python3 gfr.py --help`

Rename files in directories (or trees) according to a per-directory ordering file
while retaining grouping based on the ID field in the existing file names.

Usage: see --help

## Renaming in directories
Here's the driving use case: Epson's scanner software scans groups of photos into a directory (let's say `FOO`) and gives each photo file a name with a structure incorporating an ID, but the ID is based on scan order and as a photo publisher I want to rename the files.

The filenames are structured in each directory with the directory name as a prefix, a sequential ID, and then an optional suffix that tells whether the image file is:
* the raw scan (no suffix) or
* an enhanced version (the `_a` suffix) or
* something found on the back of the photo (the `_b` suffix)

The pattern is like `<dir>/<prefix>_<ID>_<suffix>.<ext>`

So after a couple group scans you end up with a tree like:

```
scans\FOO\FOO_0001.jpg
scans\FOO\FOO_0001_b.jpg
scans\FOO\FOO_0002.jpg
scans\FOO\FOO_0002_a.jpg
scans\FOO\FOO_0002_b.jpg
scans\FOO\FOO_0003.jpg

(starting a new scan group)
scans\BAR\BAR_0001.jpg
scans\BAR\BAR_0001_b.jpg
scans\BAR\BAR_0002.jpg
scans\BAR\BAR_0002_a.jpg
```

Maybe you are OK with the order of the `BAR` files, but in the `FOO` dir you wish that image `FOO_0003.jpg` would be first. So, you use some third party tool to generate a simple text file in the `FOO` dir listing the file in the order you want (I am impressed with [FastStone](https://www.faststone.org/index.htm), which creates the order file as `.fssort.ini`) looking like:
```
FOO_0003.jpg
FOO_0001.jpg
FOO_0001_b.jpg
FOO_0002.jpg
FOO_0002_a.jpg
FOO_0002_b.jpg
```
and then use this program to rename the scanner files

`~/scans python3 gfr.py rename FOO` (accepting defaults for how to handle the new ID field)

So:
```
FOO_0003.jpg   -> FOO_i0010.jpg
FOO_0001.jpg   -> FOO_i0020.jpg
FOO_0001_b.jpg -> FOO_i0020_b.jpg
FOO_0002.jpg   -> FOO_i0030.jpg
FOO_0002_a.jpg -> FOO_i0030_a.jpg
FOO_0002_b.jpg -> FOO_i0030_b.jpg
```

The program also enforces the name grouping even if the ordering file has
split the group (the programs lists the groups in the order of first encounter in the ordering file). For example, if the ordering file lists

```
FOO_0003.jpg
FOO_0001.jpg
FOO_0001_b.jpg
FOO_0002.jpg
FOO_0004.jpg
FOO_0002_a.jpg
FOO_0002_b.jpg
FOO_0004_b.jpg
```
then the new names will be assigned:
```
FOO_0003.jpg   -> FOO_i0010.jpg
FOO_0001.jpg   -> FOO_i0020.jpg
FOO_0001_b.jpg -> FOO_i0020_b.jpg
FOO_0002.jpg   -> FOO_i0030.jpg
FOO_0002_a.jpg -> FOO_i0030_a.jpg
FOO_0002_b.jpg -> FOO_i0030_b.jpg
FOO_0004.jpg   -> FOO_i0040.jpg
FOO_0004_b.jpg -> FOO_i0040_b.jpg
```
Using command line options you can change the way the the ID field is prefixed, where it starts, how many characters it pads out to, and what is the step size.


The program doesn't blindly apply renaming to all files; it only renames files which meet a regular expression you pass in, called the `id-regex`. The default is `\d{2,5}` meaning "a string of  2 to 5 digits" so files with names like "my letter.doc" or "my_letter_3.doc" won't be renamed, but "my_letter_003.doc" would be renamed.

## After-Scan sorting

Another use is to all after-scan sorting. SUppose you just scan many files into an `in` directory, then drag and drop them into many different directories (and then maybe sort the diles in each directory). So now you have the "topic" in the directoy name, but not in the file name:
```
vacation/in_0001_a.jpg
vacation/in_0123.jpg
vacation_in_0123_b.jpb
work_party/in_0002.jpg
work_party/in_0002_a.jpg
```

When renaming, the generated name starts with a prefix, and the default is the name of the directory, and the default is to resart the ID number field in each directory (you have controls for all those) so these will be renamed something like:
```
vacation/vacation_i0010_a.jpg
vacation/vacation_i0020.jpg
vacation/vacation_i0020_b.jpb
work_party/work_party_i0010.jpg
work_party/woork_party_i0010_a.jpg
```
Now if you grab files and toss them the same folder, their name keeps them grouped, and the ID field/suffix keeps them ordered with the group.

## Undo
After the renaming, the `FOO` directory holds a file named `rename_history.csv` and the ordering file is renamed (by appending the date/time of the renaming); the program then supports:
`~/scans python3 gfr.py undo FOO` to read in the rename history and revert all the renames (and delete the `rename_history.csv` file) so you're back where you started.

The program does not descend into or beyond a list of excluded subdirectories:
```
.git
.vscode
__pycache__
```

On each useage the program renames the ordering file (if it exists)
and writes a rename_history from/to CSV file. Future plans include an "undo"

### NOTE: partly written to force me into learning some Python (3.11),
so apologies if coding sucks/is non-Pythonic (suggestions for improvement?)

# Future
This has met my needs, but as part of learning more Python I expect to tackle:
* modularize (`rename`, `undo`, `topshell`, and `support` modules I think)
* tests covering UNDO
* filtering on extension as well as embedded-ID

