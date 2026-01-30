import unittest
from enum import Enum

from htmlnode import LeafNode, ParentNode

from textnode import (
    TextNode,
    TextType,
    BlockType,
    text_node_to_html_node,
    split_nodes_delimiter,
    extract_markdown_images,
    extract_markdown_links,
    split_nodes_image,
    split_nodes_link,
    text_to_textnodes,
    markdown_to_blocks,
    block_to_block_type,
    markdown_to_html_node,
    extract_title,
)


class TestTextNode(unittest.TestCase):
    def test_eq(self):
        node = TextNode("This is a text node", TextType.BOLD)
        node2 = TextNode("This is a text node", TextType.BOLD)
        self.assertEqual(node, node2)

    def test_eq_with_url_none(self):
        node = TextNode("Plain text", TextType.TEXT)
        node2 = TextNode("Plain text", TextType.TEXT, None)
        self.assertEqual(node, node2)

    def test_eq_with_url(self):
        node = TextNode("Click here", TextType.LINK, "https://example.com")
        node2 = TextNode("Click here", TextType.LINK, "https://example.com")
        self.assertEqual(node, node2)

    def test_not_equal_different_text(self):
        node = TextNode("First", TextType.TEXT)
        node2 = TextNode("Second", TextType.TEXT)
        self.assertNotEqual(node, node2)

    def test_not_equal_different_text_type(self):
        node = TextNode("Same text", TextType.BOLD)
        node2 = TextNode("Same text", TextType.ITALIC)
        self.assertNotEqual(node, node2)

    def test_not_equal_different_url(self):
        node = TextNode("Link", TextType.LINK, "https://a.com")
        node2 = TextNode("Link", TextType.LINK, "https://b.com")
        self.assertNotEqual(node, node2)

    def test_not_equal_url_none_vs_set(self):
        node = TextNode("Link", TextType.LINK)
        node2 = TextNode("Link", TextType.LINK, "https://example.com")
        self.assertNotEqual(node, node2)


class TestTextNodeToHTMLNode(unittest.TestCase):
    def test_text(self):
        node = TextNode("This is a text node", TextType.TEXT)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, None)
        self.assertEqual(html_node.value, "This is a text node")

    def test_bold(self):
        node = TextNode("Bold text", TextType.BOLD)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "b")
        self.assertEqual(html_node.value, "Bold text")
        self.assertEqual(html_node.to_html(), "<b>Bold text</b>")

    def test_italic(self):
        node = TextNode("Italic text", TextType.ITALIC)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "i")
        self.assertEqual(html_node.value, "Italic text")
        self.assertEqual(html_node.to_html(), "<i>Italic text</i>")

    def test_code(self):
        node = TextNode("code snippet", TextType.CODE)
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "code")
        self.assertEqual(html_node.value, "code snippet")
        self.assertEqual(html_node.to_html(), "<code>code snippet</code>")

    def test_link(self):
        node = TextNode("Click here", TextType.LINK, "https://example.com")
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "a")
        self.assertEqual(html_node.value, "Click here")
        self.assertEqual(html_node.props, {"href": "https://example.com"})
        self.assertEqual(
            html_node.to_html(),
            '<a href="https://example.com">Click here</a>',
        )

    def test_image(self):
        node = TextNode("Alt text", TextType.IMAGE, "https://example.com/img.png")
        html_node = text_node_to_html_node(node)
        self.assertEqual(html_node.tag, "img")
        self.assertEqual(html_node.value, "")
        self.assertEqual(
            html_node.props,
            {"src": "https://example.com/img.png", "alt": "Alt text"},
        )
        self.assertEqual(
            html_node.to_html(),
            '<img src="https://example.com/img.png" alt="Alt text">',
        )

    def test_unknown_type_raises(self):
        class UnknownType(Enum):
            UNKNOWN = "unknown"

        node = TextNode("x", UnknownType.UNKNOWN)
        with self.assertRaises(ValueError) as ctx:
            text_node_to_html_node(node)
        self.assertIn("Unknown text type", str(ctx.exception))


class TestSplitNodesDelimiter(unittest.TestCase):
    def test_code_delimiter(self):
        node = TextNode(
            "This is text with a `code block` word", TextType.TEXT
        )
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(
            new_nodes,
            [
                TextNode("This is text with a ", TextType.TEXT),
                TextNode("code block", TextType.CODE),
                TextNode(" word", TextType.TEXT),
            ],
        )

    def test_bold_delimiter(self):
        node = TextNode("This is **bold** and normal", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "**", TextType.BOLD)
        self.assertEqual(
            new_nodes,
            [
                TextNode("This is ", TextType.TEXT),
                TextNode("bold", TextType.BOLD),
                TextNode(" and normal", TextType.TEXT),
            ],
        )

    def test_italic_delimiter(self):
        node = TextNode("Mix of _italic_ here", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "_", TextType.ITALIC)
        self.assertEqual(
            new_nodes,
            [
                TextNode("Mix of ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
                TextNode(" here", TextType.TEXT),
            ],
        )

    def test_no_delimiter_passthrough(self):
        node = TextNode("No delimiter here", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(new_nodes, [node])

    def test_non_text_node_passthrough(self):
        node = TextNode("Already bold", TextType.BOLD)
        new_nodes = split_nodes_delimiter([node], "**", TextType.BOLD)
        self.assertEqual(new_nodes, [node])

    def test_multiple_delimiters(self):
        node = TextNode("a `one` b `two` c", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertEqual(
            new_nodes,
            [
                TextNode("a ", TextType.TEXT),
                TextNode("one", TextType.CODE),
                TextNode(" b ", TextType.TEXT),
                TextNode("two", TextType.CODE),
                TextNode(" c", TextType.TEXT),
            ],
        )

    def test_unclosed_delimiter_raises(self):
        node = TextNode("Unclosed `code here", TextType.TEXT)
        with self.assertRaises(ValueError) as ctx:
            split_nodes_delimiter([node], "`", TextType.CODE)
        self.assertIn("unclosed delimiter", str(ctx.exception).lower())
        self.assertIn("`", str(ctx.exception))

    def test_multiple_nodes_mixed(self):
        text_node = TextNode("Some `code` inside", TextType.TEXT)
        bold_node = TextNode("Already bold", TextType.BOLD)
        new_nodes = split_nodes_delimiter(
            [text_node, bold_node], "`", TextType.CODE
        )
        self.assertEqual(
            new_nodes,
            [
                TextNode("Some ", TextType.TEXT),
                TextNode("code", TextType.CODE),
                TextNode(" inside", TextType.TEXT),
                TextNode("Already bold", TextType.BOLD),
            ],
        )

    def test_delimiter_at_edges(self):
        node = TextNode("**bold**", TextType.TEXT)
        new_nodes = split_nodes_delimiter([node], "**", TextType.BOLD)
        self.assertEqual(
            new_nodes,
            [
                TextNode("", TextType.TEXT),
                TextNode("bold", TextType.BOLD),
                TextNode("", TextType.TEXT),
            ],
        )


class TestExtractMarkdown(unittest.TestCase):
    def test_extract_markdown_images(self):
        matches = extract_markdown_images(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png)"
        )
        self.assertListEqual(
            [("image", "https://i.imgur.com/zjjcJKZ.png")], matches
        )

    def test_extract_markdown_images_multiple(self):
        text = "This is text with a ![rick roll](https://i.imgur.com/aKaOqIh.gif) and ![obi wan](https://i.imgur.com/fJRm4Vk.jpeg)"
        matches = extract_markdown_images(text)
        self.assertListEqual(
            [
                ("rick roll", "https://i.imgur.com/aKaOqIh.gif"),
                ("obi wan", "https://i.imgur.com/fJRm4Vk.jpeg"),
            ],
            matches,
        )

    def test_extract_markdown_images_none(self):
        self.assertListEqual([], extract_markdown_images("No images here"))

    def test_extract_markdown_links(self):
        matches = extract_markdown_links(
            "This is text with a link [to boot dev](https://www.boot.dev) and [to youtube](https://www.youtube.com/@bootdotdev)"
        )
        self.assertListEqual(
            [
                ("to boot dev", "https://www.boot.dev"),
                ("to youtube", "https://www.youtube.com/@bootdotdev"),
            ],
            matches,
        )

    def test_extract_markdown_links_single(self):
        matches = extract_markdown_links(
            "Check out [this link](https://example.com)"
        )
        self.assertListEqual(
            [("this link", "https://example.com")], matches
        )

    def test_extract_markdown_links_none(self):
        self.assertListEqual([], extract_markdown_links("No links here"))

    def test_extract_markdown_links_excludes_images(self):
        text = "Here is ![an image](https://img.com/x.png) and [a link](https://link.com)"
        images = extract_markdown_images(text)
        links = extract_markdown_links(text)
        self.assertListEqual(
            [("an image", "https://img.com/x.png")], images
        )
        self.assertListEqual(
            [("a link", "https://link.com")], links
        )


class TestSplitNodesImage(unittest.TestCase):
    def test_split_images(self):
        node = TextNode(
            "This is text with an ![image](https://i.imgur.com/zjjcJKZ.png) and another ![second image](https://i.imgur.com/3elNhQu.png)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            [
                TextNode("This is text with an ", TextType.TEXT),
                TextNode(
                    "image", TextType.IMAGE, "https://i.imgur.com/zjjcJKZ.png"
                ),
                TextNode(" and another ", TextType.TEXT),
                TextNode(
                    "second image",
                    TextType.IMAGE,
                    "https://i.imgur.com/3elNhQu.png",
                ),
            ],
            new_nodes,
        )

    def test_split_images_no_images(self):
        node = TextNode("Just plain text", TextType.TEXT)
        new_nodes = split_nodes_image([node])
        self.assertListEqual(new_nodes, [node])

    def test_split_images_single(self):
        node = TextNode(
            "Before ![alt](https://example.com/img.png) after",
            TextType.TEXT,
        )
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            new_nodes,
            [
                TextNode("Before ", TextType.TEXT),
                TextNode("alt", TextType.IMAGE, "https://example.com/img.png"),
                TextNode(" after", TextType.TEXT),
            ],
        )

    def test_split_images_non_text_passthrough(self):
        node = TextNode("Already an image", TextType.IMAGE, "https://x.com/a.png")
        new_nodes = split_nodes_image([node])
        self.assertListEqual(new_nodes, [node])

    def test_split_images_multiple_nodes(self):
        text_node = TextNode(
            "Text with ![one](https://a.com) here",
            TextType.TEXT,
        )
        bold_node = TextNode("Bold", TextType.BOLD)
        new_nodes = split_nodes_image([text_node, bold_node])
        self.assertListEqual(
            new_nodes,
            [
                TextNode("Text with ", TextType.TEXT),
                TextNode("one", TextType.IMAGE, "https://a.com"),
                TextNode(" here", TextType.TEXT),
                TextNode("Bold", TextType.BOLD),
            ],
        )

    def test_split_images_at_start(self):
        node = TextNode("![first](https://a.png) and more", TextType.TEXT)
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            new_nodes,
            [
                TextNode("first", TextType.IMAGE, "https://a.png"),
                TextNode(" and more", TextType.TEXT),
            ],
        )

    def test_split_images_at_end(self):
        node = TextNode("Start and ![last](https://b.png)", TextType.TEXT)
        new_nodes = split_nodes_image([node])
        self.assertListEqual(
            new_nodes,
            [
                TextNode("Start and ", TextType.TEXT),
                TextNode("last", TextType.IMAGE, "https://b.png"),
            ],
        )


class TestSplitNodesLink(unittest.TestCase):
    def test_split_links(self):
        node = TextNode(
            "This is text with a link [to boot dev](https://www.boot.dev) and [to youtube](https://www.youtube.com/@bootdotdev)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            new_nodes,
            [
                TextNode("This is text with a link ", TextType.TEXT),
                TextNode("to boot dev", TextType.LINK, "https://www.boot.dev"),
                TextNode(" and ", TextType.TEXT),
                TextNode(
                    "to youtube",
                    TextType.LINK,
                    "https://www.youtube.com/@bootdotdev",
                ),
            ],
        )

    def test_split_links_no_links(self):
        node = TextNode("Just plain text", TextType.TEXT)
        new_nodes = split_nodes_link([node])
        self.assertListEqual(new_nodes, [node])

    def test_split_links_single(self):
        node = TextNode(
            "Check out [this link](https://example.com) for more",
            TextType.TEXT,
        )
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            new_nodes,
            [
                TextNode("Check out ", TextType.TEXT),
                TextNode("this link", TextType.LINK, "https://example.com"),
                TextNode(" for more", TextType.TEXT),
            ],
        )

    def test_split_links_non_text_passthrough(self):
        node = TextNode("Already a link", TextType.LINK, "https://x.com")
        new_nodes = split_nodes_link([node])
        self.assertListEqual(new_nodes, [node])

    def test_split_links_excludes_images(self):
        node = TextNode(
            "Here is ![image](https://img.com/x.png) and [link](https://link.com)",
            TextType.TEXT,
        )
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            new_nodes,
            [
                TextNode("Here is ![image](https://img.com/x.png) and ", TextType.TEXT),
                TextNode("link", TextType.LINK, "https://link.com"),
            ],
        )

    def test_split_links_multiple_nodes(self):
        text_node = TextNode(
            "See [one](https://a.com) and [two](https://b.com)",
            TextType.TEXT,
        )
        code_node = TextNode("code", TextType.CODE)
        new_nodes = split_nodes_link([text_node, code_node])
        self.assertListEqual(
            new_nodes,
            [
                TextNode("See ", TextType.TEXT),
                TextNode("one", TextType.LINK, "https://a.com"),
                TextNode(" and ", TextType.TEXT),
                TextNode("two", TextType.LINK, "https://b.com"),
                TextNode("code", TextType.CODE),
            ],
        )

    def test_split_links_at_start(self):
        node = TextNode("[first](https://a.com) then text", TextType.TEXT)
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            new_nodes,
            [
                TextNode("first", TextType.LINK, "https://a.com"),
                TextNode(" then text", TextType.TEXT),
            ],
        )

    def test_split_links_at_end(self):
        node = TextNode("Start with [last](https://b.com)", TextType.TEXT)
        new_nodes = split_nodes_link([node])
        self.assertListEqual(
            new_nodes,
            [
                TextNode("Start with ", TextType.TEXT),
                TextNode("last", TextType.LINK, "https://b.com"),
            ],
        )


class TestTextToTextnodes(unittest.TestCase):
    def test_text_to_textnodes_full(self):
        text = "This is **text** with an _italic_ word and a `code block` and an ![obi wan image](https://i.imgur.com/fJRm4Vk.jpeg) and a [link](https://boot.dev)"
        nodes = text_to_textnodes(text)
        self.assertListEqual(
            nodes,
            [
                TextNode("This is ", TextType.TEXT),
                TextNode("text", TextType.BOLD),
                TextNode(" with an ", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
                TextNode(" word and a ", TextType.TEXT),
                TextNode("code block", TextType.CODE),
                TextNode(" and an ", TextType.TEXT),
                TextNode(
                    "obi wan image",
                    TextType.IMAGE,
                    "https://i.imgur.com/fJRm4Vk.jpeg",
                ),
                TextNode(" and a ", TextType.TEXT),
                TextNode("link", TextType.LINK, "https://boot.dev"),
            ],
        )

    def test_text_to_textnodes_plain(self):
        nodes = text_to_textnodes("Just plain text")
        self.assertListEqual(nodes, [TextNode("Just plain text", TextType.TEXT)])

    def test_text_to_textnodes_bold_only(self):
        nodes = text_to_textnodes("Some **bold** here")
        self.assertListEqual(
            nodes,
            [
                TextNode("Some ", TextType.TEXT),
                TextNode("bold", TextType.BOLD),
                TextNode(" here", TextType.TEXT),
            ],
        )

    def test_text_to_textnodes_mixed_inline(self):
        nodes = text_to_textnodes("_italic_ and `code`")
        self.assertListEqual(
            nodes,
            [
                TextNode("", TextType.TEXT),
                TextNode("italic", TextType.ITALIC),
                TextNode(" and ", TextType.TEXT),
                TextNode("code", TextType.CODE),
                TextNode("", TextType.TEXT),
            ],
        )

    def test_text_to_textnodes_image_and_link(self):
        text = "See ![img](https://img.com/x.png) and [link](https://link.com)"
        nodes = text_to_textnodes(text)
        self.assertListEqual(
            nodes,
            [
                TextNode("See ", TextType.TEXT),
                TextNode("img", TextType.IMAGE, "https://img.com/x.png"),
                TextNode(" and ", TextType.TEXT),
                TextNode("link", TextType.LINK, "https://link.com"),
            ],
        )


class TestMarkdownToBlocks(unittest.TestCase):
    def test_markdown_to_blocks(self):
        md = """
This is **bolded** paragraph

This is another paragraph with _italic_ text and `code` here
This is the same paragraph on a new line

- This is a list
- with items
"""
        blocks = markdown_to_blocks(md)
        self.assertEqual(
            blocks,
            [
                "This is **bolded** paragraph",
                "This is another paragraph with _italic_ text and `code` here\nThis is the same paragraph on a new line",
                "- This is a list\n- with items",
            ],
        )

    def test_markdown_to_blocks_empty(self):
        self.assertEqual(markdown_to_blocks(""), [])
        self.assertEqual(markdown_to_blocks("   \n\n   "), [])

    def test_markdown_to_blocks_single(self):
        blocks = markdown_to_blocks("Single block")
        self.assertEqual(blocks, ["Single block"])

    def test_markdown_to_blocks_excessive_newlines(self):
        md = "First\n\n\n\nSecond"
        blocks = markdown_to_blocks(md)
        self.assertEqual(blocks, ["First", "Second"])

    def test_markdown_to_blocks_strips_whitespace(self):
        md = "  First block  \n\n  Second block  "
        blocks = markdown_to_blocks(md)
        self.assertEqual(blocks, ["First block", "Second block"])


class TestBlockToBlockType(unittest.TestCase):
    def test_heading(self):
        self.assertEqual(block_to_block_type("# Heading"), BlockType.HEADING)
        self.assertEqual(block_to_block_type("## H2"), BlockType.HEADING)
        self.assertEqual(block_to_block_type("###### H6"), BlockType.HEADING)

    def test_heading_not_without_space(self):
        self.assertEqual(block_to_block_type("#no space"), BlockType.PARAGRAPH)
        self.assertEqual(block_to_block_type("####### too many"), BlockType.PARAGRAPH)

    def test_code(self):
        block = "```\ncode here\nmore code\n```"
        self.assertEqual(block_to_block_type(block), BlockType.CODE)

    def test_code_minimal(self):
        block = "```\n```"
        self.assertEqual(block_to_block_type(block), BlockType.CODE)

    def test_code_not_without_newline_after_open(self):
        self.assertEqual(block_to_block_type("```code```"), BlockType.PARAGRAPH)

    def test_quote(self):
        block = "> First line\n> Second line"
        self.assertEqual(block_to_block_type(block), BlockType.QUOTE)

    def test_quote_with_space_after_gt(self):
        block = "> quote\n> more"
        self.assertEqual(block_to_block_type(block), BlockType.QUOTE)

    def test_quote_single_line(self):
        self.assertEqual(block_to_block_type("> One line"), BlockType.QUOTE)

    def test_quote_not_partial(self):
        block = "> line one\nnot quoted"
        self.assertEqual(block_to_block_type(block), BlockType.PARAGRAPH)

    def test_unordered_list(self):
        block = "- First\n- Second\n- Third"
        self.assertEqual(block_to_block_type(block), BlockType.UNORDERED_LIST)

    def test_unordered_list_single(self):
        self.assertEqual(block_to_block_type("- One"), BlockType.UNORDERED_LIST)

    def test_unordered_list_not_without_space(self):
        self.assertEqual(block_to_block_type("-no space"), BlockType.PARAGRAPH)

    def test_ordered_list(self):
        block = "1. First\n2. Second\n3. Third"
        self.assertEqual(block_to_block_type(block), BlockType.ORDERED_LIST)

    def test_ordered_list_single(self):
        self.assertEqual(block_to_block_type("1. One"), BlockType.ORDERED_LIST)

    def test_ordered_list_must_start_at_one(self):
        block = "2. First\n3. Second"
        self.assertEqual(block_to_block_type(block), BlockType.PARAGRAPH)

    def test_ordered_list_must_increment(self):
        block = "1. First\n3. Second"
        self.assertEqual(block_to_block_type(block), BlockType.PARAGRAPH)

    def test_paragraph(self):
        self.assertEqual(
            block_to_block_type("Just a normal paragraph."),
            BlockType.PARAGRAPH,
        )

    def test_paragraph_empty(self):
        self.assertEqual(block_to_block_type(""), BlockType.PARAGRAPH)


class TestExtractTitle(unittest.TestCase):
    def test_extract_title_simple(self):
        self.assertEqual(extract_title("# Hello"), "Hello")

    def test_extract_title_strips_whitespace(self):
        self.assertEqual(extract_title("#  My Title  "), "My Title")

    def test_extract_title_first_h1_only(self):
        md = "# First\n\n## Second\n\n# Another"
        self.assertEqual(extract_title(md), "First")

    def test_extract_title_no_h2(self):
        md = "## Not an h1"
        with self.assertRaises(ValueError) as ctx:
            extract_title(md)
        self.assertIn("h1", str(ctx.exception).lower())

    def test_extract_title_empty_raises(self):
        with self.assertRaises(ValueError):
            extract_title("")

    def test_extract_title_no_header_raises(self):
        with self.assertRaises(ValueError):
            extract_title("Just a paragraph\n\nAnother paragraph")


class TestMarkdownToHTMLNode(unittest.TestCase):
    def test_paragraphs(self):
        md = """
This is **bolded** paragraph
text in a p
tag here

This is another paragraph with _italic_ text and `code` here

"""
        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><p>This is <b>bolded</b> paragraph text in a p tag here</p><p>This is another paragraph with <i>italic</i> text and <code>code</code> here</p></div>",
        )

    def test_codeblock(self):
        md = """
```
This is text that _should_ remain
the **same** even with inline stuff
```
"""
        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><pre><code>This is text that _should_ remain\nthe **same** even with inline stuff\n</code></pre></div>",
        )

    def test_headings(self):
        md = "# Heading one\n\n## Heading **bold**"
        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><h1>Heading one</h1><h2>Heading <b>bold</b></h2></div>",
        )

    def test_unordered_list(self):
        md = "- First item\n- Second **item**"
        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><ul><li>First item</li><li>Second <b>item</b></li></ul></div>",
        )

    def test_ordered_list(self):
        md = "1. First\n2. Second"
        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><ol><li>First</li><li>Second</li></ol></div>",
        )

    def test_quote(self):
        md = "> Quote line one\n> Quote **two**"
        node = markdown_to_html_node(md)
        html = node.to_html()
        self.assertEqual(
            html,
            "<div><blockquote>Quote line one Quote <b>two</b></blockquote></div>",
        )


if __name__ == "__main__":
    unittest.main()