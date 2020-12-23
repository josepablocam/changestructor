# Project
Empty readme for now...

# Setup

Run

```
make
```

and make sure to export the following environment variable

```
export CHG_ROOT_DIR=$(pwd)
```

from chgstructor's source root folder.

You may want to add this environment variable to your usual dot files.


Whenever you want to use chgstructor you need to activate it's conda
environment (which we used to avoid clobbering other installs).

```
conda activate changestructor-env
```


# Annotate
After you have staged your git changes (with `git add`), in the
corresponding project's root:

```
chg annotate
```

# Ask
In the corresponding project's root:

```
chg ask
```


# With existing git repo
* At root of project


```
git-to-chg
```

builds chgstructor database.


```
chg-to-index
```

creates a queryable index.
