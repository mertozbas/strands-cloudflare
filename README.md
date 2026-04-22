# strands-cloudflare

[![Awesome Strands Agents](https://img.shields.io/badge/Awesome-Strands%20Agents-00FF77?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjkwIiBoZWlnaHQ9IjQ2MyIgdmlld0JveD0iMCAwIDI5MCA0NjMiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik05Ny4yOTAyIDUyLjc4ODRDODUuMDY3NCA0OS4xNjY3IDcyLjIyMzQgNTYuMTM4OSA2OC42MDE3IDY4LjM2MTZDNjQuOTgwMSA4MC41ODQzIDcxLjk1MjQgOTMuNDI4MyA4NC4xNzQ5IDk3LjA1MDFMMjM1LjExNyAxMzkuNzc1QzI0NS4yMjMgMTQyLjc2OSAyNDYuMzU3IDE1Ni42MjggMjM2Ljg3NCAxNjEuMjI2TDMyLjU0NiAyNjAuMjkxQy0xNC45NDM5IDI4My4zMTYgLTkuMTYxMDcgMzUyLjc0IDQxLjQ4MzUgMzY3LjU5MUwxODkuNTUxIDQxMS4wMDlMMTkwLjEyNSA0MTEuMTY5QzIwMi4xODMgNDE0LjM3NiAyMTQuNjY1IDQwNy4zOTYgMjE4LjE5NiAzOTUuMzU1QzIyMS43ODQgMzgzLjEyMiAyMTQuNzc0IDM3MC4yOTYgMjAyLjU0MSAzNjYuNzA5TDU0LjQ3MzggMzIzLjI5MUM0NC4zNDQ3IDMyMC4zMjEgNDMuMTg3OSAzMDYuNDM2IDUyLjY4NTcgMzAxLjgzMUwyNTcuMDE0IDIwMi43NjZDMzA0LjQzMiAxNzkuNzc2IDI5OC43NTggMTEwLjQ4MyAyNDguMjMzIDk1LjUxMkw5Ny4yOTAyIDUyLjc4ODRaIiBmaWxsPSIjRkZGRkZGIi8+CjxwYXRoIGQ9Ik0yNTkuMTQ3IDAuOTgxODEyQzI3MS4zODkgLTIuNTc0OTggMjg0LjE5NyA0LjQ2NTcxIDI4Ny43NTQgMTYuNzA3NEMyOTEuMzExIDI4Ljk0OTIgMjg0LjI3IDQxLjc1NyAyNzIuMDI4IDQ1LjMxMzhMNzEuMTcyNyAxMDMuNjcxQzQwLjcxNDIgMTEyLjUyMSAzNy4xOTc2IDE1NC4yNjIgNjUuNzQ1OSAxNjguMDgzTDI0MS4zNDMgMjUzLjA5M0MzMDcuODcyIDI4NS4zMDIgMjk5Ljc5NCAzODIuNTQ2IDIyOC44NjIgNDAzLjMzNkwzMC40MDQxIDQ2MS41MDJDMTguMTcwNyA0NjUuMDg4IDUuMzQ3MDggNDU4LjA3OCAxLjc2MTUzIDQ0NS44NDRDLTEuODIzOSA0MzMuNjExIDUuMTg2MzcgNDIwLjc4NyAxNy40MTk3IDQxNy4yMDJMMjE1Ljg3OCAzNTkuMDM1QzI0Ni4yNzcgMzUwLjEyNSAyNDkuNzM5IDMwOC40NDkgMjIxLjIyNiAyOTQuNjQ1TDQ1LjYyOTcgMjA5LjYzNUMtMjAuOTgzNCAxNzcuMzg2IC0xMi43NzcyIDc5Ljk4OTMgNTguMjkyOCA1OS4zNDAyTDI1OS4xNDcgMC45ODE4MTJaIiBmaWxsPSIjRkZGRkZGIi8+Cjwvc3ZnPgo=&logoColor=white)](https://github.com/cagataycali/awesome-strands-agents)

[![PyPI version](https://badge.fury.io/py/strands-cloudflare.svg)](https://badge.fury.io/py/strands-cloudflare)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A universal Cloudflare tool for [Strands Agents](https://github.com/strands-agents/sdk-python). Dynamically access the **entire Cloudflare API** through a single tool using the official `cloudflare-python` SDK.

## Installation

```bash
pip install strands-cloudflare
```

## Quick Start

```python
from strands import Agent
from strands_cloudflare import use_cloudflare

agent = Agent(tools=[use_cloudflare])
agent("List all my Cloudflare zones")
```

## Configuration

Set your Cloudflare credentials as environment variables:

```bash
# Option 1: API Token (recommended)
export CLOUDFLARE_API_TOKEN="your-api-token"

# Option 2: API Key + Email
export CLOUDFLARE_API_KEY="your-api-key"
export CLOUDFLARE_EMAIL="your-email@example.com"

# Optional defaults
export CLOUDFLARE_ACCOUNT_ID="your-account-id"
export CLOUDFLARE_ZONE_ID="your-zone-id"
```

## How It Works

This tool dynamically maps to any `cloudflare-python` SDK method. Specify:

| Parameter | Description |
|-----------|-------------|
| `service` | SDK service path (e.g., `zones`, `dns.records`, `workers.scripts`) |
| `operation` | Method to call (e.g., `list`, `get`, `create`, `delete`, `update`) |
| `params` | JSON string of parameters for the operation |
| `account_id` | Cloudflare account ID (optional, uses env var if not set) |
| `zone_id` | Cloudflare zone ID (optional, uses env var if not set) |

### Service Discovery

Use `"_"` to discover available services and operations:

```python
# List all top-level services
use_cloudflare(service="_", operation="_")

# List operations available on a service
use_cloudflare(service="dns.records", operation="_")
```

## Usage Examples

### Zones

```python
# List all zones
use_cloudflare(service="zones", operation="list")

# Get specific zone
use_cloudflare(service="zones", operation="get", zone_id="abc123")
```

### DNS Records

```python
# List DNS records
use_cloudflare(service="dns.records", operation="list", zone_id="abc123")

# Create DNS record
use_cloudflare(
    service="dns.records",
    operation="create",
    zone_id="abc123",
    params='{"type": "A", "name": "www", "content": "192.0.2.1", "proxied": true}'
)

# Update DNS record
use_cloudflare(
    service="dns.records",
    operation="update",
    zone_id="abc123",
    params='{"dns_record_id": "record-id", "type": "A", "name": "www", "content": "192.0.2.2"}'
)

# Delete DNS record
use_cloudflare(
    service="dns.records",
    operation="delete",
    zone_id="abc123",
    params='{"dns_record_id": "record-id"}'
)
```

### Workers

```python
# List Workers scripts
use_cloudflare(service="workers.scripts", operation="list", account_id="xyz")

# Get Worker script
use_cloudflare(
    service="workers.scripts",
    operation="get",
    account_id="xyz",
    params='{"script_name": "my-worker"}'
)

# List Worker routes
use_cloudflare(service="workers.routes", operation="list", zone_id="abc123")
```

### KV Storage

```python
# List KV namespaces
use_cloudflare(service="kv.namespaces", operation="list", account_id="xyz")

# Create KV namespace
use_cloudflare(
    service="kv.namespaces",
    operation="create",
    account_id="xyz",
    params='{"title": "MY_KV"}'
)

# List keys in namespace
use_cloudflare(
    service="kv.namespaces.keys",
    operation="list",
    account_id="xyz",
    params='{"namespace_id": "ns-id"}'
)
```

### D1 Database

```python
# List D1 databases
use_cloudflare(service="d1.database", operation="list", account_id="xyz")

# Query D1 database
use_cloudflare(
    service="d1.database",
    operation="query",
    account_id="xyz",
    params='{"database_id": "db-id", "sql": "SELECT * FROM users"}'
)
```

### R2 Storage

```python
# List R2 buckets
use_cloudflare(service="r2.buckets", operation="list", account_id="xyz")

# Create R2 bucket
use_cloudflare(
    service="r2.buckets",
    operation="create",
    account_id="xyz",
    params='{"name": "my-bucket"}'
)
```

### Cloudflare Tunnels (Zero Trust)

```python
# List tunnels
use_cloudflare(service="zero_trust.tunnels", operation="list", account_id="xyz")

# Create tunnel
use_cloudflare(
    service="zero_trust.tunnels",
    operation="create",
    account_id="xyz",
    params='{"name": "my-tunnel", "tunnel_secret": "base64-secret"}'
)

# Get tunnel config
use_cloudflare(
    service="zero_trust.tunnels.configurations",
    operation="get",
    account_id="xyz",
    params='{"tunnel_id": "tunnel-id"}'
)
```

### Workers AI

```python
# Run AI model
use_cloudflare(
    service="ai",
    operation="run",
    account_id="xyz",
    params='{"model_name": "@cf/meta/llama-2-7b-chat-int8", "prompt": "Hello, how are you?"}'
)
```

### Cache

```python
# Purge everything
use_cloudflare(
    service="cache",
    operation="purge",
    zone_id="abc123",
    params='{"purge_everything": true}'
)

# Purge specific URLs
use_cloudflare(
    service="cache",
    operation="purge",
    zone_id="abc123",
    params='{"files": ["https://example.com/style.css"]}'
)
```

### Pages

```python
# List Pages projects
use_cloudflare(service="pages.projects", operation="list", account_id="xyz")

# Get project details
use_cloudflare(
    service="pages.projects",
    operation="get",
    account_id="xyz",
    params='{"project_name": "my-site"}'
)
```

## Service Reference

| Service Path | Description |
|--------------|-------------|
| `zones` | Zone management |
| `dns.records` | DNS record management |
| `workers.scripts` | Worker scripts |
| `workers.routes` | Worker routes |
| `kv.namespaces` | KV storage namespaces |
| `kv.namespaces.keys` | KV keys |
| `kv.namespaces.values` | KV values |
| `d1.database` | D1 SQL databases |
| `r2.buckets` | R2 object storage |
| `pages.projects` | Pages projects |
| `zero_trust.tunnels` | Cloudflare Tunnels |
| `zero_trust.access.applications` | Access applications |
| `firewall.rules` | Firewall rules |
| `cache` | Cache operations |
| `ssl.certificate_packs` | SSL certificates |
| `load_balancers` | Load balancers |
| `ai` | Workers AI |
| `queues` | Queues |
| `vectorize.indexes` | Vectorize indexes |
| `images.v1` | Cloudflare Images |
| `stream` | Cloudflare Stream |

## With Strands Agent

```python
from strands import Agent
from strands_cloudflare import use_cloudflare

agent = Agent(tools=[use_cloudflare])

# Natural language queries work seamlessly
agent("Create a DNS A record for api.example.com pointing to 203.0.113.50")
agent("List all my Workers scripts")
agent("Purge the cache for my zone")
agent("List all Cloudflare tunnels in my account")
agent("Query my D1 database for all users")
```

## Security

- API tokens/keys are never logged or included in responses
- Sensitive data (keys, tokens, secrets) is automatically redacted from output
- Use API tokens with minimal required permissions

## Requirements

- Python 3.9+
- `strands-agents`
- `cloudflare`

## License

Apache License 2.0

## Links

- [PyPI](https://pypi.org/project/strands-cloudflare/)
- [GitHub](https://github.com/cagataycali/strands-cloudflare)
- [Strands Agents](https://github.com/strands-agents/sdk-python)
- [Cloudflare Python SDK](https://github.com/cloudflare/cloudflare-python)
- [Cloudflare API Docs](https://developers.cloudflare.com/api/)
