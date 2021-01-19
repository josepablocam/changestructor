# Project
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
* curses UI
  - CLI UI but nicer than the plain text stuff right now. I ran into some issues
  getting diff ASCII color espace sequences to work here, so punted for now
* Browser UI
  - This should become the main UI (at least for demo), but haven't start anything here.
* Real annotator
  - We can start with template based questions for now, but will want to improve here at some point.
* Debug FAISS lookups (really slow right now for some reason)


# Ideas
* For purposes of dialogue generation, we can source info (e.g. entity names) from:
  - the modified code (i.e. the patch)
  - the files modified (e.g. basic call graph -- can then ask questions about any
    other functions with edge to the modified one, e.g. does this break function X?)
  - repo issues/pull requests


# Optimization Idea
* How do we judge if a commit message is good?
  - It should be "reflective" of the code it is committing
  - Let's define "reflective" as the ability of retrieving the changeset using
  this commit message from a set of (changeset, commit message)

* Concretely:
  - Given a dataset of D = {(changeset, commit messages)},
  a function F to compute similarity between a changeset and msg,
  the current commit c and the accompanying commit message m,
  maximize F(c, m) and minimize F(c' in D, m)

* Practical options:
  - Option 1: Binary outcome -> ensure we can retrieve c within the top K
  commits when sorting commits based on their similarity with m
  - Option 2: Ordinal -> minimize the rank of c (lower better) when sorting
  commits based on their similarity with m
  - Option 3: "Soft" variants of (1) and (2) -> randomly sample N negative examples (i.e.
    N commits that are not c), and then use option (1) or (2)
    - Much cheaper
    - Can repeat N times given random sampling

* Given this criteria, (assuming commit message derived from dialogue) we can no:
  - Decide when to stop the bot dialogue:
    - e.g. binary outcome: once satisfied
    - e.g. ordinal outcome: after no improvement in rank
  - Decide which questions to ask:
    - Treat question template as multi-armed bandit
    - Reward: improvement in similarity metric for message after the answer
    to question is integrated into commit message
    - Can use standard MAB to choose template to ask


## Implementation needed
### Templatized questions
  * Create questions as templates with holes for program info (e.g. variables and functions) that need to be populated
  * Questions for now can be served in fixed order
  * Fill holes by enumerating questions with program info

Need to:
  - design templates that are useful
  - implement program info retrieval
  - implement template filling


### Commit message generation
  * Currently users write their commit message. But we have talked about
  using dialogue to produce a commit message
  * Simplest option: concatenate questions and answers and return as commit message

Need to:
  - minor change in current annotators (i.e. question/answering bot) to produce
  concatenation


### Scoring current commit message
  * Compute similarity for commit message and changeset
  * Choose one of the goals described above in optimization

Need to:
  - we can use the current "semantic search" (chg/search/embedded_search.py)
  approach of using cosine similarity over an embedded version of message and changeset
  - change the build_semantic_db.sh to include the changeset when computing embeddings
  (simplest thing we could do: concatenate code changeset and natural language in single line)


Once we have these, we can implement the stopping criteria and then MAB over templates
for question generation.
