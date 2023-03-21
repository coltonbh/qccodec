from pathlib import Path

import pytest


@pytest.fixture
def test_data_dir():
    """Test data directory Path"""
    return Path(__file__).parent / "data"


@pytest.fixture
def energy_output(test_data_dir):
    with open(test_data_dir / "energy.out") as f:
        return f.read()
