"""Module used to seperate the HTML file into multiple files
based on the sections and subsections in the HTML file."""

import os
import sys
import shutil
from bs4 import BeautifulSoup, Tag, NavigableString


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


def copy_css_folder(css_dir, target_dir):
    """
    Copies the CSS folder to the target directory.
    """
    target_css_dir = os.path.join(target_dir, os.path.basename(css_dir))
    if os.path.exists(target_css_dir):
        shutil.rmtree(target_css_dir)
    shutil.copytree(css_dir, target_css_dir)


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

    section_num = 0
    doctype = '<!DOCTYPE html>'
    head = soup.find('head')
    if head:
        # update_css_paths(head, css_dir)
        head_content = str(head.prettify())

    sections = soup.find_all(id=lambda x: x and x.startswith('section-'))
    for section in sections:
        section_num += 1
        section_id = section.get('id')
        section_folder_name = section_id.replace('section-', '')
        section_folder = os.path.join(
            output_dir, f"{section_num:03d}_{section_folder_name}")
        os.makedirs(section_folder, exist_ok=True)

        # Update image paths in the section
        # update_img_paths(section, css_dir, section_folder)

        # Copy the CSS folder to the section folder
        copy_css_folder(css_dir, section_folder)

        section_file = os.path.join(
            section_folder, f"{section_folder_name}.html")
        with open(section_file, 'w', encoding='utf-8') as file:
            if head:
                file.write(f"""{doctype}\n<html>{
                    head_content}<body>{str(section)}</body></html>""")
                print(f"Saved section {section_id} to {section_file}")
            else:
                file.write(f"""{doctype}\n<html
                           ><head></head><body>{str(section)}</body></html>""")
                print(f"Saved section {section_id} to {section_file}")

        # Split <h2> children into their own files
        subsection_num = 0
        h2_tags = section.find_all('h2', class_="compendium-hr heading-anchor")
        for h2_tag in h2_tags:
            subsection_num += 1
            subsection_id = h2_tag.get(
                'id', None) or f"subsection-{hash(h2_tag)}"
            # Gather all content following this <h2> tag until the next <h2>
            content = [str(h2_tag)]  # Start with the <h2> tag itself
            next_node = h2_tag
            while True:
                next_node = next_node.find_next_sibling()
                if next_node is None:
                    break
                if isinstance(next_node, NavigableString):
                    content.append(next_node.strip())
                elif isinstance(next_node, Tag):
                    if next_node.name == "h2":
                        break
                    content.append(str(next_node))

            subsection_folder = os.path.join(section_folder, 'subsections')
            os.makedirs(subsection_folder, exist_ok=True)
            subsection_file = os.path.join(
                subsection_folder, f"{subsection_num:03d}_{subsection_id}.html")

            # Create a BeautifulSoup object for the subsection content
            subsection_soup = BeautifulSoup(''.join(content), 'html.parser')

            # Update image paths in the subsection
            # update_img_paths(subsection_soup, css_dir, subsection_folder)

            # Copy the CSS folder to the section folder
            copy_css_folder(css_dir, subsection_folder)

            with open(subsection_file, 'w', encoding='utf-8') as file:
                file.write(f"""{doctype}\n{
                           head_content}<body>{str(subsection_soup)}</body></html>""")
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
