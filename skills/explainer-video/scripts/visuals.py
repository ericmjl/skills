"""A cumulative file tree driven by each beat's ``delta``.

A path-shaped delta (``environment.yml``, ``data/raw.csv``) grows a diagram.
A sentence stays a single labeled row, which is the scaffold the timing pass
still uses. The newest delta is the node marked ``added``.

Four named kinds render as seek-safe picture templates instead of a tree
row: ``number-counter``, ``before-after-stat``, ``cause-chain``, and
``checklist-pop``.
"""

from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from typing import Any

PATH_RE = re.compile(r"^[A-Za-z0-9_./~-]+$")
TEMPLATE_KINDS: frozenset[str] = frozenset(
    {"number-counter", "before-after-stat", "cause-chain", "checklist-pop"}
)
KIND_RE = re.compile(
    r"^(number-counter|before-after-stat|cause-chain|checklist-pop)"
    r"(?:\s+|:)(.*)$",
    re.IGNORECASE | re.DOTALL,
)
PAIR_RE = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\[.*?\]|\S+)')


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


def parse_delta_kind(delta: str) -> tuple[str, dict[str, Any]] | None:
    """Parse a named picture template out of a delta field.

    Accepted forms::

        number-counter {"title": "Users", "value": 1285000, "suffix": "+"}
        before-after-stat label=Build before=12 after=3 unit=h
        cause-chain
        checklist-pop {"title": "Ship", "items": ["Lint", "Tests"]}

    :param delta: The beat's delta field.
    :returns: ``(kind, payload)``, or None when this is a path or sentence.
    :raises ValueError: The payload looks like JSON but is not an object.
    """
    text = delta.strip()
    if not text or text.lower() == "none":
        return None
    if text.lower() in TEMPLATE_KINDS:
        return text.lower(), {}
    match = KIND_RE.match(text)
    if match is None:
        return None
    kind = match.group(1).lower()
    return kind, _parse_payload(match.group(2).strip())


def is_template_delta(delta: str) -> bool:
    """Return whether a delta is a named picture template.

    This is a syntactic check. A kind with broken JSON still counts as a
    template so ``split_delta`` will not treat the payload as a path list.

    :param delta: A single delta string.
    :returns: True for the four template kinds.
    """
    text = delta.strip()
    if not text:
        return False
    if text.lower() in TEMPLATE_KINDS:
        return True
    return KIND_RE.match(text) is not None


def is_file_path(delta: str) -> bool:
    """Return whether a delta should grow the file tree.

    :param delta: The beat's delta field, already a single path.
    :returns: True for a slash path, a dotted filename, or a ``~/`` home path,
        with no spaces.
    """
    text = delta.strip()
    if not text or text.lower() == "none" or " " in text:
        return False
    if is_template_delta(text):
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
    if is_template_delta(text):
        return (text,)
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
    added_kind = parse_delta_kind(added or "")
    if added_kind is not None:
        kind, payload = added_kind
        return render_template(kind, payload, index=index)
    items = [item for item in items if parse_delta_kind(item) is None]
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


def render_template(kind: str, payload: dict[str, Any], *, index: int) -> str:
    """Render one named picture template in the house palette.

    :param kind: One of :data:`TEMPLATE_KINDS`.
    :param payload: Fields from the delta (JSON or ``key=value``).
    :param index: Beat index, used in element ids.
    :returns: HTML for the picture.
    :raises ValueError: The kind is unknown.
    """
    if kind == "number-counter":
        return _render_number_counter(payload, index=index)
    if kind == "before-after-stat":
        return _render_before_after(payload, index=index)
    if kind == "cause-chain":
        return _render_cause_chain(payload, index=index)
    if kind == "checklist-pop":
        return _render_checklist(payload, index=index)
    raise ValueError(f"Unknown picture template {kind!r}.")


def template_items(payload: dict[str, Any]) -> tuple[str, ...]:
    """Return checklist rows from ``items`` or ``item1`` / ``item2`` / ``item3``.

    :param payload: Template fields.
    :returns: Non-empty item strings, in order.
    """
    raw = payload.get("items")
    if isinstance(raw, list):
        return tuple(str(item).strip() for item in raw if str(item).strip())
    if isinstance(raw, str) and raw.strip():
        splitter = "|" if "|" in raw else ","
        return tuple(part.strip() for part in raw.split(splitter) if part.strip())
    found: list[str] = []
    for ordinal in range(1, 9):
        value = payload.get(f"item{ordinal}")
        if value is None:
            break
        text = str(value).strip()
        if text:
            found.append(text)
    return tuple(found)


def _parse_payload(rest: str) -> dict[str, Any]:
    """Parse a JSON object or ``key=value`` pairs.

    :param rest: Text after the kind name.
    :returns: A field map. Empty input is an empty map.
    :raises ValueError: JSON is present but is not an object.
    """
    if not rest:
        return {}
    if rest.startswith("{"):
        try:
            data = json.loads(rest)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Template payload is not valid JSON: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("Template payload JSON must be an object.")
        return data
    payload: dict[str, Any] = {}
    for match in PAIR_RE.finditer(rest):
        key = match.group(1)
        raw = match.group(2)
        if raw.startswith(("[", '"')):
            payload[key] = json.loads(raw)
        else:
            payload[key] = _coerce(raw)
    return payload


def _coerce(raw: str) -> int | float | str:
    """Turn a bare token into a number when it looks like one.

    :param raw: An unquoted ``key=value`` token.
    :returns: int, float, or the original string.
    """
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _escape(value: object) -> str:
    """Escape text for an HTML text node.

    :param value: Any payload value.
    :returns: Escaped text.
    """
    return html.escape(str(value))


def _number_value(payload: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    """Read the first present numeric field.

    :param payload: Template fields.
    :param keys: Names to try, in order.
    :param default: Fallback when none of the keys are present.
    :returns: A float (integers come through as whole numbers).
    """
    for key in keys:
        if key not in payload or payload[key] in (None, ""):
            continue
        return float(payload[key])
    return default


def _render_number_counter(payload: dict[str, Any], *, index: int) -> str:
    """Giant number that counts up on the timeline.

    :param payload: ``title``, ``value`` (or ``target`` / ``targetValue``),
        ``prefix``, ``suffix``, ``note``.
    :param index: Beat index.
    :returns: HTML.
    """
    title = _escape(payload.get("title") or "Count")
    prefix = _escape(payload.get("prefix") or "")
    suffix = _escape(payload.get("suffix") or "")
    note = _escape(payload.get("note") or "")
    target = _number_value(payload, "value", "target", "targetValue")
    note_html = f'<div class="delta-note">{note}</div>' if note else ""
    return (
        f'<div class="delta-counter" id="counter-{index}" data-target="{target:g}">'
        f'<div class="delta-kicker">{title}</div>'
        f'<div class="delta-num">'
        f'<span class="delta-prefix" id="counter-prefix-{index}">{prefix}</span>'
        f'<span class="delta-value" id="counter-value-{index}">0</span>'
        f'<span class="delta-suffix" id="counter-suffix-{index}">{suffix}</span>'
        f"</div>"
        f"{note_html}"
        f"</div>"
    )


def _render_before_after(payload: dict[str, Any], *, index: int) -> str:
    """Two stats on either side of an arrow, after value emphasized.

    :param payload: ``label``, ``before`` / ``beforeValue``, ``after`` /
        ``afterValue``, ``unit``, ``before_label`` / ``beforeLabel``,
        ``after_label`` / ``afterLabel``, ``conclusion``.
    :param index: Beat index.
    :returns: HTML.
    """
    label = _escape(payload.get("label") or payload.get("title") or "Before / after")
    before_label = _escape(
        payload.get("before_label") or payload.get("beforeLabel") or "Before"
    )
    after_label = _escape(
        payload.get("after_label") or payload.get("afterLabel") or "After"
    )
    unit = _escape(payload.get("unit") or "")
    unit_html = f'<span class="delta-unit">{unit}</span>' if unit else ""
    before = _escape(_format_stat(_number_value(payload, "before", "beforeValue")))
    conclusion = _escape(payload.get("conclusion") or "")
    conclusion_html = f'<div class="delta-note">{conclusion}</div>' if conclusion else ""
    return (
        f'<div class="delta-stat" id="stat-{index}">'
        f'<div class="delta-kicker">{label}</div>'
        f'<div class="delta-pair">'
        f'<div class="delta-before">'
        f'<div class="delta-tag">{before_label}</div>'
        f'<div class="delta-num"><span id="stat-before-{index}">{before}</span>{unit_html}</div>'
        f"</div>"
        f'<div class="delta-arrow">→</div>'
        f'<div class="delta-after">'
        f'<div class="delta-tag">{after_label}</div>'
        f'<div class="delta-num"><span class="delta-value" id="stat-after-{index}">0</span>{unit_html}</div>'
        f"</div>"
        f"</div>"
        f"{conclusion_html}"
        f"</div>"
    )


def _render_cause_chain(payload: dict[str, Any], *, index: int) -> str:
    """Three-step cause → mechanism → result.

    :param payload: ``title``, ``cause``, ``mechanism``, ``result``.
    :param index: Beat index.
    :returns: HTML.
    """
    title = _escape(payload.get("title") or "Cause chain")
    steps = (
        ("Cause", str(payload.get("cause") or "")),
        ("Mechanism", str(payload.get("mechanism") or "")),
        ("Result", str(payload.get("result") or "")),
    )
    cards: list[str] = []
    for ordinal, (tag, body) in enumerate(steps):
        extra = " result" if tag == "Result" else ""
        cards.append(
            f'<div class="delta-step{extra}" id="chain-step-{index}-{ordinal}">'
            f'<div class="delta-dot"></div>'
            f'<div class="delta-tag">{tag}</div>'
            f'<div class="delta-body">{_escape(body)}</div>'
            f"</div>"
        )
    return (
        f'<div class="delta-chain" id="chain-{index}">'
        f'<div class="delta-kicker">{title}</div>'
        f'<div class="delta-chain-track">'
        f'<div class="delta-chain-fill" id="chain-fill-{index}"></div>'
        f"</div>"
        f'<div class="delta-chain-steps">{"".join(cards)}</div>'
        f"</div>"
    )


def _render_checklist(payload: dict[str, Any], *, index: int) -> str:
    """Rows that pop in, then mark themselves checked.

    :param payload: ``title`` and ``items`` or ``item1``..``itemN``.
    :param index: Beat index.
    :returns: HTML.
    """
    title = _escape(payload.get("title") or "Checklist")
    items = template_items(payload) or ("Item",)
    rows: list[str] = []
    for ordinal, item in enumerate(items):
        rows.append(
            f'<li class="delta-check-item" id="check-{index}-{ordinal}">'
            f'<span class="delta-box" id="check-mark-{index}-{ordinal}">✓</span>'
            f"<span>{_escape(item)}</span>"
            f"</li>"
        )
    return (
        f'<div class="delta-checks" id="checks-{index}">'
        f'<div class="delta-kicker">{title}</div>'
        f'<ul class="delta-check-list">{"".join(rows)}</ul>'
        f"</div>"
    )


def _format_stat(value: float) -> str:
    """Format a before/after number without trailing zeros.

    :param value: The statistic.
    :returns: A compact decimal string.
    """
    if float(value).is_integer():
        return str(int(value))
    return f"{value:g}"
