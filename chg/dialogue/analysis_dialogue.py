def get_overlapping_context_questions(analysis):
    # contexts appearing in both before/after
    question_template = "How does this affect the functionality of {}?"
    questions = set()
    for l in analysis.lines_analyzed:
        before, after = l.contexts
        overlap = set(before).intersection(after)
        for o in overlap:
            questions.add(question_template.format(o))
    return questions


def get_new_entities_questions(analysis):
    # ask questions about entities that only appear in after but not before
    question_template = "What does {} do?"
    questions = set()
    for l in analysis.lines_analyzed:
        before, after = l.entities
        only_in_after = set(after).difference(before)
        for o in only_in_after:
            questions.add(question_template.format(o))
    return questions


def get_removed_entities_questions(analysis):
    # ask questions about entities that appear only in before but not after
    question_template = "What replaced {} (if anything)?"
    questions = set()
    for l in analysis.lines_analyzed:
        before, after = l.entities
        only_in_before = set(before).difference(after)
        for o in only_in_before:
            questions.add(question_template.format(o))
    return questions


def get_call_graph_questions(analysis):
    # TODO: Use PyCG
    # https://conf.researchr.org/details/icse-2021/icse-2021-papers/39/PyCG-Practical-Call-Graph-Generation-in-Python
    # Idea: build CG, identify location where change was made
    # identify callers/callees that may need to know about this change
    raise NotImplementedError()


def get_questions(analysis):
    questions = []
    overlap_qs = get_overlapping_context_questions(analysis)
    new_entities_qs = get_new_entities_questions(analysis)
    removed_entities_qs = get_removed_entities_questions(analysis)

    questions.extend(overlap_qs)
    questions.extend(new_entities_qs)
    questions.extend(removed_entities_qs)
    return questions
