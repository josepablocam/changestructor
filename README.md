# Project
`changestructor` overview.

# Setup

Run

```
make
```

and make sure to add the following to your PATH variable

```
export PATH=${PATH}:$(realpath bin/)
```

from `changestructor`'s source root folder.

You may want to add this environment variable to your usual dot files.


# Annotate
After you have staged your git changes (with `git add`), in the
corresponding project.

```
chg annotate
```

# Ask
Similarly, within the same git repository subtree

```
chg ask
```

will bring up the (very simple) CLI for question asking.
You can exit with standard ctrl+c or ctrl+d.


# Build from an existing git repo
The idea here is that we take the git log and:
  * consider diffs between commits as chunks
  * commit messages as dialogue answering the question *"Commit: "*


```
git-to-chg
```

builds `changestructor` database.


```
chg-to-index
```

creates a queryable index.

# Some `chg` details
* Much like git, chg creates a folder (`.chg`) in the same location as
corresponding `.git` folder.
* The `.chg` folder contains:
  * a sqlite database of dialogue and chunks (`db.sqlite3`)
  * semantic search related artifacts:
    - `db.txt` a text version of the dialogues table
    - `embeddings.bin` a fasttext embeddings model to map dialogue to vectors
    - `db.vec` an embedded version of the text dialogue
    - `faiss.db` a FAISS indexed version of the vectors for fast lookups


# Source code overview
* `bin/` holds top-level scripts that the user calls, user should not touch any other code
* `build.sh` installs necessary software etc, user interacts with it only through `make`
* `chg/` is the root package directory. The idea of the structure here is to be somewhat
self explanatory.


# Development
If you want to make source changes, you will likely want to make you activate
the corresponding conda environment (installed and built during `chg` installation)
by running

```
source chg/scripts/defaults.sh
conda activate ${CHG_CONDA_ENV}
```


# TODOs
* Make sure the git wrapper handles standard things without issues: (Jose)
  - adding new files
  - removing files
  - renaming files
  - modifying existing file
  - wrap these up in a proper test suite
* Tkinter UI (Jose)
  - Nicer UI, but not browser based
* curses UI
  - CLI UI but nicer than the plain text stuff right now. I ran into some issues
  getting diff ASCII color espace sequences to work here, so punted for now
* Browser UI
  - This is the main UI (at least for demo), but haven't start anything here.
* Real annotator
  - We can start with template based questions for now, but will want to improve here at some point.
* Debug FAISS lookups (really slow right now for some reason)
*
