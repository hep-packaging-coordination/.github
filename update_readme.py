#!/usr/bin/env python3
import json
import os
import requests
from datetime import datetime, timezone

# Global variable to hold the feedstock outputs mapping.
FEEDSTOCK_OUTPUTS = {}

def load_feedstock_outputs():
    """
    Load the feedstock outputs mapping from the remote JSON file.
    Returns a dict mapping feedstock names to a list of outputs.
    """
    url = "https://raw.githubusercontent.com/conda-forge/feedstock-outputs/single-file/feedstock-outputs.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error loading feedstock outputs: {e}")
        return {}

def get_open_prs_count(feedstock):
    """
    Given a feedstock name (e.g. "collier" or the first output from a feedstock),
    query the GitHub API for open pull requests (ignoring draft PRs) in the corresponding
    conda-forge feedstock repository. Assumes the repository is named "conda-forge/<feedstock>-feedstock".
    """
    repo = f"conda-forge/{feedstock}-feedstock"
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
    # Filter out draft PRs.
    non_draft_pulls = [pr for pr in pulls if not pr.get("draft", False)]
    return len(non_draft_pulls)

def generate_tool_row(tool):
    """
    Generate a Markdown table row for a given tool with badges for:
      - Conda Recipe (linking to the feedstock repository on GitHub for the first output)
      - Conda Downloads (linking to the Anaconda page for the first output)
      - Conda Version (linking to the Anaconda page for the first output)
      - Conda Platforms (linking to the Anaconda page for the first output)
      - Open non-draft PRs (linking to the pull requests page on GitHub for the first output)
      - A comma-separated list of all outputs for that feedstock.
    """
    # Look up the outputs for this tool from the remote mapping.
    outputs = FEEDSTOCK_OUTPUTS.get(tool, [tool])
    first_output = outputs[0]
    all_outputs_text = ", ".join(outputs)

    # Use the first output for building URLs.
    feedstock_url = f"https://github.com/conda-forge/{first_output}-feedstock"
    anaconda_url = f"https://anaconda.org/conda-forge/{first_output}"
    pr_page_url = f"{feedstock_url}/pulls"

    recipe_badge = f"[![Conda Recipe](https://img.shields.io/badge/recipe-{first_output}-green.svg)]({feedstock_url})"
    downloads_badge = f"[![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/{first_output}.svg)]({anaconda_url})"
    version_badge = f"[![Conda Version](https://img.shields.io/conda/vn/conda-forge/{first_output}.svg)]({anaconda_url})"
    platforms_badge = f"[![Conda Platforms](https://img.shields.io/conda/pn/conda-forge/{first_output}.svg)]({anaconda_url})"

    pr_count = get_open_prs_count(first_output)
    pr_count_link = f"[{pr_count}]({pr_page_url})" if pr_count != "N/A" else pr_count

    return f"| {recipe_badge} | {downloads_badge} | {version_badge} | {platforms_badge} | {pr_count_link} | {all_outputs_text} |"

def process_tools_section(section_title, tools):
    """
    Returns a list of Markdown lines for a section (table) listing a set of tools.
    """
    lines = []
    # Section header.
    lines.append(f"### {section_title}")
    lines.append("")
    # Table header now includes an extra column for all outputs.
    lines.append("| Name | Downloads | Version | Platforms | Open PRs | Outputs |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for tool in tools:
        lines.append(generate_tool_row(tool))
    lines.append("")
    return lines

def main():
    global FEEDSTOCK_OUTPUTS
    # Load the feedstock outputs from the remote JSON.
    FEEDSTOCK_OUTPUTS = load_feedstock_outputs()

    # Load the local JSON data containing categories and tools.
    with open("feedstocks.json", "r") as f:
        data = json.load(f)

    lines = []
    lines.append("# HEP Packaging Coordination")
    lines.append("")
    lines.append("A community project working to get as many cross-platform builds of HEP tools on conda-forge as possible.")
    lines.append("")
    lines.append("## Tools distributed on conda-forge")
    lines.append("")

    # Process each top-level category in the JSON.
    for category, content in data.items():
        if isinstance(content, list):
            lines.append(f"## {category}")
            lines.append("")
            lines.extend(process_tools_section(category, content))
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

    # Append the last updated timestamp in UTC.
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines.append(f"Last updated: {now_utc}")

    # Write output to README.md in the "profile" directory relative to this script.
    script_dir = os.path.dirname(os.path.realpath(__file__))
    output_path = os.path.join(script_dir, "profile", "README.md")
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    print(f"README.md updated successfully at {output_path}")

if __name__ == "__main__":
    main()
