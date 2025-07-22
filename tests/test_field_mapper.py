"""
Tests for field type mapping functionality.
"""

from datetime import date, datetime

from kintone_mcp.field_mapper import FieldMapper


class TestFieldMapper:
    """Test FieldMapper class functionality."""

    def test_to_kintone_value_single_line_text(self):
        """Test conversion to SINGLE_LINE_TEXT format."""
        result = FieldMapper.to_kintone_value("SINGLE_LINE_TEXT", "Hello World")
        assert result == {"value": "Hello World"}

        # Test None value
        result = FieldMapper.to_kintone_value("SINGLE_LINE_TEXT", None)
        assert result == {"value": ""}

    def test_to_kintone_value_multi_line_text(self):
        """Test conversion to MULTI_LINE_TEXT format."""
        text = "Line 1\nLine 2\nLine 3"
        result = FieldMapper.to_kintone_value("MULTI_LINE_TEXT", text)
        assert result == {"value": text}

    def test_to_kintone_value_number(self):
        """Test conversion to NUMBER format."""
        result = FieldMapper.to_kintone_value("NUMBER", 123.45)
        assert result == {"value": "123.45"}

        result = FieldMapper.to_kintone_value("NUMBER", 100)
        assert result == {"value": "100"}

    def test_to_kintone_value_dropdown_radio(self):
        """Test conversion to DROP_DOWN and RADIO_BUTTON formats."""
        result = FieldMapper.to_kintone_value("DROP_DOWN", "Option 1")
        assert result == {"value": "Option 1"}

        result = FieldMapper.to_kintone_value("RADIO_BUTTON", "Option A")
        assert result == {"value": "Option A"}

    def test_to_kintone_value_checkbox_multiselect(self):
        """Test conversion to CHECK_BOX and MULTI_SELECT formats."""
        # List input
        result = FieldMapper.to_kintone_value("CHECK_BOX", ["Option 1", "Option 2"])
        assert result == {"value": ["Option 1", "Option 2"]}

        # Single value input
        result = FieldMapper.to_kintone_value("MULTI_SELECT", "Single Option")
        assert result == {"value": ["Single Option"]}

    def test_to_kintone_value_date(self):
        """Test conversion to DATE format."""
        # Date object
        test_date = date(2025, 12, 31)
        result = FieldMapper.to_kintone_value("DATE", test_date)
        assert result == {"value": "2025-12-31"}

        # Datetime object
        test_datetime = datetime(2025, 12, 31, 15, 30, 0)
        result = FieldMapper.to_kintone_value("DATE", test_datetime)
        assert result == {"value": "2025-12-31"}

        # String input
        result = FieldMapper.to_kintone_value("DATE", "2025-12-31")
        assert result == {"value": "2025-12-31"}

    def test_to_kintone_value_time(self):
        """Test conversion to TIME format."""
        # Datetime object
        test_datetime = datetime(2025, 12, 31, 15, 30, 0)
        result = FieldMapper.to_kintone_value("TIME", test_datetime)
        assert result == {"value": "15:30"}

        # String input
        result = FieldMapper.to_kintone_value("TIME", "09:45")
        assert result == {"value": "09:45"}

    def test_to_kintone_value_datetime(self):
        """Test conversion to DATETIME format."""
        # Datetime object
        test_datetime = datetime(2025, 12, 31, 15, 30, 45)
        result = FieldMapper.to_kintone_value("DATETIME", test_datetime)
        assert result == {"value": "2025-12-31T15:30:45"}

        # String input
        result = FieldMapper.to_kintone_value("DATETIME", "2025-12-31T10:00:00")
        assert result == {"value": "2025-12-31T10:00:00"}

    def test_to_kintone_value_user_select(self):
        """Test conversion to USER_SELECT format."""
        # List input
        result = FieldMapper.to_kintone_value("USER_SELECT", ["user1", "user2"])
        assert result == {"value": [{"code": "user1"}, {"code": "user2"}]}

        # Single value input
        result = FieldMapper.to_kintone_value("USER_SELECT", "user1")
        assert result == {"value": [{"code": "user1"}]}

    def test_to_kintone_value_organization_group_select(self):
        """Test conversion to ORGANIZATION_SELECT and GROUP_SELECT formats."""
        # ORGANIZATION_SELECT
        result = FieldMapper.to_kintone_value("ORGANIZATION_SELECT", ["org1", "org2"])
        assert result == {"value": [{"code": "org1"}, {"code": "org2"}]}

        # GROUP_SELECT
        result = FieldMapper.to_kintone_value("GROUP_SELECT", "group1")
        assert result == {"value": [{"code": "group1"}]}

    def test_to_kintone_value_unknown_type(self):
        """Test conversion with unknown field type."""
        result = FieldMapper.to_kintone_value("UNKNOWN_TYPE", "test value")
        assert result == {"value": "test value"}

    def test_from_kintone_value_single_line_text(self):
        """Test conversion from SINGLE_LINE_TEXT format."""
        kintone_value = {"value": "Hello World"}
        result = FieldMapper.from_kintone_value("SINGLE_LINE_TEXT", kintone_value)
        assert result == "Hello World"

        # Empty value
        kintone_value = {"value": ""}
        result = FieldMapper.from_kintone_value("SINGLE_LINE_TEXT", kintone_value)
        assert result == ""

    def test_from_kintone_value_number(self):
        """Test conversion from NUMBER format."""
        kintone_value = {"value": "123.45"}
        result = FieldMapper.from_kintone_value("NUMBER", kintone_value)
        assert result == 123.45

        # Integer
        kintone_value = {"value": "100"}
        result = FieldMapper.from_kintone_value("NUMBER", kintone_value)
        assert result == 100.0

        # Empty value
        kintone_value = {"value": ""}
        result = FieldMapper.from_kintone_value("NUMBER", kintone_value)
        assert result == 0.0

    def test_from_kintone_value_checkbox_multiselect(self):
        """Test conversion from CHECK_BOX and MULTI_SELECT formats."""
        # List value
        kintone_value = {"value": ["Option 1", "Option 2"]}
        result = FieldMapper.from_kintone_value("CHECK_BOX", kintone_value)
        assert result == ["Option 1", "Option 2"]

        # Single value (shouldn't happen but handle gracefully)
        kintone_value = {"value": "Single Option"}
        result = FieldMapper.from_kintone_value("MULTI_SELECT", kintone_value)
        assert result == ["Single Option"]

        # Empty value
        kintone_value = {"value": ""}
        result = FieldMapper.from_kintone_value("CHECK_BOX", kintone_value)
        assert result == []

    def test_from_kintone_value_user_select(self):
        """Test conversion from USER_SELECT format."""
        # List of users
        kintone_value = {"value": [{"code": "user1", "name": "User 1"}, {"code": "user2", "name": "User 2"}]}
        result = FieldMapper.from_kintone_value("USER_SELECT", kintone_value)
        assert result == ["user1", "user2"]

        # Empty value
        kintone_value = {"value": []}
        result = FieldMapper.from_kintone_value("USER_SELECT", kintone_value)
        assert result == []

    def test_from_kintone_value_organization_group_select(self):
        """Test conversion from ORGANIZATION_SELECT and GROUP_SELECT formats."""
        # ORGANIZATION_SELECT
        kintone_value = {"value": [{"code": "org1", "name": "Organization 1"}]}
        result = FieldMapper.from_kintone_value("ORGANIZATION_SELECT", kintone_value)
        assert result == ["org1"]

        # GROUP_SELECT
        kintone_value = {"value": [{"code": "group1", "name": "Group 1"}]}
        result = FieldMapper.from_kintone_value("GROUP_SELECT", kintone_value)
        assert result == ["group1"]

    def test_from_kintone_value_file(self):
        """Test conversion from FILE format."""
        kintone_value = {
            "value": [
                {"fileKey": "file123", "name": "document.pdf", "size": "1024"},
                {"fileKey": "file456", "name": "image.jpg", "size": "2048"},
            ]
        }
        result = FieldMapper.from_kintone_value("FILE", kintone_value)
        expected = [{"fileKey": "file123", "name": "document.pdf"}, {"fileKey": "file456", "name": "image.jpg"}]
        assert result == expected

    def test_from_kintone_value_unknown_type(self):
        """Test conversion from unknown field type."""
        kintone_value = {"value": "test value"}
        result = FieldMapper.from_kintone_value("UNKNOWN_TYPE", kintone_value)
        assert result == "test value"

    def test_convert_record_to_kintone(self, field_type_mapping, sample_record_data):
        """Test converting record data to Kintone format."""
        result = FieldMapper.convert_record_to_kintone(field_type_mapping, sample_record_data)

        assert result["title"] == {"value": "テストタスク"}
        assert result["description"] == {"value": "これはテスト用のタスクです。"}
        assert result["priority"] == {"value": "高"}
        assert result["due_date"] == {"value": "2025-12-31"}
        assert result["assignee"] == {"value": [{"code": "test_user"}]}
        assert result["cost"] == {"value": "1000.5"}

    def test_convert_record_to_kintone_unknown_field(self):
        """Test converting record with unknown field type."""
        field_types = {"known_field": "SINGLE_LINE_TEXT"}
        record_data = {"known_field": "value1", "unknown_field": "value2"}

        result = FieldMapper.convert_record_to_kintone(field_types, record_data)

        assert result["known_field"] == {"value": "value1"}
        assert result["unknown_field"] == {"value": "value2"}  # Treated as string

    def test_convert_record_from_kintone(self, field_type_mapping, sample_kintone_record):
        """Test converting Kintone record to Python format."""
        result = FieldMapper.convert_record_from_kintone(field_type_mapping, sample_kintone_record)

        assert result["title"] == "テストタスク"
        assert result["description"] == "これはテスト用のタスクです。"
        assert result["priority"] == "高"
        assert result["due_date"] == "2025-12-31"
        assert result["assignee"] == ["test_user"]
        assert result["cost"] == 1000.5

    def test_convert_record_from_kintone_unknown_field(self):
        """Test converting Kintone record with unknown field type."""
        field_types = {"known_field": "SINGLE_LINE_TEXT"}
        kintone_record = {"known_field": {"value": "known_value"}, "unknown_field": {"value": "unknown_value"}}

        result = FieldMapper.convert_record_from_kintone(field_types, kintone_record)

        assert result["known_field"] == "known_value"
        assert result["unknown_field"] == "unknown_value"  # Value extracted as-is

    def test_field_type_case_insensitive(self):
        """Test that field type matching is case insensitive."""
        # Test lowercase
        result = FieldMapper.to_kintone_value("single_line_text", "test")
        assert result == {"value": "test"}

        # Test mixed case
        result = FieldMapper.from_kintone_value("Single_Line_Text", {"value": "test"})
        assert result == "test"

    def test_error_handling_in_conversion(self):
        """Test error handling during conversion."""
        # This should not raise an exception, but log a warning
        result = FieldMapper.to_kintone_value("DATE", "invalid-date")
        assert result == {"value": "invalid-date"}  # Falls back to string conversion

        result = FieldMapper.from_kintone_value("NUMBER", {"value": "not-a-number"})
        # Should handle ValueError gracefully and return string
        assert isinstance(result, str)
