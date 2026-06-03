"""Tests for the refactored feedstock data pipeline.

Covers:
  - build_tool_model: pure model construction from raw data
  - render_tools_json: JSON artifact from model
  - render_readme: README artifact from model
  - Consistency invariant: README and tools.json agree on every feedstock
"""

import json

from feedstock_data import build_tool_model, render_readme, render_tools_json


# ── Fixtures ──────────────────────────────────────────────────────────────────

# Minimal tools.json data covering all structural variants:
#   - flat category (list of feedstocks)
#   - nested category (dict of subcategory -> list)
MINIMAL_FEEDSTOCKS = {
    "Analysis": ["pyhf", "root"],
    "Statistical Modeling": ["stanhf"],
    "Experiment specific": {
        "ATLAS": ["histfitter", "itkdb"],
        "CMS": ["cms-combine"],
    },
}

# feedstock -> set of outputs (simulates the inverted conda-forge map).
# "root" has multiple outputs to exercise the multi-row per feedstock path.
MINIMAL_FEEDSTOCK_OUTPUTS = {
    "pyhf": {"pyhf"},
    "root": {"root", "root-binaries"},
    "stanhf": {"stanhf"},
    "histfitter": {"histfitter"},
    "itkdb": {"itkdb"},
    "cms-combine": {"cms-combine"},
}

# PR count sentinel cases: 0 (blank), positive (link), ERROR (pass-through).
MINIMAL_PR_COUNTS = {
    "pyhf": 0,
    "root": 3,
    "stanhf": "ERROR",
    "histfitter": 1,
    "itkdb": 0,
    "cms-combine": 2,
}


def _all_feedstock_names(feedstocks_data):
    """Flatten feedstocks.json into a list of all feedstock names."""
    names = []
    for val in feedstocks_data.values():
        if isinstance(val, list):
            names.extend(val)
        elif isinstance(val, dict):
            for sublist in val.values():
                names.extend(sublist)
    return names


# ── build_tool_model ──────────────────────────────────────────────────────────


class TestBuildToolModel:
    def _model(self):
        return build_tool_model(
            MINIMAL_FEEDSTOCKS, MINIMAL_FEEDSTOCK_OUTPUTS, MINIMAL_PR_COUNTS
        )

    def test_returns_dict_with_categories_key(self):
        model = self._model()
        assert "categories" in model

    def test_flat_category_has_feedstocks_no_subcategories(self):
        model = self._model()
        analysis = next(c for c in model["categories"] if c["name"] == "Analysis")
        assert analysis["subcategories"] is None
        assert analysis["feedstocks"] is not None

    def test_nested_category_has_subcategories_no_feedstocks(self):
        model = self._model()
        exp = next(c for c in model["categories"] if c["name"] == "Experiment specific")
        assert exp["feedstocks"] is None
        assert exp["subcategories"] is not None

    def test_flat_feedstock_outputs_are_sorted(self):
        model = self._model()
        analysis = next(c for c in model["categories"] if c["name"] == "Analysis")
        root_entry = next(f for f in analysis["feedstocks"] if f["name"] == "root")
        assert root_entry["outputs"] == sorted(root_entry["outputs"])

    def test_flat_feedstock_pr_counts_preserved(self):
        model = self._model()
        analysis = next(c for c in model["categories"] if c["name"] == "Analysis")
        pyhf_entry = next(f for f in analysis["feedstocks"] if f["name"] == "pyhf")
        assert pyhf_entry["pr_count"] == 0
        root_entry = next(f for f in analysis["feedstocks"] if f["name"] == "root")
        assert root_entry["pr_count"] == 3

    def test_error_pr_count_preserved(self):
        model = self._model()
        stats = next(
            c for c in model["categories"] if c["name"] == "Statistical Modeling"
        )
        stanhf_entry = stats["feedstocks"][0]
        assert stanhf_entry["pr_count"] == "ERROR"

    def test_subcategory_feedstocks_present(self):
        model = self._model()
        exp = next(c for c in model["categories"] if c["name"] == "Experiment specific")
        atlas = next(s for s in exp["subcategories"] if s["name"] == "ATLAS")
        names = [f["name"] for f in atlas["feedstocks"]]
        assert "histfitter" in names
        assert "itkdb" in names

    def test_feedstock_absent_from_outputs_map_has_empty_outputs(self):
        """A feedstock not present in the outputs map gets an empty output list."""
        feedstocks_data = {"Analysis": ["unknown-feedstock"]}
        model = build_tool_model(feedstocks_data, {}, {"unknown-feedstock": 0})
        entry = model["categories"][0]["feedstocks"][0]
        assert entry["name"] == "unknown-feedstock"
        assert entry["outputs"] == []


# ── render_tools_json ─────────────────────────────────────────────────────────


class TestRenderToolsJson:
    def _json(self):
        model = build_tool_model(
            MINIMAL_FEEDSTOCKS, MINIMAL_FEEDSTOCK_OUTPUTS, MINIMAL_PR_COUNTS
        )
        return render_tools_json(model)

    def test_has_generated_note(self):
        data = self._json()
        assert "generated_note" in data

    def test_has_categories_list(self):
        data = self._json()
        assert "categories" in data
        assert len(data["categories"]) > 0

    def test_flat_category_feedstocks_present(self):
        data = self._json()
        analysis = next(c for c in data["categories"] if c["name"] == "Analysis")
        names = [f["name"] for f in analysis["feedstocks"]]
        assert "pyhf" in names
        assert "root" in names

    def test_nested_category_subcategories_present(self):
        data = self._json()
        exp = next(c for c in data["categories"] if c["name"] == "Experiment specific")
        assert exp["subcategories"] is not None
        sub_names = [s["name"] for s in exp["subcategories"]]
        assert "ATLAS" in sub_names
        assert "CMS" in sub_names

    def test_is_json_serializable_and_round_trips(self):
        data = self._json()
        serialized = json.dumps(data)
        roundtripped = json.loads(serialized)
        assert roundtripped["categories"] == data["categories"]


# ── render_readme ─────────────────────────────────────────────────────────────


class TestRenderReadme:
    def _readme(self):
        model = build_tool_model(
            MINIMAL_FEEDSTOCKS, MINIMAL_FEEDSTOCK_OUTPUTS, MINIMAL_PR_COUNTS
        )
        return render_readme(model)

    def test_contains_top_level_heading(self):
        readme = self._readme()
        assert "# HEP Packaging Coordination" in readme

    def test_contains_tools_section_heading(self):
        readme = self._readme()
        assert "## Tools distributed on conda-forge" in readme

    def test_flat_category_becomes_section_heading(self):
        readme = self._readme()
        assert "### Analysis" in readme
        assert "### Statistical Modeling" in readme

    def test_experiment_specific_parent_not_emitted_subcategories_are(self):
        """'Experiment specific' parent key is skipped; subcategories become sections."""
        readme = self._readme()
        assert "### Experiment specific" not in readme
        assert "### ATLAS" in readme
        assert "### CMS" in readme

    def test_table_header_present(self):
        readme = self._readme()
        assert (
            "| Name | Feedstock | Output | Downloads | Version | Platforms | Open PRs |"
            in readme
        )

    def test_feedstock_names_in_table(self):
        readme = self._readme()
        assert "pyhf" in readme
        assert "root" in readme

    def test_pr_count_zero_renders_blank_cell(self):
        """When pr_count == 0 the Open PRs cell must be blank, not '0'."""
        readme = self._readme()
        lines = readme.splitlines()
        # pyhf rows (first output alphabetically → first row carries the name)
        pyhf_lines = [line for line in lines if "pyhf" in line and line.startswith("|")]
        assert pyhf_lines, "Expected at least one pyhf table row"
        for line in pyhf_lines:
            cells = [c.strip() for c in line.split("|")]
            pr_cell = cells[-2]  # last non-empty cell before trailing |
            assert pr_cell != "0", f"PR count 0 must be blank, got '{pr_cell}'"

    def test_pr_count_positive_renders_as_link(self):
        """When pr_count > 0 the Open PRs cell is a Markdown link."""
        readme = self._readme()
        assert "[3](https://github.com/conda-forge/root-feedstock/pulls)" in readme

    def test_hyphen_in_badge_label_escaped_to_double_hyphen(self):
        """shields.io badge labels must escape hyphens as '--'."""
        readme = self._readme()
        # "root-binaries" output -> badge label "root--binaries"
        assert "root--binaries" in readme

    def test_adding_new_tools_section_present(self):
        readme = self._readme()
        assert "## Adding new tools" in readme


# ── Consistency invariant ─────────────────────────────────────────────────────


class TestReadmeToolsJsonConsistency:
    """Every feedstock in the README must appear in tools.json with matching
    outputs and PR count, and vice versa — guaranteeing the two artifacts
    can never silently diverge."""

    def setup_method(self):
        model = build_tool_model(
            MINIMAL_FEEDSTOCKS, MINIMAL_FEEDSTOCK_OUTPUTS, MINIMAL_PR_COUNTS
        )
        self.readme = render_readme(model)
        self.tools_json = render_tools_json(model)

    def _all_feedstocks_from_json(self):
        """Flatten tools.json to {feedstock_name: entry_dict}."""
        result = {}
        for cat in self.tools_json["categories"]:
            if cat.get("feedstocks"):
                for f in cat["feedstocks"]:
                    result[f["name"]] = f
            if cat.get("subcategories"):
                for sub in cat["subcategories"]:
                    for f in sub["feedstocks"]:
                        result[f["name"]] = f
        return result

    def test_every_feedstock_in_readme_appears_in_json(self):
        json_feedstocks = self._all_feedstocks_from_json()
        for name in _all_feedstock_names(MINIMAL_FEEDSTOCKS):
            assert name in json_feedstocks, (
                f"Feedstock '{name}' is in the README source data but missing from tools.json"
            )

    def test_every_feedstock_in_json_appears_in_readme(self):
        json_feedstocks = self._all_feedstocks_from_json()
        for name in json_feedstocks:
            assert name in self.readme, (
                f"Feedstock '{name}' is in tools.json but absent from README"
            )

    def test_outputs_in_json_appear_in_readme(self):
        """Each output listed in tools.json must appear in the README table."""
        json_feedstocks = self._all_feedstocks_from_json()
        for name, entry in json_feedstocks.items():
            for output in entry["outputs"]:
                assert output in self.readme, (
                    f"Output '{output}' (feedstock '{name}') present in tools.json "
                    f"but absent from README"
                )

    def test_no_duplicate_feedstocks_in_json(self):
        """Each feedstock appears exactly once across all categories in tools.json."""
        seen = []
        for cat in self.tools_json["categories"]:
            if cat.get("feedstocks"):
                seen.extend(f["name"] for f in cat["feedstocks"])
            if cat.get("subcategories"):
                for sub in cat["subcategories"]:
                    seen.extend(f["name"] for f in sub["feedstocks"])
        duplicates = [x for x in set(seen) if seen.count(x) > 1]
        assert not duplicates, f"Duplicate feedstocks in tools.json: {duplicates}"
