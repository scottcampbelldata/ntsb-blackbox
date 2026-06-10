import pytest

from build_index import chunk_text


def test_short_text_is_a_single_chunk():
    assert chunk_text("just a few words", size=10, overlap=2) == ["just a few words"]


def test_empty_text_gives_no_chunks():
    assert chunk_text("   ") == []


def test_windows_overlap_and_cover_the_whole_text():
    words = [f"w{i}" for i in range(450)]
    chunks = chunk_text(" ".join(words), size=200, overlap=40)
    assert chunks[0].split()[0] == "w0"
    assert chunks[1].split()[0] == "w160"  # steps back by the overlap
    assert chunks[-1].split()[-1] == "w449"  # nothing dropped at the tail


def test_overlap_must_be_smaller_than_chunk_size():
    # overlap >= size would make the window stop advancing: an infinite loop
    with pytest.raises(ValueError):
        chunk_text("word " * 100, size=50, overlap=50)
