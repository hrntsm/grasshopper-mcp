# Grasshopper MCP Command Generation Guide

When you need to create and connect components in Grasshopper, please generate commands according to the following structured format. This will ensure that commands can be correctly parsed and executed.

## Add Component

```json
{
  "command": "add_component",
  "type": "[component_type]",
  "x": [x_coordinate],
  "y": [y_coordinate]
}
```

### Important Notes:

- For components that require plane input (such as Box, Circle, Rectangle, etc.), always use "xy plane" as the plane source, not Point components
- Use standardized component names such as "xy plane", "box", "circle", "number slider", etc.
- Coordinate values should be numbers, recommend using grid layout (spacing of about 200-300 units between x and y)

## Connect Components

```json
{
  "command": "connect_components",
  "sourceId": "[source_component_id]",
  "sourceParam": "[source_parameter_name]",
  "targetId": "[target_component_id]",
  "targetParam": "[target_parameter_name]"
}
```

### Important Notes:

- Use standardized parameter names such as "Plane", "Base", "Radius", "X Size", "Y Size", "Z Size", "Number", etc.
- Ensure all components are created first, then perform connections
- For connections from plane to geometry components, source parameter should be "Plane", target parameter should be "Base" or "Plane"

## Complete Example for Creating a Cube

The following is the complete command sequence for creating a cube:

```json
// 1. Add XY Plane component
{
  "command": "add_component",
  "type": "xy plane",
  "x": 100,
  "y": 100
}

// 2. Add X size slider
{
  "command": "add_component",
  "type": "number slider",
  "x": 100,
  "y": 200
}

// 3. Add Y size slider
{
  "command": "add_component",
  "type": "number slider",
  "x": 100,
  "y": 300
}

// 4. Add Z size slider
{
  "command": "add_component",
  "type": "number slider",
  "x": 100,
  "y": 400
}

// 5. Add Box component
{
  "command": "add_component",
  "type": "box",
  "x": 400,
  "y": 250
}

// 6. Connect XY Plane to Box
{
  "command": "connect_components",
  "sourceId": "[plane_id]",
  "sourceParam": "Plane",
  "targetId": "[box_id]",
  "targetParam": "Base"
}

// 7. Connect X size slider to Box
{
  "command": "connect_components",
  "sourceId": "[slider1_id]",
  "sourceParam": "Number",
  "targetId": "[box_id]",
  "targetParam": "X Size"
}

// 8. Connect Y size slider to Box
{
  "command": "connect_components",
  "sourceId": "[slider2_id]",
  "sourceParam": "Number",
  "targetId": "[box_id]",
  "targetParam": "Y Size"
}

// 9. Connect Z size slider to Box
{
  "command": "connect_components",
  "sourceId": "[slider3_id]",
  "sourceParam": "Number",
  "targetId": "[box_id]",
  "targetParam": "Z Size"
}
```

## Common Errors and Solutions

1. **Using Point component instead of XY Plane**:

   - Error: Using Point component as plane input source
   - Solution: Always use XY Plane component as plane input source

2. **Incorrect parameter names**:

   - Error: Using non-standard parameter names, such as "radius" instead of "Radius"
   - Solution: Use standardized parameter names with capitalized first letters

3. **Incorrect connection order**:

   - Error: Attempting to connect before creating all components
   - Solution: Create all components first, then perform connections

4. **Incorrect component type**:
   - Error: Using parameter containers instead of actual components, such as using Circle parameter container instead of Circle component
   - Solution: Ensure using the correct component type
