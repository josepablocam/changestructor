#!/usr/bin/env python3

from argparse import ArgumentParser
import os
import subprocess

import numpy as np
from transformers import RobertaTokenizer, RobertaModel
import torch
import tqdm

from chg.db.database import get_store

# fix odd fault...
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'


def remove_color_ascii(msg):
    proc = subprocess.Popen(
        "sed 's/\x1b\[[0-9;]*m//g'",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        shell=True,
    )
    output, _ = proc.communicate(msg.encode())
    return output.decode().strip()


def normalize_vectors(mat):
    # make vectors unit norm
    norm = np.sqrt(np.sum(mat**2, axis=1))
    # set to 1.0 to avoid nan
    norm[norm == 0] = 1.0
    norm_mat = mat / norm.reshape(-1, 1)
    return norm_mat


class BasicEmbedder(object):
    def __init__(self):
        self.tokenizer = RobertaTokenizer.from_pretrained(
            "microsoft/codebert-base"
        )
        self.model = RobertaModel.from_pretrained("microsoft/codebert-base")
        self.model = self.model.to("cpu")
        # self.model = self.model.eval()
        self.max_len = self.model.config.max_position_embeddings

    def embed_(self, txt):
        tokens = [self.tokenizer.cls_token]
        tokens = self.tokenizer.tokenize(txt)

        # split up chunks according to max_len
        embeddings = []
        chunk_len = self.max_len - 4
        for i in tqdm.tqdm(list(range(0, len(tokens), chunk_len))):
            chunk = [self.tokenizer.cls_token]
            chunk.extend(tokens[i:(i + chunk_len)])
            chunk.append(self.tokenizer.sep_token)
            chunk_token_ids = self.tokenizer.convert_tokens_to_ids(chunk)
            with torch.no_grad():
                chunk_embedding = self.model(
                    torch.tensor(chunk_token_ids)[None, :]
                )[0]
                # average over tokens
                chunk_embedding = chunk_embedding.mean(dim=1)
                embeddings.append(chunk_embedding)
        embeddings = torch.stack(embeddings)
        # average over chunks
        txt_embedding = embeddings.mean(dim=0)
        txt_embedding = txt_embedding.numpy()
        # unit norm
        txt_embedding = normalize_vectors(txt_embedding)
        txt_embedding = txt_embedding.flatten()
        return txt_embedding

    def embed_code(self, code):
        return self.embed_(remove_color_ascii(code))

    def embed_nl(self, nl):
        return self.embed_(nl)

    def embed_dialogue(self, question_and_answers):
        # empty history
        if len(question_and_answers) == 0:
            question_and_answers = [("", "")]
        merged_dialogue = "\n".join(
            "{}:{}".format(q, a) for q, a in question_and_answers
        )
        return self.embed_nl(merged_dialogue)


def get_args():
    parser = ArgumentParser(description="Embed chg database")
    return parser.parse_args()


def main():
    _ = get_args()
    embedder = BasicEmbedder()
    store = get_store()

    # need to embed every chunk
    chunk_ids = store.run_query(
        "SELECT id FROM Chunks WHERE chunk IS NOT NULL"
    )
    chunk_ids = [row[0] for row in chunk_ids]
    print("Embedding code and dialogue for {} chunks".format(len(chunk_ids)))
    for chunk_id in tqdm.tqdm(chunk_ids):
        chunk = store.run_query(
            "SELECT chunk FROM Chunks WHERE id={}".format(chunk_id)
        )
        assert len(chunk) == 1, "Chunks should be uniquely identified"
        chunk = chunk[0]
        code_embedding = embedder.embed_code(chunk[0])
        # embed dialogue associated with this chunk
        dialogue = store.run_query(
            "SELECT question, answer FROM Dialogue WHERE chunk_id={} ORDER BY id"
            .format(chunk_id)
        )
        assert len(dialogue) >= 1, "Should have at least one commit message"
        nl_embedding = embedder.embed_dialogue(dialogue)
        store.record_embeddings((chunk_id, code_embedding, nl_embedding))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        import pdb
        pdb.post_mortem()
