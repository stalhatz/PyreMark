import hashlib
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

test_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(test_dir.parent))

from src.git_utils import is_git_repo, get_git_hash, get_project_version
from src.xmp_metadata import compute_data_hash, build_xmp_metadata, inject_xmp_metadata
from pypdf import PdfReader


class TestComputeDataHash:
    def test_compute_data_hash_deterministic(self):
        data = {"a": 1, "b": [2, 3]}
        hash1 = compute_data_hash(data)
        hash2 = compute_data_hash(data)
        assert hash1 == hash2

    def test_compute_data_hash_order_independent(self):
        data1 = {"a": 1, "b": 2}
        data2 = {"b": 2, "a": 1}
        assert compute_data_hash(data1) == compute_data_hash(data2)

    def test_compute_data_hash_different_data(self):
        data1 = {"a": 1}
        data2 = {"a": 2}
        assert compute_data_hash(data1) != compute_data_hash(data2)

    def test_compute_data_hash_returns_hex(self):
        data = {"key": "value"}
        result = compute_data_hash(data)
        assert len(result) == 64
        int(result, 16)


class TestBuildXmpMetadata:
    def test_build_xmp_metadata_all_fields(self, tmp_git_repo):
        data_hash = compute_data_hash({"test": "data"})
        pyremark_git = get_git_hash(str(tmp_git_repo))
        data_git = get_git_hash(str(tmp_git_repo))

        xmp_xml = build_xmp_metadata(
            data_hash=data_hash,
            pyremark_version="0.1.0",
            pyremark_git=pyremark_git,
            data_git=data_git,
            tags=["cv", "engineering"],
        )

        assert "xmp:CreatorTool" in xmp_xml
        assert "cv" in xmp_xml
        assert "engineering" in xmp_xml
        assert "PyreMark 0.1.0" in xmp_xml
        assert pyremark_git in xmp_xml
        assert data_hash in xmp_xml
        assert data_git in xmp_xml
        assert "xmp:CreateDate" in xmp_xml
        assert "xmp:ModifyDate" in xmp_xml
        assert "xmp:MetadataDate" in xmp_xml

    def test_build_xmp_metadata_no_data_git(self):
        data_hash = compute_data_hash({"test": "data"})

        xmp_xml = build_xmp_metadata(
            data_hash=data_hash,
            pyremark_version="0.1.0",
            pyremark_git="abc123",
            data_git=None,
            tags=["test"],
        )

        assert "xmp:CreatorTool" in xmp_xml
        assert "test" in xmp_xml
        assert "xmpMM:VersionID" not in xmp_xml

    def test_build_xmp_metadata_no_pyremark_git(self):
        data_hash = compute_data_hash({"test": "data"})

        xmp_xml = build_xmp_metadata(
            data_hash=data_hash,
            pyremark_version="0.1.0",
            pyremark_git=None,
            data_git="def456",
            tags=[],
        )

        assert "PyreMark 0.1.0" in xmp_xml
        assert "abc123" not in xmp_xml
        assert "dc:subject" not in xmp_xml

    def test_build_xmp_metadata_empty_tags(self):
        data_hash = compute_data_hash({"test": "data"})

        xmp_xml = build_xmp_metadata(
            data_hash=data_hash,
            pyremark_version="0.1.0",
            pyremark_git="abc123",
            data_git="def456",
            tags=[],
        )

        assert "dc:subject" not in xmp_xml


class TestInjectXmpMetadata:
    def test_inject_xmp_metadata_roundtrip(self, tmp_path):
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=612, height=792)
        pdf_path = tmp_path / "test.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)

        xmp_xml = build_xmp_metadata(
            data_hash="abc123",
            pyremark_version="0.1.0",
            pyremark_git="git123",
            data_git="data456",
            tags=["tag1", "tag2"],
        )

        inject_xmp_metadata(str(pdf_path), xmp_xml)

        reader = PdfReader(str(pdf_path))
        assert reader.xmp_metadata is not None
        meta = reader.xmp_metadata
        assert meta.dc_subject == ["tag1", "tag2"]
        assert meta.xmpmm_document_id == "abc123"

        from pypdf.xmp import XMPMM_NAMESPACE
        version_id_nodes = list(meta.get_nodes_in_namespace("", XMPMM_NAMESPACE))
        version_id_text = None
        for node in version_id_nodes:
            if node.localName == "VersionID":
                version_id_text = node.firstChild.data
                break
        assert version_id_text == "data456"


class TestGitUtils:
    def test_git_utils_is_git_repo_true(self, tmp_git_repo):
        assert is_git_repo(str(tmp_git_repo)) is True

    def test_git_utils_is_git_repo_false(self, tmp_path):
        non_repo = tmp_path / "not_a_repo"
        non_repo.mkdir()
        assert is_git_repo(str(non_repo)) is False

    def test_git_utils_get_git_hash(self, tmp_git_repo):
        result = get_git_hash(str(tmp_git_repo))
        assert result is not None
        assert len(result) == 40

    def test_git_utils_get_git_hash_no_repo(self, tmp_path, caplog):
        non_repo = tmp_path / "not_a_repo"
        non_repo.mkdir()
        with caplog.at_level(logging.WARNING):
            result = get_git_hash(str(non_repo))
        assert result is None
        assert "not a git repository" in caplog.text

    def test_get_project_version(self):
        version = get_project_version()
        assert isinstance(version, str)
        assert len(version) > 0
