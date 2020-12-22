#!/usr/bin/env python3
from argparse import ArgumentParser
import subprocess

import faiss
import numpy as np

from chg.db.database import get_store


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


def embed_query(model_path, query):
    proc = subprocess.Popen(
        ["fasttext", "print-sentence-vectors", model_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, _ = proc.communicate(input=str.encode(query))
    vector_str = stdout.strip().decode()
    return np.array([float(v) for v in vector_str.split()])


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
    return store.get_dialogue_by_id(ids)


class EmbeddedSearcher(object):
    def __init__(self, fasttext_model, faiss_index):
        self.fasttext_model = fasttext_model
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
    # TODO: write proper subparses
    parser.add_argument("action", choices=["build", "query"], help="Actions")
    parser.add_argument(
        "--vectors",
        type=str,
        help="Path to file with vectors",
    )
    parser.add_argument(
        "--index",
        type=str,
        help="Path to store FAISS index",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Path to fasttext embedding model",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Query to search with",
    )
    parser.add_argument(
        "--k",
        type=int,
        help="Number of records to return for query",
        default=5,
    )
    return parser.parse_args()


def main():
    args = get_args()
    if args.action == "build":
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
