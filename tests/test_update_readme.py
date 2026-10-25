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
    REQUEST_TIMEOUT_SECONDS,
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
    def test_request_sets_timeout(self):
        responses.get(FEEDSTOCK_OUTPUTS_URL, json={})
        load_feedstock_outputs()
        assert (
            responses.calls[0].request.req_kwargs["timeout"] == REQUEST_TIMEOUT_SECONDS
        )

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
    def test_requests_set_timeout(self):
        self._stub_page(1, [])
        _fetch_pr_counts_rest(["pyhf"])
        assert (
            responses.calls[0].request.req_kwargs["timeout"] == REQUEST_TIMEOUT_SECONDS
        )

    @responses.activate
    def test_connection_error_raises(self):
        responses.get(PULLS_URL, body=requests.ConnectionError("no network"))
        with pytest.raises(requests.ConnectionError):
            _fetch_pr_counts_rest(["pyhf"])

    @responses.activate
    def test_not_found_records_error_sentinel(self):
        # A 404 means this one feedstock is missing or renamed, so it is
        # reported in the PR count column rather than failing the run.
        responses.get(PULLS_URL, status=404)
        assert _fetch_pr_counts_rest(["pyhf"]) == {"pyhf": "ERROR"}

    @pytest.mark.parametrize("status", [401, 403, 429, 500, 503])
    @responses.activate
    def test_other_http_errors_raise(self, status):
        # Bad tokens, rate limits, and outages affect every repo, so they
        # must fail the run instead of writing "ERROR" for all feedstocks.
        responses.get(PULLS_URL, status=status)
        with pytest.raises(requests.HTTPError):
            _fetch_pr_counts_rest(["pyhf"])
