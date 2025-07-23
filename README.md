# Kintone MCP Server

A Model Context Protocol (MCP) server for integrating with Kintone applications using API token authentication. This server enables AI assistants like Claude to interact with Kintone apps through standardized tools.

## Features

- 🔐 **API Token Authentication**: Secure connection using Kintone API tokens
- 📊 **Record Operations**: Full CRUD operations (create, read, update, delete)
- 🔍 **Flexible Querying**: Support for Kintone query syntax
- 🎯 **Field Type Mapping**: Automatic conversion between Python and Kintone field types
- ⚡ **High Performance**: Built with modern async/await patterns using httpx
- 🛠️ **Type Safety**: Full type hints and validation using Pydantic

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd kintone-mcp

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

### 2. Configuration

```bash
# Copy example configuration
cp config.example.json config.json

# Edit config.json with your Kintone details:
# - domain: Your Kintone domain (e.g., "company.cybozu.com")
# - app_id: Target Kintone app ID
# - api_token: API token with appropriate permissions
# - app_description: Descriptive text about your app's purpose
# - fields: Define your app's field mappings
```

### 3. Running the Server

```bash
# Using uv
uv run kintone-mcp

# Using pip installation
kintone-mcp

# For development
uv run python -m kintone_mcp.server
```

## Configuration

The `config.json` file defines your Kintone app connection and field mappings:

```json
{
  "kintone": {
    "domain": "your-subdomain.cybozu.com",
    "app_id": "123", 
    "api_token": "your-api-token",
    "api_permissions": ["record_read", "record_create", "record_update", "record_delete"],
    "app_code": "task_manager",
    "app_description": "Task management app for tracking project tasks and progress"
  },
  "fields": [
    {
      "field_name": "タイトル",
      "field_type": "SINGLE_LINE_TEXT", 
      "field_code": "title",
      "description": "Task title"
    }
  ]
}
```

### Supported Field Types

- `SINGLE_LINE_TEXT`, `MULTI_LINE_TEXT`, `RICH_TEXT`
- `NUMBER`, `CALC`
- `RADIO_BUTTON`, `CHECK_BOX`, `MULTI_SELECT`, `DROP_DOWN`
- `DATE`, `TIME`, `DATETIME`
- `USER_SELECT`, `ORGANIZATION_SELECT`, `GROUP_SELECT`
- `LINK`, `FILE`
- System fields: `RECORD_NUMBER`, `CREATED_TIME`, `UPDATED_TIME`, etc.

## Available MCP Tools

### 1. `get_app_info`
Get detailed information about the configured Kintone app including field definitions.

### 2. `get_records`
Retrieve records with optional query filtering and limit.
- **Parameters**: 
  - `query` (optional): Kintone query string
  - `limit` (optional): Max records (default: 100, max: 500)

### 3. `get_record` 
Get a specific record by ID.
- **Parameters**:
  - `record_id`: Record ID to retrieve

### 4. `create_record`
Create a new record in the app.
- **Parameters**:
  - `record_data`: Object with field_code: value pairs

### 5. `update_record`
Update an existing record.
- **Parameters**:
  - `record_id`: Record ID to update
  - `record_data`: Object with field_code: value pairs
  - `revision` (optional): For optimistic locking

### 6. `delete_record`
Delete a record from the app.
- **Parameters**:
  - `record_id`: Record ID to delete
  - `revision` (optional): For optimistic locking

### 7. `search_records`
Search records using Kintone query syntax.
- **Parameters**:
  - `query`: Kintone query string
  - `limit` (optional): Max records (default: 100, max: 500)

## Development

### Setup Development Environment

```bash
# Install with development dependencies
uv sync --dev
```

### Code Quality

```bash
# Format code
uv run black src/

# Lint code  
uv run ruff check src/

# Type checking
uv run mypy src/

# Run tests
uv run pytest
```

### Project Structure

```
kintone-mcp/
├── src/kintone_mcp/
│   ├── __init__.py
│   ├── server.py          # MCP server implementation
│   ├── config.py          # Configuration management
│   ├── kintone_client.py  # Kintone API client
│   └── field_mapper.py    # Field type conversion
├── config.example.json    # Example configuration
├── pyproject.toml        # Project configuration
└── README.md
```

## Error Handling

The server provides comprehensive error handling for:
- ❌ Invalid configuration files
- 🔐 Authentication failures
- 🚫 API permission errors  
- 🌐 Network connectivity issues
- 📝 Invalid field type conversions
- 🔒 Record revision conflicts

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run code quality checks
5. Submit a pull request

## Support

For issues and questions:
1. Check the existing issues on GitHub
2. Review the Kintone REST API documentation
3. Ensure your API token has the required permissions