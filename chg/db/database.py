import sqlite3


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


def db_to_text(conn):
    stmt = """
    SELECT question, answer FROM Dialogue
    """
    cursor = conn.cursor()
    results = cursor.execute(stmt)
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

    def _create_tables(self, ):
        create_chunks_table(self.conn)
        create_dialogue_table(self.conn)

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
