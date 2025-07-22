"""
Field type mapping and value conversion for Kintone fields.
"""

import logging
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)


class FieldMapper:
    """Handles field type mapping and value conversion for Kintone."""

    # Kintone field types
    FIELD_TYPES = {
        "SINGLE_LINE_TEXT": "single_line_text",
        "MULTI_LINE_TEXT": "multi_line_text",
        "RICH_TEXT": "rich_text",
        "NUMBER": "number",
        "CALC": "calc",
        "RADIO_BUTTON": "radio_button",
        "CHECK_BOX": "check_box",
        "MULTI_SELECT": "multi_select",
        "DROP_DOWN": "drop_down",
        "DATE": "date",
        "TIME": "time",
        "DATETIME": "datetime",
        "LINK": "link",
        "FILE": "file",
        "USER_SELECT": "user_select",
        "ORGANIZATION_SELECT": "organization_select",
        "GROUP_SELECT": "group_select",
        "REFERENCE_TABLE": "reference_table",
        "RECORD_NUMBER": "record_number",
        "CREATED_TIME": "created_time",
        "UPDATED_TIME": "updated_time",
        "CREATOR": "creator",
        "MODIFIER": "modifier",
        "STATUS": "status",
        "STATUS_ASSIGNEE": "status_assignee",
        "CATEGORY": "category",
    }

    @staticmethod
    def to_kintone_value(field_type: str, value: Any) -> dict[str, Any]:
        """Convert Python value to Kintone field value format."""
        if value is None:
            return {"value": ""}

        field_type = field_type.upper()

        try:
            if field_type in ["SINGLE_LINE_TEXT", "MULTI_LINE_TEXT", "RICH_TEXT"]:
                return {"value": str(value)}

            elif field_type == "NUMBER":
                return {"value": str(value)}

            elif field_type in ["RADIO_BUTTON", "DROP_DOWN"]:
                return {"value": str(value)}

            elif field_type in ["CHECK_BOX", "MULTI_SELECT"]:
                if isinstance(value, list):
                    return {"value": [str(v) for v in value]}
                else:
                    return {"value": [str(value)]}

            elif field_type == "DATE":
                if isinstance(value, date | datetime):
                    return {"value": value.strftime("%Y-%m-%d")}
                else:
                    return {"value": str(value)}

            elif field_type == "TIME":
                if isinstance(value, datetime):
                    return {"value": value.strftime("%H:%M")}
                else:
                    return {"value": str(value)}

            elif field_type == "DATETIME":
                if isinstance(value, datetime):
                    return {"value": value.isoformat()}
                else:
                    return {"value": str(value)}

            elif field_type == "LINK":
                return {"value": str(value)}

            elif field_type == "USER_SELECT":
                if isinstance(value, list):
                    return {"value": [{"code": str(v)} for v in value]}
                else:
                    return {"value": [{"code": str(value)}]}

            elif field_type in ["ORGANIZATION_SELECT", "GROUP_SELECT"]:
                if isinstance(value, list):
                    return {"value": [{"code": str(v)} for v in value]}
                else:
                    return {"value": [{"code": str(value)}]}

            else:
                # Default: treat as string
                return {"value": str(value)}

        except Exception as e:
            logger.warning(f"Error converting value for field type {field_type}: {e}")
            return {"value": str(value)}

    @staticmethod
    def from_kintone_value(field_type: str, kintone_value: dict[str, Any]) -> Any:
        """Convert Kintone field value to Python value."""
        field_type = field_type.upper()
        value = kintone_value.get("value", "")

        try:
            if field_type in ["SINGLE_LINE_TEXT", "MULTI_LINE_TEXT", "RICH_TEXT"]:
                return str(value) if value else ""

            elif field_type == "NUMBER":
                return float(value) if value else 0.0

            elif field_type in ["RADIO_BUTTON", "DROP_DOWN"]:
                return str(value) if value else ""

            elif field_type in ["CHECK_BOX", "MULTI_SELECT"]:
                if isinstance(value, list):
                    return [str(v) for v in value]
                else:
                    return [str(value)] if value else []

            elif field_type in ["DATE", "TIME", "DATETIME"]:
                return str(value) if value else ""

            elif field_type == "LINK":
                return str(value) if value else ""

            elif field_type == "USER_SELECT":
                if isinstance(value, list):
                    return [user.get("code", "") for user in value]
                else:
                    return []

            elif field_type in ["ORGANIZATION_SELECT", "GROUP_SELECT"]:
                if isinstance(value, list):
                    return [item.get("code", "") for item in value]
                else:
                    return []

            elif field_type == "FILE":
                if isinstance(value, list):
                    return [{"fileKey": f.get("fileKey", ""), "name": f.get("name", "")} for f in value]
                else:
                    return []

            else:
                return str(value) if value else ""

        except Exception as e:
            logger.warning(f"Error converting Kintone value for field type {field_type}: {e}")
            return str(value) if value else ""

    @staticmethod
    def convert_record_to_kintone(
        field_configs: dict[str, str], record_data: dict[str, Any]
    ) -> dict[str, dict[str, Any]]:
        """Convert record data to Kintone format using field configurations."""
        kintone_record = {}

        for field_code, value in record_data.items():
            if field_code in field_configs:
                field_type = field_configs[field_code]
                kintone_record[field_code] = FieldMapper.to_kintone_value(field_type, value)
            else:
                # Unknown field, treat as string
                kintone_record[field_code] = {"value": str(value)}

        return kintone_record

    @staticmethod
    def convert_record_from_kintone(
        field_configs: dict[str, str], kintone_record: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Convert Kintone record to Python format using field configurations."""
        record_data = {}

        for field_code, kintone_value in kintone_record.items():
            if field_code in field_configs:
                field_type = field_configs[field_code]
                record_data[field_code] = FieldMapper.from_kintone_value(field_type, kintone_value)
            else:
                # Unknown field, extract value as-is
                record_data[field_code] = kintone_value.get("value", "")

        return record_data
