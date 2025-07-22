"""
Tests for Kintone API client functionality.

Note: These tests use a test server or mocked HTTP responses to avoid
dependency on a real Kintone instance while still testing the actual logic.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from kintone_mcp.kintone_client import KintoneClient, KintoneError


class TestKintoneClient:
    """Test KintoneClient functionality."""

    @pytest.fixture
    def kintone_client(self, kintone_config):
        """Create KintoneClient instance."""
        return KintoneClient(kintone_config)

    def test_initialization(self, kintone_client, kintone_config):
        """Test client initialization."""
        assert kintone_client.config == kintone_config
        assert kintone_client.base_url == "https://test-domain.cybozu.com/k/v1"
        assert kintone_client.headers["X-Cybozu-API-Token"] == "test-api-token-12345"
        assert kintone_client.headers["Content-Type"] == "application/json"

        # Check field type mapping
        assert kintone_client.field_types["title"] == "SINGLE_LINE_TEXT"
        assert kintone_client.field_types["priority"] == "DROP_DOWN"
        assert len(kintone_client.field_types) == 6

    @pytest.mark.asyncio
    async def test_request_get_success(self, kintone_client):
        """Test successful GET request."""
        mock_response_data = {"test": "data"}

        with patch("httpx.AsyncClient") as mock_client_class:
            # Create the client instance that will be returned by the context manager
            mock_client = AsyncMock()

            # Mock the context manager behavior properly
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_client
            mock_context_manager.__aexit__.return_value = None
            mock_client_class.return_value = mock_context_manager

            # Create a proper mock response with fixed attributes
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.get = AsyncMock(return_value=mock_response)

            result = await kintone_client._request("GET", "test.json", params={"param": "value"})

            assert result == mock_response_data
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args.kwargs["params"] == {"param": "value"}

    @pytest.mark.asyncio
    async def test_request_post_success(self, kintone_client):
        """Test successful POST request."""
        mock_response_data = {"id": "123"}
        request_data = {"record": {"field": {"value": "test"}}}

        with patch("httpx.AsyncClient") as mock_client_class:
            # Create the client instance that will be returned by the context manager
            mock_client = AsyncMock()

            # Mock the context manager behavior properly
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_client
            mock_context_manager.__aexit__.return_value = None
            mock_client_class.return_value = mock_context_manager

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_client.post = AsyncMock(return_value=mock_response)

            result = await kintone_client._request("POST", "record.json", request_data)

            assert result == mock_response_data
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args.kwargs["json"] == request_data

    @pytest.mark.asyncio
    async def test_request_http_error(self, kintone_client):
        """Test HTTP error handling."""
        with patch("httpx.AsyncClient") as mock_client_class:
            # Create the client instance that will be returned by the context manager
            mock_client = AsyncMock()

            # Mock the context manager behavior properly
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_client
            mock_context_manager.__aexit__.return_value = None
            mock_client_class.return_value = mock_context_manager

            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "code": "CB_VA01",
                "message": "Missing or invalid input.",
                "id": "test-error",
            }
            mock_client.get = AsyncMock(return_value=mock_response)

            with pytest.raises(KintoneError) as exc_info:
                await kintone_client._request("GET", "test.json")

            assert "Missing or invalid input." in str(exc_info.value)
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_request_network_error(self, kintone_client):
        """Test network error handling."""
        with patch("httpx.AsyncClient") as mock_client_class:
            # Create the client instance that will be returned by the context manager
            mock_client = AsyncMock()

            # Mock the context manager behavior properly
            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value = mock_client
            mock_context_manager.__aexit__.return_value = None
            mock_client_class.return_value = mock_context_manager

            mock_client.get.side_effect = httpx.RequestError("Connection failed")

            with pytest.raises(KintoneError) as exc_info:
                await kintone_client._request("GET", "test.json")

            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_app_info(self, kintone_client):
        """Test getting app information."""
        mock_response = {"appId": "123", "name": "Test App", "description": "Test application"}

        with patch.object(kintone_client, "_request", return_value=mock_response) as mock_request:
            result = await kintone_client.get_app_info()

            assert result == mock_response
            mock_request.assert_called_once_with("GET", "app.json", params={"id": "123"})

    @pytest.mark.asyncio
    async def test_get_app_fields(self, kintone_client):
        """Test getting app fields."""
        mock_response = {
            "properties": {
                "title": {"type": "SINGLE_LINE_TEXT", "label": "Title"},
                "description": {"type": "MULTI_LINE_TEXT", "label": "Description"},
            }
        }

        with patch.object(kintone_client, "_request", return_value=mock_response) as mock_request:
            result = await kintone_client.get_app_fields()

            assert result == mock_response["properties"]
            mock_request.assert_called_once_with("GET", "app/form/fields.json", params={"app": "123"})

    @pytest.mark.asyncio
    async def test_get_records(self, kintone_client):
        """Test getting records."""
        mock_response = {
            "records": [{"$id": {"value": "1"}, "$revision": {"value": "1"}, "title": {"value": "Test Task"}}],
            "totalCount": 1,
        }

        with patch.object(kintone_client, "_request", return_value=mock_response) as mock_request:
            result = await kintone_client.get_records('priority = "高"', 50)

            assert len(result["records"]) == 1
            assert result["totalCount"] == 1
            assert result["records"][0]["title"] == "Test Task"
            assert result["records"][0]["$id"] == "1"

            mock_request.assert_called_once_with(
                "GET", "records.json", params={"app": "123", "totalCount": True, "query": 'priority = "高" limit 50'}
            )

    @pytest.mark.asyncio
    async def test_get_records_no_query(self, kintone_client):
        """Test getting records without query."""
        mock_response = {"records": [], "totalCount": 0}

        with patch.object(kintone_client, "_request", return_value=mock_response) as mock_request:
            result = await kintone_client.get_records()

            assert result["records"] == []
            mock_request.assert_called_once_with(
                "GET", "records.json", params={"app": "123", "totalCount": True, "query": "limit 100"}
            )

    @pytest.mark.asyncio
    async def test_get_record(self, kintone_client):
        """Test getting a single record."""
        mock_response = {
            "record": {"$id": {"value": "123"}, "$revision": {"value": "1"}, "title": {"value": "Test Task"}}
        }

        with patch.object(kintone_client, "_request", return_value=mock_response) as mock_request:
            result = await kintone_client.get_record("123")

            assert result["title"] == "Test Task"
            assert result["$id"] == "123"

            mock_request.assert_called_once_with("GET", "record.json", params={"app": "123", "id": "123"})

    @pytest.mark.asyncio
    async def test_create_record(self, kintone_client):
        """Test creating a record."""
        record_data = {"title": "New Task", "description": "Task description", "priority": "高"}
        mock_response = {"id": "456", "revision": "1"}

        with patch.object(kintone_client, "_request", return_value=mock_response) as mock_request:
            result = await kintone_client.create_record(record_data)

            assert result == {"id": "456", "revision": "1"}

            # Verify the request was made with proper Kintone format
            mock_request.assert_called_once_with(
                "POST",
                "record.json",
                {
                    "app": "123",
                    "record": {
                        "title": {"value": "New Task"},
                        "description": {"value": "Task description"},
                        "priority": {"value": "高"},
                    },
                },
            )

    @pytest.mark.asyncio
    async def test_update_record(self, kintone_client):
        """Test updating a record."""
        record_data = {"title": "Updated Task"}
        mock_response = {"revision": "2"}

        with patch.object(kintone_client, "_request", return_value=mock_response) as mock_request:
            result = await kintone_client.update_record("123", record_data, "1")

            assert result == {"revision": "2"}

            mock_request.assert_called_once_with(
                "PUT",
                "record.json",
                {"app": "123", "id": "123", "record": {"title": {"value": "Updated Task"}}, "revision": "1"},
            )

    @pytest.mark.asyncio
    async def test_update_record_no_revision(self, kintone_client):
        """Test updating a record without revision."""
        record_data = {"title": "Updated Task"}
        mock_response = {"revision": "2"}

        with patch.object(kintone_client, "_request", return_value=mock_response) as mock_request:
            result = await kintone_client.update_record("123", record_data)

            assert result == {"revision": "2"}

            # Should not include revision in request
            call_data = mock_request.call_args[0][2]
            assert "revision" not in call_data

    @pytest.mark.asyncio
    async def test_delete_record(self, kintone_client):
        """Test deleting a record."""
        mock_response = {"revision": "3"}

        with patch.object(kintone_client, "_request", return_value=mock_response) as mock_request:
            result = await kintone_client.delete_record("123", "2")

            assert result == {"revision": "3"}

            mock_request.assert_called_once_with(
                "DELETE", "records.json", {"app": "123", "ids": ["123"], "revisions": ["2"]}
            )

    @pytest.mark.asyncio
    async def test_delete_record_no_revision(self, kintone_client):
        """Test deleting a record without revision."""
        mock_response = {"revision": "3"}

        with patch.object(kintone_client, "_request", return_value=mock_response) as mock_request:
            result = await kintone_client.delete_record("123")

            assert result == {"revision": "3"}

            # Should not include revisions in request
            call_data = mock_request.call_args[0][2]
            assert "revisions" not in call_data

    @pytest.mark.asyncio
    async def test_search_records(self, kintone_client):
        """Test search records method."""
        mock_response = {"records": [], "totalCount": 0}

        with patch.object(kintone_client, "get_records", return_value=mock_response) as mock_get:
            result = await kintone_client.search_records('status = "完了"', 25)

            assert result == mock_response
            mock_get.assert_called_once_with('status = "完了"', 25)

    @pytest.mark.asyncio
    async def test_field_type_integration(self, kintone_client):
        """Test integration with field type mapping."""
        # Test with complex field types
        record_data = {
            "title": "Test Task",
            "assignee": "user1",  # USER_SELECT
            "due_date": "2025-12-31",  # DATE
            "cost": 1500.75,  # NUMBER
        }

        mock_response = {"id": "789", "revision": "1"}

        with patch.object(kintone_client, "_request", return_value=mock_response) as mock_request:
            await kintone_client.create_record(record_data)

            # Verify field type conversion
            call_data = mock_request.call_args[0][2]
            expected_record = {
                "title": {"value": "Test Task"},
                "assignee": {"value": [{"code": "user1"}]},  # USER_SELECT format
                "due_date": {"value": "2025-12-31"},
                "cost": {"value": "1500.75"},  # NUMBER format
            }
            assert call_data["record"] == expected_record


class TestKintoneError:
    """Test KintoneError exception class."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = KintoneError("Test error")
        assert str(error) == "Test error"
        assert error.status_code is None
        assert error.response_data == {}

    def test_error_with_status_code(self):
        """Test error with status code."""
        error = KintoneError("Test error", status_code=400)
        assert error.status_code == 400

    def test_error_with_response_data(self):
        """Test error with response data."""
        response_data = {"code": "CB_VA01", "message": "Invalid input"}
        error = KintoneError("Test error", response_data=response_data)
        assert error.response_data == response_data
