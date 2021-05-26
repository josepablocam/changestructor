#!/usr/bin/env python3
from argparse import ArgumentParser
import os
import pickle

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_validate
from scipy.stats import norm
import tqdm

from chg.db import database
from chg.defaults import CHG_PROJ_RANKER
from chg.search import embedded_search
from chg.embed.basic import BasicEmbedder, remove_color_ascii


# TODO: we could replace this RF model
# with a NN, and use that to tune the
# CodeBERT embeddings as well
class RFModel(object):
    def __init__(self):
        self.model = RandomForestRegressor()

    def fit(self, X, y):
        self.model.fit(X, y)

    def predict(self, x):
        return self.model.predict(x)

    def expected_improvement(self, x, curr_loss=None):
        x = x.reshape(1, -1)
        pred_mean = self.predict(x)[0]
        pred_std = np.std([
            tree.predict(x)[0] for tree in self.model.estimators_
        ])
        z = (curr_loss - pred_mean) / pred_std
        ei = (curr_loss - pred_mean) * norm.cdf(z) + pred_std * norm.pdf(z)
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

    def sample_negative_code_vecs(self, exclude_id=None):
        query = """
        SELECT code_embedding FROM Embeddings
        """
        if exclude_id is not None:
            query += " WHERE NOT chunk_id={}".format(exclude_id)
        # sample some number of these
        query += "  ORDER BY RANDOM() LIMIT {}".format(self.negative_k)

        results = []
        for row in self.database.run_query(query):
            # comes out as a tuple by default, so take first elem
            code_blob = row[0]
            code_embedding = self.database.blob_to_array(code_blob)
            results.append(code_embedding)
        mat = np.vstack(results)
        return mat

    def compute_loss(self, code_vec, nl_vec, neg_code_vecs):
        code_vec = code_vec.reshape(1, -1)
        nl_vec = nl_vec.reshape(1, -1).T

        pos_sim = np.dot(code_vec, nl_vec)
        neg_sims = np.dot(neg_code_vecs, nl_vec)
        # hinge loss w/ positive and negative pairs
        losses = self.delta - pos_sim + neg_sims
        losses[losses < 0] = 0.0
        mean_loss = np.mean(losses)
        return mean_loss

    def embed_nl(self, _input):
        return self.embed_model.embed_nl(_input)

    def embed_dialogue(self, _input):
        return self.embed_model.embed_dialogue(_input)

    def embed_code(self, _input):
        return self.embed_model.embed_code(_input)

    def get_features_and_curr_loss(
        self,
        code,
        dialogue,
        negative_examples=None,
        embed_code=True,
        embed_dialogue=True
    ):
        if embed_code:
            code_vec = self.embed_code(code)
        else:
            code_vec = code

        if embed_dialogue:
            nl_vec = self.embed_dialogue(dialogue)
        else:
            nl_vec = dialogue

        if negative_examples is None:
            neg_code_vecs = self.sample_negative_code_vecs()
        else:
            neg_code_vecs = negative_examples

        flat_neg_code_vecs = neg_code_vecs.flatten()
        context_vec = np.concatenate([code_vec, nl_vec, flat_neg_code_vecs])
        # hinge loss based on current dialogue for this chunk
        curr_loss = self.compute_loss(code_vec, nl_vec, neg_code_vecs)
        result = {
            "code_vec": code_vec,
            "neg_code_vecs": neg_code_vecs,
            "context_vec": context_vec,
            "curr_loss": curr_loss,
        }
        return result

    def predict(self, code, dialogue, questions):
        info = self.get_features_and_curr_loss(
            code,
            dialogue,
            negative_examples=None,
        )

        # context corresponds to code embedding,
        # embedded dialogue up to this point
        # and negative code embeddings sampled
        context_vec = info["context_vec"]
        # ranking loss
        curr_loss = info["curr_loss"]

        best_score = None
        best_i = None
        best_x = None

        scores = []
        # candidate questions: pick the one that
        # we believe will produce the best score
        for i, q in enumerate(questions):
            q_vec = self.embed_nl(q)
            x = np.concatenate((context_vec, q_vec))
            y = self.loss_model.expected_improvement(x, curr_loss)
            scores.append(y)
            # larger expected improvement than previous best
            if best_score is None or y > best_score:
                best_score = y
                best_x = x
                best_i = i

        # keep around some state
        # so we can compute realized loss later on
        # (after user types out answer to proposed question)
        self.curr = {
            "code_vec": info["code_vec"],
            "neg_code_vecs": info["neg_code_vecs"],
            "x": best_x,
        }
        return best_i, best_score

    def fit_model(self, X=None, y=None, cv=None):
        if X is None:
            X = self.X
        if y is None:
            y = self.y
        if cv is not None:
            metric = "r2"
            cv_results = cross_validate(
                self.loss_model.model,
                X,
                y,
                cv=cv,
                scoring=metric,
            )
            scores = cv_results["test_score"]
            print("{}-fold CV".format(cv))
            print(
                "Mean {} (sd): {:.2f} ({:.2f})".format(
                    metric, scores.mean(), scores.std()
                )
            )
        self.loss_model.fit(X, y)

    def update(self, code, dialogue):
        # not doing anything with code right now
        # embed full dialogue (including answer to latest
        # proposed question)
        nl_vec = self.embed_dialogue(dialogue)
        # compute *realized* loss
        real_loss = self.compute_loss(
            self.curr["code_vec"],
            nl_vec,
            self.curr["neg_code_vecs"],
        )
        # add observations to training data
        self.X = np.vstack((self.X, self.curr["x"]))
        self.y = np.append(self.y, real_loss)
        self.step_ct += 1
        if (self.train_every > 0) and self.step_ct % self.train_every == 0:
            self.fit_model()


def build_ranker_from_git_log():
    store = database.get_store()
    ranker = QuestionRanker()
    X = []
    y = []
    rows = store.run_query("SELECT id FROM Chunks WHERE chunk IS NOT NULL")
    chunk_ids = [row[0] for row in rows]

    print("Training ranker")
    for chunk_id in tqdm.tqdm(chunk_ids):
        code_embedding, _ = store.get_embeddings_by_chunk_id(chunk_id)
        # q/a associated with this code chunk change
        dialogue = store.run_query(
            "SELECT question, answer FROM Dialogue WHERE chunk_id={}".
            format(chunk_id)
        )
        for i, (current_q, future_answer) in enumerate(dialogue):
            past_dialogue = dialogue[:i]
            # sample negative code examples
            negative_code_vecs = ranker.sample_negative_code_vecs(
                exclude_id=chunk_id,
            )
            info = ranker.get_features_and_curr_loss(
                code=code_embedding,
                dialogue=past_dialogue,
                negative_examples=negative_code_vecs,
                embed_code=False,
                embed_dialogue=True,
            )
            # embed the current question
            current_q_vec = ranker.embed_nl(current_q)
            # add this embedded question to context to create feature vec
            features = np.concatenate([info["context_vec"], current_q_vec])

            # realized loss once the answer is given
            # our goal is to *predict* this loss based on the
            # code, context, and question
            full_dialogue_vec = ranker.embed_dialogue(dialogue[:(i + 1)])
            realized_loss = ranker.compute_loss(
                code_embedding,
                full_dialogue_vec,
                negative_code_vecs,
            )
            X.append(features)
            y.append(realized_loss)
    X = np.vstack(X)
    y = np.array(y)
    ranker.X = X
    ranker.y = y
    ranker.fit_model(cv=5)
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
    _ = get_args()
    print("Building ranking model")
    ranker = build_ranker_from_git_log()
    store_ranker(ranker)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        import pdb
        pdb.post_mortem()
