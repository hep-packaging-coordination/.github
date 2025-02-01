#!/usr/bin/env python3
import json
import os
import requests

def get_open_prs_count(tool):
    """
    Given a tool name (e.g. "collier"), query the GitHub API for open pull requests
    (ignoring draft PRs) in the corresponding conda-forge feedstock repository.
    Assumes the feedstock repository is named "conda-forge/<tool>-feedstock".
    """
    repo = f"conda-forge/{tool}-feedstock"
    api_url = f"https://api.github.com/repos/{repo}/pulls?state=open"
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching PRs for {repo}: {e}")
        return "N/A"
    pulls = response.json()
    # Filter out draft PRs
    non_draft_pulls = [pr for pr in pulls if not pr.get("draft", False)]
    return len(non_draft_pulls)

def generate_tool_row(tool):
    """
    Generate a Markdown table row for a given tool with badges for:
      - Conda Recipe
      - Conda Downloads
      - Conda Version
      - Conda Platforms
      - Open non-draft PRs (queried via GitHub API)
    """
    base_url = f"https://anaconda.org/conda-forge/{tool}"
    recipe_badge = f"[![Conda Recipe](https://img.shields.io/badge/recipe-{tool}-green.svg)]({base_url})"
    downloads_badge = f"[![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/{tool}.svg)]({base_url})"
    version_badge = f"[![Conda Version](https://img.shields.io/conda/vn/conda-forge/{tool}.svg)]({base_url})"
    platforms_badge = f"[![Conda Platforms](https://img.shields.io/conda/pn/conda-forge/{tool}.svg)]({base_url})"
    pr_count = get_open_prs_count(tool)
    return f"| {recipe_badge} | {downloads_badge} | {version_badge} | {platforms_badge} | {pr_count} |"

def process_tools_section(section_title, tools):
    """
    Returns a list of Markdown lines for a section (table) listing a set of tools.
    """
    lines = []
    # Use a header for the section; adjust level as needed.
    lines.append(f"### {section_title}")
    lines.append("")
    lines.append("| Name | Downloads | Version | Platforms | Open PRs |")
    lines.append("| --- | --- | --- | --- | --- |")
    for tool in tools:
        lines.append(generate_tool_row(tool))
    lines.append("")
    return lines

def main():
    # Load the JSON data
    with open("feedstocks.json", "r") as f:
        data = json.load(f)

    lines = []
    lines.append("# HEP Packaging Coordination")
    lines.append("")
    lines.append("A community project working to get as many cross-platform builds of HEP tools on conda-forge as possible.")
    lines.append("")
    lines.append("## Tools distributed on conda-forge")
    lines.append("")

    # The JSON structure may have top-level categories that are either:
    # - A list of tools, or
    # - A dict (for subcategories)
    for category, content in data.items():
        # If content is a list, output the table directly.
        if isinstance(content, list):
            lines.append(f"## {category}")
            lines.append("")
            lines.extend(process_tools_section(category, content))
        # If content is a dict, then iterate over its subcategories.
        elif isinstance(content, dict):
            lines.append(f"## {category}")
            lines.append("")
            for subcategory, tools in content.items():
                lines.extend(process_tools_section(subcategory, tools))
        else:
            print(f"Unexpected data type for category '{category}': {type(content)}")

    # Add instructions for adding new tools.
    lines.append("## Adding new tools")
    lines.append("")
    lines.append("Contributions of new HEP tools are very welcome!")
    lines.append("")
    lines.append("To get a new tool listed:")
    lines.append("1. Package and distribute your tool on conda-forge.")
    lines.append("2. Open up an [Issue](https://github.com/hep-packaging-coordination/.github/issues) with title \"Add `<tool name>` to HEP Packaging Coordination\" with a link to the tool's conda-forge feedstock.")
    lines.append("")

    # Write output to .profile relative to this script.
    script_dir = os.path.dirname(os.path.realpath(__file__))
    output_path = os.path.join(script_dir, "profile", "README.md")
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    print(f".profile updated successfully at {output_path}")

if __name__ == "__main__":
    main()
