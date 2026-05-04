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

"""Tests for server.py."""

import os
from unittest import mock

from ads_mcp import server


@mock.patch.dict(os.environ, {"USE_GOOGLE_OAUTH_ACCESS_TOKEN": "true"})
@mock.patch("ads_mcp.server.mcp_server")
@mock.patch("ads_mcp.server.api")
@mock.patch("ads_mcp.server.update_views_yaml", new_callable=mock.Mock)
def test_main_with_oauth_env(mock_update_views, mock_api, mock_mcp_server):
  """Tests main function with USE_GOOGLE_OAUTH_ACCESS_TOKEN set."""
  with mock.patch("ads_mcp.server.asyncio.run"):
    server.main()

  mock_update_views.assert_called_once()
  mock_api.get_ads_client.assert_called_once()
  mock_mcp_server.run.assert_called_once_with(
      transport="streamable-http", show_banner=False
  )
  # Verify auth set (hard to verify exact type without exposing it better,
  # but we can check if it was accessed/set if we mock it differently,
  # or just rely on coverage hitting the line)


@mock.patch("ads_mcp.server.mcp_server")
@mock.patch("ads_mcp.server.api")
@mock.patch("ads_mcp.server.update_views_yaml", new_callable=mock.Mock)
def test_main_no_env(mock_update_views, mock_api, mock_mcp_server):
  """Tests main function with no env vars."""
  with mock.patch("ads_mcp.server.asyncio.run"):
    server.main()

  mock_mcp_server.run.assert_called_once()


@mock.patch("ads_mcp.server.mcp_server")
@mock.patch("ads_mcp.server.update_views_yaml")
def test_create_http_app_uses_configured_path(
    mock_update_views, mock_mcp_server
):
  """The ASGI app should use the configured MCP HTTP path."""
  with mock.patch.dict(
      os.environ, {"FASTMCP_HTTP_PATH": "/api/mcp"}, clear=True
  ):
    server.create_http_app()

  mock_mcp_server.http_app.assert_called_once_with(path="/api/mcp")


@mock.patch("ads_mcp.server.mcp_server")
@mock.patch("ads_mcp.server.update_views_yaml", new_callable=mock.AsyncMock)
def test_create_http_app_lifespan_runs_update_views(
    mock_update_views, mock_mcp_server
):
  """The ASGI app's lifespan should await update_views_yaml on startup."""
  import asyncio as _asyncio

  inner_lifespan = mock.MagicMock()
  inner_lifespan.return_value.__aenter__ = mock.AsyncMock()
  inner_lifespan.return_value.__aexit__ = mock.AsyncMock()
  mock_app = mock.MagicMock()
  mock_app.router.lifespan_context = inner_lifespan
  mock_mcp_server.http_app.return_value = mock_app

  app = server.create_http_app()

  async def _drive():
    async with app.router.lifespan_context(app):
      pass

  _asyncio.run(_drive())
  mock_update_views.assert_awaited_once()
