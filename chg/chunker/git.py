from chg.platform import git


class SingleChunk(object):
    def __init__(self, path=None):
        chunk = git.diff()

        if chunk is None:
            raise Exception("Must run git add first")
        self.chunks = [chunk]

    def get_chunks(self):
        return self.chunks

    def commit(self, msg):
        # all changes committed at once
        git.commit()


class FileBasedChunker(object):
    def __init__(self):
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
        return git.commit(msg, paths=[f])
