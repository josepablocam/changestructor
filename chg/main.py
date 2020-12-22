from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os

from chg.platform import git as git_platform
from chg.chunker import git as git_chunker
from chg.annotator.template_annotator import FixedListAnnotator
from chg.dialogue import basic_dialogue
from chg.db import database
import chg.defaults

from chg.ui import (
    simple_cli_ui,
)

DEBUG = False


def annotate(chunker, store, annotator, ui, platform):
    for chunk in chunker.get_chunks():
        ui.display_chunk(chunk)
        annotator.consume_chunk(chunk)

        answered = []
        while not annotator.done():
            question = annotator.ask()
            chunk_update = annotator.get_chunk_update()
            ui.display_chunk_update(chunk_update)
            ui.display_question(question)

            answer = ui.prompt("")
            annotator.consume_answer(answer)
            answered.append((question, answer))

        # (current hash, chunk)
        old_hash = platform.hash()
        if annotator.has_commit_message():
            generate_msg = ui.prompt("Generate commit msg?", ["Y", "n"])
            if generate_msg == "Y":
                msg = annotator.get_commit_message()
            else:
                msg = ui.prompt("Commit message: ")
        else:
            msg = ui.prompt("Commit message: ")
            # if user writes commit message, we should take that
            # as more info for db
            answered.append(("Commit message", msg))

        if not DEBUG:
            chunker.commit(msg)

        new_hash = platform.hash()

        chunk_id = store.record_chunk((old_hash, chunk, new_hash))
        store.record_dialogue((chunk_id, answered))


def ask(ui, store, search, k):
    try:
        while True:
            user_question = ui.prompt("Question:")
            results = search.search(store, user_question, k=k)
            for r in results:
                ui.display_search_result(r)
    except KeyboardInterrupt:
        return


def index_existing():
    # pass
    # take existing git log
    # take diff for each as chunk
    # take commit message as dialogue, answer: "what is this commit about?"
    pass


def get_chunker(args):
    if args.chunker == "single":
        return git_chunker.SingleChunk()
    elif args.chunker == "file":
        return git_chunker.FileBasedChunker()
    else:
        raise ValueError("Unknown chunker:", args.chunker)


def get_store(args):
    if not os.path.exists(chg.defaults.CHG_PROJ_DIR):
        print("Creating folder for chg at", chg.defaults.CHG_PROJ_DIR)
        os.makedirs(chg.defaults.CHG_PROJ_DIR)
    db_path = chg.defaults.CHG_PROJ_DB_PATH
    return database.Database(db_path)


def get_annotator(args):
    if args.annotator == "fixed":
        return FixedListAnnotator(basic_dialogue.QUESTIONS)
    else:
        raise ValueError("Unknown annotator:", args.annotator)


def get_ui(args):
    if args.ui == "cli":
        return simple_cli_ui.SimpleCLIUI()
    else:
        raise ValueError("Unknown ui:", args.ui)


def get_args():
    parser = ArgumentParser(
        description="chgstructor: dialogue-based change-set annotation",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    # annotate only for now
    parser.add_argument(
        "-c",
        "--chunker",
        type=str,
        choices=["single", "file"],
        help="Chunking approach",
        default="file"
    )
    parser.add_argument(
        "-u",
        "--ui",
        type=str,
        choices=["cli"],
        help="UI for interaction",
        default="cli"
    )
    parser.add_argument(
        "-a",
        "--annotator",
        type=str,
        help="Type of annotator",
        choices=["fixed"],
        default="fixed"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Set debug flag",
    )

    return parser.parse_args()


def main():
    args = get_args()

    if args.debug:
        global DEBUG
        DEBUG = True

    chunker = get_chunker(args)
    store = get_store(args)
    annotator = get_annotator(args)
    ui = get_ui(args)
    global UI
    UI = ui
    # only supporting git for now...
    annotate(chunker, store, annotator, ui, platform=git_platform)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        import pdb
        pdb.post_mortem()
