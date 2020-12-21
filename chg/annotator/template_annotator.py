class FixedListAnnotator(object):
    def __init__(self, questions):
        self.orig_questions = list(questions)
        self.current_chunk = None
        self._init_stack()

    def _init_stack(self):
        self.question_stack = list(reversed(self.orig_questions))

    def consume_chunk(self, chunk):
        # copy questions to start again
        self._init_stack()
        self.current_chunk = chunk

    def get_chunk_update(self):
        # no updates based on chunk
        return None

    def done(self):
        return len(self.question_stack) == 0

    def ask(self):
        if self.done():
            return None
        else:
            return self.question_stack.pop(0)

    def consume_answer(self, ans):
        # doesn't use answer in any way
        pass

    def has_commit_message(self):
        return False
