"""
Tests for MCP server functionality.

These tests focus on the MCP protocol implementation and tool execution
logic, using minimal mocking to test actual functionality.
"""

from unittest.mock import AsyncMock, patch

import pytest

from kintone_mcp.kintone_client import KintoneClient, KintoneError
from kintone_mcp.server import handle_call_tool, handle_list_resources, handle_list_tools, handle_read_resource


class TestMCPServerTools:
    """Test MCP server tool functionality."""

    @pytest.mark.asyncio
    async def test_handle_list_tools(self):
        """Test listing available MCP tools."""
        tools = await handle_list_tools()

        assert len(tools) == 7
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "get_app_info",
            "get_records",
            "get_record",
            "create_record",
            "update_record",
            "delete_record",
            "search_records",
        ]

        for expected_tool in expected_tools:
            assert expected_tool in tool_names

        # Check tool properties
        get_app_info_tool = next(t for t in tools if t.name == "get_app_info")
        assert "Get information about the configured Kintone app" in get_app_info_tool.description
        assert get_app_info_tool.inputSchema["type"] == "object"
        assert get_app_info_tool.inputSchema["required"] == []

        # Check tool with parameters
        get_records_tool = next(t for t in tools if t.name == "get_records")
        assert "query" in get_records_tool.inputSchema["properties"]
        assert "limit" in get_records_tool.inputSchema["properties"]
        assert get_records_tool.inputSchema["properties"]["limit"]["type"] == "integer"

    @pytest.mark.asyncio
    async def test_handle_list_resources_success(self, kintone_config):
        """Test listing MCP resources successfully."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.get_app_info.return_value = {"appId": "123", "name": "Test App", "description": "Test application"}

        # Mock global variables
        with patch("kintone_mcp.server.kintone_client", mock_client):
            with patch("kintone_mcp.server.config_manager") as mock_config_manager:
                mock_config_manager.config = kintone_config

                resources = await handle_list_resources()

                assert len(resources) == 1
                resource = resources[0]
                assert resource.name == "Kintone App: Test App"
                assert str(resource.uri) == "kintone://app/123"
                assert kintone_config.app_description in resource.description
                assert resource.mimeType == "application/json"

    @pytest.mark.asyncio
    async def test_handle_list_resources_no_client(self):
        """Test listing resources when client is not initialized."""
        with patch("kintone_mcp.server.kintone_client", None):
            resources = await handle_list_resources()
            assert resources == []

    @pytest.mark.asyncio
    async def test_handle_list_resources_api_error(self, kintone_config):
        """Test listing resources when API call fails."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.get_app_info.side_effect = Exception("API Error")

        with patch("kintone_mcp.server.kintone_client", mock_client):
            with patch("kintone_mcp.server.config_manager") as mock_config_manager:
                mock_config_manager.config = kintone_config

                resources = await handle_list_resources()
                assert resources == []

    @pytest.mark.asyncio
    async def test_handle_read_resource_success(self, kintone_config):
        """Test reading a resource successfully."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.get_app_info.return_value = {"name": "Test App"}
        mock_client.get_app_fields.return_value = {"title": {"type": "SINGLE_LINE_TEXT"}}

        with patch("kintone_mcp.server.kintone_client", mock_client):
            with patch("kintone_mcp.server.config_manager") as mock_config_manager:
                mock_config_manager.config = kintone_config

                result = await handle_read_resource("kintone://app/123")

                # Should return JSON string
                assert isinstance(result, str)
                assert "Test App" in result
                assert "app_description" in result
                assert kintone_config.app_description in result

    @pytest.mark.asyncio
    async def test_handle_read_resource_invalid_uri(self, kintone_config):
        """Test reading resource with invalid URI."""
        with patch("kintone_mcp.server.kintone_client", AsyncMock()):
            with patch("kintone_mcp.server.config_manager") as mock_config_manager:
                mock_config_manager.config = kintone_config
                with pytest.raises(ValueError, match="Unknown resource URI"):
                    await handle_read_resource("invalid://uri")

    @pytest.mark.asyncio
    async def test_handle_call_tool_get_app_info(self, kintone_config):
        """Test get_app_info tool execution."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.get_app_info.return_value = {"name": "Test App"}
        mock_client.get_app_fields.return_value = {"title": {"type": "SINGLE_LINE_TEXT"}}

        with patch("kintone_mcp.server.kintone_client", mock_client):
            with patch("kintone_mcp.server.config_manager") as mock_config_manager:
                mock_config_manager.config = kintone_config

                result = await handle_call_tool("get_app_info", {})

                assert len(result) == 1
                assert result[0].type == "text"
                assert "App Information:" in result[0].text
                assert "Test App" in result[0].text
                assert kintone_config.app_description in result[0].text

    @pytest.mark.asyncio
    async def test_handle_call_tool_get_records(self):
        """Test get_records tool execution."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.get_records.return_value = {"records": [{"title": "Test Task"}], "totalCount": 1}

        with patch("kintone_mcp.server.kintone_client", mock_client):
            result = await handle_call_tool("get_records", {"query": 'priority = "高"', "limit": 10})

            assert len(result) == 1
            assert result[0].type == "text"
            assert "Records (Total: 1)" in result[0].text
            assert "Test Task" in result[0].text

            mock_client.get_records.assert_called_once_with('priority = "高"', 10)

    @pytest.mark.asyncio
    async def test_handle_call_tool_get_records_default_params(self):
        """Test get_records tool with default parameters."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.get_records.return_value = {"records": [], "totalCount": 0}

        with patch("kintone_mcp.server.kintone_client", mock_client):
            await handle_call_tool("get_records", {})

            mock_client.get_records.assert_called_once_with("", 100)

    @pytest.mark.asyncio
    async def test_handle_call_tool_get_records_limit_cap(self):
        """Test get_records tool with limit cap at 500."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.get_records.return_value = {"records": [], "totalCount": 0}

        with patch("kintone_mcp.server.kintone_client", mock_client):
            await handle_call_tool("get_records", {"limit": 1000})

            # Should cap at 500
            mock_client.get_records.assert_called_once_with("", 500)

    @pytest.mark.asyncio
    async def test_handle_call_tool_get_record(self):
        """Test get_record tool execution."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.get_record.return_value = {"title": "Specific Task"}

        with patch("kintone_mcp.server.kintone_client", mock_client):
            result = await handle_call_tool("get_record", {"record_id": "123"})

            assert len(result) == 1
            assert "Record 123:" in result[0].text
            assert "Specific Task" in result[0].text

            mock_client.get_record.assert_called_once_with("123")

    @pytest.mark.asyncio
    async def test_handle_call_tool_create_record(self):
        """Test create_record tool execution."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.create_record.return_value = {"id": "456", "revision": "1"}

        record_data = {"title": "New Task", "description": "Task description"}

        with patch("kintone_mcp.server.kintone_client", mock_client):
            result = await handle_call_tool("create_record", {"record_data": record_data})

            assert len(result) == 1
            assert "Record created successfully:" in result[0].text
            assert "456" in result[0].text

            mock_client.create_record.assert_called_once_with(record_data)

    @pytest.mark.asyncio
    async def test_handle_call_tool_update_record(self):
        """Test update_record tool execution."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.update_record.return_value = {"revision": "2"}

        record_data = {"title": "Updated Task"}

        with patch("kintone_mcp.server.kintone_client", mock_client):
            result = await handle_call_tool(
                "update_record", {"record_id": "123", "record_data": record_data, "revision": "1"}
            )

            assert "Record 123 updated successfully:" in result[0].text

            mock_client.update_record.assert_called_once_with("123", record_data, "1")

    @pytest.mark.asyncio
    async def test_handle_call_tool_update_record_no_revision(self):
        """Test update_record tool without revision."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.update_record.return_value = {"revision": "2"}

        with patch("kintone_mcp.server.kintone_client", mock_client):
            await handle_call_tool("update_record", {"record_id": "123", "record_data": {"title": "Updated Task"}})

            mock_client.update_record.assert_called_once_with("123", {"title": "Updated Task"}, None)

    @pytest.mark.asyncio
    async def test_handle_call_tool_delete_record(self):
        """Test delete_record tool execution."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.delete_record.return_value = {"revision": "3"}

        with patch("kintone_mcp.server.kintone_client", mock_client):
            result = await handle_call_tool("delete_record", {"record_id": "123", "revision": "2"})

            assert "Record 123 deleted successfully:" in result[0].text

            mock_client.delete_record.assert_called_once_with("123", "2")

    @pytest.mark.asyncio
    async def test_handle_call_tool_search_records(self):
        """Test search_records tool execution."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.search_records.return_value = {"records": [{"title": "Found Task"}], "totalCount": 1}

        with patch("kintone_mcp.server.kintone_client", mock_client):
            result = await handle_call_tool("search_records", {"query": 'status = "完了"', "limit": 25})

            assert 'Search Results (Query: status = "完了", Total: 1)' in result[0].text
            assert "Found Task" in result[0].text

            mock_client.search_records.assert_called_once_with('status = "完了"', 25)

    @pytest.mark.asyncio
    async def test_handle_call_tool_search_records_default_limit(self):
        """Test search_records tool with default limit."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.search_records.return_value = {"records": [], "totalCount": 0}

        with patch("kintone_mcp.server.kintone_client", mock_client):
            await handle_call_tool("search_records", {"query": "test"})

            mock_client.search_records.assert_called_once_with("test", 100)

    @pytest.mark.asyncio
    async def test_handle_call_tool_unknown_tool(self):
        """Test calling unknown tool."""
        with patch("kintone_mcp.server.kintone_client", AsyncMock()):
            result = await handle_call_tool("unknown_tool", {})
            assert len(result) == 1
            assert result[0].type == "text"
            assert "Unknown tool: unknown_tool" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_call_tool_no_client(self):
        """Test calling tool when client is not initialized."""
        with patch("kintone_mcp.server.kintone_client", None):
            with pytest.raises(ValueError, match="Kintone client not initialized"):
                await handle_call_tool("get_app_info", {})

    @pytest.mark.asyncio
    async def test_handle_call_tool_kintone_error(self):
        """Test tool execution with Kintone API error."""
        mock_client = AsyncMock(spec=KintoneClient)
        kintone_error = KintoneError(
            "API Error", status_code=400, response_data={"code": "CB_VA01", "message": "Invalid input"}
        )
        mock_client.get_app_info.side_effect = kintone_error

        with patch("kintone_mcp.server.kintone_client", mock_client):
            result = await handle_call_tool("get_app_info", {})

            assert len(result) == 1
            assert result[0].type == "text"
            assert "Kintone API Error:" in result[0].text
            assert "Status Code: 400" in result[0].text
            assert "Invalid input" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_call_tool_general_error(self):
        """Test tool execution with general error."""
        mock_client = AsyncMock(spec=KintoneClient)
        mock_client.get_app_info.side_effect = Exception("Unexpected error")

        with patch("kintone_mcp.server.kintone_client", mock_client):
            result = await handle_call_tool("get_app_info", {})

            assert len(result) == 1
            assert "Error: Unexpected error" in result[0].text

    @pytest.mark.asyncio
    async def test_app_description_integration_in_tools(self, kintone_config):
        """Test app_description integration in tool descriptions."""
        with patch("kintone_mcp.server.config_manager") as mock_config_manager:
            mock_config_manager.config = kintone_config

            tools = await handle_list_tools()

            get_app_info_tool = next(t for t in tools if t.name == "get_app_info")
            assert kintone_config.app_description in get_app_info_tool.description
