import os
import shutil
import sys

from textnode import TextNode, TextType, markdown_to_html_node, extract_title


def generate_page(
    from_path: str, template_path: str, dest_path: str, basepath: str = "/"
) -> None:
    """Generate an HTML page from markdown using a template. Writes to dest_path."""
    print(f"Generating page from {from_path} to {dest_path} using {template_path}")
    with open(from_path, encoding="utf-8") as f:
        markdown = f.read()
    with open(template_path, encoding="utf-8") as f:
        template = f.read()
    html_content = markdown_to_html_node(markdown).to_html()
    title = extract_title(markdown)
    html = template.replace("{{ Title }}", title).replace("{{ Content }}", html_content)
    html = html.replace('href="/', f'href="{basepath}').replace('src="/', f'src="{basepath}')
    dest_dir = os.path.dirname(dest_path)
    if dest_dir:
        os.makedirs(dest_dir, exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(html)


def copy_dir_contents(src: str, dest: str) -> None:
    """Recursively copy all contents of src into dest. Cleans dest first."""
    if not os.path.exists(src):
        return
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.mkdir(dest)
    for name in os.listdir(src):
        src_path = os.path.join(src, name)
        dest_path = os.path.join(dest, name)
        if os.path.isfile(src_path):
            shutil.copy(src_path, dest_path)
            print(f"Copied {src_path} -> {dest_path}")
        else:
            os.mkdir(dest_path)
            copy_dir_contents(src_path, dest_path)


def generate_pages_recursive(
    dir_path_content: str,
    template_path: str,
    dest_dir_path: str,
    basepath: str = "/",
) -> None:
    """Crawl content dir for .md files and generate HTML into dest dir using the template (same structure)."""
    for dirpath, _dirnames, filenames in os.walk(dir_path_content):
        for name in filenames:
            if not name.endswith(".md"):
                continue
            from_path = os.path.join(dirpath, name)
            rel = os.path.relpath(from_path, dir_path_content)
            dest_rel = os.path.splitext(rel)[0] + ".html"
            dest_path = os.path.join(dest_dir_path, dest_rel)
            generate_page(from_path, template_path, dest_path, basepath)


def main():
    basepath = sys.argv[1] if len(sys.argv) > 1 else "/"
    copy_dir_contents("static", "docs")
    generate_pages_recursive("content", "template.html", "docs", basepath)


if __name__ == "__main__":
    main()