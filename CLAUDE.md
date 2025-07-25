# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Grasshopper MCP Bridge is a bridging server that connects Grasshopper (visual programming interface for Rhino 3D) with Claude Desktop using the Model Context Protocol (MCP). The system enables natural language control of Grasshopper through Claude.

## Development Commands

### Python MCP Bridge Server

**Install for development:**

```bash
pip install -e .
```

**Install from PyPI:**

```bash
pip install grasshopper-mcp
```

**Run the bridge server:**

```bash
python -m grasshopper_mcp.bridge
```

**Run from repository:**

```bash
cd grasshopper-mcp
python -m grasshopper_mcp.bridge
```

### C# Grasshopper Plugin

**Build the plugin:**

```bash
dotnet build GH_MCP/GH_MCP.sln
```

**Debug in Visual Studio:**

- Use launch profiles "Rhino 8 - netcore" or "Rhino 8 - netfx"
- Automatically launches Rhino with Grasshopper and loads the plugin

**Manual installation:**

- Copy compiled `GH_MCP.gha` to `%APPDATA%\Grasshopper\Libraries\`
- Or use pre-built version from `releases/GH_MCP.gha`

## Architecture Overview

The system consists of three main components:

### 1. Grasshopper Plugin (C# - `GH_MCP/`)

- **Main Component**: `GH_MCPComponent.cs` - TCP server that listens on port 8080
- **Command Registry**: `Commands/GrasshopperCommandRegistry.cs` - Routes commands to appropriate handlers
- **Command Handlers**:
  - `ComponentCommandHandler.cs` - Add/manage Grasshopper components
  - `ConnectionCommandHandler.cs` - Connect components together
  - `DocumentCommandHandler.cs` - Document operations (save/load/clear)
  - `GeometryCommandHandler.cs` - Geometry creation
  - `IntentCommandHandler.cs` - High-level intent recognition

### 2. Python MCP Bridge (`grasshopper_mcp/`)

- **Bridge Server**: `bridge.py` - FastMCP server that translates MCP calls to TCP commands
- **Communication**: TCP client that sends JSON commands to Grasshopper plugin
- **Tools**: Exposes MCP tools for component creation, connection, document management

### 3. Component Knowledge Base

- **Configuration**: `GH_MCP/GH_MCP/Resources/ComponentKnowledgeBase.json`
- **Component Library**: Definitions of inputs/outputs for common Grasshopper components
- **Fuzzy Matching**: `Utils/FuzzyMatcher.cs` handles component name variations
- **Intent Recognition**: `Utils/IntentRecognizer.cs` processes high-level descriptions

## Key Communication Flow

1. Claude Desktop → Python MCP Bridge (MCP protocol)
2. Python Bridge → Grasshopper Plugin (TCP/JSON on localhost:8080)
3. Grasshopper Plugin → Grasshopper Canvas (Direct API calls)

## Component Architecture Patterns

### Command Pattern

All operations use the `Command` class (`Models/GrasshopperCommand.cs`) with:

- `type`: Command type (add_component, connect_components, etc.)
- `parameters`: Dictionary of command parameters

### Handler Registration

Commands are registered in `GrasshopperCommandRegistry.Initialize()`:

```csharp
RegisterCommand("add_component", ComponentCommandHandler.AddComponent);
RegisterCommand("connect_components", ConnectionCommandHandler.ConnectComponents);
```

### Enhanced Component Information

The bridge provides enriched component data by:

- Merging runtime component state with knowledge base definitions
- Adding connection information for each component
- Providing usage examples and common issues from the knowledge base

## Important Development Notes

### Component Name Normalization

The system handles component name variations through `FuzzyMatcher`:

- "number slider" → "Number Slider"
- "add" → "Addition"
- "xy plane" → "XY Plane"

### Connection Intelligence

`connect_components` automatically handles:

- Smart input assignment for math components (A/B inputs)
- Connection validation before execution
- Parameter name resolution (supports both names and indices)

### Threading Considerations

- Grasshopper operations must run on UI thread via `RhinoApp.InvokeOnUiThread()`
- TCP server runs on background thread
- All component modifications are synchronized

### Error Handling

Commands return structured responses:

```json
{
  "success": true/false,
  "result": {...},
  "error": "error message if failed"
}
```

## Common Development Patterns

### Adding New MCP Tools

1. Add tool function in `bridge.py` with `@server.tool` decorator
2. Implement corresponding command handler in C#
3. Register command in `GrasshopperCommandRegistry`
4. Update component knowledge base if needed

### Extending Component Support

1. Add component definition to `ComponentKnowledgeBase.json`
2. Update fuzzy matcher patterns if needed
3. Add any special handling in `ComponentCommandHandler`

### Testing Components

1. Start Rhino/Grasshopper with GH_MCP component on canvas
2. Run Python bridge: `python -m grasshopper_mcp.bridge`
3. Connect Claude Desktop with MCP configuration
4. Test commands through Claude Desktop interface

## Port Configuration

- **Default Port**: 8080 (configurable in Grasshopper component)
- **Bridge Connection**: `localhost:8080`
- **Claude Desktop**: Connects to Python bridge via MCP protocol

## File Structure Context

```
grasshopper-mcp/
├── grasshopper_mcp/           # Python MCP bridge
│   ├── bridge.py             # Main bridge server (FastMCP)
│   └── __init__.py
├── GH_MCP/                   # C# Grasshopper plugin
│   └── GH_MCP/
│       ├── Commands/         # Command handlers
│       ├── Models/          # Data models
│       ├── Utils/           # Utilities (fuzzy matching, etc.)
│       ├── Resources/       # Component knowledge base
│       └── *.cs            # Main component files
├── releases/                # Pre-built binaries
│   └── GH_MCP.gha          # Compiled plugin
└── setup.py               # Python package setup
```

This architecture enables seamless integration between Claude's natural language interface and Grasshopper's visual programming environment through a robust, extensible bridge system.
