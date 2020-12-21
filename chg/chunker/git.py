import os
from contextlib import contextmanager
from chg.platform import git


# https://gist.github.com/howardhamilton/537e13179489d6896dd3
@contextmanager
def pushd(new_dir):
    previous_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(previous_dir)


class SingleChunk(object):
    def __init__(self, path=None):
        self.path = path
        if self.path is not None:
            with pushd(self.path):
                chunk = git.diff()
        else:
            chunk = git.diff()

        if chunk is None:
            raise Exception("Must run git add first")
        self.chunks = [chunk]

    def get_chunks(self):
        return self.chunks

    def commit(self, msg):
        # all changes committed at once
        if self.path is not None:
            with pushd(self.path):
                return git.commit()
        else:
            git.commit()


class FileBasedChunker(object):
    def __init__(self, path=None):
        self.path = path
        if self.path is not None:
            with pushd(self.path):
                self._collect_files_and_chunks()
        else:
            self._collect_files_and_chunks()

    def _collect_files_and_chunks(self):
        # each file is its own chunk
        self.file_to_chunk = {}
        self.chunks = []
        self.files = []
        files_changed = git.diff_files()

        if len(files_changed) == 0:
            raise Exception("Must run git add first")

        for f in files_changed:
            chunk = git.diff(f)
            self.files.append(f)
            self.file_to_chunk[f] = chunk
            self.chunks.append(chunk)

    def get_chunks(self):
        return self.chunks

    def commit(self, msg):
        # commit one file at a time
        assert len(self.files) > 0
        f = self.files.pop(0)
        if self.path is not None:
            with pushd(self.path):
                return git.commit(msg, paths=[f])
        else:
            return git.commit(msg, paths=[f])
