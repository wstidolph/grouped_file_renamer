# grouped_file_renamer

Usage: `python3 gfr.py --help`

Command line utility to rename files in directories (or trees) according to a per-directory ordering file
while retaining grouping based on the ID field in the existing file names.

Usage: see --help

## Renaming in directories
Here's the driving use case: Epson's scanner software scans groups of photos into a directory (let's say `FOO`) and gives each photo file a name with a structure incorporating an ID, but the ID is based on scan order and as a photo publisher I want to rename the files so they show up in my operating system's user interface with the order I want (based on the file names)

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
This is fine ... the photos display in the order you want, in tha tprgram (FastSTone or whatever). But, the operating system doesn't care about that order file - that's only for the third-party program to use! So if you just open the directory in your File Explorere or Finder or list them in your terminal, they're not in your desired order.

So then, use this program to rename the scanner files to follow the order file listing: something like this command line (depending on how you invoke python scripts in your environment):

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

Suppose you just scan many files into an `in` directory, then drag and drop them into many different directories (and then maybe sort the files in each directory):
```
vacation/in_0001_a.jpg
vacation/in_0123.jpg
vacation/in_0123_b.jpb
vacation/.fssort.ini <= controls order just in vacation
work_party/in_0002.jpg
work_party/in_0002_a.jpg
work_party/.fssort.ini <= controls order just in work_party
```
So now you want to start renaming at a root directory but decend into the driectories below (e.g., descend into `vacation` and `work_party`):

``~/scans python3 gfr.py --do-subtree rename FOO` 

When renaming, the generated name starts with a prefix, and the default is the name of the directory, and the default is to resart the ID number field in each directory (you have controls for all those) so these will be renamed something like:
```
vacation/vacation_i0010_a.jpg
vacation/vacation_i0020.jpg
vacation/vacation_i0020_b.jpb
work_party/work_party_i0010.jpg
work_party/work_party_i0010_a.jpg
```
Now if you grab files and toss them the same folder (for example, `pictures`), their name keeps them grouped, and the ID field/suffix keeps them ordered with the group:

```
pictures/vacation_i0010_a.jpg
pictures/vacation_i0020.jpg
pictures/vacation_i0020_b.jpb
pictures/work_party_i0010.jpg
pictures/work_party_i0010_a.jpg
```

If you don't want to use the directories you grouped them with, you can just specify your own prefix, and let the ID counter increment between directories:
```
vacation/P_5_i0010_a.jpg
vacation/P_5_i0020.jpg
vacation/P_5_i0020_b.jpb
work_party/P_5_i0030.jpg
work_party/P_5_i0030_a.jpg
```

## Renaming if no sort file
You don't have to have a sort order; maybe you don't care about the order of file groups within the directory, you just want to get the directory name into the group filename. And maybe some directories you sorted but others you didn't care. So, you can use the `--skip-if-no-orderfile` option ... if it's set (as is the default) then the program doesn't alter that directoty, but if `--no-skip-if-no-orderfile` then directories without an orderfile will be processed. With no order file, the program falls back on whatver order the file system has the files (probably alphabetic by filename).

## Undo
After the renaming, every directory in which renaming occurred holds a file named `rename_history.csv` and the ordering file is renamed (by appending the date/time of the renaming). In the event you do multiple renames, you'll end up with multiple `rename_history_<datetime>.csv` files. The program then supports:
`~/scans python3 gfr.py undo FOO` to read in the latest rename history and revert all the renames (and delete the `rename_history.csv` file) so you're back where you started. 

The program does not descend into or beyond a list of excluded subdirectories (from file `.gfr.ignore`):
```
.git
.vscode
__pycache__
```

On each useage the program renames the ordering file (if it exists)
and writes a rename_history from/to CSV file.

### NOTE: partly written to force me into learning some Python (3.11),
so apologies if coding sucks/is non-Pythonic (suggestions for improvement?)

# Future
This has met my needs, but as part of learning more Python I expect to tackle:
* ~~modularize (`rename`, `undo`, `topshell`, and `support` modules I think)~~
* ~~tests covering UNDO~~
* ~~adopt python logging~~
* filtering on extension as well as embedded-ID
* add a simple per-directory flag/control file (`.gfr-control.ini`) to skip the dir, set different id-regex, whatever

