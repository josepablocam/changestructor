# light-weight analysis
# of python programs for
# purposes of dialogue building
import ast
import astunparse
from collections import defaultdict

from chg.platform import git


class LinesAnalysis(object):
    def __init__(self, lines, entities, contexts):
        self.lines = lines
        self.entities = entities
        self.contexts = contexts


class PythonAnalysis(object):
    @staticmethod
    def can_apply(chunk):
        try:
            return chunk.path.endswith(".py")
        except AttributeError:
            return False

    def __init__(self, chunk):
        self.chunk = chunk
        # line-based changes in source -> target
        self.lines_changed = git.get_lines_changed(self.chunk.path)
        # old version of the file -- before changes
        self.source = AnalyzedPythonFile(
            git.cat(self.chunk.path, commit="HEAD"),
            self.chunk.path,
        )
        # this is just the current file
        with open(self.chunk.path, "r") as fin:
            self.target = AnalyzedPythonFile(fin.read(), self.chunk.path)

        # information per LinesChanged set
        # lines: (source, target)
        # entities: (source, target)
        # context: (source, target)
        self.lines_analyzed = []
        for c in self.lines_changed:
            analyzers = [self.source, self.target]
            entities = [a.get_entities(l) for a, l in zip(analyzers, c.lines)]
            contexts = [a.get_contexts(l) for a, l in zip(analyzers, c.lines)]
            ca = LinesAnalysis(c.lines, entities, contexts)
            self.lines_analyzed.append(ca)


def is_method_node(node, node_to_context):
    """
    is a function def node and the immediate parent context is a class
    """
    if not isinstance(node, ast.FunctionDef):
        return False
    ctx = node_to_context.get(node, None)
    return isinstance(ctx, ast.ClassDef)


def get_enclosing_class_node(node, node_to_context):
    """
    Get lowest *enclosing* class definition
    """
    if isinstance(node, ast.ClassDef):
        return node
    ctx = node_to_context.get(node, None)
    while ctx is not None:
        if isinstance(ctx, ast.ClassDef):
            return ctx
        ctx = node_to_context.get(ctx, None)
    return None


def get_method_name(node, node_to_context):
    class_name = node_to_context[node].name
    func_name = node.name
    return class_name + "." + func_name


def get_entity_name(node, node_to_context=None):
    if isinstance(node, ast.ClassDef):
        return "class definition {}".format(node.name)
    elif is_method_node(node, node_to_context):
        return "method definition {}".format(
            get_method_name(node, node_to_context)
        )
    elif isinstance(node, ast.FunctionDef):
        return "function definition {}".format(node.name)
    elif isinstance(node, ast.Attribute):
        name = astunparse.unparse(node).strip()
        if name.startswith("self."):
            class_node = get_enclosing_class_node(node, node_to_context)
            if class_node is not None:
                trimmed_name = ".".join(name.split(".")[1:])
                return class_node.name + "." + trimmed_name
        else:
            return name
    elif isinstance(node, ast.Name):
        name = node.id
        if name == "self":
            # not interesting
            return None
        return name
    elif isinstance(node, ast.Call):
        func_name = get_entity_name(node.func, node_to_context)
        return "function call {}".format(func_name)
    else:
        return None


class AnalyzedPythonFile(object):
    def __init__(self, src, path):
        tree = ast.parse(src, filename=path)
        self.tree = tree
        self.node_to_context = SimpleContextCollector().get(tree)
        self.line_to_nodes = LineToNodeMapper().get(tree)

    def get_entities(self, lines):
        # entities -> variables, functions, classes etc
        entities = set()
        for line in lines:
            nodes = self.line_to_nodes[line]
            line_entities = set()
            for node in nodes:
                entity = get_entity_name(node, self.node_to_context)
                if entity is not None:
                    line_entities.add(entity)
            entities.update(line_entities)
        return entities

    def get_contexts(self, lines):
        contexts = set()
        for line in lines:
            nodes = self.line_to_nodes.get(line, [])
            for node in nodes:
                ctx = self.node_to_context.get(node, None)
                # recurse up in the context chain
                while ctx is not None:
                    ctx_name = get_entity_name(ctx, self.node_to_context)
                    if ctx_name is not None:
                        contexts.add(ctx_name)
                    ctx = self.node_to_context.get(ctx, None)
        return contexts


class SimpleContextCollector(ast.NodeVisitor):
    def _reset(self):
        self.context = []
        self.node_to_context = {}

    def is_context_node(self, node):
        # we define contextual node
        # as nodes that define a function/method
        # or a class
        return isinstance(node, (ast.ClassDef, ast.FunctionDef))

    def visit(self, node):
        # map to innermost context node
        self.node_to_context[node] = self.context[-1] if len(
            self.context
        ) > 0 else None
        is_context = self.is_context_node(node)
        if is_context:
            self.context.append(node)
        self.generic_visit(node)
        if is_context:
            self.context.pop()

    def get(self, tree):
        self._reset()
        self.visit(tree)
        return self.node_to_context


class LineToNodeMapper(ast.NodeVisitor):
    def _reset(self):
        self.line_to_nodes = defaultdict(lambda: [])

    def visit(self, node):
        try:
            self.line_to_nodes[node.lineno].append(node)
        except AttributeError:
            pass
        self.generic_visit(node)

    def get(self, tree):
        self._reset()
        self.visit(tree)
        return self.line_to_nodes
