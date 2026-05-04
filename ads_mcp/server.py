# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The server for the Google Ads API MCP."""
import asyncio
import contextlib
import os

from ads_mcp.coordinator import mcp_server
from ads_mcp.scripts.generate_views import update_views_yaml
from ads_mcp.tools import api
from ads_mcp.tools import docs

import dotenv
from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.server.auth.providers.google import GoogleTokenVerifier
from starlette.requests import Request
from starlette.responses import JSONResponse


dotenv.load_dotenv()


tools = [api, docs]
_CONTEXT_SYNC_ERROR: str | None = None


def configure_auth():
  """Configures optional Google auth for the FastMCP server."""
  if os.getenv("USE_GOOGLE_OAUTH_ACCESS_TOKEN"):
    mcp_server.auth = GoogleTokenVerifier()

  if os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID") and os.getenv(
      "FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET"
  ):
    base_url = os.getenv("FASTMCP_SERVER_BASE_URL", "http://localhost:8000")
    mcp_server.auth = GoogleProvider(
        base_url=base_url,
        required_scopes=["https://www.googleapis.com/auth/adwords"],
    )


def get_http_path() -> str:
  """Returns the public MCP HTTP path."""
  return os.getenv("FASTMCP_HTTP_PATH", "/mcp")


def get_service_status() -> dict[str, str | bool | None]:
  """Builds a lightweight service status payload."""
  return {
      "name": "Adeqo Paid Ads MCP",
      "transport": "streamable-http",
      "mcp_path": get_http_path(),
      "credentials_configured": api.has_ads_credentials(),
      "credentials_source": api.get_credentials_source(),
      "context_sync_error": _CONTEXT_SYNC_ERROR,
  }


@mcp_server.custom_route("/", methods=["GET"])
async def root(_: Request):
  """Returns a small landing payload for platform deployments."""
  return JSONResponse(get_service_status())


@mcp_server.custom_route("/health", methods=["GET"])
async def health(_: Request):
  """Returns a health response suitable for uptime checks."""
  status_code = 200 if api.has_ads_credentials() else 503
  return JSONResponse(get_service_status(), status_code=status_code)


def create_http_app():
  """Builds an ASGI app for serverless and HTTP deployments."""
  configure_auth()
  app = mcp_server.http_app(path=get_http_path())
  inner_lifespan = app.router.lifespan_context

  @contextlib.asynccontextmanager
  async def lifespan(starlette_app):
    global _CONTEXT_SYNC_ERROR
    try:
      await update_views_yaml()
      _CONTEXT_SYNC_ERROR = None
    except Exception as exc:  # pragma: no cover - defensive startup path
      _CONTEXT_SYNC_ERROR = str(exc)
    async with inner_lifespan(starlette_app):
      yield

  app.router.lifespan_context = lifespan
  return app


def main():
  """Initializes and runs the MCP server."""
  configure_auth()
  asyncio.run(update_views_yaml())  # Check and update docs resource
  api.get_ads_client()  # Check Google Ads credentials
  print("mcp server starting...")
  mcp_server.run(
      transport="streamable-http",
      show_banner=False,
  )  # Initialize and run the server


if __name__ == "__main__":
  main()
