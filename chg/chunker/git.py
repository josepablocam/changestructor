import sys
from chg.platform import git


class UnifiedChunk(object):
    """
    Entire diff is single chunk
    """
    def __init__(self, diff):
        self.diff = diff

    def __str__(self):
        return self.diff


class SingleChunker(object):
    def __init__(self, path=None):
        chunk = git.diff()

        if chunk is None:
            print("Must run git add first")
            sys.exit(1)
        chunk = UnifiedChunk(chunk)
        self.chunks = [chunk]

    def get_chunks(self):
        return self.chunks

    def stage(self, chunk):
        # just add everything
        git.add()

    def commit(self, chunk, msg):
        # all changes committed at once
        git.commit()


class FileChunk(object):
    """
    Diff of each file is its own chunk
    """
    def __init__(self, diff, path):
        self.diff = diff
        self.path = path

    def __str__(self):
        return self.diff


class FileBasedChunker(object):
    def __init__(self):
        self._collect_files_and_chunks()
        self.staged = set()

    def _collect_files_and_chunks(self):
        # each file is its own chunk
        self.chunks = []
        self.files = []
        files_changed = git.diff_files()

        if len(files_changed) == 0:
            print("Must run git add first")
            sys.exit(1)

        for f in files_changed:
            diff = git.diff(f)
            chunk = FileChunk(diff, f)
            self.chunks.append(chunk)

    def get_chunks(self):
        return self.chunks

    def stage(self, chunk):
        f = chunk.path
        git.add(paths=[f])
        self.staged.add(f)

    def commit(self, chunk, msg):
        # commit one file at a time
        f = chunk.path
        assert f in self.staged
        return git.commit(msg, paths=[f])
