"""Tests for the YAML comparer module."""

import pytest

from src.comparer import YamlComparer


class TestYamlComparer:
    """Test cases for YamlComparer."""

    @pytest.fixture
    def comparer(self):
        """Create a YamlComparer instance."""
        return YamlComparer()

    def test_compare_no_differences(self, comparer):
        """Test comparison with identical YAML structures."""
        yaml1 = {
            "extensions": [{"Ext1": {"commit": "abc123"}}],
            "skins": [{"Skin1": {"commit": "def456"}}]
        }

        yaml2 = {
            "extensions": [{"Ext1": {"commit": "abc123"}}],
            "skins": [{"Skin1": {"commit": "def456"}}]
        }

        result = comparer.compare(yaml1, yaml2, "master", "main")

        assert "No differences found!" in result
        assert "Comparing Taqasta (master) vs Canasta (main)" in result

    def test_compare_extensions_only_in_taqasta(self, comparer):
        """Test extensions present only in Taqasta."""
        taqasta = {
            "extensions": [
                {"Ext1": {"commit": "abc123", "repository": "https://github.com/example/ext1"}},
                {"Ext2": {"commit": "def456"}}
            ]
        }

        canasta = {
            "extensions": [{"Ext3": {"commit": "xyz789"}}]
        }

        result = comparer.compare(taqasta, canasta, "master", "main")

        assert "Extensions only in Taqasta:" in result
        assert "+ Ext1" in result
        assert "+ Ext2" in result
        assert "repository: https://github.com/example/ext1" in result
        assert "commit: abc123" in result

    def test_compare_extensions_only_in_canasta(self, comparer):
        """Test extensions present only in Canasta."""
        taqasta = {
            "extensions": [{"Ext1": {"commit": "abc123"}}]
        }

        canasta = {
            "extensions": [
                {"Ext1": {"commit": "abc123"}},
                {"Ext2": {"commit": "def456", "repository": "https://github.com/example/ext2"}}
            ]
        }

        result = comparer.compare(taqasta, canasta, "master", "main")

        assert "Extensions only in Canasta:" in result
        assert "- Ext2" in result

    def test_compare_extensions_different_commits(self, comparer):
        """Test extensions with different commits."""
        taqasta = {
            "extensions": [{"Ext1": {"commit": "abc123"}}]
        }

        canasta = {
            "extensions": [{"Ext1": {"commit": "def456"}}]
        }

        result = comparer.compare(taqasta, canasta, "master", "main")

        assert "Extensions with different configurations:" in result
        assert "~ Ext1:" in result
        assert "Taqasta commit: abc123" in result
        assert "Canasta commit: def456" in result

    def test_compare_extensions_different_repositories(self, comparer):
        """Test extensions with different repositories."""
        taqasta = {
            "extensions": [{"Ext1": {"repository": "https://github.com/taqasta/ext1"}}]
        }

        canasta = {
            "extensions": [{"Ext1": {"repository": "https://github.com/canasta/ext1"}}]
        }

        result = comparer.compare(taqasta, canasta, "master", "main")

        assert "Extensions with different configurations:" in result
        assert "Taqasta repo: https://github.com/taqasta/ext1" in result
        assert "Canasta repo: https://github.com/canasta/ext1" in result

    def test_compare_extensions_different_branches(self, comparer):
        """Test extensions with different branches."""
        taqasta = {
            "extensions": [{"Ext1": {"branch": "master"}}]
        }

        canasta = {
            "extensions": [{"Ext1": {"branch": "develop"}}]
        }

        result = comparer.compare(taqasta, canasta, "master", "main")

        assert "Extensions with different configurations:" in result
        assert "Taqasta branch: master" in result
        assert "Canasta branch: develop" in result

    def test_compare_extensions_different_additional_steps(self, comparer):
        """Test extensions with different additional steps."""
        taqasta = {
            "extensions": [{"Ext1": {"additional steps": ["composer update", "step1"]}}]
        }

        canasta = {
            "extensions": [{"Ext1": {"additional steps": ["composer update", "step2"]}}]
        }

        result = comparer.compare(taqasta, canasta, "master", "main")

        assert "Extensions with different configurations:" in result
        assert "Only in Taqasta: ['step1']" in result
        assert "Only in Canasta: ['step2']" in result

    def test_compare_skins_only_in_taqasta(self, comparer):
        """Test skins present only in Taqasta."""
        taqasta = {
            "skins": [{"Skin1": {"commit": "abc123"}}]
        }

        canasta = {
            "skins": [{"Skin2": {"commit": "def456"}}]
        }

        result = comparer.compare(taqasta, canasta, "master", "main")

        assert "Skins only in Taqasta:" in result
        assert "+ Skin1" in result

    def test_compare_skins_different_commits(self, comparer):
        """Test skins with different commits."""
        taqasta = {
            "skins": [{"Skin1": {"commit": "abc123"}}]
        }

        canasta = {
            "skins": [{"Skin1": {"commit": "def456"}}]
        }

        result = comparer.compare(taqasta, canasta, "master", "main")

        assert "Skins with different configurations:" in result
        assert "~ Skin1:" in result

    def test_compare_packages_only_in_taqasta(self, comparer):
        """Test packages present only in Taqasta."""
        taqasta = {
            "packages": [
                {"name": "mediawiki/package1", "version": "1.0.0"},
                {"name": "mediawiki/package2", "version": "2.0.0"}
            ]
        }

        canasta = {
            "extensions": [{"Package1": {"additional steps": ["composer update"]}}]
        }

        result = comparer.compare(taqasta, canasta, "master", "main")

        assert "Composer packages only in Taqasta:" in result
        assert "+ mediawiki/package2 @ 2.0.0" in result

    def test_compare_packages_only_in_canasta(self, comparer):
        """Test packages present only in Canasta."""
        taqasta = {
            "packages": [{"name": "mediawiki/package1", "version": "1.0.0"}]
        }

        canasta = {
            "extensions": [
                {"Package1": {"additional steps": ["composer update"]}},
                {"Package2": {"additional steps": ["composer update"]}}
            ]
        }

        result = comparer.compare(taqasta, canasta, "master", "main")

        assert "Extensions requiring composer update only in Canasta:" in result
        assert "- package2" in result

    def test_compare_repositories(self, comparer):
        """Test repository comparison."""
        taqasta = {
            "repositories": [
                {"url": "https://github.com/taqasta/repo1"},
                {"url": "https://github.com/taqasta/repo2"}
            ]
        }

        canasta = {
            "extensions": [
                {"Ext1": {"repository": "https://github.com/canasta/repo1"}},
                {"Ext2": {"repository": "https://github.com/canasta/repo3"}}
            ]
        }

        result = comparer.compare(taqasta, canasta, "master", "main")

        assert "Custom repositories only in Taqasta:" in result
        assert "+ https://github.com/taqasta/repo2" in result
        assert "Custom repositories only in Canasta:" in result
        assert "- https://github.com/canasta/repo3" in result

    def test_compare_complex_scenario(self, comparer):
        """Test a complex comparison scenario."""
        taqasta = {
            "extensions": [
                {"AbuseFilter": {"bundled": True, "additional steps": ["composer update"]}},
                {"OnlyInTaqasta": {"commit": "taq123"}},
                {"DifferentCommit": {"commit": "taq456"}}
            ],
            "skins": [
                {"OnlyInTaqastaSkin": {"commit": "skin123"}}
            ],
            "packages": [{"name": "mediawiki/pkg1", "version": "1.0"}],
            "repositories": [{"url": "https://github.com/taqasta/custom"}]
        }

        canasta = {
            "extensions": [
                {"AbuseFilter": {"bundled": True, "additional steps": ["composer update"]}},
                {"OnlyInCanasta": {"commit": "can123"}},
                {"DifferentCommit": {"commit": "can456"}}
            ],
            "skins": [
                {"OnlyInCanastaSkin": {"commit": "skin456"}}
            ]
        }

        result = comparer.compare(taqasta, canasta, "master", "main")

        # Check that all sections are present
        assert "EXTENSIONS:" in result
        assert "SKINS:" in result
        assert "COMPOSER PACKAGES:" in result
        assert "REPOSITORIES:" in result

        # Check specific differences
        assert "+ OnlyInTaqasta" in result
        assert "- OnlyInCanasta" in result
        assert "~ DifferentCommit:" in result
        assert "+ OnlyInTaqastaSkin" in result
        assert "- OnlyInCanastaSkin" in result
        assert "+ mediawiki/pkg1 @ 1.0" in result
        assert "+ https://github.com/taqasta/custom" in result
