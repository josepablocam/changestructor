import os
import sqlite3

import numpy as np

from chg.defaults import CHG_PROJ_DB_PATH
from chg.platform import git


def create_chunks_table(conn):
    stmt = """
    CREATE TABLE IF NOT EXISTS Chunks (
        id INTEGER PRIMARY KEY,
        prehash TEXT,
        chunk TEXT,
        posthash TEXT
    )
    """
    cursor = conn.cursor()
    cursor.execute(stmt)
    conn.commit()
    cursor.close()


def insert_chunk(conn, row):
    assert len(row) == 3
    stmt = """
    INSERT INTO Chunks(prehash, chunk, posthash) VALUES(?, ?, ?)
    """
    cursor = conn.cursor()
    cursor.execute(stmt, row)
    conn.commit()
    chunk_id = cursor.lastrowid
    cursor.close()
    return chunk_id


def create_dialogue_table(conn):
    stmt = """
    CREATE TABLE IF NOT Exists Dialogue (
        id INTEGER PRIMARY KEY,
        question TEXT,
        answer TEXT,
        chunk_id INTEGER,
        FOREIGN KEY(chunk_id) REFERENCES Chunks(id)
    )
    """
    cursor = conn.cursor()
    cursor.execute(stmt)
    conn.commit()
    cursor.close()


def insert_answered_question(conn, row):
    stmt = """
    INSERT INTO Dialogue(question, answer, chunk_id)
    VALUES(?, ?, ?)
    """
    cursor = conn.cursor()
    cursor.execute(stmt, row)
    conn.commit()
    qa_id = cursor.lastrowid
    cursor.close()
    return qa_id


def create_embeddings_table(conn):
    stmt = """
    CREATE TABLE IF NOT Exists Embeddings (
        id INTEGER PRIMARY KEY,
        chunk_id INTEGER,
        code_embedding BLOB,
        nl_embedding BLOB,
        FOREIGN KEY(chunk_id) REFERENCES Chunks(id)
    )
    """
    cursor = conn.cursor()
    cursor.execute(stmt)
    conn.commit()
    cursor.close()


def insert_embeddings(conn, row):
    assert len(row) == 3, "(chunk_id, code_embedding, nl_embedding) required"
    stmt = """
    INSERT INTO Embeddings(chunk_id, code_embedding, nl_embedding) VALUES(?, ?, ?)
    """
    cursor = conn.cursor()
    cursor.execute(stmt, row)
    conn.commit()
    chunk_id = cursor.lastrowid
    cursor.close()
    return chunk_id


def get_embeddings_by_chunk_id(conn, chunk_id):
    stmt = """
    SELECT code_embedding, nl_embedding FROM Embeddings WHERE chunk_id = ?
    """
    cursor = conn.cursor()
    cursor.execute(stmt, (chunk_id, ))
    results = cursor.fetchall()
    cursor.close()
    return results


def get_dialogue_by_ids(conn, ids):
    stmt = """
    SELECT * from Dialogue WHERE id in ({})
    """.format(", ".join(str(i) for i in ids))
    cursor = conn.cursor()
    cursor.execute(stmt)
    results = cursor.fetchall()
    cursor.close()
    return results


class Database(object):
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self._connect()
        # in case don't exist
        self._create_tables()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)

    def _create_tables(self):
        create_chunks_table(self.conn)
        create_dialogue_table(self.conn)
        create_embeddings_table(self.conn)

    def run_query(self, stmt):
        cursor = self.conn.cursor()
        cursor.execute(stmt)
        results = cursor.fetchall()
        cursor.close()
        return results

    def record_chunk(self, data):
        # prehash, chunk, posthash = data
        return insert_chunk(self.conn, data)

    def record_dialogue(self, data):
        chunk_id, answered_questions = data
        ids = []
        for (question, answer) in answered_questions:
            qa_id = insert_answered_question(
                self.conn, (question, answer, chunk_id)
            )
            ids.append(qa_id)
        return ids

    def array_to_blob(self, arr):
        arr = arr.astype(np.float32)
        return arr.tobytes()

    def blob_to_array(self, blob):
        return np.frombuffer(blob, dtype=np.float32)

    def record_embeddings(self, data):
        chunk_id, code_embedding, nl_embedding = data

        code_blob = self.array_to_blob(code_embedding)
        nl_blob = self.array_to_blob(nl_embedding)
        return insert_embeddings(self.conn, (chunk_id, code_blob, nl_blob))

    def get_embeddings_by_chunk_id(self, _id):
        row = get_embeddings_by_chunk_id(self.conn, _id)
        code_blob, nl_blob = row[0]
        code_embedding = self.blob_to_array(code_blob)
        nl_embedding = self.blob_to_array(nl_blob)
        return code_embedding, nl_embedding

    def get_dialogue_by_ids(self, ids):
        return get_dialogue_by_ids(self.conn, ids)


def get_store():
    db_dir = os.path.dirname(CHG_PROJ_DB_PATH)
    if not os.path.exists(db_dir):
        print("Creating folder for chg database at", db_dir)
        os.makedirs(db_dir)
    return Database(CHG_PROJ_DB_PATH)
