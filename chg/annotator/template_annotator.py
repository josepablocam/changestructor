import random
import pdb

from chg.dialogue import analysis_dialogue
from chg.analysis.py_analysis import PythonAnalysis


class FixedListAnnotator(object):
    def __init__(self, questions):
        self.orig_questions = list(questions)
        self.current_chunk = None
        self._init_stack()

    def _init_stack(self):
        self.question_stack = list(self.orig_questions)

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


class DynamicListAnnotator(object):
    def __init__(
        self,
        questions,
        analyzers=None,
        num_analyzer_questions=4,
    ):
        self.orig_questions = list(questions)
        self.current_chunk = None
        if analyzers is None:
            # default analyzers
            analyzers = [PythonAnalysis]
        self.analyzers = analyzers
        self.num_analyzer_questions = num_analyzer_questions
        self._init_stack()

    def _init_stack(self):
        self.question_stack = list(self.orig_questions)

    def consume_chunk(self, chunk):
        # copy questions to start again
        self._init_stack()
        self.current_chunk = chunk
        analyzer_questions = []

        for analyzer in self.analyzers:
            if analyzer.can_apply(self.current_chunk):
                analysis_result = analyzer(self.current_chunk)
                new_questions = analysis_dialogue.get_questions(
                    analysis_result
                )
                analyzer_questions.extend(new_questions)
        # randomly sample from analyzer questions -- otherwise too many
        random.shuffle(analyzer_questions)
        sampled_questions = analyzer_questions[:self.num_analyzer_questions]
        self.question_stack.extend(sampled_questions)

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
        # import pdb; pdb.set_trace()
        pass

    def has_commit_message(self):
        return False
