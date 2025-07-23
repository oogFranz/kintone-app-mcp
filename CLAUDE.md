# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a kintone-mcp project - a Model Context Protocol (MCP) server that integrates with Kintone applications using API token authentication.

The server provides tools for:
- Reading app information and form fields
- CRUD operations on records (create, read, update, delete)
- Searching records with queries
- Field type mapping and validation

## Development Workflow

- Run formatter, lint, and unit tests before committing. Fix any issues before proceeding with the commit.

## Architecture Design

### Authentication
- Uses Kintone API tokens for authentication
- Header: `X-Cybozu-API-Token: {api_token}`
- Endpoint: `https://{domain}/k/v1/`

### Project Structure
```
kintone-mcp/
├── pyproject.toml         # uv project configuration
├── uv.lock               # dependency lock file
├── config.json           # Kintone app configuration
├── .python-version       # Python version specification
├── src/
│   └── kintone_mcp/
│       ├── __init__.py
│       ├── server.py          # Main MCP server
│       ├── config.py          # Configuration management
│       ├── kintone_client.py  # Kintone API client
│       └── field_mapper.py    # Field type mapping
├── tests/                 # Comprehensive test suite
│   ├── conftest.py           # Test fixtures and utilities
│   ├── test_config.py        # Configuration tests
│   ├── test_field_mapper.py  # Field mapping tests
│   ├── test_kintone_client.py # API client tests
│   └── test_server.py        # MCP server tests
└── README.md
```

### Configuration File Structure (config.json)
```json
{
  "kintone": {
    "domain": "your-domain.cybozu.com",
    "app_id": "123",
    "api_token": "your-api-token", 
    "api_permissions": ["record_read", "record_create", "record_update", "record_delete"],
    "app_code": "my_app",
    "app_description": "Descriptive text about the app's purpose and functionality"
  },
  "fields": [
    {
      "field_name": "Title",
      "field_type": "SINGLE_LINE_TEXT",
      "field_code": "title",
      "description": "Task title"
    },
    {
      "field_name": "Description", 
      "field_type": "MULTI_LINE_TEXT",
      "field_code": "description",
      "description": "Detailed description"
    },
    {
      "field_name": "Priority",
      "field_type": "DROP_DOWN",
      "field_code": "priority", 
      "description": "Task priority (High/Medium/Low)"
    },
    {
      "field_name": "Due Date",
      "field_type": "DATE",
      "field_code": "due_date",
      "description": "Expected completion date"
    },
    {
      "field_name": "Assignee",
      "field_type": "USER_SELECT",
      "field_code": "assignee",
      "description": "Person assigned to this task"
    },
    {
      "field_name": "Cost",
      "field_type": "NUMBER",
      "field_code": "cost",
      "description": "Estimated cost for the task"
    }
  ]
}
```

## Development Environment (using uv)

### Setup Commands
```bash
# Project initialization
uv init kintone-mcp
cd kintone-mcp

# Python version setup
uv python install 3.11
uv python pin 3.11

# Install dependencies
uv sync

# Install with dev dependencies
uv sync --dev
```

### Development Commands
```bash
# Run MCP server
uv run kintone-mcp

# Code quality checks
uv run black src/ tests/
uv run ruff check src/ tests/
uv run mypy src/

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Add new dependencies
uv add package-name
uv add --dev dev-package-name

# Update dependencies
uv lock --upgrade
```

### Dependencies
- **Core**: mcp, httpx, pydantic
- **Dev**: pytest, pytest-asyncio, black, ruff, mypy

### Testing
- Comprehensive test suite with minimal mocking
- Tests for config management, field mapping, API client, and MCP server
- Fixtures and utilities in `tests/conftest.py`
- Test data in `tests/fixtures/`

## Available MCP Tools

1. **get_app_info** - Get application information
   - Parameters: none
   - Returns app metadata, field definitions, and configured fields

2. **get_records** - Get record list
   - Parameters: query (optional), limit (optional)
   - Returns records matching the query with pagination

3. **get_record** - Get single record
   - Parameters: record_id
   - Returns specific record by ID

4. **create_record** - Create record
   - Parameters: record_data (field_code: value mapping)
   - Creates new record with provided data

5. **update_record** - Update record
   - Parameters: record_id, record_data, revision (optional)
   - Updates existing record with optimistic locking

6. **delete_record** - Delete record
   - Parameters: record_id, revision (optional)
   - Deletes record with optimistic locking

7. **search_records** - Search records
   - Parameters: query, limit (optional)
   - Search records using Kintone query syntax

## Main Components

### Config Classes
- **KintoneConfig**: Domain, app_id, api_token, api_permissions, app_code, app_description, fields
- **FieldConfig**: Field_name, field_type, field_code, description
- **ConfigManager**: Loads and validates configuration from JSON files

### KintoneClient Class  
- API token authentication with proper headers
- REST API wrapper functionality with async HTTP client
- Record CRUD operations with field type conversion
- Automatic field type conversion using FieldMapper
- Comprehensive error handling with custom KintoneError

### FieldMapper Class
- Bidirectional field type conversion between Python and Kintone formats
- Support for all major Kintone field types
- Robust error handling with graceful fallbacks
- Case-insensitive field type matching

### MCPServer Implementation
- Complete Model Context Protocol server
- 7 MCP tools for comprehensive Kintone integration
- Resource listing and reading for app information
- Proper error handling for API and general exceptions
- JSON formatting with Unicode support

## Field Types Supported

### Text Fields
- SINGLE_LINE_TEXT, MULTI_LINE_TEXT, RICH_TEXT
- LINK (URL fields)

### Numeric Fields  
- NUMBER, CALC (calculated fields)

### Selection Fields
- RADIO_BUTTON, CHECK_BOX, MULTI_SELECT, DROP_DOWN

### Date/Time Fields
- DATE, TIME, DATETIME

### User/Organization Fields
- USER_SELECT, ORGANIZATION_SELECT, GROUP_SELECT

### System Fields
- RECORD_NUMBER, CREATED_TIME, UPDATED_TIME
- CREATOR, MODIFIER, STATUS, STATUS_ASSIGNEE

### File Fields
- FILE (file attachments)

## Error Handling
- Configuration file loading and validation errors
- Authentication and API token permission errors
- Network connectivity and HTTP errors
- Invalid field type conversions with graceful fallbacks
- Record revision conflicts (optimistic locking)
- Comprehensive logging for debugging

## Code Quality Standards
- Line length: 120 characters (updated from 88 for better readability)
- Modern Python type annotations (3.11+)
- Comprehensive error handling with exception chaining
- Full test coverage with minimal mocking approach
- Black formatting and Ruff linting with modern configuration
- MyPy type checking for type safety