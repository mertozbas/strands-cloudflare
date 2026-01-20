# strands-cloudflare

[![PyPI version](https://badge.fury.io/py/strands-cloudflare.svg)](https://badge.fury.io/py/strands-cloudflare)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A comprehensive Cloudflare tool for [Strands Agents](https://github.com/strands-agents/strands-agents). Access **70+ Cloudflare API actions** from a single tool.

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

# Optional
export CLOUDFLARE_ACCOUNT_ID="your-account-id"  # Required for Workers, KV, D1, R2, Pages
export CLOUDFLARE_ZONE_ID="your-zone-id"        # Default zone for DNS operations
```

## Supported Services (70+ Actions)

| Category | Actions |
|----------|---------|
| **Zones** | `list_zones`, `get_zone`, `create_zone`, `delete_zone`, `zone_settings`, `update_zone_setting` |
| **DNS** | `list_dns_records`, `get_dns_record`, `create_dns_record`, `update_dns_record`, `delete_dns_record`, `export_dns` |
| **Workers** | `list_workers`, `get_worker`, `deploy_worker`, `delete_worker`, `list_worker_routes`, `create_worker_route` |
| **KV** | `list_kv_namespaces`, `create_kv_namespace`, `delete_kv_namespace`, `list_kv_keys`, `kv_get`, `kv_put`, `kv_delete` |
| **D1** | `list_d1_databases`, `create_d1_database`, `delete_d1_database`, `d1_query` |
| **R2** | `list_r2_buckets`, `create_r2_bucket`, `delete_r2_bucket`, `r2_list_objects`, `r2_get_object`, `r2_put_object`, `r2_delete_object` |
| **Pages** | `list_pages_projects`, `get_pages_project`, `create_pages_project`, `delete_pages_project`, `list_pages_deployments` |
| **Workers AI** | `list_ai_models`, `ai_text_generation`, `ai_text_embedding`, `ai_translation`, `ai_summarization` |
| **Tunnels** | `list_tunnels`, `get_tunnel`, `create_tunnel`, `delete_tunnel`, `get_tunnel_token`, `list_tunnel_connections`, `get_tunnel_config`, `update_tunnel_config` |
| **Firewall** | `list_firewall_rules`, `create_firewall_rule`, `delete_firewall_rule` |
| **Access** | `list_access_apps`, `list_access_groups` |
| **Cache** | `purge_cache_all`, `purge_cache_urls`, `purge_cache_tags`, `get_cache_settings` |
| **SSL/TLS** | `get_ssl_settings`, `update_ssl_settings`, `list_ssl_certificates` |
| **Page Rules** | `list_page_rules`, `create_page_rule`, `delete_page_rule` |
| **Analytics** | `get_zone_analytics`, `get_dns_analytics`, `get_analytics` |
| **Load Balancing** | `list_load_balancers`, `list_lb_pools`, `list_lb_monitors` |
| **Rate Limiting** | `list_rate_limits`, `create_rate_limit` |
| **Email** | `get_email_routing`, `list_email_rules` |
| **Queues** | `list_queues`, `create_queue` |
| **Hyperdrive** | `list_hyperdrives`, `create_hyperdrive` |
| **Vectorize** | `list_vectorize_indexes`, `create_vectorize_index` |
| **Durable Objects** | `list_durable_objects` |
| **Images/Stream** | `list_images`, `list_stream_videos` |
| **Account** | `list_accounts`, `get_account`, `list_account_members` |
| **User** | `get_user` |
| **Meta** | `list_actions`, `describe`, `api_call` |

## Usage Examples

### List Zones
```python
use_cloudflare(action="list_zones")
```

### Create DNS Record
```python
use_cloudflare(
    action="create_dns_record",
    zone_id="your-zone-id",
    record_type="A",
    name="www",
    content="192.0.2.1",
    proxied=True
)
```

### Deploy Worker
```python
use_cloudflare(
    action="deploy_worker",
    worker_name="my-worker",
    script='export default { fetch(request) { return new Response("Hello!") } }'
)
```

### Query D1 Database
```python
use_cloudflare(
    action="d1_query",
    database_id="your-db-id",
    sql="SELECT * FROM users LIMIT 10"
)
```

### Purge Cache
```python
use_cloudflare(
    action="purge_cache_all",
    zone_id="your-zone-id"
)
```

### Create Tunnel
```python
use_cloudflare(
    action="create_tunnel",
    tunnel_name="my-tunnel"
)
```

### Workers AI Text Generation
```python
use_cloudflare(
    action="ai_text_generation",
    model="@cf/meta/llama-2-7b-chat-int8",
    prompt="What is the meaning of life?"
)
```

### Generic API Call
```python
use_cloudflare(
    action="api_call",
    method="GET",
    path="/zones"
)
```

## With Strands Agent

```python
from strands import Agent
from strands_cloudflare import use_cloudflare

agent = Agent(tools=[use_cloudflare])

# Natural language queries
agent("Create a DNS A record for api.example.com pointing to 203.0.113.50")
agent("Deploy a hello world worker named greeting-worker")
agent("Purge the cache for my main zone")
agent("List all my Cloudflare tunnels")
```

## Response Format

All actions return a consistent response format:

```python
{
    "status": "success",  # or "error"
    "content": [{"text": "JSON response data"}],
    "action": "list_zones",
    "ms": 234  # Response time in milliseconds
}
```

## Security

- API tokens/keys are never logged or included in responses
- Sensitive data is automatically redacted from output
- Use API tokens with minimal required permissions

## Requirements

- Python 3.9+
- `strands-agents` >= 0.1.0
- `requests` >= 2.25.0

## License

Apache License 2.0

## Links

- [PyPI](https://pypi.org/project/strands-cloudflare/)
- [GitHub](https://github.com/strands-agents/strands-cloudflare)
- [Strands Agents](https://github.com/strands-agents/strands-agents)
- [Cloudflare API Docs](https://developers.cloudflare.com/api/)
