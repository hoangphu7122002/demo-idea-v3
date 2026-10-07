"""Split an MDX post into top-level blocks (the unit that gets a stable paragraph id).

Line-based scanner following CommonMark block-start rules. markdown-it-py is not a
backend dependency yet; this module has no third-party imports.
"""

import re

_FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")
_HEADING = re.compile(r" {0,3}#{1,6}(\s|$)")
_HR = re.compile(r" {0,3}([-*_])( *\1){2,} *$")
_BULLET = re.compile(r" {0,3}[-*+]( |$)")
_ORDERED = re.compile(r" {0,3}\d{1,9}[.)]( |$)")
_QUOTE = re.compile(r" {0,3}>")
_TAG = re.compile(r" {0,3}</?[A-Za-z][\w.:-]*")
_INDENTED = re.compile(r"( {4}|\t)")


def _is_list_item(line: str) -> bool:
    return bool(_BULLET.match(line) or _ORDERED.match(line))


def _interrupts_paragraph(line: str) -> bool:
    """True when `line` starts a new block even without a blank line before it."""
    s = line.strip()
    return bool(
        _FENCE.match(line)
        or _HEADING.match(line)
        or _QUOTE.match(line)
        or _BULLET.match(line)
        or s.startswith("$$")
        or (_TAG.match(line) and not _HR.match(line))
    )


def _block_end(lines: list[str], i: int) -> int:
    """Return the index one past the last line of the block starting at non-blank line i."""
    line, n = lines[i], len(lines)
    fence = _FENCE.match(line)
    if fence:
        marker = fence.group(1)
        j = i + 1
        while j < n:
            m = _FENCE.match(lines[j])
            if m and m.group(1)[0] == marker[0] and len(m.group(1)) >= len(marker):
                if not lines[j].strip().lstrip(marker[0]):
                    return j + 1
            j += 1
        return n
    s = line.strip()
    if s.startswith("$$"):
        if len(s) > 2 and s.endswith("$$"):
            return i + 1
        j = i + 1
        while j < n and "$$" not in lines[j]:
            j += 1
        return min(j + 1, n)
    if _HEADING.match(line) or _HR.match(line):
        return i + 1
    if _INDENTED.match(line):
        j = i + 1
        while j < n and (not lines[j].strip() or _INDENTED.match(lines[j])):
            j += 1
        return j
    if _is_list_item(line):
        j = i + 1
        while j < n:
            cur = lines[j]
            if cur.strip():
                if not (_is_list_item(cur) or _INDENTED.match(cur) or cur.startswith("  ")):
                    # Lazy continuation only right after a non-blank line.
                    if not lines[j - 1].strip() or _interrupts_paragraph(cur):
                        break
            else:
                k = j
                while k < n and not lines[k].strip():
                    k += 1
                if k == n or not (_is_list_item(lines[k]) or lines[k].startswith("  ")):
                    break
            j += 1
        return j
    if _QUOTE.match(line) or _TAG.match(line):
        j = i + 1
        while j < n and lines[j].strip():
            j += 1
        return j
    j = i + 1
    while j < n and lines[j].strip() and not _interrupts_paragraph(lines[j]):
        j += 1
    return j


def split_blocks(mdx: str) -> list[str]:
    """Split MDX source into its top-level blocks, in document order.

    Each paragraph, heading, fenced/indented code block, `$$` math block, list (whole,
    with nested items), blockquote, thematic break and standalone JSX/HTML tag is one
    block. Blank lines inside fences and math stay inside their block. Blocks are the
    original lines, with surrounding blank lines removed. Pure: no I/O, deterministic.

    Args:
        mdx: MDX/Markdown source text.

    Returns:
        List of block strings; empty for blank input. Never raises on odd markdown.
    """
    lines = mdx.splitlines()
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        end = _block_end(lines, i)
        blocks.append("\n".join(lines[i:end]).strip("\n").rstrip())
        i = end
    return blocks
