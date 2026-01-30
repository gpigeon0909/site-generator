import re
from enum import Enum

from htmlnode import LeafNode, ParentNode


class TextType(Enum):
    TEXT = "text"
    BOLD = "bold"
    ITALIC = "italic"
    CODE = "code"
    LINK = "link"
    IMAGE = "image"


class TextNode:
    def __init__(self, text: str, text_type: TextType, url: str | None = None):
        self.text = text
        self.text_type = text_type
        self.url = url

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TextNode):
            return False
        return (
            self.text == other.text
            and self.text_type == other.text_type
            and self.url == other.url
        )

    def __repr__(self) -> str:
        return f"TextNode({self.text!r}, {self.text_type.value!r}, {self.url!r})"


def text_node_to_html_node(text_node: TextNode) -> LeafNode:
    if text_node.text_type == TextType.TEXT:
        return LeafNode(None, text_node.text)
    if text_node.text_type == TextType.BOLD:
        return LeafNode("b", text_node.text)
    if text_node.text_type == TextType.ITALIC:
        return LeafNode("i", text_node.text)
    if text_node.text_type == TextType.CODE:
        return LeafNode("code", text_node.text)
    if text_node.text_type == TextType.LINK:
        return LeafNode("a", text_node.text, {"href": text_node.url or ""})
    if text_node.text_type == TextType.IMAGE:
        return LeafNode("img", "", {"src": text_node.url or "", "alt": text_node.text})
    raise ValueError(f"Unknown text type: {text_node.text_type}")


def split_nodes_delimiter(
    old_nodes: list[TextNode], delimiter: str, text_type: TextType
) -> list[TextNode]:
    new_nodes: list[TextNode] = []
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        parts = node.text.split(delimiter)
        if len(parts) == 1:
            new_nodes.append(node)
            continue
        if len(parts) % 2 == 0:
            raise ValueError(
                f"Invalid markdown: unclosed delimiter {delimiter!r}"
            )
        for i, part in enumerate(parts):
            if i % 2 == 0:
                new_nodes.append(TextNode(part, TextType.TEXT))
            else:
                new_nodes.append(TextNode(part, text_type))
    return new_nodes


def extract_markdown_images(text: str) -> list[tuple[str, str]]:
    """Return list of (alt_text, url) for markdown images ![alt](url)."""
    pattern = r"!\[([^\[\]]*)\]\(([^\(\)]*)\)"
    return re.findall(pattern, text)


def extract_markdown_links(text: str) -> list[tuple[str, str]]:
    """Return list of (anchor_text, url) for markdown links [text](url). Excludes images."""
    pattern = r"(?<!!)\[([^\[\]]*)\]\(([^\(\)]*)\)"
    return re.findall(pattern, text)


def split_nodes_image(old_nodes: list[TextNode]) -> list[TextNode]:
    """Split TEXT nodes by markdown images ![alt](url); non-TEXT nodes pass through."""
    new_nodes: list[TextNode] = []
    pattern = r"!\[([^\[\]]*)\]\(([^\(\)]*)\)"
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        text = node.text
        last_end = 0
        for m in re.finditer(pattern, text):
            before = text[last_end : m.start()]
            if before:
                new_nodes.append(TextNode(before, TextType.TEXT))
            alt, url = m.groups()
            new_nodes.append(TextNode(alt, TextType.IMAGE, url))
            last_end = m.end()
        if last_end < len(text):
            new_nodes.append(TextNode(text[last_end:], TextType.TEXT))
        elif last_end == 0:
            new_nodes.append(node)
    return new_nodes


def split_nodes_link(old_nodes: list[TextNode]) -> list[TextNode]:
    """Split TEXT nodes by markdown links [anchor](url); non-TEXT nodes pass through."""
    new_nodes: list[TextNode] = []
    pattern = r"(?<!!)\[([^\[\]]*)\]\(([^\(\)]*)\)"
    for node in old_nodes:
        if node.text_type != TextType.TEXT:
            new_nodes.append(node)
            continue
        text = node.text
        last_end = 0
        for m in re.finditer(pattern, text):
            before = text[last_end : m.start()]
            if before:
                new_nodes.append(TextNode(before, TextType.TEXT))
            anchor, url = m.groups()
            new_nodes.append(TextNode(anchor, TextType.LINK, url))
            last_end = m.end()
        if last_end < len(text):
            new_nodes.append(TextNode(text[last_end:], TextType.TEXT))
        elif last_end == 0:
            new_nodes.append(node)
    return new_nodes


def text_to_textnodes(text: str) -> list[TextNode]:
    """Convert raw markdown text to a list of TextNodes (images, links, bold, italic, code)."""
    nodes = [TextNode(text, TextType.TEXT)]
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "_", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    return nodes


def markdown_to_blocks(markdown: str) -> list[str]:
    """Split raw markdown document into block strings (by double newline). Strips and drops empty blocks."""
    blocks = markdown.split("\n\n")
    return [b.strip() for b in blocks if b.strip()]


def extract_title(markdown: str) -> str:
    """Extract the h1 header (line starting with a single #) from markdown. Raises if not found."""
    for line in markdown.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    raise ValueError("No h1 header found in markdown")


class BlockType(Enum):
    HEADING = "heading"
    CODE = "code"
    QUOTE = "quote"
    UNORDERED_LIST = "unordered_list"
    ORDERED_LIST = "ordered_list"
    PARAGRAPH = "paragraph"


def block_to_block_type(block: str) -> BlockType:
    """Return the BlockType for a single markdown block (assumes block is already stripped)."""
    if not block:
        return BlockType.PARAGRAPH
    lines = block.split("\n")

    if re.match(r"^#{1,6} ", block):
        return BlockType.HEADING

    if block.startswith("```\n") and block.endswith("```"):
        return BlockType.CODE

    if all(line.startswith(">") for line in lines):
        return BlockType.QUOTE

    if all(line.startswith("- ") for line in lines):
        return BlockType.UNORDERED_LIST

    if lines:
        ordered = all(
            lines[i].startswith(f"{i + 1}. ") for i in range(len(lines))
        )
        if ordered:
            return BlockType.ORDERED_LIST

    return BlockType.PARAGRAPH


def text_to_children(text: str) -> list[LeafNode]:
    """Convert inline markdown text to a list of LeafNode children (no block-level parsing)."""
    text_nodes = text_to_textnodes(text)
    return [text_node_to_html_node(tn) for tn in text_nodes]


def _block_to_html_node(block: str) -> ParentNode:
    """Convert a single markdown block to an HTML node (ParentNode or wrapper)."""
    block_type = block_to_block_type(block)
    lines = block.split("\n")

    if block_type == BlockType.PARAGRAPH:
        text = block.replace("\n", " ")
        return ParentNode("p", text_to_children(text))

    if block_type == BlockType.HEADING:
        m = re.match(r"^(#{1,6}) ", block)
        level = len(m.group(1))
        heading_text = block[m.end() :]
        return ParentNode(f"h{level}", text_to_children(heading_text))

    if block_type == BlockType.CODE:
        content = block[4:-3]
        return ParentNode("pre", [LeafNode("code", content)])

    if block_type == BlockType.QUOTE:
        quote_text = " ".join(line.lstrip(">").strip() for line in lines)
        return ParentNode("blockquote", text_to_children(quote_text))

    if block_type == BlockType.UNORDERED_LIST:
        items = [ParentNode("li", text_to_children(line[2:])) for line in lines]
        return ParentNode("ul", items)

    if block_type == BlockType.ORDERED_LIST:
        items = [
            ParentNode("li", text_to_children(line.split(". ", 1)[1]))
            for line in lines
        ]
        return ParentNode("ol", items)

    text = block.replace("\n", " ")
    return ParentNode("p", text_to_children(text))


def markdown_to_html_node(markdown: str) -> ParentNode:
    """Convert a full markdown document to a single parent div of block nodes."""
    blocks = markdown_to_blocks(markdown)
    block_nodes = [_block_to_html_node(block) for block in blocks]
    return ParentNode("div", block_nodes)