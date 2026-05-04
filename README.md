# Adeqo Paid Ads MCP

A [Model Context Protocol](https://modelcontextprotocol.io) (MCP) server that
lets LLM agents — Claude, Gemini, or any MCP-compatible client — read and
report on **Google Ads** accounts in natural language.

It exposes the full power of the [Google Ads Query Language
(GAQL)](https://developers.google.com/google-ads/api/docs/query/overview) as a
small set of well-typed tools, plus inline documentation resources so the
model knows which fields, segments and metrics to query without round-tripping
to a human.

> Originally derived from a Google sample project (Apache-2.0). Maintained by
> [Beyond Media Global LLC](#about-beyond-media-global-llc). Not an official
> Google product.

---

## About Beyond Media Global LLC

Beyond Media Global LLC (BMG) is a multinational, award-winning digital
experiential agency specializing in full-stack, data-driven marketing and
AI-driven growth. Founded by Philip G. Chiu, BMG serves Fortune 500 firms,
multinationals, and government institutions across seven countries — with a
focus on performance media, automation, and content creation.

We maintain this MCP server so our analysts and AI agents can query Google
Ads accounts conversationally: pulling reporting data, auditing campaign
structure, and surfacing performance insights without writing GAQL by hand.

- Website: <https://www.bmgww.com>

---

## What it gives an agent

| Tool | Purpose |
|---|---|
| `list_accessible_accounts` | Lists Google Ads customer IDs the authenticated user can reach (use as `login_customer_id` / `customer_id`). |
| `execute_gaql` | Runs a GAQL query against a customer and returns rows as JSON. |
| `get_gaql_doc` | Returns the GAQL grammar reference (Markdown). |
| `get_reporting_view_doc` | Returns docs for a reporting view (`campaign`, `ad_group`, …) or an index of all views. |
| `get_reporting_fields_doc` | Returns detailed metadata (data type, filterable, sortable, enum values) for a list of fields. |

| Resource | Purpose |
|---|---|
| `resource://Google_Ads_Query_Language` | GAQL guide. |
| `resource://Google_Ads_API_Reporting_Views` | Overview of all reporting views. |
| `resource://views/{view}` | Per-view metadata (attributes, segments, metrics). |

Sample agent prompts: *"list all enabled campaigns and their last-7-day clicks"*,
*"show me metrics for campaign 123"*, *"which ad groups have the lowest CTR
this month?"*.

---

## Requirements

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pipx`
- A Google Ads API developer token + an OAuth refresh token
  (see [Google's auth example](https://github.com/googleads/google-ads-python/blob/main/examples/authentication/generate_user_credentials.py))

## Configure credentials

Create a `google-ads.yaml` with:

```yaml
client_id: ...
client_secret: ...
refresh_token: ...
developer_token: ...
login_customer_id: ...   # optional but recommended
```

Then either:

- Place the file at `$HOME/google-ads.yaml`, **or**
- Point `GOOGLE_ADS_CREDENTIALS=/abs/path/to/google-ads.yaml`, **or**
- For containerized / serverless deployments, set
  `GOOGLE_ADS_CREDENTIALS_YAML` (raw YAML) or
  `GOOGLE_ADS_CREDENTIALS_YAML_BASE64` (base64 of the YAML).

---

## Run it

### Local stdio (most common for MCP clients)

```bash
uv run -m ads_mcp.stdio
```

### Local HTTP (Streamable HTTP transport)

```bash
uv run -m ads_mcp.server
# or
uv run uvicorn app:app --host 0.0.0.0 --port 8000
```

After startup:

| Endpoint | Purpose |
|---|---|
| `GET /` | Status payload (transport, mcp path, credentials state). |
| `GET /health` | 200 if credentials are configured, 503 otherwise. |
| `POST /mcp` | MCP Streamable HTTP transport endpoint. |

---

## Wire it into a client

### Claude Code

```bash
# Local stdio
claude mcp add adeqo-paidads -- uv run --directory /abs/path/to/adeqo-paidads-mcp -m ads_mcp.stdio

# Or remote HTTP (after deploy)
claude mcp add --transport http adeqo-paidads https://your-deploy/mcp
```

Then `/mcp` inside Claude Code will list the five tools.

### Gemini CLI

```json5
{
  "mcpServers": {
    "AdeqoPaidAds": {
      "command": "pipx",
      "args": [
        "run",
        "--spec",
        "git+https://github.com/Beyond-Media-Global-LLC/adeqo-paidads-mcp.git",
        "run-mcp-server"
      ],
      "env": {
        "GOOGLE_ADS_CREDENTIALS": "/abs/path/to/google-ads.yaml"
      },
      "timeout": 30000,
      "trust": false
    }
  }
}
```

For local development, swap `pipx` for `uv run --directory <repo> -m ads_mcp.stdio`.

---

## Optional auth

If you want to require a Google OAuth access token from MCP clients
(forwarded to the Google Ads API in lieu of the YAML refresh token):

| Env var | Effect |
|---|---|
| `USE_GOOGLE_OAUTH_ACCESS_TOKEN` | Enables `GoogleTokenVerifier` (clients must present a valid Google access token). |
| `FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID` + `FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET` | Enables full `GoogleProvider` OAuth flow. |
| `FASTMCP_SERVER_BASE_URL` | Public base URL for OAuth redirects (default `http://localhost:8000`). |
| `FASTMCP_HTTP_PATH` | Path the MCP transport is served on (default `/mcp`). |

The developer token from `google-ads.yaml` is still required even when
forwarding access tokens.

---

## Development

```bash
uv sync                       # install deps
uv run pytest                 # run tests
uv run pyink .                # format (Google Python style)
uv run pylint ads_mcp tests   # lint
```

Two test files (`tests/tools/test_api.py`) require a real `google-ads.yaml`
on disk; the rest run offline.

### Layout

```
ads_mcp/
  server.py        # HTTP + stdio entrypoints
  stdio.py         # stdio-only entrypoint
  coordinator.py   # FastMCP instance
  tools/
    api.py         # list_accessible_accounts, execute_gaql
    docs.py        # get_gaql_doc, get_reporting_view_doc, get_reporting_fields_doc
  scripts/
    generate_views.py  # populates context/views/*.yaml + context/fields.yaml
                       # at server startup (via ASGI lifespan)
  context/         # GAQL.md, view + field metadata served as MCP resources
app.py             # ASGI entrypoint (Uvicorn / serverless)
tests/             # pytest suite mirroring ads_mcp/
```

---

## License

Apache-2.0 — see [LICENSE](LICENSE). Original work © Google LLC; modifications
© Beyond Media Global LLC and contributors. Distributed as-is, without
warranty of any kind.

## Contributing

Issues and PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).
