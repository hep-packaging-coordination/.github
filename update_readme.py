#!/usr/bin/env python3
import json
import os
import subprocess
import requests
from collections import defaultdict


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


def fetch_all_pr_counts(feedstocks):
    """
    Fetch open PR counts for all feedstocks in a single batched GraphQL query.
    Note: totalCount includes draft PRs (GraphQL pullRequests has no isDraft filter).
    Returns a dict mapping feedstock name -> count (int or "ERROR").
    """
    if not feedstocks:
        return {}

    # GraphQL aliases must match [_A-Za-z][_0-9A-Za-z]* — replace hyphens with underscores.
    # conda-forge feedstock names use hyphens, not underscores, so collisions are not a concern.
    def to_alias(name):
        return name.replace("-", "_")

    feedstocks = list(feedstocks)
    counts = {}
    for i in range(0, len(feedstocks), 25):
        chunk = feedstocks[i : i + 25]
        alias_to_feedstock = {to_alias(f): f for f in chunk}

        query_parts = []
        for feedstock in chunk:
            alias = to_alias(feedstock)
            repo_name = f"{feedstock}-feedstock"
            query_parts.append(
                f'  {alias}: repository(owner: "conda-forge", name: "{repo_name}") {{\n'
                f"    pullRequests(states: [OPEN]) {{\n"
                f"      totalCount\n"
                f"    }}\n"
                f"  }}"
            )

        query = "query {\n" + "\n".join(query_parts) + "\n}"

        try:
            result = subprocess.run(
                ["gh", "api", "graphql", "-f", f"query={query}"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout).get("data", {})
            for alias, feedstock in alias_to_feedstock.items():
                repo_data = data.get(alias)
                if repo_data is None:
                    counts[feedstock] = "ERROR"
                else:
                    counts[feedstock] = repo_data["pullRequests"]["totalCount"]
        except subprocess.CalledProcessError as e:
            print(
                f"GraphQL error fetching PR counts (batch {i // 25 + 1}): {e.stderr.strip()}"
            )
            for feedstock in chunk:
                counts[feedstock] = "ERROR"

    return counts


def generate_tool_row(feedstock_name):
    """
    Generate a Markdown table row for a given output with badges for:
      - Feedstock name (to enable text search)
      - Conda Recipe (linking to the feedstock repository on GitHub for the first output)
      - Conda Downloads (linking to the Anaconda page for the first output)
      - Conda Version (linking to the Anaconda page for the first output)
      - Conda Platforms (linking to the Anaconda page for the first output)
      - Open non-draft PRs (linking to the pull requests page on GitHub for the first output)
      - A comma-separated list of all outputs for that feedstock.
    """
    feedstock_url = f"https://github.com/conda-forge/{feedstock_name}-feedstock"
    pr_page_url = f"{feedstock_url}/pulls"
    pr_count = PR_COUNTS.get(feedstock_name, "ERROR")
    pr_count_link = "" if pr_count == 0 else f"[{pr_count}]({pr_page_url})"

    for i, output in enumerate(sorted(FEEDSTOCK_OUTPUTS[feedstock_name])):
        print(feedstock_name, output)
        anaconda_url = f"https://anaconda.org/conda-forge/{output}"

        if i == 0:
            feedstock_badge = f"[![Conda Recipe](https://img.shields.io/badge/feedstock-{output.replace('-', '--')}-green.svg)]({feedstock_url})"
        else:
            feedstock_badge = ""
        recipe_badge = f"[![Conda Recipe](https://img.shields.io/badge/recipe-{output.replace('-', '--')}-green.svg)]({feedstock_url})"
        downloads_badge = f"[![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/{output}.svg)]({anaconda_url})"
        version_badge = f"[![Conda Version](https://img.shields.io/conda/vn/conda-forge/{output}.svg)]({anaconda_url})"
        platforms_badge = f"[![Conda Platforms](https://img.shields.io/conda/pn/conda-forge/{output}.svg)]({anaconda_url})"

        yield f"| {feedstock_name} | {feedstock_badge} | {recipe_badge} | {downloads_badge} | {version_badge} | {platforms_badge} | {pr_count_link} |"


def process_tools_section(section_title, tools):
    """
    Returns a list of Markdown lines for a section (table) listing a set of tools.
    """
    lines = []
    # Section header.
    lines.append(f"### {section_title}")
    lines.append("")
    # Table header now includes an extra column for all outputs.
    lines.append(
        "| Name | Feedstock | Output | Downloads | Version | Platforms | Open PRs |"
    )
    lines.append("| ---| --- | --- | --- | --- | --- | --- |")
    for tool in sorted(tools):
        lines.extend(generate_tool_row(tool))
    lines.append("")
    return lines


def main():
    global FEEDSTOCK_OUTPUTS, PR_COUNTS
    by_feedstock = defaultdict(set)
    for output, feedstocks in load_feedstock_outputs().items():
        for feedstock in feedstocks:
            by_feedstock[feedstock].add(output)
    FEEDSTOCK_OUTPUTS = dict(by_feedstock)

    # Load the local JSON data containing categories and tools.
    with open("feedstocks.json", "r") as f:
        data = json.load(f)

    # Collect all feedstock names up front for a single batched GraphQL query.
    all_feedstocks = set()
    for content in data.values():
        if isinstance(content, list):
            all_feedstocks.update(content)
        elif isinstance(content, dict):
            for tools in content.values():
                all_feedstocks.update(tools)
    PR_COUNTS = fetch_all_pr_counts(all_feedstocks)

    lines = []
    lines.append("# HEP Packaging Coordination")
    lines.append("")
    lines.append(
        "A community project working to get as many cross-platform builds of HEP tools on conda-forge as possible."
    )
    lines.append("")
    lines.append("## Tools distributed on conda-forge")
    lines.append("")

    # Process each top-level category in the JSON.
    for category, content in data.items():
        if isinstance(content, list):
            lines.extend(process_tools_section(category, content))
        elif isinstance(content, dict):
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
    lines.append(
        '2. Open up an [Issue](https://github.com/hep-packaging-coordination/.github/issues) with title "Add `<tool name>` to HEP Packaging Coordination" with a link to the tool\'s conda-forge feedstock.'
    )
    lines.append("")

    # Write output to README.md in the "profile" directory relative to this script.
    script_dir = os.path.dirname(os.path.realpath(__file__))
    output_path = os.path.join(script_dir, "profile", "README.md")
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    print(f"README.md updated successfully at {output_path}")


if __name__ == "__main__":
    main()
