import unittest

from htmlnode import HTMLNode, LeafNode, ParentNode


class TestHTMLNode(unittest.TestCase):
    def test_props_to_html(self):
        node = HTMLNode(
            tag="a",
            value="Click me",
            props={"href": "https://www.google.com", "target": "_blank"},
        )
        self.assertEqual(
            node.props_to_html(),
            ' href="https://www.google.com" target="_blank"',
        )

    def test_props_to_html_empty(self):
        node = HTMLNode(tag="p", value="Hello")
        self.assertEqual(node.props_to_html(), "")

        node_none = HTMLNode(tag="p", value="Hello", props=None)
        self.assertEqual(node_none.props_to_html(), "")

        node_empty = HTMLNode(tag="p", value="Hello", props={})
        self.assertEqual(node_empty.props_to_html(), "")

    def test_props_to_html_single(self):
        node = HTMLNode(tag="img", props={"alt": "A picture"})
        self.assertEqual(node.props_to_html(), ' alt="A picture"')

    def test_repr(self):
        node = HTMLNode("p", "Hello", None, {"class": "intro"})
        repr_str = repr(node)
        self.assertIn("p", repr_str)
        self.assertIn("Hello", repr_str)
        self.assertIn("class", repr_str)
        self.assertIn("intro", repr_str)


class TestLeafNode(unittest.TestCase):
    def test_leaf_to_html_p(self):
        node = LeafNode("p", "Hello, world!")
        self.assertEqual(node.to_html(), "<p>Hello, world!</p>")

    def test_leaf_to_html_a(self):
        node = LeafNode("a", "Click me!", {"href": "https://www.google.com"})
        self.assertEqual(
            node.to_html(),
            '<a href="https://www.google.com">Click me!</a>',
        )

    def test_leaf_to_html_raw(self):
        node = LeafNode(None, "Raw text only")
        self.assertEqual(node.to_html(), "Raw text only")

    def test_leaf_to_html_other_tags(self):
        node = LeafNode("h1", "Title")
        self.assertEqual(node.to_html(), "<h1>Title</h1>")

        node = LeafNode("span", "inline", {"class": "highlight"})
        self.assertEqual(
            node.to_html(),
            '<span class="highlight">inline</span>',
        )

    def test_leaf_no_value_raises(self):
        with self.assertRaises(ValueError):
            LeafNode("p", None).to_html()

    def test_leaf_repr(self):
        node = LeafNode("p", "Hello", {"class": "intro"})
        repr_str = repr(node)
        self.assertIn("LeafNode", repr_str)
        self.assertIn("p", repr_str)
        self.assertIn("Hello", repr_str)
        self.assertNotIn("children", repr_str)


class TestParentNode(unittest.TestCase):
    def test_to_html_with_children(self):
        child_node = LeafNode("span", "child")
        parent_node = ParentNode("div", [child_node])
        self.assertEqual(parent_node.to_html(), "<div><span>child</span></div>")

    def test_to_html_with_grandchildren(self):
        grandchild_node = LeafNode("b", "grandchild")
        child_node = ParentNode("span", [grandchild_node])
        parent_node = ParentNode("div", [child_node])
        self.assertEqual(
            parent_node.to_html(),
            "<div><span><b>grandchild</b></span></div>",
        )

    def test_to_html_example_from_assignment(self):
        node = ParentNode(
            "p",
            [
                LeafNode("b", "Bold text"),
                LeafNode(None, "Normal text"),
                LeafNode("i", "italic text"),
                LeafNode(None, "Normal text"),
            ],
        )
        self.assertEqual(
            node.to_html(),
            "<p><b>Bold text</b>Normal text<i>italic text</i>Normal text</p>",
        )

    def test_to_html_multiple_children(self):
        node = ParentNode(
            "div",
            [
                LeafNode("span", "one"),
                LeafNode("span", "two"),
                LeafNode("span", "three"),
            ],
        )
        self.assertEqual(
            node.to_html(),
            "<div><span>one</span><span>two</span><span>three</span></div>",
        )

    def test_to_html_no_children(self):
        node = ParentNode("div", [])
        self.assertEqual(node.to_html(), "<div></div>")

    def test_to_html_with_props(self):
        child_node = LeafNode("span", "child")
        parent_node = ParentNode("div", [child_node], {"class": "container"})
        self.assertEqual(
            parent_node.to_html(),
            '<div class="container"><span>child</span></div>',
        )

    def test_to_html_nested_parent_nodes(self):
        inner = ParentNode("span", [LeafNode(None, "deep")])
        middle = ParentNode("p", [inner])
        outer = ParentNode("div", [middle])
        self.assertEqual(
            outer.to_html(),
            "<div><p><span>deep</span></p></div>",
        )

    def test_to_html_no_tag_raises(self):
        with self.assertRaises(ValueError) as ctx:
            ParentNode(None, [LeafNode("span", "x")]).to_html()
        self.assertIn("tag", str(ctx.exception).lower())

    def test_to_html_no_children_raises(self):
        with self.assertRaises(ValueError) as ctx:
            ParentNode("div", None).to_html()
        self.assertIn("children", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
