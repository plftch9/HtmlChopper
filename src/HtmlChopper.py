import os
import re
import sys
from bs4 import BeautifulSoup, Tag, NavigableString


def update_css_paths(head, css):
    """
    Updates <link> tags in the <head> section to use the CSS files in the given folder.
    """
    # Loop through each <link> tag with rel="stylesheet"
    for link in head.find_all('link', rel="stylesheet"):
        original_href = link.get('href', '')

        # Ensure the CSS file exists in the css_folder
        css_file_path = os.path.join(
            css, os.path.basename(original_href))

        if os.path.exists(css_file_path):
            link['href'] = os.path.relpath(
                css_file_path, os.path.dirname(original_href))
            print(f"Updated CSS link: {original_href} → {link['href']}")


def update_img_paths(soup, css):
    """
    Updates <img> tags to use the correct path for images in the css_folder.
    """
    for img_tag in soup.find_all('img'):
        img_src = img_tag.get('src', '')

        if img_src:
            img_file_path = os.path.join(css, os.path.basename(img_src))
            if os.path.exists(img_file_path):
                img_tag['src'] = os.path.relpath(
                    img_file_path, os.path.dirname(img_src))
                print(f"Updated image source: {img_src} → {img_tag['src']}")


def split_html(input_file, output_dir, css):
    """
    Splits an HTML file by extracting sections with IDs matching "section-*",
    updates CSS paths dynamically based on the CSS folder, then further splits children
    with <h2 class="compendium-hr heading-anchor"> tags, saving all text following
    each <h2> tag until the next <h2> tag with the same class is encountered.
    Also updates <img> tags with the correct path to images.
    """
    # Step 1: Read the HTML file
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' does not exist.")
        sys.exit(1)

    # Step 2: Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Step 3: Extract the <head> section and update CSS paths
    head_content = soup.head or soup.new_tag("head")
    update_css_paths(head_content, css)
    head_html = str(head_content)

    # Step 4: Find all elements with IDs matching "section-*"
    # IDs starting with "section-"
    pattern = re.compile(r'^section-[a-zA-Z0-9-]+$')
    elements_with_section_id = soup.find_all(id=pattern)

    if not elements_with_section_id:
        print("No elements with IDs matching 'section-*' were found.")
        return

    # Step 5: Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Step 6: Iterate over the matched sections
    for section in elements_with_section_id:
        section_id = section['id']
        filename = section_id.replace("section-", "")

        # Step 7: Save the section into a subfolder
        section_folder = os.path.join(output_dir, filename)
        os.makedirs(section_folder, exist_ok=True)

        combined_html = (
            f"<!DOCTYPE html>\n"
            f"<html lang=\"en-us\" class=\"no-js\">\n"
            f"{head_html}\n"
            f"{str(section)}\n"
            f"</html>"
        )
        output_file_path = os.path.join(section_folder, f"{filename}.html")
        with open(output_file_path, 'w', encoding='utf-8') as out_file:
            out_file.write(combined_html)

        print(f"Saved section '{section_id}' as '{output_file_path}'")

        # Step 8: Create an additional subfolder for splitting <h2> children
        subsection_folder = os.path.join(section_folder, "subsections")
        os.makedirs(subsection_folder, exist_ok=True)

        # Step 9: Split <h2 class="compendium-hr heading-anchor"> children into their own files
        h2_tags = section.find_all('h2', class_="compendium-hr heading-anchor")

        for h2_tag in h2_tags:
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

            # Combine <!DOCTYPE html>, <html> attributes, <head>, and the subsection content
            subsection_html = (
                f"<!DOCTYPE html>\n"
                f"<html lang=\"en-us\" class=\"no-js\">\n"
                f"{head_html}\n"
                f"{''.join(content)}\n"
                f"</html>"
            )

            # Save the subsection
            subsection_file_path = os.path.join(
                subsection_folder, f"{subsection_id}.html")
            with open(subsection_file_path, 'w', encoding='utf-8') as out_file:
                out_file.write(subsection_html)

            print(f"Saved subsection '\
                {subsection_id}' in folder: {subsection_folder}")

        # Step 10: Update image paths within the section
        update_img_paths(section, css)

    print("HTML splitting complete!")


if __name__ == "__main__":
    # Command-line argument parsing
    if len(sys.argv) != 4:
        print("Usage: python html_splitter.py <input_html_file> <output_directory> <css_folder>")
        sys.exit(1)

    input_html = sys.argv[1]
    output_directory = sys.argv[2]
    css_folder = sys.argv[3]

    split_html(input_html, output_directory, css_folder)
