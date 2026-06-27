"""Tests for Phase C citation extraction helper."""

from sisyphus.phases.phase_c import _clean_citations


def test_self_citations_filtered():
    self_nas = "nms://iliad/book-xxiii/funeral-games"
    assert _clean_citations([self_nas] * 12, self_nas) == []


def test_external_citations_kept():
    self_nas = "nms://iliad/book-xxiii/funeral-games"
    child = "nms://iliad/book-xxiii/funeral-games/chariot-race"
    assert _clean_citations([self_nas, child, self_nas, child], self_nas) == [child]


def test_dedup_preserves_order():
    self_nas = "nms://gilgamesh/tablet-xi/flood-narrative"
    a = "nms://gilgamesh/tablet-xi/cedar-forest"
    b = "nms://gilgamesh/tablet-xi/bull-of-heaven"
    assert _clean_citations([a, b, a, b], self_nas) == [a, b]


def test_empty_input():
    assert _clean_citations([], "nms://gilgamesh/tablet-xi/flood-narrative") == []


def test_mixed_external_and_self():
    self_nas = "nms://mahabharata/adi-parva/story-of-astika"
    ext_a = "nms://mahabharata/adi-parva/churning-of-the-ocean"
    ext_b = "nms://mahabharata/adi-parva/birth-of-garuda"
    raw = [self_nas, ext_a, self_nas, ext_b, ext_a]
    assert _clean_citations(raw, self_nas) == [ext_a, ext_b]
