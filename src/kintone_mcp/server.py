#!/usr/bin/env python3
"""
Kintone MCP Server

A Model Context Protocol server for interacting with Kintone applications.
"""

import asyncio
import json
import logging
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import Resource, Tool

from .config import ConfigManager
from .kintone_client import KintoneClient, KintoneError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kintone-mcp")

# Create server instance
server = Server("kintone-mcp")

# Global variables
config_manager: ConfigManager | None = None
kintone_client: KintoneClient | None = None


@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List available Kintone resources."""
    if not kintone_client:
        return []

    try:
        # Get app information as a resource
        app_info = await kintone_client.get_app_info()
        app_name = app_info.get("name", f"App {config_manager.config.app_id}")

        # Use configured app description if available, otherwise use app name
        description = (
            config_manager.config.app_description or f"Kintone app {config_manager.config.app_id} - {app_name}"
        )

        return [
            Resource(
                uri=f"kintone://app/{config_manager.config.app_id}",
                name=f"Kintone App: {app_name}",
                description=description,
                mimeType="application/json",
            )
        ]
    except Exception as e:
        logger.error(f"Error listing resources: {e}")
        return []


@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read a specific Kintone resource."""
    if not kintone_client:
        raise ValueError("Kintone client not initialized")

    if uri.startswith(f"kintone://app/{config_manager.config.app_id}"):
        try:
            app_info = await kintone_client.get_app_info()
            app_fields = await kintone_client.get_app_fields()

            resource_data = {
                "app_info": app_info,
                "app_description": config_manager.config.app_description,
                "fields": app_fields,
                "configured_fields": [
                    {
                        "field_name": field.field_name,
                        "field_type": field.field_type,
                        "field_code": field.field_code,
                        "description": field.description,
                    }
                    for field in config_manager.config.fields
                ],
            }

            return json.dumps(resource_data, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            raise
    else:
        raise ValueError(f"Unknown resource URI: {uri}")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available Kintone tools."""
    return [
        Tool(
            name="get_app_info",
            description=(
                "Get information about the configured Kintone app including fields"
                + (
                    f" - {config_manager.config.app_description}"
                    if config_manager and config_manager.config.app_description
                    else ""
                )
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="get_records",
            description="Get records from the Kintone app with optional query and limit",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query string to filter records (optional). Use Kintone query syntax.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to retrieve (default: 100, max: 500)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_record",
            description="Get a specific record by ID from the Kintone app",
            inputSchema={
                "type": "object",
                "properties": {"record_id": {"type": "string", "description": "The ID of the record to retrieve"}},
                "required": ["record_id"],
            },
        ),
        Tool(
            name="create_record",
            description="Create a new record in the Kintone app",
            inputSchema={
                "type": "object",
                "properties": {
                    "record_data": {"type": "object", "description": "Record data as field_code: value pairs"}
                },
                "required": ["record_data"],
            },
        ),
        Tool(
            name="update_record",
            description="Update an existing record in the Kintone app",
            inputSchema={
                "type": "object",
                "properties": {
                    "record_id": {"type": "string", "description": "The ID of the record to update"},
                    "record_data": {
                        "type": "object",
                        "description": "Record data to update as field_code: value pairs",
                    },
                    "revision": {"type": "string", "description": "Record revision for optimistic locking (optional)"},
                },
                "required": ["record_id", "record_data"],
            },
        ),
        Tool(
            name="delete_record",
            description="Delete a record from the Kintone app",
            inputSchema={
                "type": "object",
                "properties": {
                    "record_id": {"type": "string", "description": "The ID of the record to delete"},
                    "revision": {"type": "string", "description": "Record revision for optimistic locking (optional)"},
                },
                "required": ["record_id"],
            },
        ),
        Tool(
            name="search_records",
            description="Search records with a specific query string",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Query string using Kintone query syntax"},
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to retrieve (default: 100, max: 500)",
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls for Kintone operations."""
    if not kintone_client:
        raise ValueError("Kintone client not initialized")

    try:
        if name == "get_app_info":
            app_info = await kintone_client.get_app_info()
            app_fields = await kintone_client.get_app_fields()

            result = {
                "app_info": app_info,
                "app_description": config_manager.config.app_description,
                "app_fields": app_fields,
                "configured_fields": [
                    {
                        "field_name": field.field_name,
                        "field_type": field.field_type,
                        "field_code": field.field_code,
                        "description": field.description,
                    }
                    for field in config_manager.config.fields
                ],
            }

            return [
                types.TextContent(
                    type="text", text=f"App Information:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
                )
            ]

        elif name == "get_records":
            query = arguments.get("query", "")
            limit = min(arguments.get("limit", 100), 500)  # Cap at 500

            result = await kintone_client.get_records(query, limit)

            return [
                types.TextContent(
                    type="text",
                    text=(
                        f"Records (Total: {result['totalCount']}):\n"
                        f"{json.dumps(result['records'], indent=2, ensure_ascii=False)}"
                    ),
                )
            ]

        elif name == "get_record":
            record_id = arguments["record_id"]
            result = await kintone_client.get_record(record_id)

            return [
                types.TextContent(
                    type="text", text=f"Record {record_id}:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
                )
            ]

        elif name == "create_record":
            record_data = arguments["record_data"]
            result = await kintone_client.create_record(record_data)

            return [
                types.TextContent(
                    type="text",
                    text=f"Record created successfully:\n{json.dumps(result, indent=2, ensure_ascii=False)}",
                )
            ]

        elif name == "update_record":
            record_id = arguments["record_id"]
            record_data = arguments["record_data"]
            revision = arguments.get("revision")

            result = await kintone_client.update_record(record_id, record_data, revision)

            return [
                types.TextContent(
                    type="text",
                    text=(
                        f"Record {record_id} updated successfully:\n"
                        f"{json.dumps(result, indent=2, ensure_ascii=False)}"
                    ),
                )
            ]

        elif name == "delete_record":
            record_id = arguments["record_id"]
            revision = arguments.get("revision")

            result = await kintone_client.delete_record(record_id, revision)

            return [
                types.TextContent(
                    type="text",
                    text=(
                        f"Record {record_id} deleted successfully:\n"
                        f"{json.dumps(result, indent=2, ensure_ascii=False)}"
                    ),
                )
            ]

        elif name == "search_records":
            query = arguments["query"]
            limit = min(arguments.get("limit", 100), 500)  # Cap at 500

            result = await kintone_client.search_records(query, limit)

            return [
                types.TextContent(
                    type="text",
                    text=(
                        f"Search Results (Query: {query}, Total: {result['totalCount']}):\n"
                        f"{json.dumps(result['records'], indent=2, ensure_ascii=False)}"
                    ),
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except KintoneError as e:
        logger.error(f"Kintone error in tool call {name}: {e}")
        return [
            types.TextContent(
                type="text",
                text=(
                    f"Kintone API Error: {str(e)}\nStatus Code: {e.status_code}\n"
                    f"Details: {json.dumps(e.response_data, indent=2, ensure_ascii=False)}"
                ),
            )
        ]
    except Exception as e:
        logger.error(f"Error handling tool call {name}: {e}")
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point for the server."""
    global config_manager, kintone_client

    try:
        # Load configuration
        config_manager = ConfigManager("config.json")
        config = config_manager.load_config()

        logger.info(f"Configuration loaded for app {config.app_id} on {config.domain}")

        # Initialize Kintone client
        kintone_client = KintoneClient(config)

        # Test connection
        try:
            app_info = await kintone_client.get_app_info()
            logger.info(f"Connected to Kintone app: {app_info.get('name', 'Unknown')}")
        except Exception as e:
            logger.error(f"Failed to connect to Kintone: {e}")
            logger.error("Please check your configuration and API token permissions")
            return

        # Run the server using stdin/stdout streams
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="kintone-mcp",
                    server_version="0.1.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(), experimental_capabilities={}
                    ),
                ),
            )

    except FileNotFoundError:
        logger.error("Configuration file 'config.json' not found. Please create it based on config.example.json")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")


if __name__ == "__main__":
    asyncio.run(main())
