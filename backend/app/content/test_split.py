"""Pins exact block counts of split_blocks on a fixed fixture."""

from app.content.split import split_blocks

FIXTURE = """# Title

First paragraph
continues here.

```python
x = 1

y = 2
```

$$
a = b

c = d
$$

- one
- two
  - nested

<Callout type="note" />

Last paragraph with $x^2$ inline.
"""


def test_fixture_block_count_and_content() -> None:
    blocks = split_blocks(FIXTURE)
    assert len(blocks) == 7
    assert blocks[0] == "# Title"
    assert blocks[1] == "First paragraph\ncontinues here."
    assert blocks[2].startswith("```python") and "y = 2" in blocks[2]  # blank line kept inside
    assert blocks[3] == "$$\na = b\n\nc = d\n$$"  # blank line kept inside
    assert blocks[4] == "- one\n- two\n  - nested"
    assert blocks[5] == '<Callout type="note" />'
    assert blocks[6] == "Last paragraph with $x^2$ inline."


def test_blank_and_pure() -> None:
    assert split_blocks("") == []
    assert split_blocks("\n\n  \n") == []
    assert split_blocks(FIXTURE) == split_blocks(FIXTURE)


def test_dollars_inside_fence_are_not_math() -> None:
    src = "```\n$$\n```\n\nafter\n\nmore"
    assert len(split_blocks(src)) == 3


def test_list_ends_at_unindented_paragraph_after_blank() -> None:
    src = "1. a\n\n2. b\n   more b\n\nnext para\n\n---\n\n> quote\n> more"
    assert split_blocks(src) == ["1. a\n\n2. b\n   more b", "next para", "---", "> quote\n> more"]


def test_heading_and_tag_interrupt_paragraph() -> None:
    src = "text\n## H\n<Figure src='a.png' />\n\n    indented\n    code"
    assert split_blocks(src) == ["text", "## H", "<Figure src='a.png' />", "    indented\n    code"]
