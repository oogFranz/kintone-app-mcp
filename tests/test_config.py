"""
Tests for configuration management.
"""

import json
import tempfile

import pytest

from kintone_mcp.config import ConfigManager, FieldConfig, KintoneConfig


class TestFieldConfig:
    """Test FieldConfig dataclass."""

    def test_from_dict(self):
        """Test creating FieldConfig from dictionary."""
        data = {
            "field_name": "タイトル",
            "field_type": "SINGLE_LINE_TEXT",
            "field_code": "title",
            "description": "Task title",
        }

        field = FieldConfig.from_dict(data)

        assert field.field_name == "タイトル"
        assert field.field_type == "SINGLE_LINE_TEXT"
        assert field.field_code == "title"
        assert field.description == "Task title"


class TestKintoneConfig:
    """Test KintoneConfig dataclass."""

    def test_from_dict_complete(self, test_config_data):
        """Test creating KintoneConfig from complete dictionary."""
        config = KintoneConfig.from_dict(test_config_data)

        assert config.domain == "test-domain.cybozu.com"
        assert config.app_id == "123"
        assert config.api_token == "test-api-token-12345"
        assert config.api_permissions == ["record_read", "record_create", "record_update", "record_delete"]
        assert config.app_code == "test_app"
        assert config.app_description == "Test application for unit testing"
        assert len(config.fields) == 6

    def test_from_dict_minimal(self):
        """Test creating KintoneConfig from minimal dictionary."""
        minimal_data = {
            "kintone": {"domain": "test.cybozu.com", "app_id": "456", "api_token": "minimal-token"},
            "fields": [],
        }

        config = KintoneConfig.from_dict(minimal_data)

        assert config.domain == "test.cybozu.com"
        assert config.app_id == "456"
        assert config.api_token == "minimal-token"
        assert config.api_permissions == []
        assert config.app_code == ""
        assert config.app_description == ""
        assert len(config.fields) == 0

    def test_base_url_property(self, kintone_config):
        """Test base_url property generation."""
        assert kintone_config.base_url == "https://test-domain.cybozu.com/k/v1"

    def test_get_field_by_code(self, kintone_config):
        """Test getting field configuration by code."""
        # Existing field
        title_field = kintone_config.get_field_by_code("title")
        assert title_field is not None
        assert title_field.field_name == "タイトル"
        assert title_field.field_type == "SINGLE_LINE_TEXT"

        # Non-existing field
        missing_field = kintone_config.get_field_by_code("nonexistent")
        assert missing_field is None

    def test_validate_success(self, kintone_config):
        """Test successful validation."""
        # Should not raise any exception
        kintone_config.validate()

    def test_validate_missing_domain(self, test_config_data):
        """Test validation with missing domain."""
        test_config_data["kintone"]["domain"] = ""
        config = KintoneConfig.from_dict(test_config_data)

        with pytest.raises(ValueError, match="Domain is required"):
            config.validate()

    def test_validate_missing_app_id(self, test_config_data):
        """Test validation with missing app_id."""
        test_config_data["kintone"]["app_id"] = ""
        config = KintoneConfig.from_dict(test_config_data)

        with pytest.raises(ValueError, match="App ID is required"):
            config.validate()

    def test_validate_missing_api_token(self, test_config_data):
        """Test validation with missing api_token."""
        test_config_data["kintone"]["api_token"] = ""
        config = KintoneConfig.from_dict(test_config_data)

        with pytest.raises(ValueError, match="API token is required"):
            config.validate()

    def test_validate_duplicate_field_codes(self, test_config_data):
        """Test validation with duplicate field codes."""
        # Add duplicate field code
        duplicate_field = {
            "field_name": "重複タイトル",
            "field_type": "SINGLE_LINE_TEXT",
            "field_code": "title",  # Duplicate of existing field
            "description": "Duplicate field",
        }
        test_config_data["fields"].append(duplicate_field)

        config = KintoneConfig.from_dict(test_config_data)

        with pytest.raises(ValueError, match="Field codes must be unique"):
            config.validate()


class TestConfigManager:
    """Test ConfigManager class."""

    def test_load_config_success(self, config_manager):
        """Test successful configuration loading."""
        config = config_manager.load_config()

        assert isinstance(config, KintoneConfig)
        assert config.domain == "test-domain.cybozu.com"
        assert config.app_id == "123"
        assert len(config.fields) == 6

    def test_load_config_file_not_found(self):
        """Test loading non-existent configuration file."""
        manager = ConfigManager("nonexistent.json")

        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            manager.load_config()

    def test_load_config_invalid_json(self):
        """Test loading invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            f.flush()

            manager = ConfigManager(f.name)

            with pytest.raises(ValueError, match="Invalid JSON in configuration file"):
                manager.load_config()

    def test_load_config_missing_required_key(self):
        """Test loading configuration with missing required key."""
        invalid_data = {
            "kintone": {
                # Missing required fields
                "domain": "test.cybozu.com"
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(invalid_data, f)
            f.flush()

            manager = ConfigManager(f.name)

            with pytest.raises(ValueError, match="Missing required configuration key"):
                manager.load_config()

    def test_config_property(self, config_manager):
        """Test config property caching."""
        # First access should load config
        config1 = config_manager.config
        assert isinstance(config1, KintoneConfig)

        # Second access should return cached config
        config2 = config_manager.config
        assert config1 is config2

    def test_reload_config(self, config_manager, test_config_file):
        """Test configuration reloading."""
        # Load initial config
        config1 = config_manager.load_config()
        assert config1.app_id == "123"

        # Modify config file
        with open(test_config_file, encoding="utf-8") as f:
            data = json.load(f)
        data["kintone"]["app_id"] = "456"
        with open(test_config_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # Reload config
        config2 = config_manager.reload_config()
        assert config2.app_id == "456"
        assert config1 is not config2
