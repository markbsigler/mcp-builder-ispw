#!/usr/bin/env python3
"""
MCP Server for BMC Compuware ISPW.

This server provides tools to interact with ISPW (Interactive Source Program Workbench),
a source code management, release automation, and deployment automation tool for mainframe DevOps.
"""

import json
import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Initialize the MCP server
mcp = FastMCP("ispw_mcp")

# Environment configuration
CES_HOST = os.getenv("CES_HOST", "localhost")
CES_PORT = os.getenv("CES_PORT", "2020")
ISPW_BASE_URL = os.getenv("ISPW_BASE_URL", f"https://{CES_HOST}:{CES_PORT}")
ISPW_API_TOKEN = os.getenv("ISPW_API_TOKEN", "")
ISPW_DEFAULT_SRID = os.getenv("ISPW_DEFAULT_SRID", "ISPW")
ISPW_TIMEOUT = int(os.getenv("ISPW_TIMEOUT", "30"))

# Enums
class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class AssignmentLevel(str, Enum):
    """ISPW assignment levels."""
    DEV = "DEV"
    INT = "INT"
    ACC = "ACC"
    PRD = "PRD"


class ChangeType(str, Enum):
    """Change types for promotion."""
    STANDARD = "S"
    INCIDENTAL = "I"
    EMERGENCY = "E"


class OperationStatus(str, Enum):
    """Operation status values."""
    STARTED = "STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Shared utility functions
async def _make_api_request(
    endpoint: str,
    method: str = "GET",
    json_data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Reusable function for all ISPW API calls."""
    if not ISPW_API_TOKEN:
        raise ValueError("ISPW_API_TOKEN environment variable not set")

    headers = {
        "Authorization": f"Bearer {ISPW_API_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    url = f"{ISPW_BASE_URL}/{endpoint}"

    async with httpx.AsyncClient(verify=False) as client:  # SSL verification may vary for CES
        response = await client.request(
            method,
            url,
            headers=headers,
            json=json_data,
            params=params,
            timeout=ISPW_TIMEOUT
        )
        response.raise_for_status()
        return response.json()


def _handle_api_error(e: Exception) -> str:
    """Consistent error formatting across all tools."""
    if isinstance(e, httpx.HTTPStatusError):
        if e.response.status_code == 401:
            return "Error: Authentication failed. Check your ISPW_API_TOKEN is valid."
        elif e.response.status_code == 404:
            return "Error: Resource not found. Verify the SRID, assignment ID, release ID, or other identifiers."
        elif e.response.status_code == 403:
            return "Error: Permission denied. You don't have access to this resource."
        elif e.response.status_code == 400:
            try:
                error_detail = e.response.json()
                return f"Error: Bad request - {error_detail.get('error', {}).get('message', 'Invalid parameters')}"
            except Exception:
                return "Error: Bad request. Check your input parameters."
        elif e.response.status_code == 429:
            return "Error: Rate limit exceeded. Please wait before making more requests."
        return f"Error: API request failed with status {e.response.status_code}"
    elif isinstance(e, httpx.TimeoutException):
        return "Error: Request timed out. The ISPW server may be slow or unavailable."
    elif isinstance(e, ValueError) as ve:
        return f"Error: {str(ve)}"
    return f"Error: Unexpected error occurred: {type(e).__name__} - {str(e)}"


def _format_datetime(dt_str: Optional[str]) -> str:
    """Format datetime string to human-readable format."""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return dt_str


def _format_assignment_markdown(assignment: Dict[str, Any]) -> str:
    """Format assignment data as markdown."""
    lines = [
        f"## Assignment: {assignment.get('assignmentId', 'N/A')}",
        f"- **Description**: {assignment.get('description', 'N/A')}",
        f"- **Owner**: {assignment.get('owner', 'N/A')}",
        f"- **Stream**: {assignment.get('stream', 'N/A')}",
        f"- **Application**: {assignment.get('application', 'N/A')}",
        f"- **Level**: {assignment.get('level', 'N/A')}",
        f"- **Status**: {assignment.get('status', 'N/A')}",
        f"- **Created**: {_format_datetime(assignment.get('createdDate'))}",
        f"- **Modified**: {_format_datetime(assignment.get('modifiedDate'))}",
        ""
    ]
    return "\n".join(lines)


def _format_release_markdown(release: Dict[str, Any]) -> str:
    """Format release data as markdown."""
    lines = [
        f"## Release: {release.get('releaseId', 'N/A')}",
        f"- **Description**: {release.get('description', 'N/A')}",
        f"- **Owner**: {release.get('owner', 'N/A')}",
        f"- **Stream**: {release.get('stream', 'N/A')}",
        f"- **Application**: {release.get('application', 'N/A')}",
        f"- **Status**: {release.get('status', 'N/A')}",
        f"- **Created**: {_format_datetime(release.get('createdDate'))}",
        ""
    ]
    return "\n".join(lines)


def _format_task_markdown(task: Dict[str, Any]) -> str:
    """Format task data as markdown."""
    lines = [
        f"### Task: {task.get('taskId', 'N/A')}",
        f"- **Module**: {task.get('moduleName', 'N/A')} ({task.get('moduleType', 'N/A')})",
        f"- **Level**: {task.get('level', 'N/A')}",
        f"- **Status**: {task.get('status', 'N/A')}",
        f"- **User**: {task.get('userId', 'N/A')}",
        ""
    ]
    return "\n".join(lines)


def _format_operation_markdown(operation: Dict[str, Any]) -> str:
    """Format operation response as markdown."""
    lines = [
        f"# Operation {operation.get('status', 'UNKNOWN')}",
        f"- **Operation ID**: {operation.get('operationId', 'N/A')}",
        f"- **Status**: {operation.get('status', 'N/A')}",
        f"- **Message**: {operation.get('message', 'N/A')}",
    ]
    if operation.get('url'):
        lines.append(f"- **Status URL**: {operation['url']}")
    if operation.get('startTime'):
        lines.append(f"- **Started**: {_format_datetime(operation['startTime'])}")
    return "\n".join(lines)


# ============================================================================
# ASSIGNMENT TOOLS
# ============================================================================

class ListAssignmentsInput(BaseModel):
    """Input model for listing assignments."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier (e.g., 'ISPW', 'PROD')",
        min_length=1,
        max_length=50
    )
    level: Optional[AssignmentLevel] = Field(
        default=None,
        description="Filter by assignment level (DEV, INT, ACC, PRD)"
    )
    assignment_id: Optional[str] = Field(
        default=None,
        description="Filter by specific assignment ID",
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for machine-readable"
    )


class GetAssignmentInput(BaseModel):
    """Input model for getting assignment details."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier",
        min_length=1,
        max_length=50
    )
    assignment_id: str = Field(
        ...,
        description="Assignment identifier to retrieve",
        min_length=1,
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class CreateAssignmentInput(BaseModel):
    """Input model for creating an assignment."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier",
        min_length=1,
        max_length=50
    )
    assignment_id: str = Field(
        ...,
        description="Assignment identifier (must be unique)",
        min_length=1,
        max_length=100
    )
    stream: str = Field(
        ...,
        description="Stream name for the assignment",
        min_length=1,
        max_length=100
    )
    application: str = Field(
        ...,
        description="Application name for the assignment",
        min_length=1,
        max_length=100
    )
    description: Optional[str] = Field(
        default=None,
        description="Assignment description",
        max_length=500
    )
    default_path: Optional[str] = Field(
        default=None,
        description="Default path for the assignment",
        max_length=200
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


@mcp.tool(
    name="ispw_list_assignments",
    annotations={
        "title": "List ISPW Assignments",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def ispw_list_assignments(params: ListAssignmentsInput) -> str:
    """List ISPW assignments for a specific SRID.

    Retrieves all assignments or filters by level or assignment ID. Assignments are containers
    for related development work in ISPW, grouping related changes together.

    Args:
        params (ListAssignmentsInput): Validated input parameters containing:
            - srid (str): System Resource Identifier (default: from ISPW_DEFAULT_SRID env var)
            - level (Optional[AssignmentLevel]): Filter by assignment level (DEV, INT, ACC, PRD)
            - assignment_id (Optional[str]): Filter by specific assignment ID
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Formatted list of assignments or error message

    Examples:
        - List all assignments: srid="ISPW"
        - List DEV assignments: srid="ISPW", level="DEV"
        - Find specific assignment: srid="ISPW", assignment_id="PLAY000001"
    """
    try:
        query_params = {}
        if params.level:
            query_params["level"] = params.level.value
        if params.assignment_id:
            query_params["assignmentId"] = params.assignment_id

        data = await _make_api_request(
            f"ispw/{params.srid}/assignments",
            params=query_params
        )

        assignments = data.get("assignments", [])
        total = data.get("totalCount", len(assignments))

        if not assignments:
            filter_desc = f" matching filters" if query_params else ""
            return f"No assignments found{filter_desc} for SRID '{params.srid}'"

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# ISPW Assignments for {params.srid}", ""]
            if params.level:
                lines[0] += f" (Level: {params.level.value})"
            lines.append(f"Found {total} assignment(s)\n")

            for assignment in assignments:
                lines.append(_format_assignment_markdown(assignment))

            return "\n".join(lines)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="ispw_get_assignment",
    annotations={
        "title": "Get ISPW Assignment Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def ispw_get_assignment(params: GetAssignmentInput) -> str:
    """Get detailed information about a specific ISPW assignment.

    Retrieves complete details for an assignment including owner, stream, application,
    level, status, and timestamps.

    Args:
        params (GetAssignmentInput): Validated input parameters containing:
            - srid (str): System Resource Identifier
            - assignment_id (str): Assignment identifier to retrieve
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Formatted assignment details or error message

    Examples:
        - Get assignment: srid="ISPW", assignment_id="PLAY000001"
    """
    try:
        data = await _make_api_request(
            f"ispw/{params.srid}/assignments/{params.assignment_id}"
        )

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Assignment Details: {params.assignment_id}\n"]
            lines.append(_format_assignment_markdown(data))
            return "\n".join(lines)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="ispw_create_assignment",
    annotations={
        "title": "Create ISPW Assignment",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def ispw_create_assignment(params: CreateAssignmentInput) -> str:
    """Create a new ISPW assignment.

    Creates a new assignment container for grouping related development work. The assignment
    must have a unique ID within the SRID.

    Args:
        params (CreateAssignmentInput): Validated input parameters containing:
            - srid (str): System Resource Identifier
            - assignment_id (str): Unique assignment identifier
            - stream (str): Stream name for the assignment
            - application (str): Application name for the assignment
            - description (Optional[str]): Assignment description
            - default_path (Optional[str]): Default path for the assignment
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Created assignment details or error message

    Examples:
        - Create assignment: srid="ISPW", assignment_id="PLAY000002", stream="PLAY",
          application="PLAY", description="New feature work"
    """
    try:
        request_body = {
            "assignmentId": params.assignment_id,
            "stream": params.stream,
            "application": params.application
        }
        if params.description:
            request_body["description"] = params.description
        if params.default_path:
            request_body["defaultPath"] = params.default_path

        data = await _make_api_request(
            f"ispw/{params.srid}/assignments",
            method="POST",
            json_data=request_body
        )

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [
                f"# Assignment Created Successfully\n",
                _format_assignment_markdown(data)
            ]
            return "\n".join(lines)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# TASK TOOLS
# ============================================================================

class ListTasksInput(BaseModel):
    """Input model for listing assignment tasks."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier",
        min_length=1,
        max_length=50
    )
    assignment_id: str = Field(
        ...,
        description="Assignment identifier",
        min_length=1,
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


@mcp.tool(
    name="ispw_list_tasks",
    annotations={
        "title": "List ISPW Assignment Tasks",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def ispw_list_tasks(params: ListTasksInput) -> str:
    """List all tasks for a specific ISPW assignment.

    Retrieves all tasks (individual work items) within an assignment. Tasks represent
    individual modules or components being worked on (e.g., COBOL programs, JCL, copybooks).

    Args:
        params (ListTasksInput): Validated input parameters containing:
            - srid (str): System Resource Identifier
            - assignment_id (str): Assignment identifier
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Formatted list of tasks or error message

    Examples:
        - List tasks: srid="ISPW", assignment_id="PLAY000001"
    """
    try:
        data = await _make_api_request(
            f"ispw/{params.srid}/assignments/{params.assignment_id}/tasks"
        )

        tasks = data.get("tasks", [])
        total = data.get("totalCount", len(tasks))

        if not tasks:
            return f"No tasks found for assignment '{params.assignment_id}'"

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [
                f"# Tasks for Assignment: {params.assignment_id}",
                f"",
                f"Found {total} task(s)\n"
            ]

            for task in tasks:
                lines.append(_format_task_markdown(task))

            return "\n".join(lines)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# RELEASE TOOLS
# ============================================================================

class ListReleasesInput(BaseModel):
    """Input model for listing releases."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier",
        min_length=1,
        max_length=50
    )
    release_id: Optional[str] = Field(
        default=None,
        description="Filter by specific release ID",
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class GetReleaseInput(BaseModel):
    """Input model for getting release details."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier",
        min_length=1,
        max_length=50
    )
    release_id: str = Field(
        ...,
        description="Release identifier to retrieve",
        min_length=1,
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class CreateReleaseInput(BaseModel):
    """Input model for creating a release."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier",
        min_length=1,
        max_length=50
    )
    release_id: str = Field(
        ...,
        description="Release identifier (must be unique)",
        min_length=1,
        max_length=100
    )
    stream: str = Field(
        ...,
        description="Stream name for the release",
        min_length=1,
        max_length=100
    )
    application: str = Field(
        ...,
        description="Application name for the release",
        min_length=1,
        max_length=100
    )
    description: Optional[str] = Field(
        default=None,
        description="Release description",
        max_length=500
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


@mcp.tool(
    name="ispw_list_releases",
    annotations={
        "title": "List ISPW Releases",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def ispw_list_releases(params: ListReleasesInput) -> str:
    """List ISPW releases for a specific SRID.

    Retrieves all releases or filters by release ID. Releases are collections of assignments
    for coordinated deployment to production or other environments.

    Args:
        params (ListReleasesInput): Validated input parameters containing:
            - srid (str): System Resource Identifier
            - release_id (Optional[str]): Filter by specific release ID
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Formatted list of releases or error message

    Examples:
        - List all releases: srid="ISPW"
        - Find specific release: srid="ISPW", release_id="REL001"
    """
    try:
        query_params = {}
        if params.release_id:
            query_params["releaseId"] = params.release_id

        data = await _make_api_request(
            f"ispw/{params.srid}/releases",
            params=query_params
        )

        releases = data.get("releases", [])
        total = data.get("totalCount", len(releases))

        if not releases:
            filter_desc = f" matching filter" if query_params else ""
            return f"No releases found{filter_desc} for SRID '{params.srid}'"

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# ISPW Releases for {params.srid}", "", f"Found {total} release(s)\n"]

            for release in releases:
                lines.append(_format_release_markdown(release))

            return "\n".join(lines)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="ispw_get_release",
    annotations={
        "title": "Get ISPW Release Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def ispw_get_release(params: GetReleaseInput) -> str:
    """Get detailed information about a specific ISPW release.

    Retrieves complete details for a release including owner, stream, application,
    status, and timestamps.

    Args:
        params (GetReleaseInput): Validated input parameters containing:
            - srid (str): System Resource Identifier
            - release_id (str): Release identifier to retrieve
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Formatted release details or error message

    Examples:
        - Get release: srid="ISPW", release_id="REL001"
    """
    try:
        data = await _make_api_request(
            f"ispw/{params.srid}/releases/{params.release_id}"
        )

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Release Details: {params.release_id}\n"]
            lines.append(_format_release_markdown(data))
            return "\n".join(lines)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="ispw_create_release",
    annotations={
        "title": "Create ISPW Release",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def ispw_create_release(params: CreateReleaseInput) -> str:
    """Create a new ISPW release.

    Creates a new release container for coordinating deployment of multiple assignments.
    The release must have a unique ID within the SRID.

    Args:
        params (CreateReleaseInput): Validated input parameters containing:
            - srid (str): System Resource Identifier
            - release_id (str): Unique release identifier
            - stream (str): Stream name for the release
            - application (str): Application name for the release
            - description (Optional[str]): Release description
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Created release details or error message

    Examples:
        - Create release: srid="ISPW", release_id="REL002", stream="PLAY",
          application="PLAY", description="Q1 2026 Release"
    """
    try:
        request_body = {
            "releaseId": params.release_id,
            "stream": params.stream,
            "application": params.application
        }
        if params.description:
            request_body["description"] = params.description

        data = await _make_api_request(
            f"ispw/{params.srid}/releases",
            method="POST",
            json_data=request_body
        )

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [
                f"# Release Created Successfully\n",
                _format_release_markdown(data)
            ]
            return "\n".join(lines)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# OPERATION TOOLS (Generate, Promote, Deploy)
# ============================================================================

class GenerateAssignmentInput(BaseModel):
    """Input model for generating an assignment."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier",
        min_length=1,
        max_length=50
    )
    assignment_id: str = Field(
        ...,
        description="Assignment identifier",
        min_length=1,
        max_length=100
    )
    level: Optional[str] = Field(
        default=None,
        description="Target level for generation",
        max_length=50
    )
    runtime_configuration: Optional[str] = Field(
        default=None,
        description="Runtime configuration",
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class PromoteAssignmentInput(BaseModel):
    """Input model for promoting an assignment."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier",
        min_length=1,
        max_length=50
    )
    assignment_id: str = Field(
        ...,
        description="Assignment identifier",
        min_length=1,
        max_length=100
    )
    level: Optional[str] = Field(
        default=None,
        description="Target level for promotion",
        max_length=50
    )
    change_type: Optional[ChangeType] = Field(
        default=None,
        description="Change type: S (Standard), I (Incidental), E (Emergency)"
    )
    execution_status: Optional[str] = Field(
        default=None,
        description="Execution status",
        max_length=50
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class DeployInput(BaseModel):
    """Input model for deployment operations."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier",
        min_length=1,
        max_length=50
    )
    target_id: str = Field(
        ...,
        description="Assignment, release, or set identifier",
        min_length=1,
        max_length=100
    )
    target_type: str = Field(
        ...,
        description="Type of deployment: 'assignment', 'release', or 'set'",
        pattern="^(assignment|release|set)$"
    )
    level: Optional[str] = Field(
        default=None,
        description="Target level for deployment",
        max_length=50
    )
    deploy_implementation_time: Optional[str] = Field(
        default=None,
        description="Scheduled deployment time (ISO 8601 format)",
        max_length=50
    )
    deploy_active: Optional[bool] = Field(
        default=None,
        description="Deploy to active libraries"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


@mcp.tool(
    name="ispw_generate_assignment",
    annotations={
        "title": "Generate ISPW Assignment",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def ispw_generate_assignment(params: GenerateAssignmentInput) -> str:
    """Generate code for an ISPW assignment.

    Initiates the generation process which compiles and prepares code within an assignment.
    This is typically the first step after code changes before promoting to higher environments.

    Args:
        params (GenerateAssignmentInput): Validated input parameters containing:
            - srid (str): System Resource Identifier
            - assignment_id (str): Assignment identifier
            - level (Optional[str]): Target level for generation
            - runtime_configuration (Optional[str]): Runtime configuration
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Operation status including operation ID and status URL, or error message

    Examples:
        - Generate assignment: srid="ISPW", assignment_id="PLAY000001"
        - Generate with level: srid="ISPW", assignment_id="PLAY000001", level="DEV"
    """
    try:
        request_body = {}
        if params.level:
            request_body["level"] = params.level
        if params.runtime_configuration:
            request_body["runtimeConfiguration"] = params.runtime_configuration

        data = await _make_api_request(
            f"ispw/{params.srid}/assignments/{params.assignment_id}/generate",
            method="POST",
            json_data=request_body
        )

        if params.response_format == ResponseFormat.MARKDOWN:
            return _format_operation_markdown(data)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="ispw_promote_assignment",
    annotations={
        "title": "Promote ISPW Assignment",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def ispw_promote_assignment(params: PromoteAssignmentInput) -> str:
    """Promote an ISPW assignment to the next level.

    Moves an assignment (and its tasks) through the development lifecycle to a higher level
    (e.g., from DEV to INT, INT to ACC, or ACC to PRD). Typically done after successful
    generation and testing.

    Args:
        params (PromoteAssignmentInput): Validated input parameters containing:
            - srid (str): System Resource Identifier
            - assignment_id (str): Assignment identifier
            - level (Optional[str]): Target level for promotion
            - change_type (Optional[ChangeType]): S (Standard), I (Incidental), E (Emergency)
            - execution_status (Optional[str]): Execution status
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Operation status including operation ID and status URL, or error message

    Examples:
        - Promote assignment: srid="ISPW", assignment_id="PLAY000001"
        - Promote to specific level: srid="ISPW", assignment_id="PLAY000001", level="INT",
          change_type="S"
    """
    try:
        request_body = {}
        if params.level:
            request_body["level"] = params.level
        if params.change_type:
            request_body["changeType"] = params.change_type.value
        if params.execution_status:
            request_body["executionStatus"] = params.execution_status

        data = await _make_api_request(
            f"ispw/{params.srid}/assignments/{params.assignment_id}/promote",
            method="POST",
            json_data=request_body
        )

        if params.response_format == ResponseFormat.MARKDOWN:
            return _format_operation_markdown(data)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="ispw_deploy",
    annotations={
        "title": "Deploy ISPW Assignment, Release, or Set",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def ispw_deploy(params: DeployInput) -> str:
    """Deploy an ISPW assignment, release, or set to target environment.

    Deploys code to the target environment. This is typically the final step in the
    deployment pipeline. Can deploy immediately or schedule for a future time.

    CAUTION: This is a destructive operation that affects production or target environments.

    Args:
        params (DeployInput): Validated input parameters containing:
            - srid (str): System Resource Identifier
            - target_id (str): Assignment, release, or set identifier
            - target_type (str): Type - 'assignment', 'release', or 'set'
            - level (Optional[str]): Target level for deployment
            - deploy_implementation_time (Optional[str]): Scheduled time (ISO 8601)
            - deploy_active (Optional[bool]): Deploy to active libraries
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Operation status including operation ID and status URL, or error message

    Examples:
        - Deploy assignment: srid="ISPW", target_id="PLAY000001", target_type="assignment"
        - Deploy release: srid="ISPW", target_id="REL001", target_type="release", level="PRD"
        - Scheduled deploy: srid="ISPW", target_id="PLAY000001", target_type="assignment",
          deploy_implementation_time="2026-01-15T10:00:00Z"
    """
    try:
        request_body = {}
        if params.level:
            request_body["level"] = params.level
        if params.deploy_implementation_time:
            request_body["deployImplementationTime"] = params.deploy_implementation_time
        if params.deploy_active is not None:
            request_body["deployActive"] = params.deploy_active

        # Determine endpoint based on target type
        if params.target_type == "assignment":
            endpoint = f"ispw/{params.srid}/assignments/{params.target_id}/deploy"
        elif params.target_type == "release":
            endpoint = f"ispw/{params.srid}/releases/{params.target_id}/deploy"
        elif params.target_type == "set":
            endpoint = f"ispw/{params.srid}/sets/{params.target_id}/deploy"
        else:
            return f"Error: Invalid target_type '{params.target_type}'. Must be 'assignment', 'release', or 'set'."

        data = await _make_api_request(
            endpoint,
            method="POST",
            json_data=request_body
        )

        if params.response_format == ResponseFormat.MARKDOWN:
            return _format_operation_markdown(data)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# SET AND PACKAGE TOOLS
# ============================================================================

class ListSetsInput(BaseModel):
    """Input model for listing sets."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier",
        min_length=1,
        max_length=50
    )
    set_id: Optional[str] = Field(
        default=None,
        description="Filter by specific set ID",
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class ListPackagesInput(BaseModel):
    """Input model for listing packages."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier",
        min_length=1,
        max_length=50
    )
    package_id: Optional[str] = Field(
        default=None,
        description="Filter by specific package ID",
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class GetPackageInput(BaseModel):
    """Input model for getting package details."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    srid: str = Field(
        default=ISPW_DEFAULT_SRID,
        description="System Resource Identifier",
        min_length=1,
        max_length=50
    )
    package_id: str = Field(
        ...,
        description="Package identifier to retrieve",
        min_length=1,
        max_length=100
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


@mcp.tool(
    name="ispw_list_sets",
    annotations={
        "title": "List ISPW Sets",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def ispw_list_sets(params: ListSetsInput) -> str:
    """List ISPW sets for a specific SRID.

    Retrieves all sets or filters by set ID. Sets are collections of components
    for deployment, providing another grouping mechanism for deployment units.

    Args:
        params (ListSetsInput): Validated input parameters containing:
            - srid (str): System Resource Identifier
            - set_id (Optional[str]): Filter by specific set ID
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Formatted list of sets or error message

    Examples:
        - List all sets: srid="ISPW"
        - Find specific set: srid="ISPW", set_id="SET001"
    """
    try:
        query_params = {}
        if params.set_id:
            query_params["setId"] = params.set_id

        data = await _make_api_request(
            f"ispw/{params.srid}/sets",
            params=query_params
        )

        sets = data.get("sets", [])
        total = data.get("totalCount", len(sets))

        if not sets:
            filter_desc = f" matching filter" if query_params else ""
            return f"No sets found{filter_desc} for SRID '{params.srid}'"

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# ISPW Sets for {params.srid}", "", f"Found {total} set(s)\n"]

            for s in sets:
                lines.append(f"## Set: {s.get('setId', 'N/A')}")
                lines.append(f"- **Description**: {s.get('description', 'N/A')}")
                lines.append(f"- **Owner**: {s.get('owner', 'N/A')}")
                lines.append(f"- **Application**: {s.get('application', 'N/A')}")
                lines.append(f"- **Status**: {s.get('status', 'N/A')}")
                lines.append("")

            return "\n".join(lines)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="ispw_list_packages",
    annotations={
        "title": "List ISPW Packages",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def ispw_list_packages(params: ListPackagesInput) -> str:
    """List ISPW packages for a specific SRID.

    Retrieves all packages or filters by package ID. Packages are deployment units
    that contain the actual components ready for deployment.

    Args:
        params (ListPackagesInput): Validated input parameters containing:
            - srid (str): System Resource Identifier
            - package_id (Optional[str]): Filter by specific package ID
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Formatted list of packages or error message

    Examples:
        - List all packages: srid="ISPW"
        - Find specific package: srid="ISPW", package_id="PKG001"
    """
    try:
        query_params = {}
        if params.package_id:
            query_params["packageId"] = params.package_id

        data = await _make_api_request(
            f"ispw/{params.srid}/packages",
            params=query_params
        )

        packages = data.get("packages", [])
        total = data.get("totalCount", len(packages))

        if not packages:
            filter_desc = f" matching filter" if query_params else ""
            return f"No packages found{filter_desc} for SRID '{params.srid}'"

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# ISPW Packages for {params.srid}", "", f"Found {total} package(s)\n"]

            for package in packages:
                lines.append(f"## Package: {package.get('packageId', 'N/A')}")
                lines.append(f"- **Description**: {package.get('description', 'N/A')}")
                lines.append(f"- **Owner**: {package.get('owner', 'N/A')}")
                lines.append(f"- **Application**: {package.get('application', 'N/A')}")
                lines.append(f"- **Status**: {package.get('status', 'N/A')}")
                lines.append(f"- **Created**: {_format_datetime(package.get('createdDate'))}")
                lines.append("")

            return "\n".join(lines)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


@mcp.tool(
    name="ispw_get_package",
    annotations={
        "title": "Get ISPW Package Details",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def ispw_get_package(params: GetPackageInput) -> str:
    """Get detailed information about a specific ISPW package.

    Retrieves complete details for a package including owner, application,
    status, and creation timestamp.

    Args:
        params (GetPackageInput): Validated input parameters containing:
            - srid (str): System Resource Identifier
            - package_id (str): Package identifier to retrieve
            - response_format (ResponseFormat): Output format (default: markdown)

    Returns:
        str: Formatted package details or error message

    Examples:
        - Get package: srid="ISPW", package_id="PKG001"
    """
    try:
        data = await _make_api_request(
            f"ispw/{params.srid}/packages/{params.package_id}"
        )

        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [f"# Package Details: {params.package_id}\n"]
            lines.append(f"## Package: {data.get('packageId', 'N/A')}")
            lines.append(f"- **Description**: {data.get('description', 'N/A')}")
            lines.append(f"- **Owner**: {data.get('owner', 'N/A')}")
            lines.append(f"- **Application**: {data.get('application', 'N/A')}")
            lines.append(f"- **Status**: {data.get('status', 'N/A')}")
            lines.append(f"- **Created**: {_format_datetime(data.get('createdDate'))}")
            return "\n".join(lines)
        else:
            return json.dumps(data, indent=2)

    except Exception as e:
        return _handle_api_error(e)


# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the ISPW MCP server."""
    # Check if required environment variable is set
    if not ISPW_API_TOKEN:
        print("Warning: ISPW_API_TOKEN environment variable not set.")
        print("Please set it in your .env file or environment before using the server.")

    mcp.run()


if __name__ == "__main__":
    main()
