import random
import pdb
import nltk
from nltk.tokenize import word_tokenize

from chg.dialogue import analysis_dialogue
from chg.analysis.py_analysis import PythonAnalysis
from chg.ranker.model_based_ranking import load_ranker


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
        max_num_questions=4,
        optimize_question=True,
    ):
        self.orig_questions = list(questions)
        self.current_chunk = None
        if analyzers is None:
            # default analyzers
            analyzers = [PythonAnalysis]
        self.analyzers = analyzers
        self.max_num_questions = max_num_questions
        self.curr_num_questions = 0
        self.optimize_question = optimize_question
        if self.optimize_question:
            self.history = []
            self.question_ranker = load_ranker()
        self._init_stack()
        self.popped_question = ""

    def _init_stack(self):
        self.question_stack = list(self.orig_questions)
        if self.optimize_question:
            self.history = []
        self.curr_num_questions = 0

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
        self.question_stack.extend(analyzer_questions)

    def get_chunk_update(self):
        # no updates based on chunk
        return None

    def done(self):
        no_questions = len(self.question_stack) == 0
        hit_limit = self.curr_num_questions == self.max_num_questions
        return no_questions or hit_limit

    def ask(self):
        if self.done():
            return None
        else:
            if not self.optimize_question:
                self.popped_question = self.question_stack[0]
                return self.question_stack.pop(0)
            else:
                best_i, _ = self.question_ranker.predict(
                    str(self.current_chunk),
                    self.history,
                    self.question_stack,
                )
                self.popped_question = self.question_stack[best_i]
                return self.question_stack.pop(best_i)

    def consume_answer(self, ans):
        # user answered another question
        self.curr_num_questions += 1

        if self.optimize_question:
            # track history
            self.history.append((self.popped_question, ans))
            # update model
            self.question_ranker.update(str(self.current_chunk), self.history)

        # add more questions based on answer
        if self.popped_question in self.orig_questions:
            tokenized_words = word_tokenize(ans)
            tagged_words = nltk.pos_tag(tokenized_words)
            nouns = [x for x, y in tagged_words if 'NN' in y]
            verbs = [x for x, y in tagged_words if 'VB' in y]
            noun_template = "What is "
            verb_template = "How do you "
            questions = [noun_template + noun + "?" for noun in nouns]
            questions += [verb_template + verb + "?" for verb in verbs]
            self.question_stack = questions + self.question_stack
        else:
            pass

    def has_commit_message(self):
        return False
