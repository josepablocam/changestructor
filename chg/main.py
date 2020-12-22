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


def ask(ui, searcher, k=5):
    try:
        while True:
            user_question = ui.prompt("Question:")
            results = searcher.search(user_question, k=k)
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
    searcher = EmbeddedSearcher(
        chg.defaults.CHG_PROJ_FASTTEXT,
        chg.defaults.CHG_PROJ_FAISS,
    )
    return searcher


def get_args():
    parser = ArgumentParser(
        description="chgstructor: dialogue-based change-set annotation",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    # TODO: write proper subparses
    parser.add_argument(
        "action",
        choices=["annotate", "ask"],
        help="chgstructor mode",
        required=True,
    )
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


def main_annotate(args):
    chunker = get_chunker(args)
    store = get_store(args)
    annotator = get_annotator(args)
    ui = get_ui(args)
    # only supporting git for now...
    annotate(chunker, store, annotator, ui, platform=git_platform)


def main_ask(args):
    searcher = get_searcher(args)
    ui = get_ui()
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
