from hybrid_search import RRF_K, rrf_fuse


def test_single_list_scores_by_rank():
    ranked = rrf_fuse([["A", "B"]])
    assert ranked[0] == ("A", 1.0 / (RRF_K + 1))
    assert ranked[1] == ("B", 1.0 / (RRF_K + 2))


def test_consensus_beats_either_engines_single_top():
    # B ranks decently in both lists; A and C are each one list's favorite
    ranked = rrf_fuse([["A", "B", "C"], ["B", "C", "A"]])
    assert [nid for nid, _ in ranked] == ["B", "A", "C"]


def test_id_seen_by_only_one_engine_still_appears():
    ranked = rrf_fuse([["A"], ["B"]])
    assert {nid for nid, _ in ranked} == {"A", "B"}


def test_k_caps_the_fused_list():
    ranked = rrf_fuse([["A", "B", "C"]], k=2)
    assert len(ranked) == 2
