#!/usr/bin/env python3
from argparse import ArgumentParser

import faiss
import numpy as np

from chg.defaults import CHG_PROJ_FAISS
from chg.db.database import get_store
from chg.embed.basic import (
    BasicEmbedder,
    normalize_vectors,
)


def load_vectors():
    store = get_store()
    rows = store.run_query(
        "SELECT code_embedding FROM Embeddings ORDER BY chunk_id"
    )
    code_embeddings = [store.blob_to_array(row[0]) for row in rows]
    mat = np.array(code_embeddings, dtype=np.float32)
    return mat


def build_index(mat):
    mat = normalize_vectors(mat).astype(np.float32)
    index = faiss.IndexFlatIP(mat.shape[-1])
    index.add(mat)
    return index


def embed_query(model, query):
    return model.embed_nl(query)


def load_index():
    return faiss.read_index(CHG_PROJ_FAISS)


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
    def __init__(self):
        self.embed_model = BasicEmbedder()
        self.store = get_store()
        self.faiss_index = load_index()

    def search(self, query, k=5):
        vector = embed_query(self.embed_model, query)
        assert k > 0
        ixs = run_query(self.faiss_index, vector, k)
        return lookup_in_store(self.store, ixs)


def build(args):
    assert args.action == "build"
    mat = load_vectors()
    index = build_index(mat)
    faiss.write_index(index, CHG_PROJ_FAISS)


def query_from_cli(args):
    assert args.action == "query"
    searcher = EmbeddedSearcher()
    return searcher.search(args.query, k=args.k)


def get_args():
    parser = ArgumentParser(
        description="Semantic search based on embedded queries"
    )
    subparsers = parser.add_subparsers(help="Semantic search actions")

    build_parser = subparsers.add_parser("build")
    build_parser.set_defaults(action="build")

    query_parser = subparsers.add_parser("query")
    query_parser.set_defaults(action="query")
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
    parser.set_defaults(action="build")
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
