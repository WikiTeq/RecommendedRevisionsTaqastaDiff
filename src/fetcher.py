"""Module for fetching YAML files from GitHub repositories."""

import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

import requests
import yaml


class YamlFetcher:
    """Fetches YAML files from GitHub repositories with caching."""

    # Default timeout for HTTP requests (seconds)
    DEFAULT_TIMEOUT = 30

    # Default MediaWiki version when none is detected
    DEFAULT_MW_VERSION = "1.43"

    def __init__(self, cache_dir: Path):
        """Initialize the fetcher with a cache directory."""
        self.cache_dir = cache_dir
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise RuntimeError(f"Cannot create cache directory {cache_dir}: {e}")

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "yaml-diff-tool/1.0.0"})
        # Default timeout for requests
        self.timeout = self.DEFAULT_TIMEOUT

    def _get_cache_path(self, repo: str, ref: str, file_path: str) -> Path:
        """Generate a cache path for a file."""
        # Create a hash of the repo, ref, and file path for uniqueness
        cache_key = f"{repo}:{ref}:{file_path}"
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        return self.cache_dir / f"{cache_hash}.yaml"

    def _fetch_from_github(self, repo: str, ref: str, file_path: str) -> str:
        """Fetch a file from GitHub."""
        url = f"https://raw.githubusercontent.com/{repo}/{ref}/{file_path}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Request timed out while fetching {url}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to fetch {url}: {e}")

    def _load_cached_or_fetch(self, repo: str, ref: str, file_path: str) -> Dict[str, Any]:
        """Load from cache if available, otherwise fetch and cache."""
        cache_path = self._get_cache_path(repo, ref, file_path)

        # Try to load from cache first
        if cache_path.exists():
            try:
                with cache_path.open("r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except (yaml.YAMLError, IOError):
                # Cache is corrupted, remove it
                cache_path.unlink(missing_ok=True)

        # Fetch from GitHub
        content = self._fetch_from_github(repo, ref, file_path)

        # Parse YAML
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Parse YAML file from {repo}/{ref}/{file_path}: {e}")

        # Cache the parsed data
        with cache_path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        return data

    def fetch_taqasta_values(self, ref: str) -> Dict[str, Any]:
        """Fetch Taqasta's values.yml file."""
        return self._load_cached_or_fetch(repo="WikiTeq/Taqasta", ref=ref, file_path="values.yml")

    def _detect_mediawiki_version(self, taqasta_data: Dict[str, Any]) -> str:
        """Detect MediaWiki version from Taqasta YAML data."""
        return self._extract_version_from_yaml(taqasta_data)

    @staticmethod
    def _extract_version_from_yaml(data: Dict[str, Any]) -> str:
        """Extract MediaWiki version from YAML data.

        Looks for version information in common keys and formats.
        Returns '1.43' as default if no version found.
        """
        # Common patterns: version, mediawiki_version, mw_version, etc.
        version_keys = ["version", "mediawiki_version", "mw_version", "mediawiki"]

        for key in version_keys:
            if key in data:
                version = data[key]
                if isinstance(version, str):
                    # Extract major.minor version (e.g., "1.43" from "1.43.0")
                    version_parts = version.split(".")
                    if len(version_parts) >= 2:
                        return f"{version_parts[0]}.{version_parts[1]}"
                elif isinstance(version, (int, float)):
                    # Convert numeric version to string
                    version_str = str(version)
                    if "." in version_str:
                        return version_str
                    else:
                        # Assume it's a major version, add .0
                        return f"{version_str}.0"

        # Default to default version if no version found
        return YamlFetcher.DEFAULT_MW_VERSION

    def fetch_canasta_revisions(self, ref: str, taqasta_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch Canasta's recommended revisions YAML file for the appropriate MediaWiki version."""
        # Determine the correct YAML file based on MediaWiki version
        if taqasta_data:
            mw_version = self._detect_mediawiki_version(taqasta_data)
        else:
            mw_version = self.DEFAULT_MW_VERSION  # Default fallback

        yaml_file = f"{mw_version}.yaml"

        return self._load_cached_or_fetch(repo="CanastaWiki/RecommendedRevisions", ref=ref, file_path=yaml_file)
