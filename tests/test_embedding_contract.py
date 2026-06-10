"""The stored passage vectors and the query vectors must come from the same
model and prefix, or retrieval silently returns garbage. The contract is
enforced by build_index.py importing them from search.py - these tests fail if
anyone reintroduces a second definition."""

import build_index
import search


def test_index_builder_uses_the_query_side_model_definition():
    assert build_index.MODEL_NAME is search.MODEL_NAME


def test_index_builder_reuses_the_query_side_search():
    assert build_index.search is search.search
