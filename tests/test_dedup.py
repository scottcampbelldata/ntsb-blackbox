from dedup import dedup_accidents

RESULTS = [
    (0.9, "A", "first chunk of A"),
    (0.8, "B", "first chunk of B"),
    (0.7, "A", "second chunk of A"),
    (0.6, "C", "first chunk of C"),
]


def test_keeps_first_occurrence_per_accident():
    assert dedup_accidents(RESULTS) == [
        (0.9, "A", "first chunk of A"),
        (0.8, "B", "first chunk of B"),
        (0.6, "C", "first chunk of C"),
    ]


def test_k_caps_the_number_of_accidents():
    assert [nid for _, nid, _ in dedup_accidents(RESULTS, k=2)] == ["A", "B"]


def test_empty_results():
    assert dedup_accidents([]) == []
