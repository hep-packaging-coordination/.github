"""Tests for the network-fetching functions in update_readme.py.

Network failures must raise rather than produce degraded data, so a run
without connectivity cannot overwrite profile/README.md and tools.json.
"""

import pytest
import requests
import responses

from update_readme import _fetch_pr_counts_rest, load_feedstock_outputs

OUTPUTS_URL = "https://raw.githubusercontent.com/conda-forge/feedstock-outputs/single-file/feedstock-outputs.json"
PULLS_URL = "https://api.github.com/repos/conda-forge/pyhf-feedstock/pulls"


class TestLoadFeedstockOutputs:
    @responses.activate
    def test_returns_mapping(self):
        responses.get(OUTPUTS_URL, json={"pyhf": ["pyhf"]})
        assert load_feedstock_outputs() == {"pyhf": ["pyhf"]}

    @responses.activate
    def test_connection_error_raises(self):
        responses.get(OUTPUTS_URL, body=requests.ConnectionError("no network"))
        with pytest.raises(requests.ConnectionError):
            load_feedstock_outputs()

    @responses.activate
    def test_http_error_raises(self):
        responses.get(OUTPUTS_URL, status=500)
        with pytest.raises(requests.HTTPError):
            load_feedstock_outputs()


class TestFetchPrCountsRest:
    @responses.activate
    def test_counts_non_draft_prs(self):
        responses.get(
            PULLS_URL,
            match=[
                responses.matchers.query_param_matcher(
                    {"page": "1"}, strict_match=False
                )
            ],
            json=[{"draft": False}, {"draft": True}],
        )
        responses.get(
            PULLS_URL,
            match=[
                responses.matchers.query_param_matcher(
                    {"page": "2"}, strict_match=False
                )
            ],
            json=[],
        )
        assert _fetch_pr_counts_rest(["pyhf"]) == {"pyhf": 1}

    @responses.activate
    def test_connection_error_raises(self):
        responses.get(PULLS_URL, body=requests.ConnectionError("no network"))
        with pytest.raises(requests.ConnectionError):
            _fetch_pr_counts_rest(["pyhf"])

    @responses.activate
    def test_http_error_records_error_sentinel(self):
        # A per-repo HTTP error (e.g. a renamed or missing feedstock) is not
        # a network failure, so it is still reported in the PR count column.
        responses.get(PULLS_URL, status=404)
        assert _fetch_pr_counts_rest(["pyhf"]) == {"pyhf": "ERROR"}
