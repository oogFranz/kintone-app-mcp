"""
Pytest configuration and shared fixtures.
"""

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from kintone_mcp.config import ConfigManager, KintoneConfig


@pytest.fixture
def test_config_data() -> dict[str, Any]:
    """Provide test configuration data."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / "test_config.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def test_config_file(test_config_data: dict[str, Any]) -> Path:
    """Create temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(test_config_data, f, indent=2, ensure_ascii=False)
        return Path(f.name)


@pytest.fixture
def config_manager(test_config_file: Path) -> ConfigManager:
    """Provide configured ConfigManager instance."""
    return ConfigManager(str(test_config_file))


@pytest.fixture
def kintone_config(config_manager: ConfigManager) -> KintoneConfig:
    """Provide loaded KintoneConfig instance."""
    return config_manager.load_config()


@pytest.fixture
def sample_record_data() -> dict[str, Any]:
    """Provide sample record data for testing."""
    return {
        "title": "テストタスク",
        "description": "これはテスト用のタスクです。",
        "priority": "高",
        "due_date": "2025-12-31",
        "assignee": "test_user",
        "cost": 1000.50,
    }


@pytest.fixture
def sample_kintone_record() -> dict[str, Any]:
    """Provide sample Kintone API response format record."""
    return {
        "$id": {"type": "__ID__", "value": "123"},
        "$revision": {"type": "__REVISION__", "value": "1"},
        "title": {"type": "SINGLE_LINE_TEXT", "value": "テストタスク"},
        "description": {"type": "MULTI_LINE_TEXT", "value": "これはテスト用のタスクです。"},
        "priority": {"type": "DROP_DOWN", "value": "高"},
        "due_date": {"type": "DATE", "value": "2025-12-31"},
        "assignee": {"type": "USER_SELECT", "value": [{"code": "test_user", "name": "Test User"}]},
        "cost": {"type": "NUMBER", "value": "1000.5"},
    }


@pytest.fixture
def field_type_mapping() -> dict[str, str]:
    """Provide field code to field type mapping."""
    return {
        "title": "SINGLE_LINE_TEXT",
        "description": "MULTI_LINE_TEXT",
        "priority": "DROP_DOWN",
        "due_date": "DATE",
        "assignee": "USER_SELECT",
        "cost": "NUMBER",
    }
