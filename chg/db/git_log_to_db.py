#!/usr/bin/env python3
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from chg.platform import git
from chg.main import get_store

import tqdm


def log_to_db(store):
    print("Git log to database")
    log_entries = git.log()
    # from oldest to newest
    log_entries = list(reversed(log_entries))
    n = len(log_entries)
    for ix in tqdm.tqdm(list(range(1, n))):
        prev_commit = log_entries[ix - 1]
        curr_commit = log_entries[ix]
        old_hash = prev_commit["abbreviated_commit"]
        new_hash = curr_commit["abbreviated_commit"]

        chunk = git.diff_from_to(old_hash, new_hash)

        question = "Commit: "
        answer = curr_commit["subject"] + curr_commit["body"]
        answered = [(question, answer)]

        chunk_id = store.record_chunk((old_hash, chunk, new_hash))
        store.record_dialogue((chunk_id, answered))


def get_args():
    parser = ArgumentParser(
        description="Record all git commits to chgstructor database",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    return parser.parse_args()


def main():
    _ = get_args()
    store = get_store()
    log_to_db(store)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        import pdb
        pdb.post_mortem()
