from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os

from chg.platform import git as git_platform
from chg.chunker import git as git_chunker
from chg.annotator.template_annotator import FixedListAnnotator
from chg.dialogue import basic_dialogue
from chg.db.database import get_store
from chg.search.embedded_search import EmbeddedSearcher
import chg.defaults

from chg.ui import (
    simple_cli_ui,
)

DEBUG = False


def annotate(chunker, store, annotator, ui, platform):
    for chunk in chunker.get_chunks():
        # show chunk to user initially
        ui.display_chunk(chunk)
        # annotater gets access to chunk
        # so can produce relevant questions
        annotator.consume_chunk(chunk)

        answered = []
        while not annotator.done():
            question = annotator.ask()
            # annotator may want to update the display
            # for the chunk based on the question
            # (e.g. may want to highlight a portion of the chunk)
            chunk_update = annotator.get_chunk_update()
            ui.display_chunk_update(chunk_update)

            ui.display_question(question)

            answer = ui.prompt("")
            # annotator can update its internal state
            # based on answer (e.g. new question based on previous answer)
            annotator.consume_answer(answer)
            answered.append((question, answer))

        # changes induced by the chunk (i.e. this diff)
        # are committed directly by `chg` (i.e. the user
        # no longer needs to interact with `git commit`)
        old_hash = platform.hash()
        # some annotators may want to generate the commit message
        # directly from the user's dialogue
        # rather than prompt user for explicit commit message
        if annotator.has_commit_message():
            # but user can always override
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

        # just for dev
        if not DEBUG:
            chunker.commit(msg)

        new_hash = platform.hash()
        # info is only stored in the database after the commit
        # has taken place
        # TODO: if the user exits or crashes before this
        # the file system will reflect git changes, but not
        # any info in chg database, we should fix this...
        chunk_id = store.record_chunk((old_hash, chunk, new_hash))
        store.record_dialogue((chunk_id, answered))


def ask(ui, searcher, k=5):
    try:
        while True:
            user_question = ui.prompt("Question: ")
            results = searcher.search(user_question, k=k)
            for r in results:
                ui.display_search_result(r)
    except (EOFError, KeyboardInterrupt):
        return


def get_chunker(args):
    if args.chunker == "single":
        return git_chunker.SingleChunk()
    elif args.chunker == "file":
        return git_chunker.FileBasedChunker()
    else:
        raise ValueError("Unknown chunker:", args.chunker)


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


def get_searcher(args):
    root_dir = git_platform.root()
    searcher = EmbeddedSearcher(
        os.path.join(root_dir, chg.defaults.CHG_PROJ_FASTTEXT),
        os.path.join(root_dir, chg.defaults.CHG_PROJ_FAISS),
    )
    return searcher


def get_args():
    parser = ArgumentParser(
        description="chgstructor: dialogue-based change-set annotation",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    # shared across actions
    parser.add_argument(
        "-u",
        "--ui",
        type=str,
        choices=["cli"],
        help="UI for interaction",
        default="cli"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Set debug flag",
    )

    subparsers = parser.add_subparsers(help="chg actions")

    annotate_parser = subparsers.add_parser("annotate")
    annotate_parser.set_defaults(action="annotate")
    annotate_parser.add_argument(
        "-c",
        "--chunker",
        type=str,
        choices=["single", "file"],
        help="Chunking approach",
        default="file"
    )
    annotate_parser.add_argument(
        "-a",
        "--annotator",
        type=str,
        help="Type of annotator",
        choices=["fixed"],
        default="fixed"
    )

    ask_parser = subparsers.add_parser("ask")
    ask_parser.set_defaults(action="ask", debug=False)

    return parser.parse_args()


def main_annotate(args):
    chunker = get_chunker(args)
    store = get_store()
    annotator = get_annotator(args)
    ui = get_ui(args)
    # only supporting git for now...
    annotate(chunker, store, annotator, ui, platform=git_platform)


def main_ask(args):
    searcher = get_searcher(args)
    ui = get_ui(args)
    ask(ui, searcher, k=5)


def main():
    args = get_args()

    if args.debug:
        global DEBUG
        DEBUG = True

    if args.action == "annotate":
        main_annotate(args)
    elif args.action == "ask":
        main_ask(args)
    else:
        raise Exception("Invalid action", args.action)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        import pdb
        pdb.post_mortem()
