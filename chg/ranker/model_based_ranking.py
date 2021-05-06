#!/usr/bin/env python3
from argparse import ArgumentParser
import os
import pickle

import fasttext
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from scipy.stats import norm

from chg.db import database
from chg.defaults import CHG_PROJ_FASTTEXT, CHG_PROJ_RANKER
from chg.search import embedded_search
from chg.embed.basic import BasicEmbedder, remove_color_ascii


class RFModel(object):
    def __init__(self):
        self.model = RandomForestRegressor()

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict(self, x, curr_loss):
        # predict expected improvement
        x = x.reshape(1, -1)
        mean = self.model.predict(x)[0]
        std = np.std([tree.predict(x)[0] for tree in self.model.estimators_])
        z = (curr_loss - mean) / std
        ei = (curr_loss - mean) * norm.cdf(z) + std * norm.pdf(z)
        return ei


class QuestionRanker(object):
    def __init__(self, delta=0.05, train_every=1, negative_k=3):
        self.embed_model = BasicEmbedder()
        self.loss_model = RFModel()
        self.database = database.get_store()
        self.curr = {}
        self.delta = delta
        self.X = []
        self.y = []
        self.train_every = train_every
        self.negative_k = negative_k
        self.step_ct = 0

    def sample_negative_code(self):
        # by definition anything in DB is negative code
        # since we haven't committed this chunk
        query = """
        SELECT chunk FROM Chunks WHERE chunk IS NOT NULL
        ORDER BY RANDOM() LIMIT {}
        """.format(self.negative_k)
        results = []
        for chunk in self.database.run_query(query):
            # comes out as a tuple by default, so take first elem
            chunk = chunk[0]
            # remove color sequences
            processed_chunk = embedded_search.remove_color_ascii(chunk)
            # get rid of new lines in chunk, so we can treat all
            # as one line of text
            results.append(processed_chunk)
        return results

    def compute_loss(self, code_vec, nl_vec, neg_code_vecs):
        code_vec = embedded_search.normalize_vectors(code_vec.reshape(1, -1))
        neg_code_vecs = embedded_search.normalize_vectors(neg_code_vecs)
        nl_vec = embedded_search.normalize_vectors(nl_vec.reshape(1, -1)).T

        pos_sim = np.dot(code_vec, nl_vec)
        neg_sims = np.dot(neg_code_vecs, nl_vec)
        # hinge loss w/ positive and negative pairs
        losses = self.delta - pos_sim + neg_sims
        losses[losses < 0] = 0.0
        mean_loss = np.mean(losses)
        return mean_loss

    def history_to_str(self, qa_history):
        qa_history_str = " ".join([
            "{}:{}".format(q, a) for q, a in qa_history
        ])
        return qa_history_str

    def embed_nl(self, _input):
        return self.embed_model.embed_nl(_input)

    def embed_code(self, _input):
        return self.embed_model.embed_code(_input)

    def get_features_and_curr_loss(
        self, code, qa_history, negative_examples=None
    ):
        code_vec = self.embed_code(code)

        qa_history_str = self.history_to_str(qa_history)
        hist_vec = self.embed_nl(qa_history_str)

        if negative_examples is None:
            negative_examples = self.sample_negative_code()

        neg_code_vecs = np.array([
            self.embed_code(c) for c in negative_examples
        ])

        flat_neg_code_vecs = neg_code_vecs.flatten()
        context_vec = np.concatenate([code_vec, hist_vec, flat_neg_code_vecs])
        # hinge loss based on current dialogue for this chunk
        curr_loss = self.compute_loss(code_vec, hist_vec, neg_code_vecs)
        result = {
            "code_vec": code_vec,
            "neg_code_vecs": neg_code_vecs,
            "context_vec": context_vec,
            "curr_loss": curr_loss,
        }
        return result

    def predict(self, code, qa_history, questions):
        info = self.get_features_and_curr_loss(
            code,
            qa_history,
            negative_examples=None,
        )

        context_vec = info["context_vec"]
        curr_loss = info["curr_loss"]

        best_score = None
        best_i = None
        best_x = None

        scores = []
        for i, q in enumerate(questions):
            q_vec = self.embed_nl(q)
            x = np.concatenate((context_vec, q_vec))
            y = self.loss_model.predict(x, curr_loss)
            scores.append(y)
            if best_score is None or y > best_score:
                best_score = y
                best_x = x
                best_i = i

        self.curr = {
            "code_vec": info["code_vec"],
            "neg_code_vecs": info["neg_code_vecs"],
            "x": best_x,
        }
        return best_i, best_score

    def fit_model(self, X=None, y=None):
        if X is None:
            X = self.X
        if y is None:
            y = self.y
        self.loss_model.fit(X, y)

    def update(self, code, qa_history):
        nl_vec = self.embed_nl(self.history_to_str(qa_history))
        real_loss = self.compute_loss(
            self.curr["code_vec"],
            nl_vec,
            self.curr["neg_code_vecs"],
        )
        self.X.append(self.curr["x"])
        self.y.append(real_loss)
        self.step_ct += 1
        if (self.train_every > 0) and self.step_ct % self.train_every == 0:
            self.fit_model()


def build_ranker_from_git_log():
    db = database.get_store()

    chunks = {}
    qa_history = {}
    chunk_stmt = """
    SELECT id, chunk FROM Chunks where chunk is not NULL
    """
    for res in db.run_query(chunk_stmt):
        _id, chunk = res
        # remove color sequences
        processed_chunk = remove_color_ascii(chunk)
        chunks[_id] = processed_chunk

    dialogue_stmt = """
    SELECT question, answer, chunk_id FROM Dialogue
    """
    for res in db.run_query(dialogue_stmt):
        question, answer, chunk_id = res
        if chunk_id not in qa_history:
            qa_history[chunk_id] = []
        qa_history[chunk_id].append((question, answer))

    ranker = QuestionRanker()
    X = []
    y = []
    default_question = "what is this commit about?"
    chunk_ids = set(chunks.keys())
    for chunk_id in chunks.keys():
        code = chunks[chunk_id]
        qa_hist = qa_history[chunk_id]
        other_ids = list(chunk_ids.difference([chunk_id]))
        negative_ids = np.random.choice(
            other_ids, ranker.negative_k, replace=True
        )
        negative_code = [chunks[_id] for _id in negative_ids]
        info = ranker.get_features_and_curr_loss(code, qa_hist, negative_code)
        # assume the default question for git commit is the following
        q_vec = ranker.embed_nl(default_question)
        features = np.concatenate([info["context_vec"], q_vec])
        X.append(features)
        y.append(info["curr_loss"])
    ranker.X = X
    ranker.y = y
    ranker.fit_model()
    return ranker


def load_ranker():
    ranker_dir = os.path.dirname(CHG_PROJ_RANKER)
    if not os.path.exists(ranker_dir):
        print("Creating folder for chg ranker at", ranker_dir)
        os.makedirs(ranker_dir)

    with open(CHG_PROJ_RANKER, "rb") as fin:
        ranker = pickle.load(fin)
        # skip pickling of model or sqlite3 connections
        ranker.embed_model = BasicEmbedder()
        ranker.database = database.get_store()
    return ranker


def store_ranker(ranker):
    with open(CHG_PROJ_RANKER, "wb") as fout:
        # can't pickle fasttext or sqlite3
        ranker.embed_model = None
        ranker.database = None
        pickle.dump(ranker, fout)


def get_args():
    parser = ArgumentParser(
        description="Train question ranker based on git log"
    )
    return parser.parse_args()


def main():
    args = get_args()
    print("Building ranking model")
    ranker = build_ranker_from_git_log()
    store_ranker(ranker)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        import pdb
        pdb.post_mortem()
