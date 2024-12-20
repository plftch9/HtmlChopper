"""Module used to seperate the HTML file into multiple files 
based on the sections and subsections in the HTML file."""

import os
import sys
from bs4 import BeautifulSoup, Tag


def print_python_version():
    """
    Prints the Python version being used.
    """
    print(sys.version)


def update_css_paths(head, css):
    """
    Updates <link> tags in the <head> section to use the CSS files in the given folder.
    """
    for link in head.find_all('link', rel="stylesheet"):
        original_href = link.get('href', '')
        css_file_path = os.path.join(css, os.path.basename(original_href))
        if os.path.exists(css_file_path):
            link['href'] = os.path.relpath(
                css_file_path, os.path.dirname(original_href)).replace('\\', '/')


def update_img_paths(soup, css_dir, output_dir):
    """
    Updates <img> tags to use the correct path for images in the css_folder.
    """
    for img_tag in soup.find_all('img'):
        img_src = img_tag.get('src', '')
        if img_src:
            img_file_name = os.path.basename(img_src)
            img_file_path = os.path.join(css_dir, img_file_name)
            if os.path.exists(img_file_path):
                new_src = os.path.relpath(
                    img_file_path, output_dir).replace(os.path.sep, '/')
                img_tag['src'] = new_src
            else:
                print(f"Image file does not exist: {img_file_path}")


def split_html(input_file, output_dir, css_dir):
    """
    Splits an HTML file by extracting sections with IDs matching "section-*",
    updates CSS paths dynamically based on the CSS folder, then further splits children
    with <h2 class="compendium-hr heading-anchor"> tags, saving all text following
    each <h2> tag until the next <h2> tag with the same class is encountered.
    Also updates <img> tags with the correct path to images.
    """
    with open(input_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    head = soup.find('head')
    if head:
        update_css_paths(head, css_dir)

    sections = soup.find_all(id=lambda x: x and x.startswith('section-'))
    for section in sections:
        section_id = section.get('id')
        section_folder_name = section_id.replace('section-', '')
        section_folder = os.path.join(output_dir, section_folder_name)
        os.makedirs(section_folder, exist_ok=True)

        # Update image paths in the section
        update_img_paths(section, css_dir, section_folder)

        section_file = os.path.join(
            section_folder, f"{section_folder_name}.html")
        with open(section_file, 'w', encoding='utf-8') as file:
            file.write(str(section))
        print(f"Saved section {section_id} to {section_file}")

        # Split <h2> children into their own files
        h2_tags = section.find_all('h2', class_="compendium-hr heading-anchor")
        for h2_tag in h2_tags:
            subsection_id = h2_tag.get('id', f"subsection-{hash(h2_tag)}")
            content = [str(h2_tag)]
            next_node = h2_tag.find_next_sibling()
            while next_node and not (isinstance(next_node, Tag) and next_node.name == 'h2' and 'compendium-hr heading-anchor' in next_node.get('class', [])):
                content.append(str(next_node))
                next_node = next_node.find_next_sibling()

            subsection_folder = os.path.join(section_folder, 'subsections')
            os.makedirs(subsection_folder, exist_ok=True)
            subsection_file = os.path.join(
                subsection_folder, f"{subsection_id}.html")

            # Create a BeautifulSoup object for the subsection content
            subsection_soup = BeautifulSoup('\n'.join(content), 'html.parser')

            # Update image paths in the subsection
            update_img_paths(subsection_soup, css_dir, subsection_folder)

            with open(subsection_file, 'w', encoding='utf-8') as file:
                file.write(str(subsection_soup))
            print(f"Saved subsection {subsection_id} to {subsection_file}")

    print("HTML splitting complete!")


if __name__ == "__main__":
    print_python_version()
    if len(sys.argv) != 4:
        print("Usage: python html_splitter.py <input_html_file> <output_directory> <css_folder>")
        sys.exit(1)

    input_html = sys.argv[1]
    output_directory = sys.argv[2]
    css_folder = sys.argv[3]

    split_html(input_html, output_directory, css_folder)
