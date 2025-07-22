"""
Configuration management for Kintone MCP Server.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class FieldConfig:
    """Configuration for a Kintone field."""

    field_name: str
    field_type: str
    field_code: str
    description: str

    @classmethod
    def from_dict(cls, data: dict) -> "FieldConfig":
        """Create FieldConfig from dictionary."""
        return cls(
            field_name=data["field_name"],
            field_type=data["field_type"],
            field_code=data["field_code"],
            description=data["description"],
        )


@dataclass
class KintoneConfig:
    """Configuration for Kintone connection."""

    domain: str
    app_id: str
    api_token: str
    api_permissions: list[str]
    app_code: str
    app_description: str
    fields: list[FieldConfig]

    @classmethod
    def from_dict(cls, data: dict) -> "KintoneConfig":
        """Create KintoneConfig from dictionary."""
        kintone_data = data["kintone"]
        fields_data = data.get("fields", [])

        fields = [FieldConfig.from_dict(field) for field in fields_data]

        return cls(
            domain=kintone_data["domain"],
            app_id=kintone_data["app_id"],
            api_token=kintone_data["api_token"],
            api_permissions=kintone_data.get("api_permissions", []),
            app_code=kintone_data.get("app_code", ""),
            app_description=kintone_data.get("app_description", ""),
            fields=fields,
        )

    @property
    def base_url(self) -> str:
        """Get base URL for Kintone API."""
        return f"https://{self.domain}/k/v1"

    def get_field_by_code(self, field_code: str) -> FieldConfig | None:
        """Get field configuration by field code."""
        for field in self.fields:
            if field.field_code == field_code:
                return field
        return None

    def validate(self) -> None:
        """Validate configuration."""
        if not self.domain:
            raise ValueError("Domain is required")
        if not self.app_id:
            raise ValueError("App ID is required")
        if not self.api_token:
            raise ValueError("API token is required")

        # Validate field codes are unique
        field_codes = [field.field_code for field in self.fields]
        if len(field_codes) != len(set(field_codes)):
            raise ValueError("Field codes must be unique")


class ConfigManager:
    """Manager for loading and validating configuration."""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._config: KintoneConfig | None = None

    def load_config(self) -> KintoneConfig:
        """Load configuration from file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)

            config = KintoneConfig.from_dict(data)
            config.validate()

            self._config = config
            logger.info(f"Configuration loaded from {self.config_path}")
            return config

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}") from e
        except KeyError as e:
            raise ValueError(f"Missing required configuration key: {e}") from e
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}") from e

    @property
    def config(self) -> KintoneConfig:
        """Get loaded configuration."""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def reload_config(self) -> KintoneConfig:
        """Reload configuration from file."""
        self._config = None
        return self.load_config()
