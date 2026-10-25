"""Tests for the network-fetching functions in update_readme.py.

Network failures must raise rather than produce degraded data, so a run
without connectivity cannot overwrite profile/README.md and tools.json.
"""

import pytest
import requests
import responses
from responses import matchers

from update_readme import (
    FEEDSTOCK_OUTPUTS_URL,
    _fetch_pr_counts_rest,
    load_feedstock_outputs,
)

PULLS_URL = "https://api.github.com/repos/conda-forge/pyhf-feedstock/pulls"


class TestLoadFeedstockOutputs:
    @responses.activate
    def test_returns_mapping(self):
        responses.get(FEEDSTOCK_OUTPUTS_URL, json={"pyhf": ["pyhf"]})
        assert load_feedstock_outputs() == {"pyhf": ["pyhf"]}

    @responses.activate
    def test_connection_error_raises(self):
        responses.get(
            FEEDSTOCK_OUTPUTS_URL, body=requests.ConnectionError("no network")
        )
        with pytest.raises(requests.ConnectionError):
            load_feedstock_outputs()

    @responses.activate
    def test_http_error_raises(self):
        responses.get(FEEDSTOCK_OUTPUTS_URL, status=500)
        with pytest.raises(requests.HTTPError):
            load_feedstock_outputs()


class TestFetchPrCountsRest:
    @staticmethod
    def _stub_page(page, body):
        responses.get(
            PULLS_URL,
            match=[
                matchers.query_param_matcher({"page": str(page)}, strict_match=False)
            ],
            json=body,
        )

    @responses.activate
    def test_counts_non_draft_prs(self):
        self._stub_page(1, [{"draft": False}, {"draft": True}])
        self._stub_page(2, [])
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
