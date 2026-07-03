import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.tutorial

DOCS_ROOT = Path(__file__).resolve().parents[1] / "docs"
LITERALINCLUDE_RE = re.compile(
    r"^\.\.\s+literalinclude::\s+(\S+)",
    re.MULTILINE,
)


def _literalinclude_paths():
    paths = []
    for rst_file in DOCS_ROOT.rglob("*.rst"):
        text = rst_file.read_text()
        for match in LITERALINCLUDE_RE.finditer(text):
            rel = match.group(1)
            paths.append((rst_file.relative_to(DOCS_ROOT), rel))
    return paths


@pytest.mark.parametrize("rst_file,rel_path", _literalinclude_paths())
def test_literalinclude_target_exists(rst_file, rel_path):
    target = (DOCS_ROOT / rst_file).parent / rel_path
    target = target.resolve()
    repo_root = DOCS_ROOT.parent.resolve()
    assert target.is_file(), f"{rst_file}: missing literalinclude target {rel_path}"
    assert repo_root in target.parents or target == repo_root
