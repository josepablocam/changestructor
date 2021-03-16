#!/usr/bin/env python3
from argparse import ArgumentParser
import subprocess

import fasttext
import faiss
import numpy as np

from chg.db.database import get_store


def remove_color_ascii(msg):
    proc = subprocess.Popen(
        "sed 's/\x1b\[[0-9;]*m//g'",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True,
    )
    output, _ = proc.communicate(msg.encode())
    return output.decode().strip()


def database_to_text():
    store = get_store()

    chunks = {}
    chunk_stmt = """
    SELECT id, chunk FROM Chunks
    """
    for res in store.run_query(chunk_stmt):
        _id, chunk = res
        # remove color sequences
        processed_chunk = remove_color_ascii(chunk)
        # get rid of new lines in chunk, so we can treat all
        # as one line of text
        processed_chunk = processed_chunk.replace("\n", " ")
        chunks[_id] = processed_chunk

    text_repr = []
    dialogue_stmt = """
    SELECT id, question, answer, chunk_id FROM Dialogue
    """
    for res in store.run_query(dialogue_stmt):
        _id, question, answer, chunk_id = res
        chunk_str = chunks[chunk_id]
        entry_str = "{} {} {}".format(chunk_str, question, answer)
        text_repr.append(entry_str)

    return "\n".join(text_repr)


def load_vectors(path):
    return np.loadtxt(path, dtype=float)


def normalize_vectors(mat, eps=1e-6):
    # make vectors unit norm
    # add epsilon for zero vectors avoid nan after division
    norm = np.sqrt(np.sum(mat**2, axis=1)) + eps
    norm_mat = mat / norm.reshape(-1, 1)
    return norm_mat


def build_index(mat):
    mat = normalize_vectors(mat).astype(np.float32)
    index = faiss.IndexFlatIP(mat.shape[-1])
    index.add(mat)
    return index


def embed_query(model, query):
    return model.get_sentence_vector(query)


def load_index(index_path):
    return faiss.read_index(index_path)


def run_query(index, embedding, k):
    # make sure row vector
    embedding = embedding.reshape(1, -1)
    embedding = normalize_vectors(embedding).astype(np.float32)
    D, ix = index.search(embedding, k)
    return ix.flatten()


def lookup_in_store(store, ixs):
    # ixs are offset by 1 as ids in the database
    ids = ixs + 1
    return store.get_dialogue_by_ids(ids)


class EmbeddedSearcher(object):
    def __init__(self, fasttext_model_path, faiss_index, model_suffix=".bin"):
        if model_suffix is not None:
            # annoying fasttext convention of adding a .bin to
            # output files, despite not specifying it...
            fasttext_model_path = fasttext_model_path + model_suffix
        # silence warning
        # https://github.com/facebookresearch/fastText/issues/1067
        fasttext.FastText.eprint = lambda x: None
        self.fasttext_model = fasttext.load_model(fasttext_model_path)
        self.store = get_store()
        self.faiss_index = load_index(faiss_index)

    def search(self, query, k=5):
        vector = embed_query(self.fasttext_model, query)
        assert k > 0
        ixs = run_query(self.faiss_index, vector, k)
        return lookup_in_store(self.store, ixs)


def build(args):
    assert args.action == "build"
    mat = load_vectors(args.vectors)
    index = build_index(mat)
    faiss.write_index(index, args.index)


def query_from_cli(args):
    assert args.action == "query"
    searcher = EmbeddedSearcher(args.model, args.index)
    return searcher.search(args.query, k=args.k)


def get_args():
    parser = ArgumentParser(
        description="Semantic search based on embedded queries"
    )
    subparsers = parser.add_subparsers(help="Semantic search actions")

    text_parser = subparsers.add_parser("text")
    text_parser.set_defaults(action="text")

    build_parser = subparsers.add_parser("build")
    build_parser.set_defaults(action="build")
    build_parser.add_argument(
        "--vectors",
        type=str,
        help="Path to file with vectors",
    )
    build_parser.add_argument(
        "--index",
        type=str,
        help="Path to store FAISS index",
    )

    query_parser = subparsers.add_parser("query")
    query_parser.set_defaults(action="query")
    query_parser.add_argument(
        "--model",
        type=str,
        help="Path to fasttext embedding model",
    )
    query_parser.add_argument(
        "--index",
        type=str,
        help="Path to FAISS index",
    )
    query_parser.add_argument(
        "--query",
        type=str,
        help="Query to search with",
    )
    query_parser.add_argument(
        "--k",
        type=int,
        help="Number of records to return for query",
        default=5,
    )
    return parser.parse_args()


def main():
    args = get_args()
    if args.action == "text":
        print(database_to_text())
    elif args.action == "build":
        build(args)
    elif args.action == "query":
        query_from_cli(args)
    else:
        raise Exception("Unknown action:", args.action)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        import pdb
        pdb.post_mortem()
