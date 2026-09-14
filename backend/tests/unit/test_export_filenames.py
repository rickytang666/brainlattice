"""
zip entry names are built from llm-generated concept ids, so they are untrusted
input. these guard against writing outside the archive root.
"""
import pytest

from services.export_processor import ExportProcessor


def safe(concept_id: str, used=None) -> str:
    return ExportProcessor._safe_filename(concept_id, used if used is not None else set())


class TestPathTraversal:
    @pytest.mark.parametrize(
        "concept_id",
        [
            "../../etc/passwd",
            "a/b/c",
            "..\\..\\windows\\system32",
            "/absolute/path",
            "nested/../../escape",
        ],
    )
    def test_no_separators_survive(self, concept_id):
        result = safe(concept_id)
        assert "/" not in result
        assert "\\" not in result
        assert not result.startswith(".")

    def test_null_byte_stripped(self):
        assert "\x00" not in safe("evil\x00.md")


class TestDegenerateInput:
    @pytest.mark.parametrize("concept_id", ["", "   ", "..", ".", "..."])
    def test_empty_or_dots_become_untitled(self, concept_id):
        assert safe(concept_id) == "untitled.md"

    def test_long_name_truncated(self):
        assert len(safe("x" * 500)) <= 124  # 120 + ".md"


class TestCollisions:
    def test_duplicates_get_suffixed(self):
        used = set()
        first = safe("gradient descent", used)
        second = safe("gradient descent", used)
        assert first == "gradient descent.md"
        assert second == "gradient descent (2).md"
        assert first != second

    def test_traversal_collisions_still_unique(self):
        """distinct malicious ids must not collapse onto one entry."""
        used = set()
        names = {safe(c, used) for c in ["a/b", "a\\b", "a/b", "a-b"]}
        assert len(names) == 4


class TestNormalInput:
    def test_ordinary_concept_unchanged(self):
        assert safe("backpropagation") == "backpropagation.md"

    def test_internal_whitespace_collapsed(self):
        assert safe("chain   rule") == "chain rule.md"
