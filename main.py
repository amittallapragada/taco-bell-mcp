#!/usr/bin/env python3
"""
Taco Bell MCP Server
Provides tools for interacting with the Taco Bell API:
- Search for locations
- Browse menu items
"""

import asyncio
import json
import time
from typing import Any, Optional
from collections.abc import Sequence

import aiohttp

from mcp.server import Server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)
import mcp.server.stdio


# ============================================================================
# Taco Bell API Functions
# ============================================================================

async def taco_bell_search_locations(zipcode: Optional[str] = None, 
                                     latitude: Optional[float] = None,
                                     longitude: Optional[float] = None,
                                     radius: int = 10) -> list[dict]:
    """
    Search for Taco Bell locations by coordinates or zipcode
    """
    # If zipcode provided, convert to coordinates using a geocoding service
    if zipcode and not (latitude and longitude):
        # TODO: Implement geocoding for zipcode
        # For now, raise an error
        raise ValueError("Zipcode search not yet implemented. Please use latitude/longitude.")
    
    if not latitude or not longitude:
        raise ValueError("Either zipcode or latitude/longitude must be provided")
    
    # Taco Bell API endpoint
    url = "https://www.tacobell.com/tacobellwebservices/v4/tacobell/stores"
    
    # Build query parameters
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "_": str(int(time.time() * 1000))  # Timestamp in milliseconds
    }
    
    # Headers matching the curl request
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://www.tacobell.com/locations",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"API request failed with status {response.status}")
            
            data = await response.json()
            
            # Extract and format the nearby stores
            stores = data.get("nearByStores", [])
            
            # Simplify the response to include key information
            simplified_stores = []
            for store in stores:
                simplified_stores.append({
                    "store_id": store.get("storeNumber"),
                    "name": store.get("name"),
                    "phone": store.get("phoneNumber"),
                    "distance": store.get("formattedDistance"),
                    "status": store.get("storeStatus"),
                    "address": {
                        "street": store.get("address", {}).get("line1"),
                        "city": store.get("address", {}).get("town"),
                        "state": store.get("address", {}).get("region", {}).get("isocode"),
                        "zip": store.get("address", {}).get("postalCode")
                    },
                    "coordinates": {
                        "latitude": store.get("geoPoint", {}).get("latitude"),
                        "longitude": store.get("geoPoint", {}).get("longitude")
                    },
                    "hours": {
                        "opening": store.get("todayBusinessHours", {}).get("openingTime", {}).get("formattedHour"),
                        "closing": store.get("todayBusinessHours", {}).get("closingTime", {}).get("formattedHour"),
                        "day": store.get("todayBusinessHours", {}).get("weekDay")
                    },
                    "capabilities": store.get("capabilities", {}),
                    "delivery_available": store.get("delivery", False),
                    "pickup_available": store.get("pickupStoreStatusForLocation") == "Activated"
                })
            
            return simplified_stores


async def taco_bell_get_menu(store_id: str) -> dict:
    """
    Get menu for a specific Taco Bell location
    """
    # Taco Bell menu API endpoint
    url = f"https://www.tacobell.com/tacobellwebservices/v4/tacobell/products/menu/{store_id}"
    
    # Headers matching the curl request
    headers = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": f"https://www.tacobell.com/food?store={store_id}",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"API request failed with status {response.status}")
            
            data = await response.json()
            return data


# ============================================================================
# MCP Server Setup
# ============================================================================

server = Server("taco-bell-mcp")


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources"""
    return []


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="search_locations",
            description="Search for Taco Bell locations by zipcode or coordinates",
            inputSchema={
                "type": "object",
                "properties": {
                    "zipcode": {
                        "type": "string",
                        "description": "5-digit US zipcode"
                    },
                    "latitude": {
                        "type": "number",
                        "description": "Latitude coordinate"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude coordinate"
                    },
                    "radius": {
                        "type": "number",
                        "description": "Search radius in miles (default: 10)",
                        "default": 10
                    }
                },
                "oneOf": [
                    {"required": ["zipcode"]},
                    {"required": ["latitude", "longitude"]}
                ]
            }
        ),
        Tool(
            name="get_restaurant_menu",
            description="Get the full menu for a specific Taco Bell location",
            inputSchema={
                "type": "object",
                "properties": {
                    "store_id": {
                        "type": "string",
                        "description": "The store ID from location search"
                    }
                },
                "required": ["store_id"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls"""
    
    if name == "search_locations":
        zipcode = arguments.get("zipcode")
        latitude = arguments.get("latitude")
        longitude = arguments.get("longitude")
        radius = arguments.get("radius", 10)
        
        try:
            locations = await taco_bell_search_locations(
                zipcode=zipcode,
                latitude=latitude,
                longitude=longitude,
                radius=radius
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(locations, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error searching locations: {str(e)}"
            )]
    
    elif name == "get_restaurant_menu":
        store_id = arguments["store_id"]
        
        try:
            menu = await taco_bell_get_menu(store_id)
            
            return [TextContent(
                type="text",
                text=json.dumps(menu, indent=2)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error fetching menu: {str(e)}"
            )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def main():
    """Run the MCP server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
