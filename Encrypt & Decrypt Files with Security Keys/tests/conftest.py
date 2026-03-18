"""Shared pytest fixtures for the test suite."""
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture()
def tmp_dir(tmp_path):
    """Return a temporary directory Path."""
    return tmp_path


@pytest.fixture()
def plaintext_file(tmp_path):
    """Create a small plaintext file and return its path."""
    p = tmp_path / "plaintext.txt"
    p.write_text("Hello, this is a test document for encryption.", encoding="utf-8")
    return p


@pytest.fixture()
def original_document(tmp_path):
    """
    Copy the real 'original_document.txt' from tests/ into a temp dir so
    tests can reference it without modifying the source file.
    """
    src = Path(__file__).parent / "original_document.txt"
    dst = tmp_path / "original_document.txt"
    dst.write_bytes(src.read_bytes())
    return dst


@pytest.fixture()
def keystore_path(tmp_path):
    """Return a temporary keystore file path (does not exist yet)."""
    return tmp_path / "test_keystore.json"
