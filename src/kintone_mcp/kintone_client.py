"""
Kintone API Client

Handles communication with Kintone REST API using API token authentication.
"""

import logging
from typing import Any

import httpx

from .config import KintoneConfig
from .field_mapper import FieldMapper

logger = logging.getLogger(__name__)


class KintoneError(Exception):
    """Custom exception for Kintone API errors."""

    def __init__(self, message: str, status_code: int | None = None, response_data: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class KintoneClient:
    """Client for interacting with Kintone REST API."""

    def __init__(self, config: KintoneConfig):
        """
        Initialize Kintone client.

        Args:
            config: Kintone configuration
        """
        self.config = config
        self.base_url = config.base_url

        # Create headers for API token authentication
        self.headers = {"X-Cybozu-API-Token": config.api_token, "Content-Type": "application/json"}

        # Create field type mapping for this app
        self.field_types = {field.field_code: field.field_type for field in config.fields}

    async def _request(
        self, method: str, endpoint: str, data: dict | None = None, params: dict | None = None
    ) -> dict[str, Any]:
        """Make HTTP request to Kintone API."""
        url = f"{self.base_url}/{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self.headers, params=params or {})
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self.headers, json=data or {})
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=self.headers, json=data or {})
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=self.headers, json=data or {})
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Check for HTTP errors
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                    except Exception:
                        error_data = {"message": response.text}

                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    raise KintoneError(
                        message=f"Kintone API error: {error_message}",
                        status_code=response.status_code,
                        response_data=error_data,
                    )

                return response.json()

            except httpx.RequestError as e:
                logger.error(f"Request error: {str(e)}")
                raise KintoneError(f"Network error: {str(e)}") from e
            except Exception as e:
                if isinstance(e, KintoneError):
                    raise
                logger.error(f"Unexpected error: {str(e)}")
                raise KintoneError(f"Unexpected error: {str(e)}") from e

    async def get_app_info(self) -> dict[str, Any]:
        """Get app information."""
        try:
            params = {"id": self.config.app_id}
            response = await self._request("GET", "app.json", params=params)
            return response
        except Exception as e:
            logger.error(f"Error getting app info: {e}")
            raise

    async def get_app_fields(self) -> dict[str, Any]:
        """Get app form fields."""
        try:
            params = {"app": self.config.app_id}
            response = await self._request("GET", "app/form/fields.json", params=params)
            return response.get("properties", {})
        except Exception as e:
            logger.error(f"Error getting app fields: {e}")
            raise

    async def get_records(self, query: str = "", limit: int = 100) -> dict[str, Any]:
        """Get records from the Kintone app."""
        try:
            params = {"app": self.config.app_id, "totalCount": True}

            if query:
                params["query"] = f"{query} limit {limit}"
            else:
                params["query"] = f"limit {limit}"

            response = await self._request("GET", "records.json", params=params)

            # Convert records from Kintone format
            records = response.get("records", [])
            converted_records = []

            for record in records:
                converted_record = FieldMapper.convert_record_from_kintone(self.field_types, record)
                # Add system fields
                converted_record["$id"] = record.get("$id", {}).get("value", "")
                converted_record["$revision"] = record.get("$revision", {}).get("value", "")
                converted_records.append(converted_record)

            return {"records": converted_records, "totalCount": response.get("totalCount", len(converted_records))}
        except Exception as e:
            logger.error(f"Error getting records: {e}")
            raise

    async def get_record(self, record_id: str) -> dict[str, Any]:
        """Get a specific record from the Kintone app."""
        try:
            params = {"app": self.config.app_id, "id": record_id}

            response = await self._request("GET", "record.json", params=params)
            kintone_record = response.get("record", {})

            # Convert record from Kintone format
            converted_record = FieldMapper.convert_record_from_kintone(self.field_types, kintone_record)
            # Add system fields
            converted_record["$id"] = kintone_record.get("$id", {}).get("value", "")
            converted_record["$revision"] = kintone_record.get("$revision", {}).get("value", "")

            return converted_record
        except Exception as e:
            logger.error(f"Error getting record {record_id}: {e}")
            raise

    async def create_record(self, record_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new record in the Kintone app."""
        try:
            # Convert record to Kintone format
            kintone_record = FieldMapper.convert_record_to_kintone(self.field_types, record_data)

            data = {"app": self.config.app_id, "record": kintone_record}

            response = await self._request("POST", "record.json", data)
            return {"id": response.get("id", ""), "revision": response.get("revision", "")}
        except Exception as e:
            logger.error(f"Error creating record: {e}")
            raise

    async def update_record(
        self, record_id: str, record_data: dict[str, Any], revision: str | None = None
    ) -> dict[str, Any]:
        """Update an existing record in the Kintone app."""
        try:
            # Convert record to Kintone format
            kintone_record = FieldMapper.convert_record_to_kintone(self.field_types, record_data)

            data = {"app": self.config.app_id, "id": record_id, "record": kintone_record}

            if revision:
                data["revision"] = revision

            response = await self._request("PUT", "record.json", data)
            return {"revision": response.get("revision", "")}
        except Exception as e:
            logger.error(f"Error updating record {record_id}: {e}")
            raise

    async def delete_record(self, record_id: str, revision: str | None = None) -> dict[str, Any]:
        """Delete a record from the Kintone app."""
        try:
            data = {"app": self.config.app_id, "ids": [record_id]}

            if revision:
                data["revisions"] = [revision]

            response = await self._request("DELETE", "records.json", data)
            return response
        except Exception as e:
            logger.error(f"Error deleting record {record_id}: {e}")
            raise

    async def search_records(self, query: str, limit: int = 100) -> dict[str, Any]:
        """Search records with a specific query."""
        return await self.get_records(query, limit)
