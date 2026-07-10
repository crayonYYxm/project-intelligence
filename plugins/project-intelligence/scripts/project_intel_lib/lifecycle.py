from __future__ import annotations

from pathlib import Path
from typing import Callable


def changed_project_files(root: Path, run: Callable[..., tuple[int, str, str]]) -> list[str]:
    tracked_code, tracked, _ = run(["git", "diff", "--name-only", "HEAD", "--"], root, timeout=20)
    untracked_code, untracked, _ = run(["git", "ls-files", "--others", "--exclude-standard"], root, timeout=20)
    if tracked_code != 0 and untracked_code != 0:
        return []
    values = []
    if tracked_code == 0:
        values.extend(tracked.splitlines())
    if untracked_code == 0:
        values.extend(untracked.splitlines())
    return sorted(dict.fromkeys(value.strip() for value in values if value.strip()))


def query_paths(project_dir: Path) -> list[Path]:
    paths = [project_dir / "manifest.json", project_dir / "config.json", project_dir / "graph" / "project-graph.json"]
    paths.extend(sorted((project_dir / "standards").glob("*.md")))
    paths.extend(sorted((project_dir / "reports").glob("*.md")))
    paths.extend(sorted((project_dir / "requirements").rglob("*.md")))
    paths.extend(sorted((project_dir / "knowledge").glob("*.json")))
    return [path for path in paths if path.is_file()]


def match_context(body: str, needle: str, radius: int = 600) -> tuple[str, int] | None:
    index = body.lower().find(needle.lower())
    if index < 0:
        return None
    start = max(0, index - radius)
    end = min(len(body), index + len(needle) + radius)
    while start > 0 and body[start - 1] != "\n":
        start -= 1
    while end < len(body) and body[end] != "\n":
        end += 1
    line = body.count("\n", 0, index) + 1
    prefix = "[...省略...]\n" if start else ""
    suffix = "\n[...省略...]" if end < len(body) else ""
    return prefix + body[start:end].strip() + suffix, line
