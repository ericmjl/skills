"""A cumulative file tree driven by each beat's ``delta``.

A path-shaped delta (``environment.yml``, ``data/raw.csv``) grows a diagram.
A sentence stays a single labeled row, which is the scaffold the timing pass
still uses. The newest delta is the node marked ``added``.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

PATH_RE = re.compile(r"^[A-Za-z0-9_./~-]+$")


@dataclass(frozen=True)
class TreeNode:
    """One file or directory in the on-screen tree.

    :param name: The path segment shown on this row.
    :param file: True for a file. A directory contains children.
    :param added: True when this node is the beat's new delta.
    :param children: Nested nodes, in insertion order.
    """

    name: str
    file: bool
    added: bool
    children: tuple[TreeNode, ...] = ()


def is_file_path(delta: str) -> bool:
    """Return whether a delta should grow the file tree.

    :param delta: The beat's delta field, already a single path.
    :returns: True for a slash path, a dotted filename, or a ``~/`` home path,
        with no spaces.
    """
    text = delta.strip()
    if not text or text.lower() == "none" or " " in text:
        return False
    if PATH_RE.fullmatch(text) is None:
        return False
    return "/" in text or "." in text or text.startswith("~")


def is_home_path(delta: str) -> bool:
    """Return whether a path lives under a ``~/`` tree root.

    :param delta: A single delta string.
    :returns: True for ``~`` or a path that starts with ``~/``.
    """
    text = delta.strip()
    return text == "~" or text.startswith("~/")


def split_delta(delta: str) -> tuple[str, ...]:
    """Split a delta field into picture entries.

    Comma-separated values become separate paths when every piece is a file
    path. A sentence that happens to contain a comma stays one entry.

    :param delta: The beat's delta field.
    :returns: Zero or more picture strings. ``none`` is empty.
    """
    text = delta.strip()
    if not text or text.lower() == "none":
        return ()
    parts = tuple(part.strip() for part in text.split(",") if part.strip())
    if len(parts) > 1 and all(is_file_path(part) for part in parts):
        return parts
    return (text,)


def any_file_path(deltas: list[str]) -> bool:
    """Return whether the picture contains a file path.

    :param deltas: Cumulative delta strings.
    :returns: True when at least one delta is a path.
    """
    return any(is_file_path(item) for item in deltas)


def build_file_tree(deltas: list[str], *, added: str | None) -> tuple[TreeNode, ...]:
    """Fold path deltas into a tree. Sentence deltas become root leaves.

    :param deltas: Picture so far, in beat order.
    :param added: The delta this beat introduced, or None. May be comma-separated.
    :returns: Root nodes.
    """
    added_items = set(split_delta(added or ""))
    root: dict[str, object] = {"children": {}}
    for delta in deltas:
        text = delta.strip()
        if not text or text.lower() == "none":
            continue
        parts = _parts(text)
        _insert(
            root,
            parts,
            added=text in added_items,
            is_dir=text.strip().endswith("/"),
        )
    return _freeze(root)


def render_picture(deltas: list[str], *, index: int, added: str | None) -> str:
    """Render the cumulative picture.

    Path pictures become a nested file tree. Other pictures stay a flat list
    so a sentence delta still shows up as a row.

    :param deltas: Cumulative delta strings.
    :param index: Beat index, used in element ids.
    :param added: This beat's delta, when it should be marked.
    :returns: HTML, or an empty string when the picture is empty.
    """
    items = [item.strip() for item in deltas if item.strip() and item.strip().lower() != "none"]
    if not items:
        return ""
    if any_file_path(items):
        project = [item for item in items if not is_home_path(item)]
        home = [item for item in items if is_home_path(item)]
        trees: list[str] = []
        if project:
            trees.append(
                _render_tree(
                    build_file_tree(project, added=added),
                    index=index,
                    depth=0,
                    tree_id=f"tree-{index}",
                )
            )
        if home:
            home_id = f"tree-home-{index}" if project else f"tree-{index}"
            trees.append(
                _render_tree(
                    build_file_tree(home, added=added),
                    index=index,
                    depth=0,
                    tree_id=home_id,
                )
            )
        if len(trees) == 2:
            return f'<div class="forest">{"".join(trees)}</div>'
        return trees[0] if trees else ""
    return _render_rows(items, index=index, added=added)


def _parts(delta: str) -> list[str]:
    """Split a delta into tree segments.

    :param delta: A path or a sentence.
    :returns: Path parts, or one part for a sentence. A ``~/`` path starts at ``~``.
    """
    if is_file_path(delta):
        text = delta.strip()
        if is_home_path(text):
            rest = text[1:].lstrip("/")
            return ["~", *[part for part in rest.split("/") if part]] if rest else ["~"]
        return [part for part in text.strip("/").split("/") if part]
    return [delta.strip()]


def _insert(
    node: dict[str, object], parts: list[str], *, added: bool, is_dir: bool = False
) -> None:
    """Insert one path under ``node``.

    :param node: Mutable tree node with a ``children`` dict.
    :param parts: Remaining path segments.
    :param added: True when the leaf is this beat's delta.
    :param is_dir: True when the original delta ended with ``/``.
    """
    children = node["children"]
    assert isinstance(children, dict)
    name = parts[0]
    child = children.get(name)
    if not isinstance(child, dict):
        child = {"children": {}, "added": False}
        children[name] = child
    if len(parts) == 1:
        child["added"] = added or bool(child.get("added"))
        child["dir"] = is_dir or bool(child.get("dir"))
        return
    _insert(child, parts[1:], added=added, is_dir=is_dir)


def _freeze(node: dict[str, object]) -> tuple[TreeNode, ...]:
    """Convert the mutable tree into frozen nodes.

    :param node: A node with a ``children`` dict.
    :returns: Children, directories before files, then by name.
    """
    children = node["children"]
    assert isinstance(children, dict)
    nodes: list[TreeNode] = []
    for name, child in children.items():
        assert isinstance(child, dict)
        nested = _freeze(child)
        nodes.append(
            TreeNode(
                name=str(name),
                file=not nested and not child.get("dir"),
                added=bool(child.get("added")) and not nested,
                children=nested,
            )
        )
    nodes.sort(key=lambda item: (item.file, item.name.lower()))
    return tuple(nodes)


def _render_tree(
    nodes: tuple[TreeNode, ...],
    *,
    index: int,
    depth: int,
    tree_id: str | None = None,
    added_count: list[int] | None = None,
) -> str:
    """Render nested file-tree HTML.

    :param nodes: Siblings.
    :param index: Beat index.
    :param depth: 0 at the root, so the root list carries the id.
    :param tree_id: Element id for the root list. Defaults to ``tree-{index}``.
    :param added_count: Mutable counter so multiple new files do not share an id.
    :returns: A ``ul`` element.
    """
    marked = added_count if added_count is not None else []
    rows: list[str] = []
    for node in nodes:
        label = html.escape(node.name + ("/" if not node.file else ""))
        if node.added and not node.children:
            suffix = "" if not marked else f"-{len(marked)}"
            marked.append(1)
            rows.append(f'<li class="added" id="added-{index}{suffix}">{label}</li>')
        elif node.file or not node.children:
            rows.append(f"<li>{label}</li>")
        else:
            nested = _render_tree(
                node.children,
                index=index,
                depth=depth + 1,
                added_count=marked,
            )
            rows.append(f"<li>{label}{nested}</li>")
    body = "".join(rows)
    if depth == 0:
        element_id = tree_id or f"tree-{index}"
        return f'<ul class="filetree" id="{element_id}">{body}</ul>'
    return f"<ul>{body}</ul>"


def _render_rows(items: list[str], *, index: int, added: str | None) -> str:
    """Render a flat list of sentence deltas.

    :param items: Non-empty delta strings.
    :param index: Beat index.
    :param added: Delta to mark, or None.
    :returns: The scaffold list.
    """
    mark = (added or "").strip()
    rows: list[str] = []
    for item in items:
        text = html.escape(item)
        if mark and item == mark and item == items[-1]:
            rows.append(f'        <li class="added" id="added-{index}">{text}</li>')
        else:
            rows.append(f"        <li>{text}</li>")
    body = "\n".join(rows)
    return f"""      <ul class="tree" id="tree-{index}">
{body}
      </ul>"""
