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
    tk_ui,
)


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
        return simple_cli_ui.SimpleCLIUI(debug=args.debug)
    elif args.ui == "tk":
        return tk_ui.TkUI(debug=args.debug)
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
    annotate_parser.add_argument(
        "--debug",
        action="store_true",
        help="Set debug flag",
    )
    annotate_parser.add_argument(
        "-u",
        "--ui",
        type=str,
        choices=["cli", "tk"],
        help="UI for interaction",
        default="tk"
    )

    ask_parser = subparsers.add_parser("ask")
    ask_parser.set_defaults(action="ask", debug=False)
    ask_parser.add_argument(
        "-u",
        "--ui",
        type=str,
        choices=["cli", "tk"],
        help="UI for interaction",
        default="tk"
    )

    return parser.parse_args()


def main_annotate(args):
    chunker = get_chunker(args)
    store = get_store()
    annotator = get_annotator(args)
    ui = get_ui(args)
    ui.annotate(
        chunker,
        store,
        annotator,
        git_platform,
    )


def main_ask(args):
    searcher = get_searcher(args)
    ui = get_ui(args)
    ui.ask(searcher, k=5)


def main():
    args = get_args()

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
