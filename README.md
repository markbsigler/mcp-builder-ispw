# ISPW MCP Server

A Model Context Protocol (MCP) server for BMC Compuware ISPW (Interactive Source Program Workbench) - a comprehensive source code management, release automation, and deployment automation tool for mainframe DevOps.

## Overview

This MCP server enables LLMs to interact with ISPW through a comprehensive set of tools for:

- **Assignment Management**: Create, list, and retrieve assignments (containers for development work)
- **Task Management**: View tasks within assignments (individual modules/components)
- **Release Management**: Create and manage releases for coordinated deployments
- **Operations**: Generate, promote, and deploy code through the development lifecycle
- **Set & Package Management**: List and view deployment sets and packages

## Features

- ✅ Complete ISPW REST API coverage for core workflows
- ✅ Token-based authentication with CES (Compuware Enterprise Services)
- ✅ Dual output formats: Human-readable Markdown and machine-readable JSON
- ✅ Comprehensive error handling with actionable messages
- ✅ Pydantic validation for all inputs
- ✅ Async/await for optimal performance
- ✅ Support for both production and custom CES servers

## Installation

### Prerequisites

- Python 3.10 or higher
- Access to a BMC Compuware ISPW instance
- Personal Access Token for CES authentication

### Setup

1. **Clone or create the project directory:**
   ```bash
   cd /path/to/ispw-mcp-server
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set your values:
   ```bash
   # For custom CES server:
   CES_HOST=your-ces-host.example.com
   CES_PORT=2020
   
   # Or for production server:
   # ISPW_BASE_URL=https://ispw.api.compuware.com
   
   # Required: Your personal access token
   ISPW_API_TOKEN=your_token_here
   
   # Default SRID (optional, defaults to "ISPW")
   ISPW_DEFAULT_SRID=ISPW
   ```

## Usage

### Running the Server

#### As a standalone script:
```bash
python ispw_mcp_server.py
```

#### Using the installed command:
```bash
ispw-mcp-server
```

#### With the MCP Inspector (for testing):
```bash
npx @modelcontextprotocol/inspector python ispw_mcp_server.py
```

### Configuration in Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "ispw": {
      "command": "python",
      "args": ["/path/to/ispw-mcp-server/ispw_mcp_server.py"],
      "env": {
        "ISPW_BASE_URL": "https://your-ces-host:2020",
        "ISPW_API_TOKEN": "your_token_here",
        "ISPW_DEFAULT_SRID": "ISPW"
      }
    }
  }
}
```

Or using a virtual environment:

```json
{
  "mcpServers": {
    "ispw": {
      "command": "/path/to/ispw-mcp-server/venv/bin/python",
      "args": ["/path/to/ispw-mcp-server/ispw_mcp_server.py"],
      "env": {
        "ISPW_BASE_URL": "https://your-ces-host:2020",
        "ISPW_API_TOKEN": "your_token_here",
        "ISPW_DEFAULT_SRID": "ISPW"
      }
    }
  }
}
```

## Available Tools

### Assignment Tools

#### `ispw_list_assignments`
List all assignments for a specific SRID, with optional filtering by level or assignment ID.

**Parameters:**
- `srid` (str): System Resource Identifier (default: from env)
- `level` (optional): Filter by level (DEV, INT, ACC, PRD)
- `assignment_id` (optional): Filter by specific assignment ID
- `response_format` (optional): "markdown" or "json" (default: markdown)

**Example:**
```
List all DEV level assignments for SRID ISPW
```

#### `ispw_get_assignment`
Get detailed information about a specific assignment.

**Parameters:**
- `srid` (str): System Resource Identifier
- `assignment_id` (str): Assignment identifier
- `response_format` (optional): Output format

**Example:**
```
Get details for assignment PLAY000001 in ISPW
```

#### `ispw_create_assignment`
Create a new assignment.

**Parameters:**
- `srid` (str): System Resource Identifier
- `assignment_id` (str): Unique assignment identifier
- `stream` (str): Stream name
- `application` (str): Application name
- `description` (optional): Assignment description
- `default_path` (optional): Default path
- `response_format` (optional): Output format

**Example:**
```
Create a new assignment PLAY000002 in ISPW for stream PLAY and application PLAY
```

### Task Tools

#### `ispw_list_tasks`
List all tasks for a specific assignment.

**Parameters:**
- `srid` (str): System Resource Identifier
- `assignment_id` (str): Assignment identifier
- `response_format` (optional): Output format

**Example:**
```
List all tasks for assignment PLAY000001
```

### Release Tools

#### `ispw_list_releases`
List all releases for a specific SRID.

**Parameters:**
- `srid` (str): System Resource Identifier
- `release_id` (optional): Filter by specific release ID
- `response_format` (optional): Output format

**Example:**
```
List all releases for ISPW
```

#### `ispw_get_release`
Get detailed information about a specific release.

**Parameters:**
- `srid` (str): System Resource Identifier
- `release_id` (str): Release identifier
- `response_format` (optional): Output format

#### `ispw_create_release`
Create a new release.

**Parameters:**
- `srid` (str): System Resource Identifier
- `release_id` (str): Unique release identifier
- `stream` (str): Stream name
- `application` (str): Application name
- `description` (optional): Release description
- `response_format` (optional): Output format

### Operation Tools

#### `ispw_generate_assignment`
Generate code for an assignment (compile and prepare).

**Parameters:**
- `srid` (str): System Resource Identifier
- `assignment_id` (str): Assignment identifier
- `level` (optional): Target level for generation
- `runtime_configuration` (optional): Runtime configuration
- `response_format` (optional): Output format

**Example:**
```
Generate assignment PLAY000001 for level DEV
```

#### `ispw_promote_assignment`
Promote an assignment to the next level.

**Parameters:**
- `srid` (str): System Resource Identifier
- `assignment_id` (str): Assignment identifier
- `level` (optional): Target level for promotion
- `change_type` (optional): S (Standard), I (Incidental), E (Emergency)
- `execution_status` (optional): Execution status
- `response_format` (optional): Output format

**Example:**
```
Promote assignment PLAY000001 to INT level with Standard change type
```

#### `ispw_deploy`
Deploy an assignment, release, or set to target environment.

**⚠️ CAUTION: This is a destructive operation that affects production or target environments.**

**Parameters:**
- `srid` (str): System Resource Identifier
- `target_id` (str): Assignment, release, or set identifier
- `target_type` (str): "assignment", "release", or "set"
- `level` (optional): Target level for deployment
- `deploy_implementation_time` (optional): Scheduled time (ISO 8601)
- `deploy_active` (optional): Deploy to active libraries (boolean)
- `response_format` (optional): Output format

**Examples:**
```
Deploy assignment PLAY000001 to production
Deploy release REL001 to PRD level
Schedule deployment of assignment PLAY000001 for 2026-01-15T10:00:00Z
```

### Set and Package Tools

#### `ispw_list_sets`
List all sets for a specific SRID.

**Parameters:**
- `srid` (str): System Resource Identifier
- `set_id` (optional): Filter by specific set ID
- `response_format` (optional): Output format

#### `ispw_list_packages`
List all packages for a specific SRID.

**Parameters:**
- `srid` (str): System Resource Identifier
- `package_id` (optional): Filter by specific package ID
- `response_format` (optional): Output format

#### `ispw_get_package`
Get detailed information about a specific package.

**Parameters:**
- `srid` (str): System Resource Identifier
- `package_id` (str): Package identifier
- `response_format` (optional): Output format

## Architecture

### Key Design Decisions

1. **Comprehensive API Coverage**: Implements all major ISPW REST API endpoints for complete workflow support
2. **Dual Format Responses**: Markdown for human readability, JSON for programmatic processing
3. **Shared Utilities**: DRY principle with reusable API client, error handling, and formatting functions
4. **Strong Validation**: Pydantic models ensure all inputs are validated before API calls
5. **Async Design**: All I/O operations use async/await for optimal performance
6. **Flexible Configuration**: Support for both production and custom CES servers

### Project Structure

```
ispw-mcp-server/
├── ispw_mcp_server.py       # Main server implementation
├── ispw_openapi_spec.json   # OpenAPI specification (reference)
├── pyproject.toml           # Project configuration
├── .env.example             # Environment template
├── .env                     # Your configuration (not in git)
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Development

### Running Tests

```bash
pytest
```

### Code Quality

The project uses Ruff for linting:

```bash
ruff check .
```

### Adding New Tools

When adding new ISPW API endpoints:

1. Define Pydantic input model with validation
2. Create tool function with `@mcp.tool()` decorator
3. Add proper annotations (readOnlyHint, destructiveHint, etc.)
4. Implement using shared `_make_api_request()` utility
5. Handle errors with `_handle_api_error()`
6. Support both markdown and JSON output formats
7. Update this README with tool documentation

## Troubleshooting

### Authentication Errors

**Problem**: "Error: Authentication failed. Check your ISPW_API_TOKEN is valid."

**Solution**: 
- Verify your Personal Access Token is correct
- Ensure the token has appropriate permissions in CES
- Check token hasn't expired

### Connection Errors

**Problem**: "Error: Request timed out. The ISPW server may be slow or unavailable."

**Solution**:
- Verify CES_HOST and CES_PORT are correct
- Check network connectivity to the CES server
- Increase ISPW_TIMEOUT if operations are legitimately slow

### SSL Certificate Issues

**Problem**: SSL certificate verification fails for custom CES server

**Solution**: The server currently disables SSL verification for custom CES servers. For production use, configure proper SSL certificates.

## Security Considerations

1. **Token Management**: Store ISPW_API_TOKEN securely, never commit to version control
2. **SSL Verification**: Consider enabling SSL verification for production deployments
3. **Access Control**: Tokens should have minimal required permissions
4. **Audit Logging**: ISPW maintains audit logs of all operations

## Contributing

When contributing:

1. Follow Python best practices and PEP 8
2. Use type hints throughout
3. Add comprehensive docstrings
4. Include parameter validation
5. Test with both markdown and JSON formats
6. Update README documentation

## License

[Specify your license here]

## Support

For ISPW API issues, consult:
- BMC Compuware ISPW documentation
- BMC Compuware Support: https://www.bmc.com/support/

For MCP server issues:
- Check server logs
- Test with MCP Inspector
- Review environment configuration

## Changelog

### Version 1.0.0 (2026-01-08)

Initial release with:
- Complete assignment lifecycle management
- Task viewing capabilities
- Release creation and management
- Generate, promote, and deploy operations
- Set and package listing
- Dual output formats (Markdown/JSON)
- Comprehensive error handling
- Full Pydantic validation
