# Project

    test
`changestructor` overview.

# Docker setup
The easiest way to get setup, for development, will be to use the
provided docker container. You should install Docker, if you don't already
have it on your machine.

Once you have done so, you can call

```
make docker
```

to build the container.

You can then launch the container with


```
docker run -it chg-container
```

and then just make sure to append `--ui cli` to both `chg annotate`
and `chg ask`. (We have not yet setup propert X11 forwarding to use
the Tkinter UI).

# Standard Setup

Run

```
make
```

and make sure to add the following to your PATH variable

```
export PATH=${PATH}:$(realpath bin/)
```

from `changestructor`'s source root folder. You can do this
by just running

```
source init.sh
```

You may want to add this environment variable to your usual dot files
instead of running this script each time.


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

will bring up the (very simple) UI for question asking.


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

creates a queryable index and trains a question ranker, as such
you should run this step before you start using chg. You may
also want to run this command periodically to update the system.

# Some `chg` details
* Much like git, chg creates a folder (`.chg`) in the same location as
corresponding `.git` folder.
* The `.chg` folder contains:
  * a sqlite database of dialogue, change chunks and pre-computed
  embeddings (`db.sqlite3`)
  * semantic search related artifacts:
    - `faiss.db` a FAISS indexed version of change chunk embeddings for fast lookups
  * dialogue artifacts:
    - `ranked.pkl` a question ranking model


# Source code overview
* `bin/` holds top-level scripts that the user calls, user should not touch any other code
* `install.sh` installs necessary software etc, user interacts with it only through `make`
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
* Use https://github.com/vitsalis/pycg to statically create call graph use for further template-ized term suggestions
* curses UI
  - CLI UI but nicer than the plain text stuff right now. I ran into some issues
  getting diff ASCII color escape sequences to work here, so punted for now
* Browser UI
  - This should become the main UI (at least for demo), but haven't start anything here.
* Real annotator
  - We can start with template based questions for now, but will want to improve here at some point.
* Debug FAISS lookups (really slow right now for some reason)
* Need to have a way for users to signal they are done answering questions (rather than a predefined question number)

# Ideas
* For purposes of dialogue generation, we can source info (e.g. entity names) from:
  - repo issues/pull requests

## Related Work/ Motivation
* https://people.csail.mit.edu/mjulia/publications/The_Challenges_of_Staying_Together_While_Moving_Fast_2016.pdf


## Implementation needed
### Templatized questions
  * Create questions as templates with holes for program info (e.g. variables and functions) that need to be populated
  * Fill holes by enumerating questions with program info

Need to:
  - design templates that are useful
  - implement program info retrieval
  - implement template filling


### Commit message generation
  * Currently users write their commit message. But we have talked about
  using dialogue to produce a commit message
  * Simplest option: concatenate questions and answers and return as commit message
