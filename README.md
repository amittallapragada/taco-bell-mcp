# Taco Bell MCP Server

An MCP (Model Context Protocol) server for interacting with the Taco Bell API. Search for locations and browse menus.

## Features

### Tools

- **`search_locations`** - Find nearby Taco Bell locations by coordinates
- **`get_restaurant_menu`** - Get the full menu for a specific location

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Add to your Claude Desktop config:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "taco-bell": {
      "command": "/Users/amittallapragada/Code/taco-bell-mcp/.venv/bin/python3",
      "args": ["/Users/amittallapragada/Code/taco-bell-mcp/main.py"]
    }
  }
}
```

## Implementation Status

Both API functions are fully implemented:

1. **`taco_bell_search_locations()`** ✅
   - Searches for nearby Taco Bell locations by latitude/longitude
   - Returns store details including address, hours, distance, capabilities

2. **`taco_bell_get_menu()`** ✅
   - Fetches complete menu data for a specific store
   - Returns all menu categories, items, prices, and descriptions

Next:
I want to add sessions, adding items, customizing items, and even checking out. To my knowledge you can't do these with the exposed api on the taco bell website. I think it requires playwright or selenium to click through the pages to accomplish this. Would appreciate help if anyone is interested!

## Usage Example

```python
# 1. Search for locations by coordinates
search_locations(latitude=37.7749, longitude=-122.4194)

# 2. Get menu for a specific store
get_restaurant_menu(store_id="042266")
```

## API Endpoints Used

- **Location Search**: `https://www.tacobell.com/tacobellwebservices/v4/tacobell/stores`
- **Menu Retrieval**: `https://www.tacobell.com/tacobellwebservices/v4/tacobell/products/menu/{store_id}`
