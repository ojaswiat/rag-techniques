"""Verifies that a rewrite touched only docstrings, never executable code.

Compares the AST of two revisions of the same file with every docstring
replaced by a placeholder. If the dumps differ, something other than a
docstring moved.
"""
import ast
import subprocess
import sys


_DOC_HOLDERS = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def strip_docstrings(tree: ast.AST) -> ast.AST:
    for node in ast.walk(tree):
        if not isinstance(node, _DOC_HOLDERS):
            continue
        body = node.body
        if not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            first.value.value = "<docstring>"
    return tree


def normalise(source: str) -> str:
    return ast.dump(strip_docstrings(ast.parse(source)), annotate_fields=True)


def git_show(rev: str, path: str) -> str:
    out = subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print("usage: check_docstrings_only.py <git-rev> <file> [<file>...]")
        return 2
    rev, paths = argv[1], argv[2:]
    failures = []
    for path in paths:
        try:
            before = normalise(git_show(rev, path))
        except subprocess.CalledProcessError:
            print(f"SKIP (new file) {path}")
            continue
        with open(path, encoding="utf-8") as handle:
            after = normalise(handle.read())
        if before != after:
            failures.append(path)
            print(f"FAIL {path}: executable code changed")
        else:
            print(f"ok   {path}")
    if failures:
        print(f"\n{len(failures)} file(s) changed more than docstrings")
        return 1
    print(f"\nall {len(paths)} file(s) docstring-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
