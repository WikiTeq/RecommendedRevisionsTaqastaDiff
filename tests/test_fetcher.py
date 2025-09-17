"""Tests for the YAML fetcher module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
import yaml

from src.fetcher import YamlFetcher


class TestYamlFetcher:
    """Test cases for YamlFetcher."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def fetcher(self, temp_cache_dir):
        """Create a YamlFetcher instance with temporary cache."""
        return YamlFetcher(temp_cache_dir)

    @pytest.fixture
    def mock_response(self):
        """Mock response object."""
        mock_resp = Mock()
        mock_resp.raise_for_status.return_value = None
        return mock_resp

    def test_init_creates_cache_dir(self, temp_cache_dir):
        """Test that __init__ creates the cache directory."""
        cache_dir = temp_cache_dir / "test_cache"
        fetcher = YamlFetcher(cache_dir)
        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_get_cache_path(self, fetcher):
        """Test cache path generation."""
        path = fetcher._get_cache_path("repo", "ref", "file.yml")
        assert path.parent == fetcher.cache_dir
        assert path.suffix == ".yaml"
        # Should be deterministic
        path2 = fetcher._get_cache_path("repo", "ref", "file.yml")
        assert path == path2

    @patch('src.fetcher.requests.Session.get')
    def test_fetch_from_github_success(self, mock_get, fetcher, mock_response):
        """Test successful fetch from GitHub."""
        test_yaml = "key: value\n"
        mock_response.text = test_yaml
        mock_get.return_value = mock_response

        result = fetcher._fetch_from_github("owner/repo", "main", "path/file.yml")

        assert result == test_yaml
        mock_get.assert_called_once_with("https://raw.githubusercontent.com/owner/repo/main/path/file.yml", timeout=30)
        mock_response.raise_for_status.assert_called_once()

    @patch('src.fetcher.requests.Session.get')
    def test_fetch_from_github_failure(self, mock_get, fetcher, mock_response):
        """Test fetch failure from GitHub."""
        mock_response.raise_for_status.side_effect = Exception("404")
        mock_get.return_value = mock_response

        with pytest.raises(Exception, match="404"):
            fetcher._fetch_from_github("owner/repo", "main", "path/file.yml")

    def test_load_cached_or_fetch_cached(self, fetcher, temp_cache_dir):
        """Test loading from cache when available."""
        # Pre-populate cache
        cache_path = fetcher._get_cache_path("owner/repo", "ref", "file.yml")
        test_data = {"key": "cached_value"}
        with cache_path.open('w') as f:
            yaml.dump(test_data, f)

        result = fetcher._load_cached_or_fetch("owner/repo", "ref", "file.yml")

        assert result == test_data

    @patch('src.fetcher.requests.Session.get')
    def test_load_cached_or_fetch_fetches_and_caches(self, mock_get, fetcher, mock_response):
        """Test fetching and caching when not in cache."""
        test_yaml = "key: fetched_value\n"
        mock_response.text = test_yaml
        mock_get.return_value = mock_response

        result = fetcher._load_cached_or_fetch("owner/repo", "ref", "file.yml")

        assert result == {"key": "fetched_value"}

        # Check it was cached
        cache_path = fetcher._get_cache_path("owner/repo", "ref", "file.yml")
        assert cache_path.exists()
        with cache_path.open('r') as f:
            cached_data = yaml.safe_load(f)
        assert cached_data == result

    @patch('src.fetcher.requests.Session.get')
    def test_load_cached_or_fetch_corrupted_cache(self, mock_get, fetcher, mock_response):
        """Test handling of corrupted cache."""
        # Create corrupted cache file
        cache_path = fetcher._get_cache_path("owner/repo", "ref", "file.yml")
        with cache_path.open('w') as f:
            f.write("not valid yaml: [unclosed")

        test_yaml = "key: fetched_value\n"
        mock_response.text = test_yaml
        mock_get.return_value = mock_response

        result = fetcher._load_cached_or_fetch("owner/repo", "ref", "file.yml")

        assert result == {"key": "fetched_value"}
        # Should have overwritten corrupted cache
        with cache_path.open('r') as f:
            cached_data = yaml.safe_load(f)
        assert cached_data == result

    @patch('src.fetcher.requests.Session.get')
    def test_load_cached_or_fetch_invalid_yaml(self, mock_get, fetcher, mock_response):
        """Test handling of invalid YAML from server."""
        mock_response.text = "invalid: yaml: content: {"
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="Parse YAML file from"):
            fetcher._load_cached_or_fetch("owner/repo", "ref", "file.yml")

    @patch('src.fetcher.requests.Session.get')
    def test_fetch_from_github_timeout(self, mock_get, fetcher):
        """Test timeout error when fetching from GitHub."""
        mock_get.side_effect = requests.exceptions.Timeout()

        with pytest.raises(RuntimeError, match="Request timed out"):
            fetcher._fetch_from_github("owner/repo", "main", "path/file.yml")

    @patch('src.fetcher.requests.Session.get')
    def test_fetch_from_github_request_exception(self, mock_get, fetcher):
        """Test request exception when fetching from GitHub."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        with pytest.raises(RuntimeError, match="Failed to fetch"):
            fetcher._fetch_from_github("owner/repo", "main", "path/file.yml")

    def test_detect_mediawiki_version_string(self, fetcher):
        """Test MediaWiki version detection from string."""
        taqasta_data = {"version": "1.43.0"}
        version = fetcher._detect_mediawiki_version(taqasta_data)
        assert version == "1.43"

    def test_detect_mediawiki_version_float(self, fetcher):
        """Test MediaWiki version detection from float."""
        taqasta_data = {"mediawiki_version": 1.44}
        version = fetcher._detect_mediawiki_version(taqasta_data)
        assert version == "1.44"

    def test_detect_mediawiki_version_int(self, fetcher):
        """Test MediaWiki version detection from int."""
        taqasta_data = {"mw_version": 143}
        version = fetcher._detect_mediawiki_version(taqasta_data)
        assert version == "143.0"

    def test_detect_mediawiki_version_default(self, fetcher):
        """Test MediaWiki version detection with no version found."""
        taqasta_data = {"extensions": []}
        version = fetcher._detect_mediawiki_version(taqasta_data)
        assert version == "1.43"

    def test_detect_mediawiki_version_multiple_keys(self, fetcher):
        """Test MediaWiki version detection with multiple version keys."""
        taqasta_data = {"version": "1.39.0", "mediawiki_version": "1.44.0"}
        version = fetcher._detect_mediawiki_version(taqasta_data)
        assert version == "1.39"  # Should use first found key

    @patch('src.fetcher.YamlFetcher._load_cached_or_fetch')
    def test_fetch_canasta_revisions_with_version(self, mock_load, fetcher):
        """Test fetching Canasta revisions with version detection."""
        taqasta_data = {"version": "1.44.0"}
        mock_load.return_value = {"extensions": []}

        result = fetcher.fetch_canasta_revisions("main", taqasta_data)

        # Should fetch 1.44.yaml
        mock_load.assert_called_once_with(
            repo="CanastaWiki/RecommendedRevisions",
            ref="main",
            file_path="1.44.yaml"
        )
        assert result == {"extensions": []}

    @patch('src.fetcher.YamlFetcher._load_cached_or_fetch')
    def test_fetch_canasta_revisions_without_version(self, mock_load, fetcher):
        """Test fetching Canasta revisions without version data."""
        mock_load.return_value = {"extensions": []}

        result = fetcher.fetch_canasta_revisions("main")

        # Should default to 1.43.yaml
        mock_load.assert_called_once_with(
            repo="CanastaWiki/RecommendedRevisions",
            ref="main",
            file_path="1.43.yaml"
        )
        assert result == {"extensions": []}

    @patch('src.fetcher.YamlFetcher._load_cached_or_fetch')
    def test_fetch_taqasta_values(self, mock_load, fetcher):
        """Test fetching Taqasta values."""
        mock_load.return_value = {"extensions": []}

        result = fetcher.fetch_taqasta_values("master")

        mock_load.assert_called_once_with(
            repo="WikiTeq/Taqasta",
            ref="master",
            file_path="values.yml"
        )
        assert result == {"extensions": []}

    @patch('src.fetcher.YamlFetcher._load_cached_or_fetch')
    def test_fetch_canasta_revisions(self, mock_load, fetcher):
        """Test fetching Canasta revisions."""
        mock_load.return_value = {"extensions": []}

        result = fetcher.fetch_canasta_revisions("main")

        mock_load.assert_called_once_with(
            repo="CanastaWiki/RecommendedRevisions",
            ref="main",
            file_path="1.43.yaml"
        )
        assert result == {"extensions": []}

    def test_init_cache_dir_error(self, temp_cache_dir):
        """Test that __init__ handles cache directory creation errors."""
        # Create a file with the same name as the cache directory
        cache_dir = temp_cache_dir / "test_cache"
        cache_dir.touch()  # Create a file instead of directory

        with pytest.raises(RuntimeError, match="Cannot create cache directory"):
            YamlFetcher(cache_dir)

    @patch('src.fetcher.requests.Session.get')
    def test_fetch_from_github_timeout(self, mock_get, fetcher, mock_response):
        """Test fetch timeout handling."""
        mock_get.side_effect = Exception("Timeout")

        with pytest.raises(Exception, match="Timeout"):
            fetcher._fetch_from_github("owner/repo", "main", "path/file.yml")

    @patch('src.fetcher.requests.Session.get')
    def test_load_cached_or_fetch_network_error(self, mock_get, fetcher, mock_response):
        """Test handling of network errors during fetch."""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            fetcher._load_cached_or_fetch("owner/repo", "ref", "file.yml")
