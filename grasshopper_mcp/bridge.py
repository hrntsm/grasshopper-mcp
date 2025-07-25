import json
import socket
import sys
import traceback
from typing import Any

# Use MCP server
from mcp.server.fastmcp import FastMCP

# Set Grasshopper MCP connection parameters
GRASSHOPPER_HOST = "localhost"
GRASSHOPPER_PORT = 8080  # Default port, can be modified as needed

# Create MCP server
server = FastMCP("Grasshopper Bridge")


def load_component_mapping():
    """Load component mapping from external JSON file"""
    try:
        import os

        # Get the path to the component mapping JSON file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(current_dir, "component_mapping.json")

        # Read the JSON file
        with open(json_file_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(
            f"Warning: component_mapping.json not found at {json_file_path}. Using fallback data.",
            file=sys.stderr,
        )
        # Fallback to a minimal component mapping if file is not found
        return {"slider": "Number Slider", "panel": "Panel", "add": "Addition"}
    except json.JSONDecodeError as e:
        print(
            f"Warning: Error parsing component_mapping.json: {e}. Using fallback data.",
            file=sys.stderr,
        )
        # Fallback to a minimal component mapping if JSON is invalid
        return {"slider": "Number Slider", "panel": "Panel", "add": "Addition"}
    except Exception as e:
        print(
            f"Warning: Unexpected error loading component_mapping.json: {e}. Using fallback data.",
            file=sys.stderr,
        )
        # Fallback to a minimal component mapping for any other errors
        return {"slider": "Number Slider", "panel": "Panel", "add": "Addition"}


def send_to_grasshopper(
    command_type: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Send command to Grasshopper MCP"""
    if params is None:
        params = {}

    # Create command
    command = {"type": command_type, "parameters": params}

    try:
        print(
            f"Sending command to Grasshopper: {command_type} with params: {params}",
            file=sys.stderr,
        )

        # Connect to Grasshopper MCP
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((GRASSHOPPER_HOST, GRASSHOPPER_PORT))

        # Send command
        command_json = json.dumps(command)
        client.sendall((command_json + "\n").encode("utf-8"))
        print(f"Command sent: {command_json}", file=sys.stderr)

        # Receive response
        response_data = b""
        while True:
            chunk = client.recv(4096)
            if not chunk:
                break
            response_data += chunk
            if response_data.endswith(b"\n"):
                break

        # Handle possible BOM
        response_str = response_data.decode("utf-8-sig").strip()
        print(f"Response received: {response_str}", file=sys.stderr)

        # Parse JSON response
        response = json.loads(response_str)
        client.close()
        return response
    except Exception as e:
        print(f"Error communicating with Grasshopper: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {
            "success": False,
            "error": f"Error communicating with Grasshopper: {str(e)}",
        }


# Register MCP tools
@server.tool("add_component")
def add_component(component_type: str, x: float, y: float):
    """
    Add a component to the Grasshopper canvas

    Args:
        component_type: Component type (point, curve, circle, line, panel, slider)
        x: X coordinate on the canvas
        y: Y coordinate on the canvas

    Returns:
        Result of adding the component
    """
    # Handle common component name confusion issues
    component_mapping = load_component_mapping()

    # Check and correct component type
    normalized_type = component_type.lower()
    if normalized_type in component_mapping:
        component_type = component_mapping[normalized_type]
        print(
            f"Component type normalized from '{normalized_type}' to '{component_mapping[normalized_type]}'",
            file=sys.stderr,
        )

    params = {"type": component_type, "x": x, "y": y}

    return send_to_grasshopper("add_component", params)


@server.tool("clear_document")
def clear_document():
    """Clear the Grasshopper document"""
    return send_to_grasshopper("clear_document")


@server.tool("save_document")
def save_document(path: str):
    """
    Save the Grasshopper document

    Args:
        path: Save path

    Returns:
        Result of the save operation
    """
    params = {"path": path}

    return send_to_grasshopper("save_document", params)


@server.tool("load_document")
def load_document(path: str):
    """
    Load a Grasshopper document

    Args:
        path: Document path

    Returns:
        Result of the load operation
    """
    params = {"path": path}

    return send_to_grasshopper("load_document", params)


@server.tool("get_document_info")
def get_document_info():
    """Get information about the Grasshopper document"""
    return send_to_grasshopper("get_document_info")


@server.tool("connect_components")
def connect_components(
    source_id: str,
    target_id: str,
    source_param: str | None = None,
    target_param: str | None = None,
    source_param_index: int | None = None,
    target_param_index: int | None = None,
):
    """
    Connect two components in the Grasshopper canvas

    Args:
        source_id: ID of the source component (output)
        target_id: ID of the target component (input)
        source_param: Name of the source parameter (optional)
        target_param: Name of the target parameter (optional)
        source_param_index: Index of the source parameter (optional, used if source_param is not provided)
        target_param_index: Index of the target parameter (optional, used if target_param is not provided)

    Returns:
        Result of connecting the components
    """
    # Get target component information, check if connections already exist
    target_info = send_to_grasshopper("get_component_info", {"componentId": target_id})

    # Check component type, if it's a component that needs multiple inputs (like Addition, Subtraction, etc.), intelligently assign inputs
    if target_info and "result" in target_info and "type" in target_info["result"]:
        component_type = target_info["result"]["type"]

        # Get existing connections
        connections = send_to_grasshopper("get_connections")
        existing_connections = []

        if connections and "result" in connections:
            for conn in connections["result"]:
                if conn.get("targetId") == target_id:
                    existing_connections.append(conn)

        # For specific components that need multiple inputs, automatically select the correct input port
        if component_type in [
            "Addition",
            "Subtraction",
            "Multiplication",
            "Division",
            "Math",
        ]:
            # If no target parameter is specified and there's already a connection to the first input, automatically connect to the second input
            if target_param is None and target_param_index is None:
                # Check if the first input is already occupied
                first_input_occupied = False
                for conn in existing_connections:
                    if (
                        conn.get("targetParam") == "A"
                        or conn.get("targetParamIndex") == 0
                    ):
                        first_input_occupied = True
                        break

                # If the first input is already occupied, connect to the second input
                if first_input_occupied:
                    target_param = "B"  # The second input is usually named B
                else:
                    target_param = "A"  # Otherwise connect to the first input

    params = {"sourceId": source_id, "targetId": target_id}

    if source_param is not None:
        params["sourceParam"] = source_param
    elif source_param_index is not None:
        params["sourceParamIndex"] = str(source_param_index)

    if target_param is not None:
        params["targetParam"] = target_param
    elif target_param_index is not None:
        params["targetParamIndex"] = str(target_param_index)

    return send_to_grasshopper("connect_components", params)


@server.tool("create_pattern")
def create_pattern(description: str):
    """
    Create a pattern of components based on a high-level description

    Args:
        description: High-level description of what to create (e.g., '3D voronoi cube')

    Returns:
        Result of creating the pattern
    """
    params = {"description": description}

    return send_to_grasshopper("create_pattern", params)


@server.tool("get_available_patterns")
def get_available_patterns(query: str):
    """
    Get a list of available patterns that match a query

    Args:
        query: Query to search for patterns

    Returns:
        List of available patterns
    """
    params = {"query": query}

    return send_to_grasshopper("get_available_patterns", params)


@server.tool("get_component_info")
def get_component_info(component_id: str):
    """
    Get detailed information about a specific component

    Args:
        component_id: ID of the component to get information about

    Returns:
        Detailed information about the component, including inputs, outputs, and current values
    """
    params = {"componentId": component_id}

    result = send_to_grasshopper("get_component_info", params)

    # Enhance return result, add more parameter information
    if result and "result" in result:
        component_data = result["result"]

        # Get component type
        if "type" in component_data:
            component_type = component_data["type"]

            # Query component library to get detailed parameter information for this component type
            component_library = get_component_library()
            if "components" in component_library:
                for lib_component in component_library["components"]:
                    if (
                        lib_component.get("name") == component_type
                        or lib_component.get("fullName") == component_type
                    ):
                        # Merge parameter information from component library into return result
                        if "settings" in lib_component:
                            component_data["availableSettings"] = lib_component[
                                "settings"
                            ]
                        if "inputs" in lib_component:
                            component_data["inputDetails"] = lib_component["inputs"]
                        if "outputs" in lib_component:
                            component_data["outputDetails"] = lib_component["outputs"]
                        if "usage_examples" in lib_component:
                            component_data["usageExamples"] = lib_component[
                                "usage_examples"
                            ]
                        if "common_issues" in lib_component:
                            component_data["commonIssues"] = lib_component[
                                "common_issues"
                            ]
                        break

            # Special handling for certain component types
            if component_type == "Number Slider":
                # Try to get actual settings of current slider from component data
                if "currentSettings" not in component_data:
                    component_data["currentSettings"] = {
                        "min": component_data.get("min", 0),
                        "max": component_data.get("max", 10),
                        "value": component_data.get("value", 5),
                        "rounding": component_data.get("rounding", 0.1),
                        "type": component_data.get("type", "float"),
                    }

            # Add component connection information
            connections = send_to_grasshopper("get_connections")
            if connections and "result" in connections:
                # Find all connections related to this component
                related_connections = []
                for conn in connections["result"]:
                    if (
                        conn.get("sourceId") == component_id
                        or conn.get("targetId") == component_id
                    ):
                        related_connections.append(conn)

                if related_connections:
                    component_data["connections"] = related_connections

    return result


@server.tool("get_all_components")
def get_all_components():
    """
    Get a list of all components in the current document

    Returns:
        List of all components in the document with their IDs, types, and positions
    """
    result = send_to_grasshopper("get_all_components")

    # Enhance return result, add more parameter information for each component
    if result and "result" in result:
        components = result["result"]
        component_library = get_component_library()

        # Get all connection information
        connections = send_to_grasshopper("get_connections")
        connections_data = connections.get("result", []) if connections else []

        # Add detailed information for each component
        for component in components:
            if "id" in component and "type" in component:
                component_id = component["id"]
                component_type = component["type"]

                # Add detailed parameter information for the component
                if "components" in component_library:
                    for lib_component in component_library["components"]:
                        if (
                            lib_component.get("name") == component_type
                            or lib_component.get("fullName") == component_type
                        ):
                            # Merge parameter information from component library into component data
                            if "settings" in lib_component:
                                component["availableSettings"] = lib_component[
                                    "settings"
                                ]
                            if "inputs" in lib_component:
                                component["inputDetails"] = lib_component["inputs"]
                            if "outputs" in lib_component:
                                component["outputDetails"] = lib_component["outputs"]
                            break

                # Add component connection information
                related_connections = []
                for conn in connections_data:
                    if (
                        conn.get("sourceId") == component_id
                        or conn.get("targetId") == component_id
                    ):
                        related_connections.append(conn)

                if related_connections:
                    component["connections"] = related_connections

                # Special handling for certain component types
                if component_type == "Number Slider":
                    # Try to get the current slider settings
                    component_info = send_to_grasshopper(
                        "get_component_info", {"componentId": component_id}
                    )
                    if component_info and "result" in component_info:
                        info_data = component_info["result"]
                        component["currentSettings"] = {
                            "min": info_data.get("min", 0),
                            "max": info_data.get("max", 10),
                            "value": info_data.get("value", 5),
                            "rounding": info_data.get("rounding", 0.1),
                        }

    return result


@server.tool("get_connections")
def get_connections():
    """
    Get a list of all connections between components in the current document

    Returns:
        List of all connections between components
    """
    return send_to_grasshopper("get_connections")


@server.tool("search_components")
def search_components(query: str):
    """
    Search for components by name or category

    Args:
        query: Search query

    Returns:
        List of components matching the search query
    """
    params = {"query": query}

    return send_to_grasshopper("search_components", params)


@server.tool("get_component_parameters")
def get_component_parameters(component_type: str):
    """
    Get a list of parameters for a specific component type

    Args:
        component_type: Type of component to get parameters for

    Returns:
        List of input and output parameters for the component type
    """
    params = {"componentType": component_type}

    return send_to_grasshopper("get_component_parameters", params)


@server.tool("validate_connection")
def validate_connection(
    source_id: str,
    target_id: str,
    source_param: str | None = None,
    target_param: str | None = None,
):
    """
    Validate if a connection between two components is possible

    Args:
        source_id: ID of the source component (output)
        target_id: ID of the target component (input)
        source_param: Name of the source parameter (optional)
        target_param: Name of the target parameter (optional)

    Returns:
        Whether the connection is valid and any potential issues
    """
    params = {"sourceId": source_id, "targetId": target_id}

    if source_param is not None:
        params["sourceParam"] = source_param

    if target_param is not None:
        params["targetParam"] = target_param

    return send_to_grasshopper("validate_connection", params)


# Register MCP resources
@server.resource("grasshopper://status")
def get_grasshopper_status():
    """Get Grasshopper status"""
    try:
        # Get document information
        doc_info = send_to_grasshopper("get_document_info")

        # Get all components (using enhanced get_all_components)
        components_result = get_all_components()
        components = components_result.get("result", []) if components_result else []

        # Get all connections
        connections = send_to_grasshopper("get_connections")

        # Add hint information for common components
        component_hints = {
            "Number Slider": {
                "description": "Single numeric value slider with adjustable range",
                "common_usage": "Use for single numeric inputs like radius, height, count, etc.",
                "parameters": ["min", "max", "value", "rounding", "type"],
                "NOT_TO_BE_CONFUSED_WITH": "MD Slider (which is for multi-dimensional values)",
            },
            "MD Slider": {
                "description": "Multi-dimensional slider for vector input",
                "common_usage": "Use for vector inputs, NOT for simple numeric values",
                "NOT_TO_BE_CONFUSED_WITH": "Number Slider (which is for single numeric values)",
            },
            "Panel": {
                "description": "Displays text or numeric data",
                "common_usage": "Use for displaying outputs and debugging",
            },
            "Addition": {
                "description": "Adds two or more numbers",
                "common_usage": "Connect two Number Sliders to inputs A and B",
                "parameters": ["A", "B"],
                "connection_tip": "First slider should connect to input A, second to input B",
            },
        }

        # Add summary of current parameter values for each component
        component_summaries = []
        for component in components:
            summary = {
                "id": component.get("id", ""),
                "type": component.get("type", ""),
                "position": {"x": component.get("x", 0), "y": component.get("y", 0)},
            }

            # Add component-specific parameter information
            if "currentSettings" in component:
                summary["settings"] = component["currentSettings"]
            elif component.get("type") == "Number Slider":
                # Try to extract slider settings from component information
                summary["settings"] = {
                    "min": component.get("min", 0),
                    "max": component.get("max", 10),
                    "value": component.get("value", 5),
                    "rounding": component.get("rounding", 0.1),
                }

            # Add connection information summary
            if "connections" in component:
                conn_summary = []
                for conn in component["connections"]:
                    if conn.get("sourceId") == component.get("id"):
                        conn_summary.append(
                            {
                                "type": "output",
                                "to": conn.get("targetId", ""),
                                "sourceParam": conn.get("sourceParam", ""),
                                "targetParam": conn.get("targetParam", ""),
                            }
                        )
                    else:
                        conn_summary.append(
                            {
                                "type": "input",
                                "from": conn.get("sourceId", ""),
                                "sourceParam": conn.get("sourceParam", ""),
                                "targetParam": conn.get("targetParam", ""),
                            }
                        )

                if conn_summary:
                    summary["connections"] = conn_summary

            component_summaries.append(summary)

        return {
            "status": "Connected to Grasshopper",
            "document": doc_info.get("result", {}),
            "components": component_summaries,
            "connections": connections.get("result", []),
            "component_hints": component_hints,
            "recommendations": [
                "When needing a simple numeric input control, ALWAYS use 'Number Slider', not MD Slider",
                "For vector inputs (like 3D points), use 'MD Slider' or 'Construct Point' with multiple Number Sliders",
                "Use 'Panel' to display outputs and debug values",
                "When connecting multiple sliders to Addition, first slider goes to input A, second to input B",
            ],
            "canvas_summary": f"Current canvas has {len(component_summaries)} components and {len(connections.get('result', []))} connections",
        }
    except Exception as e:
        print(f"Error getting Grasshopper status: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return {
            "status": f"Error: {str(e)}",
            "document": {},
            "components": [],
            "connections": [],
        }


@server.resource("grasshopper://component_guide")
def get_component_guide():
    """Get guide for Grasshopper components and connections"""
    try:
        import json
        import os

        # Get the path to the component guide JSON file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(current_dir, "component_guide.json")

        # Read the JSON file
        with open(json_file_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(
            f"Warning: component_guide.json not found at {json_file_path}. Using fallback data.",
            file=sys.stderr,
        )
        # Fallback to a minimal component guide if file is not found
        return {
            "title": "Grasshopper Component Guide",
            "description": "Guide for creating and connecting Grasshopper components",
            "components": [],
            "connectionRules": [],
            "commonIssues": [],
            "tips": [],
        }
    except json.JSONDecodeError as e:
        print(
            f"Warning: Error parsing component_guide.json: {e}. Using fallback data.",
            file=sys.stderr,
        )
        # Fallback to a minimal component guide if JSON is invalid
        return {
            "title": "Grasshopper Component Guide",
            "description": "Guide for creating and connecting Grasshopper components",
            "components": [],
            "connectionRules": [],
            "commonIssues": [],
            "tips": [],
        }
    except Exception as e:
        print(
            f"Warning: Unexpected error loading component_guide.json: {e}. Using fallback data.",
            file=sys.stderr,
        )
        # Fallback to a minimal component guide for any other errors
        return {
            "title": "Grasshopper Component Guide",
            "description": "Guide for creating and connecting Grasshopper components",
            "components": [],
            "connectionRules": [],
            "commonIssues": [],
            "tips": [],
        }


@server.resource("grasshopper://component_library")
def get_component_library():
    """Get a comprehensive library of Grasshopper components"""
    # This resource provides a more comprehensive component library with detailed information for common components
    try:
        import json
        import os

        # Get the path to the component library JSON file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(current_dir, "component_library.json")

        # Read the JSON file
        with open(json_file_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(
            f"Warning: component_library.json not found at {json_file_path}. Using fallback data.",
            file=sys.stderr,
        )
        # Fallback to a minimal component library if file is not found
        return {"categories": [], "dataTypes": []}
    except json.JSONDecodeError as e:
        print(
            f"Warning: Error parsing component_library.json: {e}. Using fallback data.",
            file=sys.stderr,
        )
        # Fallback to a minimal component library if JSON is invalid
        return {"categories": [], "dataTypes": []}
    except Exception as e:
        print(
            f"Warning: Unexpected error loading component_library.json: {e}. Using fallback data.",
            file=sys.stderr,
        )
        # Fallback to a minimal component library for any other errors
        return {"categories": [], "dataTypes": []}


def main():
    """Main entry point for the Grasshopper MCP Bridge Server"""
    try:
        # Start MCP server
        print("Starting Grasshopper MCP Bridge Server...", file=sys.stderr)
        print("Please add this MCP server to Claude Desktop", file=sys.stderr)
        server.run()
    except Exception as e:
        print(f"Error starting MCP server: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
