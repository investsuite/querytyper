"""Test querytyper."""

import querytyper


def test_import() -> None:
    """Test that the package can be imported."""
    assert isinstance(querytyper.__name__, str)
