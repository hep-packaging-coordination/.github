#!/usr/bin/env python3
"""Generate profile/README.md and site/src/data/tools.json.

Fetches live data (conda-forge feedstock-outputs map, GitHub open-PR counts)
and delegates model construction and rendering to feedstock_data.py so the
two output files are always derived from the same in-memory model.
"""

import json
import os
import subprocess

import requests

from feedstock_data import build_tool_model, render_readme, render_tools_json


def load_feedstock_outputs():
    """Load the feedstock-outputs mapping from conda-forge's single-file JSON.

    Returns a dict mapping output name -> list of feedstock names.
    """
    url = "https://raw.githubusercontent.com/conda-forge/feedstock-outputs/single-file/feedstock-outputs.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error loading feedstock outputs: {e}")
        return {}


def _fetch_pr_counts_graphql(feedstocks):
    """Fetch open PR counts via gh CLI GraphQL in batches of 25.

    Note: totalCount includes draft PRs (GraphQL pullRequests has no isDraft filter).
    Returns a dict mapping feedstock name -> count, or None if gh CLI is unavailable/unauthenticated.
    """

    # GraphQL aliases must match [_A-Za-z][_0-9A-Za-z]* — replace hyphens with underscores.
    # conda-forge feedstock names use hyphens, not underscores, so collisions are not a concern.
    def to_alias(name):
        return name.replace("-", "_")

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
        except FileNotFoundError:
            print("gh CLI not found; falling back to REST API.")
            return None
        except subprocess.CalledProcessError as e:
            print(
                f"gh CLI error (batch {i // 25 + 1}): {e.stderr.strip()}; falling back to REST API."
            )
            return None

    return counts


def _fetch_pr_counts_rest(feedstocks):
    """Fetch open non-draft PR counts via the GitHub REST API, one feedstock at a time.

    Uses GITHUB_TOKEN if set, otherwise makes unauthenticated requests.
    Paginates through all open PRs to avoid missing any beyond the first page.
    """
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    counts = {}
    for feedstock in feedstocks:
        repo = f"conda-forge/{feedstock}-feedstock"
        page, non_draft_count = 1, 0
        while True:
            url = f"https://api.github.com/repos/{repo}/pulls?state=open&per_page=100&page={page}"
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                pulls = response.json()
                if not pulls:
                    break
                non_draft_count += sum(1 for pr in pulls if not pr.get("draft", False))
                page += 1
            except Exception as e:
                print(f"Error fetching PRs for {repo}: {e}")
                non_draft_count = "ERROR"
                break
        counts[feedstock] = non_draft_count

    return counts


def fetch_all_pr_counts(feedstocks):
    """Fetch open PR counts for all feedstocks.

    Tries gh CLI GraphQL (batched, authenticated) first; falls back to REST API with GITHUB_TOKEN.
    """
    if not feedstocks:
        return {}

    feedstocks = list(feedstocks)
    counts = _fetch_pr_counts_graphql(feedstocks)
    if counts is None:
        counts = _fetch_pr_counts_rest(feedstocks)
    return counts


def _invert_feedstock_outputs(raw_outputs: dict) -> dict[str, set[str]]:
    """Invert the conda-forge output->feedstocks map to feedstock->outputs."""
    by_feedstock: dict[str, set[str]] = {}
    for output, feedstocks in raw_outputs.items():
        for feedstock in feedstocks:
            by_feedstock.setdefault(feedstock, set()).add(output)
    return by_feedstock


def main():
    # Load local feedstocks.json.
    with open("feedstocks.json") as f:
        feedstocks_data = json.load(f)

    # Collect all feedstock names for a single batched PR-count fetch.
    all_feedstocks: set[str] = set()
    for content in feedstocks_data.values():
        if isinstance(content, list):
            all_feedstocks.update(content)
        elif isinstance(content, dict):
            for tools in content.values():
                all_feedstocks.update(tools)

    # Fetch live data (network calls happen exactly once).
    raw_outputs = load_feedstock_outputs()
    feedstock_outputs = _invert_feedstock_outputs(raw_outputs)
    pr_counts = fetch_all_pr_counts(all_feedstocks)

    # Build the shared model, then render both artifacts.
    model = build_tool_model(feedstocks_data, feedstock_outputs, pr_counts)

    script_dir = os.path.dirname(os.path.realpath(__file__))

    readme_path = os.path.join(script_dir, "profile", "README.md")
    with open(readme_path, "w") as f:
        f.write(render_readme(model))
    print(f"README.md updated at {readme_path}")

    tools_json_path = os.path.join(script_dir, "site", "src", "data", "feedstocks.json")
    os.makedirs(os.path.dirname(tools_json_path), exist_ok=True)
    with open(tools_json_path, "w") as f:
        json.dump(render_tools_json(model), f, indent=2)
        f.write("\n")
    print(f"tools.json updated at {tools_json_path}")


if __name__ == "__main__":
    main()
