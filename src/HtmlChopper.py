import os
import re
import sys
import subprocess


# Function to install missing packages
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


# Attempt to import dependencies and install if missing
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing missing dependencies...")
    install_package("beautifulsoup4")
    from bs4 import BeautifulSoup


def split_html(input_file, output_dir):
    """
    Splits an HTML file by extracting sections with IDs matching "section-*",
    then further splits children with <h2 class="compendium-hr heading-anchor"> tags,
    saving all text following each <h2> tag until the next <h2> tag.
    """
    # Read the HTML file
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' does not exist.")
        sys.exit(1)

    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract the <head> section
    head_content = soup.head
    head_html = str(head_content) if head_content else "<head></head>"

    # Find all elements with IDs matching "section-*"
    # IDs starting with "section-"
    pattern = re.compile(r'^section-[a-zA-Z0-9-]+$')
    elements_with_section_id = soup.find_all(id=pattern)

    if not elements_with_section_id:
        print("No elements with IDs matching 'section-*' were found.")
        return

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Iterate over the matched sections
    for section in elements_with_section_id:
        section_id = section['id']
        # Extract the filename by removing "section-" from the ID
        filename = section_id.replace("section-", "")

        # Save the section into a subfolder
        section_folder = os.path.join(output_dir, filename)
        os.makedirs(section_folder, exist_ok=True)

        # Combine <!DOCTYPE html>, <html> attributes, <head>, and the section content
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

        # Create an additional subfolder for splitting <h2> children
        subsection_folder = os.path.join(section_folder, "subsections")
        os.makedirs(subsection_folder, exist_ok=True)

        # Split <h2 class="compendium-hr heading-anchor"> children into their own files
        h2_tags = section.find_all('h2', class_="compendium-hr heading-anchor")
        for h2_tag in h2_tags:
            subsection_id = h2_tag.get('id', None)
            if not subsection_id:
                print("Warning: <h2> tag without an ID encountered, skipping...")
                continue

            # Gather all content between this <h2> and the next <h2>
            content = [str(h2_tag)]  # Include the <h2> tag itself
            next_tag = h2_tag.find_next_sibling()
            while next_tag and not (next_tag.name == "h2" and "compendium-hr heading-anchor" in next_tag.get("class", [])):
                content.append(str(next_tag))
                next_tag = next_tag.find_next_sibling()

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

            print(f"Saved subsection ' \
                  {subsection_id}' in folder: {subsection_folder}")

    print("HTML splitting complete!")


if __name__ == "__main__":
    # Command-line argument parsing
    if len(sys.argv) != 3:
        print("Usage: python html_splitter.py <input_html_file> <output_directory>")
        sys.exit(1)

    input_html = sys.argv[1]
    output_directory = sys.argv[2]

    split_html(input_html, output_directory)
