"""ASGI entrypoint for the Google Ads MCP server."""

from ads_mcp.server import create_http_app


app = create_http_app()
