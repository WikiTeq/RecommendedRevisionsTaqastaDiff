"""Tests for the YAML comparer module for the overall report."""

import pytest
import yaml

from src.comparer import YamlComparer
from src.fetcher import YamlFetcher


class TestRegression:
    """Test cases for YamlComparer."""

    @pytest.fixture
    def comparer(self):
        """Create a YamlComparer instance."""
        return YamlComparer()
 
    def test_compare_regression(self, comparer):
        """Test a complex comparison scenario (full contents)."""
        # Paths are based on run_tests.py being run in the main directory
        TAQASTA_DATA_PATH = 'tests/regression/taqasta.yaml'
        CANASTA_DATA_PATH = 'tests/regression/canasta.yaml'
        EXPECTED_PATH = 'tests/regression/expected.txt'

        with open(TAQASTA_DATA_PATH, 'r') as f:
            taqasta = yaml.safe_load(f)
        with open(CANASTA_DATA_PATH, 'r') as f:
            canasta = yaml.safe_load(f)

        mw_version = YamlFetcher._extract_version_from_yaml(taqasta)
        result = comparer.compare(taqasta, canasta, "master", "main", mw_version)

        with open(EXPECTED_PATH, 'r') as f:
            expected = f.read()
        assert expected.strip() == result.strip()
