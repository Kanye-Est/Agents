#!/usr/bin/env python3
"""Statically compare scorer keys with observation reads; never import either.

Checked scopes are the returned score object, summary, final_assistant, and
each argument_and_frozen_return_fidelity row. Key sets come from producer AST
dictionary construction, not a duplicated schema. Consumer aliases, identity
guards, finite key loops and row comprehensions retain their separate scopes.

This is a bounded syntax contract, not Python execution or a type checker.
Computed keys/constructions, unsupported mutations, opaque calls receiving a
checked container, and unsupported control flow fail closed. Descendants of
other report branches are explicitly outside these four scopes.

--staged reads both sources from index stage 0, irrespective of working-tree
edits. The repository hook also loads this checker itself from the index.
Exit codes: 0 compatible, 1 missing producer key, 2 unresolved/input error.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
BASE = "secskill-lab/utcs/rig/goose_validation"
PRODUCER = BASE + "/score_baseline.py"
CONSUMER = BASE + "/calibration_observations.py"
CHECKER = BASE + "/check_score_observation_contract.py"
ROW_FIELD = "argument_and_frozen_return_fidelity"
MAPPING_FIELDS = ("summary", "final_assistant")
SCOPES = ((), *( (name,) for name in MAPPING_FIELDS), (ROW_FIELD, "[]"))


class Unresolved(ValueError):
    def __init__(self, code, node, detail):
        self.code, self.line, self.detail = code, getattr(node, "lineno", 0), detail
        super().__init__(detail)


def demand(ok, code, node, detail):
    if not ok:
        raise Unresolved(code, node, detail)


def scope_name(path):
    return "score" + "".join("[]" if p == "[]" else "." + p for p in path)


def function(tree, name):
    matches = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    demand(len(matches) == 1, "function_not_unique", tree, name)
    return matches[0]


def nodes_in(node):
    """Visit this function's syntax, without entering a nested definition."""
    yield node
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        yield from nodes_in(child)


def literal_key(node):
    demand(isinstance(node, ast.Constant) and isinstance(node.value, str),
           "computed_producer_key", node, "Expected a literal string dictionary key")
    return node.value


def bindings(target, value):
    if isinstance(target, ast.Name):
        return [(target.id, value)]
    if isinstance(target, (ast.Tuple, ast.List)) and isinstance(value, (ast.Tuple, ast.List)):
        demand(len(target.elts) == len(value.elts), "producer_unpacking", target, "Unequal tuple lengths")
        return [pair for left, right in zip(target.elts, value.elts) for pair in bindings(left, right)]
    return []


def producer_keys(tree):
    fn = function(tree, "score")
    nodes = list(nodes_in(fn))
    returns = [n for n in nodes if isinstance(n, ast.Return)]
    demand(returns and all(isinstance(n.value, ast.Name) for n in returns),
           "producer_return_unresolved", fn, "score must return one named report")
    names = {n.value.id for n in returns}
    demand(len(names) == 1, "producer_return_unresolved", fn, "Multiple returned report variables")
    report = names.pop()
    assignments = {}
    for n in nodes:
        if isinstance(n, ast.Assign):
            for target in n.targets:
                for name, value in bindings(target, n.value):
                    assignments.setdefault(name, []).append(value)
        elif isinstance(n, ast.AnnAssign) and n.value is not None:
            for name, value in bindings(n.target, n.value):
                assignments.setdefault(name, []).append(value)

    mapping_aliases = set()
    def dictionary(expr, trail=()):
        if isinstance(expr, ast.Name):
            values = assignments.get(expr.id, [])
            demand(expr.id not in trail and len(values) == 1, "producer_mapping_alias_unresolved", expr, expr.id)
            mapping_aliases.add(expr.id)
            return dictionary(values[0], trail + (expr.id,))
        demand(isinstance(expr, ast.Dict), "producer_mapping_unresolved", expr,
               "Expected a dictionary literal or a single literal alias")
        demand(all(key is not None for key in expr.keys), "producer_mapping_unpacking", expr,
               "Dictionary unpacking is outside the checked construction grammar")
        keys = [literal_key(key) for key in expr.keys]
        demand(len(keys) == len(set(keys)), "producer_duplicate_key", expr, repr(keys))
        return dict(zip(keys, expr.values))

    roots = assignments.get(report, [])
    demand(len(roots) == 1 and any(isinstance(n, ast.Assign) and roots[0] is n.value for n in fn.body),
           "producer_root_unresolved", fn, "Report needs one unconditional dictionary initialization")
    fields = dictionary(roots[0])
    assigned_fields = set()
    for statement in fn.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name) and target.value.id == report:
                    key = literal_key(target.slice)
                    demand(key not in assigned_fields and key not in fields, "producer_field_reassigned", target, key)
                    assigned_fields.add(key)
                    fields[key] = statement.value
    for n in nodes:
        if isinstance(n, ast.Subscript) and isinstance(n.ctx, (ast.Store, ast.Del)):
            base = n
            while isinstance(base, ast.Subscript):
                base = base.value
            if isinstance(base, ast.Name) and base.id == report:
                demand(isinstance(n.value, ast.Name) and any(
                    isinstance(s, ast.Assign) and n in s.targets for s in fn.body),
                    "producer_conditional_or_nested_write", n,
                    "Report writes must be unconditional literal fields; nested mutations are unsupported")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            base = n.func.value
            if isinstance(base, ast.Name) and base.id == report:
                raise Unresolved("producer_report_method", n, "Report method calls may change its key set")
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Name) and n.value.id == report:
            raise Unresolved("producer_report_escape", n, "An alias of the report is outside the construction grammar")

    schemas = {(): set(fields)}
    for name in MAPPING_FIELDS:
        demand(name in fields, "producer_scope_missing", fn, name)
        schemas[(name,)] = set(dictionary(fields[name]))
    demand(ROW_FIELD in fields and isinstance(fields[ROW_FIELD], ast.Name),
           "producer_rows_unresolved", fn, ROW_FIELD + " must refer to an append-built list")
    buffer = fields[ROW_FIELD].id
    initial = assignments.get(buffer, [])
    demand(len(initial) == 1 and isinstance(initial[0], ast.List) and not initial[0].elts,
           "producer_rows_initialization", fields[ROW_FIELD], buffer + " must start as one empty list")
    shapes = []
    for n in nodes:
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == buffer:
            demand(n.func.attr == "append" and len(n.args) == 1 and not n.keywords,
                   "producer_rows_mutation", n, "Only append of a resolved dictionary is supported")
            shapes.append(set(dictionary(n.args[0])))
        if isinstance(n, ast.Subscript) and isinstance(n.ctx, (ast.Store, ast.Del)) and isinstance(n.value, ast.Name) and n.value.id == buffer:
            raise Unresolved("producer_rows_mutation", n, "Indexed row-list mutation is unsupported")
        if isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name) and n.target.id == buffer:
            raise Unresolved("producer_rows_mutation", n, "Augmented row-list mutation is unsupported")
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Name) and n.value.id == buffer:
            demand(all(isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name) and t.value.id == report
                       and literal_key(t.slice) == ROW_FIELD for t in n.targets),
                   "producer_rows_escape", n, "An alias of the row list is unsupported")
    demand(shapes, "producer_rows_shape_missing", fn, "No row append found")
    for n in nodes:
        if isinstance(n, ast.Assign):
            value = n.value
            if isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name) and value.value.id == report:
                demand(literal_key(value.slice) not in {*MAPPING_FIELDS, ROW_FIELD},
                       "producer_nested_scope_escape", n,
                       "A returned checked container is assigned to an unanalyzed alias")
            if isinstance(value, ast.Name) and value.id in mapping_aliases:
                demand(all(isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                           and t.value.id == report for t in n.targets),
                       "producer_mapping_escape", n, "A mapping alias escapes its report assignment")
        if isinstance(n, ast.Subscript) and isinstance(n.ctx, (ast.Store, ast.Del)):
            base = n
            while isinstance(base, ast.Subscript):
                base = base.value
            demand(not isinstance(base, ast.Name) or base.id not in mapping_aliases,
                   "producer_mapping_alias_mutation", n, "Mapping-alias mutation is unsupported")
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            receiver = n.func.value
            alias = isinstance(receiver, ast.Name) and receiver.id in mapping_aliases
            field = (isinstance(receiver, ast.Subscript) and isinstance(receiver.value, ast.Name)
                     and receiver.value.id == report and literal_key(receiver.slice) in {*MAPPING_FIELDS, ROW_FIELD})
            demand(not alias and not field, "producer_nested_scope_method", n,
                   "Method calls on a checked producer mapping are unsupported")
    # Every emitted row must supply a read key. A union would conceal a branch
    # emitting a different shape, and would miss a missing-key error.
    schemas[(ROW_FIELD, "[]")] = set.intersection(*shapes)
    return schemas


@dataclass(frozen=True)
class Ref:
    path: tuple
    sequence: bool = False


@dataclass(frozen=True)
class Literal:
    value: object


@dataclass(frozen=True)
class Sequence:
    values: tuple


@dataclass(frozen=True)
class Unknown:
    refs: tuple = ()


UNKNOWN = Unknown()


def refs(value):
    if isinstance(value, Ref):
        return {value}
    if isinstance(value, Sequence):
        return set().union(*(refs(item) for item in value.values))
    return set(value.refs) if isinstance(value, Unknown) else set()


class Reader:
    SAFE_SCALARS = {"len", "bool", "type", "isinstance", "str", "repr", "int", "sorted", "set", "all", "any"}

    def __init__(self, tree, schemas):
        self.tree, self.schemas, self.reads = tree, schemas, []
        self.identity = set()
        for fn in tree.body:
            if isinstance(fn, ast.FunctionDef) and fn.args.args:
                returns = [n for n in nodes_in(fn) if isinstance(n, ast.Return)]
                guard_only = all(isinstance(n, ast.Return) or (isinstance(n, ast.Expr) and (
                    isinstance(n.value, ast.Constant) or (isinstance(n.value, ast.Call)
                    and isinstance(n.value.func, ast.Name) and n.value.func.id == "require"))) for n in fn.body)
                if guard_only and returns and all(isinstance(n.value, ast.Name) and n.value.id == fn.args.args[0].arg for n in returns):
                    self.identity.add(fn.name)

    def checked_container(self, value):
        return any(r.path in self.schemas or r.path == (ROW_FIELD,) for r in refs(value))

    def key(self, receiver, key, node):
        if isinstance(receiver, Unknown):
            demand(not self.checked_container(receiver), "consumer_alias_unresolved", node,
                   "Cannot resolve the dictionary behind this read")
            return UNKNOWN
        if not isinstance(receiver, Ref):
            return UNKNOWN
        if receiver.sequence:
            return Ref(receiver.path + ("[]",))
        if not isinstance(key, Literal) or not isinstance(key.value, str):
            demand(receiver.path not in self.schemas, "consumer_key_unresolved", node,
                   "Computed key in " + scope_name(receiver.path))
            return Unknown((receiver,))
        if receiver.path in self.schemas:
            self.reads.append({"scope": scope_name(receiver.path), "path": receiver.path,
                               "key": key.value, "line": node.lineno})
        path = receiver.path + (key.value,)
        return Ref(path, path == (ROW_FIELD,))

    def bind(self, target, value, env):
        if isinstance(target, ast.Name):
            env[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            if isinstance(value, Sequence) and len(value.values) == len(target.elts):
                for name, item in zip(target.elts, value.values):
                    self.bind(name, item, env)
            else:
                demand(not self.checked_container(value), "consumer_unpacking_unresolved", target,
                       "Cannot unpack a checked container")
                for name in target.elts:
                    self.bind(name, UNKNOWN, env)
        elif isinstance(target, ast.Subscript):
            container = self.expr(target.value, env)
            demand(not self.checked_container(container), "consumer_mapping_mutation", target,
                   "Mutation of a checked input is unsupported")
            self.expr(target.slice, env)
        else:
            demand(not self.checked_container(value), "consumer_assignment_unresolved", target,
                   "Cannot follow this checked-container assignment")

    def iterations(self, value):
        if isinstance(value, Sequence):
            return value.values
        if isinstance(value, Ref) and value.sequence:
            return (Ref(value.path + ("[]",)),)
        return (Unknown(tuple(refs(value))),)

    def expr(self, node, env):
        if node is None:
            return UNKNOWN
        if isinstance(node, ast.Name):
            return env.get(node.id, UNKNOWN)
        if isinstance(node, ast.Constant):
            return Literal(node.value)
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            return Sequence(tuple(self.expr(n, env) for n in node.elts))
        if isinstance(node, ast.Subscript):
            return self.key(self.expr(node.value, env), self.expr(node.slice, env), node)
        if isinstance(node, ast.Call):
            args = [self.expr(n, env) for n in node.args]
            args += [self.expr(n.value, env) for n in node.keywords]
            if isinstance(node.func, ast.Attribute):
                receiver = self.expr(node.func.value, env)
                if node.func.attr == "get" and isinstance(receiver, (Ref, Unknown)):
                    demand(bool(args), "consumer_get_without_key", node, "Missing key")
                    return self.key(receiver, args[0], node)
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "copy" and node.func.attr == "deepcopy":
                    return args[0] if args else UNKNOWN
                demand(not self.checked_container(receiver), "consumer_method_unresolved", node,
                       "Unsupported method on a checked container: " + node.func.attr)
            if isinstance(node.func, ast.Name):
                name = node.func.id
                if name in self.identity:
                    result = args[0] if args else UNKNOWN
                    if name == "list_value" and isinstance(result, Ref):
                        return Ref(result.path, True)
                    return result
                if name == "enumerate" and args:
                    return Sequence(tuple(Sequence((UNKNOWN, item)) for item in self.iterations(args[0])))
                if name in self.SAFE_SCALARS:
                    return UNKNOWN
            demand(not any(self.checked_container(arg) for arg in args), "consumer_call_unresolved", node,
                   "Opaque call receives a checked container")
            return UNKNOWN
        if isinstance(node, (ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)):
            outputs = []
            def visit(index, local):
                if index == len(node.generators):
                    if isinstance(node, ast.DictComp):
                        self.expr(node.key, local)
                        outputs.append(self.expr(node.value, local))
                    else:
                        outputs.append(self.expr(node.elt, local))
                    return
                generator = node.generators[index]
                demand(not generator.is_async, "consumer_async_comprehension", node, "Async iteration unsupported")
                for item in self.iterations(self.expr(generator.iter, local)):
                    child = dict(local)
                    self.bind(generator.target, item, child)
                    for condition in generator.ifs:
                        self.expr(condition, child)
                    visit(index + 1, child)
            visit(0, dict(env))
            return Sequence(tuple(outputs))
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                self.expr(key, env)
                self.expr(value, env)
            return UNKNOWN
        values = [self.expr(child, env) for child in ast.iter_child_nodes(node) if isinstance(child, ast.expr)]
        if isinstance(node, (ast.Compare, ast.BoolOp, ast.UnaryOp, ast.JoinedStr, ast.FormattedValue)):
            return UNKNOWN
        return Unknown(tuple(set().union(*(refs(value) for value in values))))

    def block(self, statements, env):
        for node in statements:
            if isinstance(node, ast.Assign):
                value = self.expr(node.value, env)
                for target in node.targets:
                    self.bind(target, value, env)
            elif isinstance(node, ast.AnnAssign):
                self.bind(node.target, self.expr(node.value, env), env)
            elif isinstance(node, (ast.Expr, ast.Return, ast.Raise, ast.Assert)):
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.expr):
                        self.expr(child, env)
            elif isinstance(node, ast.For):
                for item in self.iterations(self.expr(node.iter, env)):
                    self.bind(node.target, item, env)
                    self.block(node.body, env)
                self.block(node.orelse, env)
            elif isinstance(node, ast.If):
                self.expr(node.test, env)
                left, right = dict(env), dict(env)
                self.block(node.body, left)
                self.block(node.orelse, right)
                for name in left.keys() | right.keys():
                    a, b = left.get(name, UNKNOWN), right.get(name, UNKNOWN)
                    env[name] = a if a == b else Unknown(tuple(refs(a) | refs(b)))
            elif isinstance(node, ast.Pass):
                pass
            else:
                raise Unresolved("consumer_control_flow_unresolved", node,
                                 "Unsupported statement: " + type(node).__name__)

    def run(self):
        fn = function(self.tree, "observe")
        demand(bool(fn.args.args), "consumer_argument_missing", fn, "observe needs its score argument")
        self.block(fn.body, {fn.args.args[0].arg: Ref(())})
        demand(all(any(tuple(row["path"]) == scope for row in self.reads) for scope in SCOPES),
               "consumer_scope_not_resolved", fn, "All four configured scopes must have resolved reads")
        return self.reads


def check_sources(producer, consumer):
    source = PRODUCER
    try:
        schemas = producer_keys(ast.parse(producer, filename=PRODUCER))
        source = CONSUMER
        reads = Reader(ast.parse(consumer, filename=CONSUMER), schemas).run()
        missing = [dict(code="missing_producer_key", source=CONSUMER, **row) for row in reads
                   if row["key"] not in schemas[tuple(row["path"])]]
        result = {"status": "incompatible" if missing else "compatible",
                  "checked_scopes": {scope_name(path): sorted(keys) for path, keys in schemas.items()},
                  "consumer_reads": reads, "diagnostics": missing,
                  "scope_limit": "Only the listed dictionary scopes; no runtime/type/semantic guarantee."}
        return (1 if missing else 0), result
    except (Unresolved, SyntaxError, UnicodeError) as error:
        return 2, {"status": "unresolved", "diagnostics": [{
            "code": getattr(error, "code", "source_parse_error"),
            "source": source, "line": getattr(error, "line", getattr(error, "lineno", 0)), "detail": str(error)}]}


def index_bytes(repo, path):
    proc = subprocess.run(["git", "-C", str(repo), "show", ":" + path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        raise ValueError("Cannot read index stage 0 for " + path + ": " + proc.stderr.decode(errors="replace"))
    return proc.stdout


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        read = (lambda path: index_bytes(args.repo, path)) if args.staged else (lambda path: (args.repo / path).read_bytes())
        code, result = check_sources(read(PRODUCER), read(CONSUMER))
    except (OSError, ValueError) as error:
        code, result = 2, {"status": "unresolved", "diagnostics": [{"code": "source_read_error", "detail": str(error)}]}
    result["source"] = "index-stage-0" if args.staged else "working-tree"
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif code:
        print("Score/observation AST contract: " + result["status"] + " (" + result["source"] + ")", file=sys.stderr)
        for item in result["diagnostics"]:
            print(json.dumps(item, ensure_ascii=False), file=sys.stderr)
    else:
        print("Score/observation AST contract: PASS (" + result["source"] + "; "
              + ", ".join(result["checked_scopes"]) + ")")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
