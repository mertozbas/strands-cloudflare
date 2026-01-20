#!/usr/bin/env python3
"""
Universal Cloudflare Tool for Strands Agents

A unified tool for interacting with all Cloudflare services.
Supports Zones, DNS, Workers, KV, R2, D1, Pages, AI, Tunnels, and 25+ more services.

Licensed under the Apache License, Version 2.0
"""

from __future__ import annotations

import base64
import json
import os
import time
import traceback
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from strands import tool

# Sensitive keys to redact from output
SENSITIVE_KEYS = {
    "api_key", "api_token", "auth_key", "auth_token",
    "secret", "password", "private_key", "certificate",
    "X-Auth-Key", "Authorization", "Cookie",
}

VALID_ACTIONS = {
    # Meta
    "list_actions", "describe",
    # Account
    "list_accounts", "get_account", "list_account_members",
    # Zones
    "list_zones", "get_zone", "create_zone", "delete_zone", "zone_settings", "update_zone_setting",
    # DNS
    "list_dns_records", "get_dns_record", "create_dns_record", "update_dns_record", "delete_dns_record", "export_dns",
    # Workers
    "list_workers", "get_worker", "deploy_worker", "delete_worker", "list_worker_routes", "create_worker_route",
    # KV
    "list_kv_namespaces", "create_kv_namespace", "delete_kv_namespace", 
    "list_kv_keys", "kv_get", "kv_put", "kv_delete",
    # D1
    "list_d1_databases", "create_d1_database", "delete_d1_database", "d1_query",
    # R2
    "list_r2_buckets", "create_r2_bucket", "delete_r2_bucket",
    "r2_list_objects", "r2_get_object", "r2_put_object", "r2_delete_object",
    # Pages
    "list_pages_projects", "get_pages_project", "create_pages_project", "delete_pages_project", "list_pages_deployments",
    # AI
    "list_ai_models", "ai_text_generation", "ai_text_embedding", "ai_translation", "ai_summarization",
    # Tunnels
    "list_tunnels", "get_tunnel", "create_tunnel", "delete_tunnel", 
    "get_tunnel_token", "list_tunnel_connections", "get_tunnel_config", "update_tunnel_config",
    # Firewall
    "list_firewall_rules", "create_firewall_rule", "delete_firewall_rule",
    # Access
    "list_access_apps", "list_access_groups",
    # Cache
    "purge_cache_all", "purge_cache_urls", "purge_cache_tags", "get_cache_settings",
    # SSL
    "get_ssl_settings", "update_ssl_settings", "list_ssl_certificates",
    # Page Rules
    "list_page_rules", "create_page_rule", "delete_page_rule",
    # Analytics
    "get_zone_analytics", "get_dns_analytics", "get_analytics",
    # Load Balancing
    "list_load_balancers", "list_lb_pools", "list_lb_monitors",
    # Rate Limiting
    "list_rate_limits", "create_rate_limit",
    # Email
    "get_email_routing", "list_email_rules",
    # Queues
    "list_queues", "create_queue",
    # Hyperdrive
    "list_hyperdrives", "create_hyperdrive",
    # Vectorize
    "list_vectorize_indexes", "create_vectorize_index",
    # Durable Objects
    "list_durable_objects",
    # Images/Stream
    "list_images", "list_stream_videos",
    # User
    "get_user",
    # Generic
    "api_call",
}

ACTION_DESCRIPTIONS = {
    "list_actions": {"description": "List all available actions"},
    "describe": {"description": "Describe all actions with their parameters"},
    "list_zones": {"description": "List all zones in the account", "params": ["page", "limit"]},
    "list_dns_records": {"description": "List DNS records for a zone", "params": ["zone_id"]},
    "create_dns_record": {"description": "Create a DNS record", "params": ["zone_id", "type", "name", "content"]},
    "update_dns_record": {"description": "Update a DNS record", "params": ["zone_id", "record_id"]},
    "delete_dns_record": {"description": "Delete a DNS record", "params": ["zone_id", "record_id"]},
    "list_workers": {"description": "List Workers scripts", "params": ["account_id"]},
    "deploy_worker": {"description": "Deploy a Worker script", "params": ["name", "script"]},
    "delete_worker": {"description": "Delete a Worker script", "params": ["name"]},
    "list_kv_namespaces": {"description": "List KV namespaces", "params": ["account_id"]},
    "kv_get": {"description": "Get a KV value", "params": ["namespace_id", "key"]},
    "kv_put": {"description": "Put a KV value", "params": ["namespace_id", "key", "value"]},
    "kv_delete": {"description": "Delete a KV key", "params": ["namespace_id", "key"]},
    "list_d1_databases": {"description": "List D1 databases", "params": ["account_id"]},
    "d1_query": {"description": "Execute D1 SQL query", "params": ["database_id", "sql"]},
    "list_r2_buckets": {"description": "List R2 buckets", "params": ["account_id"]},
    "r2_list_objects": {"description": "List R2 bucket objects", "params": ["bucket_name"]},
    "r2_get_object": {"description": "Get R2 object", "params": ["bucket_name", "key"]},
    "r2_put_object": {"description": "Put R2 object", "params": ["bucket_name", "key", "body"]},
    "list_pages_projects": {"description": "List Pages projects", "params": ["account_id"]},
    "list_tunnels": {"description": "List Cloudflare Tunnels", "params": ["account_id"]},
    "purge_cache_all": {"description": "Purge all cached content", "params": ["zone_id"]},
    "get_ssl_settings": {"description": "Get SSL/TLS settings", "params": ["zone_id"]},
    "get_cache_settings": {"description": "Get cache settings", "params": ["zone_id"]},
    "list_firewall_rules": {"description": "List firewall rules", "params": ["zone_id"]},
    "get_user": {"description": "Get current user info", "params": []},
    "get_analytics": {"description": "Get zone analytics", "params": ["zone_id"]},
    "ai_text_generation": {"description": "Generate text with Workers AI", "params": ["model", "prompt"]},
    "api_call": {"description": "Make a generic API call", "params": ["content", "name", "data"]},
}



# Cloudflare API base URL
CF_API_BASE = "https://api.cloudflare.com/client/v4"


def _redact(obj: Any) -> Any:
    """Recursively redact sensitive data from output."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            key_lower = str(k).lower()
            if str(k) in SENSITIVE_KEYS or any(s in key_lower for s in ["secret", "apikey", "password", "token", "key"]):
                out[k] = "***REDACTED***"
            else:
                out[k] = _redact(v)
        return out
    if isinstance(obj, list):
        return [_redact(x) for x in obj]
    return obj


def _parse_json(value: Any, default: Any = None) -> Any:
    """Parse JSON string or return value as-is if already parsed."""
    if value is None:
        return default
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return default
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            return json.loads(s)
        return value
    return value


def _get_credentials() -> Dict[str, str]:
    """Get Cloudflare API credentials from environment."""
    headers = {}
    
    # Prefer API Token (more secure, scoped permissions)
    api_token = os.getenv("CLOUDFLARE_API_TOKEN") or os.getenv("CF_API_TOKEN")
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
        return headers
    
    # Fallback to Global API Key + Email
    api_key = os.getenv("CLOUDFLARE_API_KEY") or os.getenv("CF_API_KEY")
    email = os.getenv("CLOUDFLARE_EMAIL") or os.getenv("CF_EMAIL")
    
    if api_key and email:
        headers["X-Auth-Key"] = api_key
        headers["X-Auth-Email"] = email
        return headers
    
    raise ValueError(
        "Cloudflare credentials required. Set either:\n"
        "  - CLOUDFLARE_API_TOKEN (recommended)\n"
        "  - CLOUDFLARE_API_KEY + CLOUDFLARE_EMAIL"
    )


def _cf_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    raw_body: Optional[bytes] = None,
    content_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Make a request to Cloudflare API."""
    import urllib.request
    import urllib.error
    
    headers = _get_credentials()
    headers["Content-Type"] = content_type or "application/json"
    
    url = f"{CF_API_BASE}{endpoint}"
    if params:
        url += "?" + urlencode(params)
    
    body = None
    if raw_body:
        body = raw_body
    elif data:
        body = json.dumps(data).encode("utf-8")
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            response_data = resp.read().decode("utf-8")
            return json.loads(response_data) if response_data else {"success": True}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            return json.loads(error_body)
        except:
            return {"success": False, "errors": [{"message": error_body}]}


def _get_account_id() -> str:
    """Get Cloudflare Account ID from environment."""
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID") or os.getenv("CF_ACCOUNT_ID")
    if not account_id:
        raise ValueError("CLOUDFLARE_ACCOUNT_ID required for this operation")
    return account_id


def _get_zone_id(zone: Optional[str] = None) -> str:
    """Get Zone ID from parameter or environment."""
    zone_id = zone or os.getenv("CLOUDFLARE_ZONE_ID") or os.getenv("CF_ZONE_ID")
    if not zone_id:
        raise ValueError("zone_id required (or set CLOUDFLARE_ZONE_ID)")
    return zone_id


@tool
def use_cloudflare(
    action: str,
    # Common identifiers
    zone_id: Optional[str] = None,
    account_id: Optional[str] = None,
    record_id: Optional[str] = None,
    worker_name: Optional[str] = None,
    namespace_id: Optional[str] = None,
    database_id: Optional[str] = None,
    project_name: Optional[str] = None,
    tunnel_id: Optional[str] = None,
    rule_id: Optional[str] = None,
    # DNS parameters
    record_type: Optional[str] = None,
    name: Optional[str] = None,
    content: Optional[str] = None,
    ttl: int = 1,
    proxied: bool = False,
    priority: Optional[int] = None,
    # Worker parameters
    script: Optional[str] = None,
    script_path: Optional[str] = None,
    bindings: Optional[str] = None,
    # KV parameters
    key: Optional[str] = None,
    value: Optional[str] = None,
    keys_prefix: Optional[str] = None,
    # D1 parameters
    sql: Optional[str] = None,
    database_name: Optional[str] = None,
    # R2 parameters
    bucket_name: Optional[str] = None,
    object_key: Optional[str] = None,
    object_data: Optional[str] = None,
    # Pages parameters
    production_branch: Optional[str] = None,
    repo_url: Optional[str] = None,
    # Firewall/Rules parameters
    expression: Optional[str] = None,
    rule_action: Optional[str] = None,
    description: Optional[str] = None,
    # Cache parameters
    purge_urls: Optional[str] = None,
    purge_tags: Optional[str] = None,
    # AI parameters
    model: Optional[str] = None,
    prompt: Optional[str] = None,
    messages: Optional[str] = None,
    image_url: Optional[str] = None,
    # Tunnel parameters
    tunnel_name: Optional[str] = None,
    tunnel_secret: Optional[str] = None,
    config_src: Optional[str] = None,
    # Generic
    data: Optional[str] = None,
    params: Optional[str] = None,
    limit: int = 50,
    page: int = 1,
) -> Dict[str, Any]:
    """
    Universal Cloudflare client tool for managing all Cloudflare services.

    Provides unified access to Zones, DNS, Workers, KV, R2, D1, Pages, AI,
    Tunnels, Firewall, Cache, and 25+ more Cloudflare services.

    Args:
        action: Operation to perform (see Actions section below)
        
        Common Identifiers:
        - zone_id: Zone/domain ID (or set CLOUDFLARE_ZONE_ID)
        - account_id: Account ID (or set CLOUDFLARE_ACCOUNT_ID)
        - record_id: DNS record ID
        - worker_name: Worker script name
        - namespace_id: KV namespace ID
        - database_id: D1 database ID
        - project_name: Pages project name
        - tunnel_id: Tunnel ID
        - rule_id: Firewall/Page rule ID
        
        DNS Parameters:
        - record_type: A, AAAA, CNAME, MX, TXT, etc.
        - name: Record name (e.g., "www", "@")
        - content: Record content (IP, hostname, text)
        - ttl: Time to live (1 = auto)
        - proxied: Enable Cloudflare proxy
        - priority: MX priority
        
        Worker Parameters:
        - script: Worker script content
        - script_path: Path to script file
        - bindings: JSON bindings config
        
        KV Parameters:
        - key: KV key name
        - value: KV value
        - keys_prefix: Prefix for listing keys
        
        D1 Parameters:
        - sql: SQL query to execute
        - database_name: Database name
        
        R2 Parameters:
        - bucket_name: R2 bucket name
        - object_key: Object key/path
        - object_data: Object content
        
        Pages Parameters:
        - production_branch: Git branch for production
        - repo_url: Git repository URL
        
        Firewall Parameters:
        - expression: Firewall expression
        - rule_action: block, challenge, allow, etc.
        - description: Rule description
        
        Cache Parameters:
        - purge_urls: JSON array of URLs to purge
        - purge_tags: JSON array of cache tags to purge
        
        AI Parameters:
        - model: AI model name
        - prompt: Text prompt
        - messages: JSON messages for chat
        - image_url: Image URL for vision models
        
        Tunnel Parameters:
        - tunnel_name: Tunnel name
        - tunnel_secret: Tunnel secret
        - config_src: Configuration source
        
        Generic:
        - data: JSON object for request body
        - params: JSON object for query parameters
        - limit: Results per page (default: 50)
        - page: Page number (default: 1)

    Returns:
        Dict with:
            - status: "success" or "error"
            - content: Response data
            - action: Action performed
            - ms: Execution time in milliseconds

    Environment Variables:
        Authentication (choose one):
        - CLOUDFLARE_API_TOKEN: API Token (recommended)
        - CLOUDFLARE_API_KEY + CLOUDFLARE_EMAIL: Global API Key
        
        Optional:
        - CLOUDFLARE_ACCOUNT_ID: Default account ID
        - CLOUDFLARE_ZONE_ID: Default zone ID

    Actions:
        === ACCOUNT ===
        - list_accounts: List all accounts
        - get_account: Get account details
        - list_account_members: List account members
        
        === ZONES ===
        - list_zones: List all zones/domains
        - get_zone: Get zone details
        - create_zone: Create new zone
        - delete_zone: Delete zone
        - zone_settings: Get zone settings
        - update_zone_setting: Update a zone setting
        
        === DNS ===
        - list_dns_records: List DNS records
        - get_dns_record: Get DNS record details
        - create_dns_record: Create DNS record
        - update_dns_record: Update DNS record
        - delete_dns_record: Delete DNS record
        - import_dns: Import DNS zone file
        - export_dns: Export DNS zone file
        
        === WORKERS ===
        - list_workers: List Worker scripts
        - get_worker: Get Worker script
        - deploy_worker: Deploy Worker script
        - delete_worker: Delete Worker script
        - list_worker_routes: List Worker routes
        - create_worker_route: Create Worker route
        - delete_worker_route: Delete Worker route
        - get_worker_settings: Get Worker settings
        - worker_tail: Get Worker tail logs
        
        === WORKERS KV ===
        - list_kv_namespaces: List KV namespaces
        - create_kv_namespace: Create KV namespace
        - delete_kv_namespace: Delete KV namespace
        - list_kv_keys: List keys in namespace
        - get_kv_value: Get value by key
        - put_kv_value: Put key-value pair
        - delete_kv_value: Delete key
        - bulk_kv_write: Bulk write key-value pairs
        
        === D1 DATABASE ===
        - list_d1_databases: List D1 databases
        - create_d1_database: Create D1 database
        - delete_d1_database: Delete D1 database
        - d1_query: Execute SQL query
        
        === R2 STORAGE ===
        - list_r2_buckets: List R2 buckets
        - create_r2_bucket: Create R2 bucket
        - delete_r2_bucket: Delete R2 bucket
        - get_r2_object: Get object from bucket
        - put_r2_object: Put object to bucket
        - delete_r2_object: Delete object from bucket
        - list_r2_objects: List objects in bucket
        
        === PAGES ===
        - list_pages_projects: List Pages projects
        - get_pages_project: Get project details
        - create_pages_project: Create Pages project
        - delete_pages_project: Delete Pages project
        - list_pages_deployments: List deployments
        - get_pages_deployment: Get deployment details
        - create_pages_deployment: Create deployment
        - rollback_pages_deployment: Rollback deployment
        
        === CLOUDFLARE AI ===
        - list_ai_models: List available AI models
        - ai_text_generation: Generate text
        - ai_text_classification: Classify text
        - ai_text_embedding: Generate embeddings
        - ai_image_classification: Classify image
        - ai_speech_recognition: Speech to text
        - ai_translation: Translate text
        - ai_summarization: Summarize text
        
        === TUNNELS ===
        - list_tunnels: List Cloudflare Tunnels
        - get_tunnel: Get tunnel details
        - create_tunnel: Create tunnel
        - delete_tunnel: Delete tunnel
        - get_tunnel_token: Get tunnel token
        - list_tunnel_connections: List tunnel connections
        - cleanup_tunnel_connections: Cleanup stale connections
        - get_tunnel_config: Get tunnel configuration
        - update_tunnel_config: Update tunnel configuration
        
        === FIREWALL ===
        - list_firewall_rules: List firewall rules
        - create_firewall_rule: Create firewall rule
        - update_firewall_rule: Update firewall rule
        - delete_firewall_rule: Delete firewall rule
        - list_waf_rules: List WAF rules
        - list_waf_packages: List WAF packages
        
        === ACCESS (Zero Trust) ===
        - list_access_apps: List Access applications
        - create_access_app: Create Access application
        - delete_access_app: Delete Access application
        - list_access_policies: List Access policies
        - list_access_groups: List Access groups
        
        === CACHE ===
        - purge_cache_all: Purge all cached content
        - purge_cache_urls: Purge specific URLs
        - purge_cache_tags: Purge by cache tags
        - purge_cache_prefix: Purge by URL prefix
        
        === SSL/TLS ===
        - get_ssl_settings: Get SSL/TLS settings
        - update_ssl_settings: Update SSL/TLS mode
        - list_ssl_certificates: List SSL certificates
        - create_ssl_certificate: Create/order certificate
        - list_origin_certificates: List origin certificates
        - create_origin_certificate: Create origin certificate
        
        === PAGE RULES ===
        - list_page_rules: List page rules
        - create_page_rule: Create page rule
        - update_page_rule: Update page rule
        - delete_page_rule: Delete page rule
        
        === ANALYTICS ===
        - get_zone_analytics: Get zone analytics
        - get_dns_analytics: Get DNS analytics
        - get_worker_analytics: Get Worker analytics
        
        === LOAD BALANCING ===
        - list_load_balancers: List load balancers
        - list_lb_pools: List load balancer pools
        - list_lb_monitors: List health monitors
        
        === RATE LIMITING ===
        - list_rate_limits: List rate limiting rules
        - create_rate_limit: Create rate limiting rule
        - delete_rate_limit: Delete rate limiting rule
        
        === EMAIL ROUTING ===
        - get_email_routing: Get email routing settings
        - list_email_rules: List email routing rules
        - create_email_rule: Create email routing rule
        
        === QUEUES ===
        - list_queues: List Queues
        - create_queue: Create Queue
        - delete_queue: Delete Queue
        - send_queue_message: Send message to Queue
        
        === HYPERDRIVE ===
        - list_hyperdrives: List Hyperdrive configs
        - create_hyperdrive: Create Hyperdrive config
        - delete_hyperdrive: Delete Hyperdrive config
        
        === VECTORIZE ===
        - list_vectorize_indexes: List Vectorize indexes
        - create_vectorize_index: Create Vectorize index
        - delete_vectorize_index: Delete Vectorize index
        - vectorize_insert: Insert vectors
        - vectorize_query: Query vectors
        
        === DURABLE OBJECTS ===
        - list_durable_objects: List Durable Object namespaces
        - list_durable_object_instances: List DO instances
        
        === IMAGES ===
        - list_images: List images
        - upload_image: Upload image
        - delete_image: Delete image
        - get_image_details: Get image details
        
        === STREAM ===
        - list_stream_videos: List videos
        - get_stream_video: Get video details
        - delete_stream_video: Delete video
        - get_stream_embed: Get embed code
        
        === GENERIC ===
        - api_call: Make custom API call

    Examples:
        # List zones
        use_cloudflare(action="list_zones")

        # Create DNS record
        use_cloudflare(
            action="create_dns_record",
            record_type="A",
            name="www",
            content="192.0.2.1",
            proxied=True
        )

        # Deploy Worker
        use_cloudflare(
            action="deploy_worker",
            worker_name="my-worker",
            script='export default { fetch(request) { return new Response("Hello!") } }'
        )

        # Query D1 database
        use_cloudflare(
            action="d1_query",
            database_id="xxx",
            sql="SELECT * FROM users LIMIT 10"
        )

        # Purge cache
        use_cloudflare(
            action="purge_cache_urls",
            purge_urls='["https://example.com/page1", "https://example.com/page2"]'
        )

        # AI text generation
        use_cloudflare(
            action="ai_text_generation",
            model="@cf/meta/llama-2-7b-chat-int8",
            prompt="Explain quantum computing"
        )

        # Create tunnel
        use_cloudflare(
            action="create_tunnel",
            tunnel_name="my-tunnel",
            tunnel_secret="base64-encoded-secret"
        )
    """
    t0 = time.time()
    
    try:

        # Normalize action
        action = action.strip().lower().replace("-", "_")
        
        # === META ACTIONS (no credentials needed) ===
        if action == "list_actions":
            return {
                "status": "success",
                "content": [{"text": json.dumps({"count": len(VALID_ACTIONS), "actions": sorted(list(VALID_ACTIONS))}, indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "describe":
            return {
                "status": "success",
                "content": [{"text": json.dumps({"actions": ACTION_DESCRIPTIONS}, indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_user":
            result = _cf_request("GET", "/user")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result.get("result", result)), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_analytics":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/analytics/dashboard")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result.get("result", result)), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_cache_settings":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/settings/cache_level")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result.get("result", result)), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        

        # === ACCOUNT ===
        if action == "list_accounts":
            result = _cf_request("GET", "/accounts", params={"page": page, "per_page": limit})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_account":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "list_account_members":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/members", params={"page": page, "per_page": limit})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === ZONES ===
        if action == "list_zones":
            params_dict = {"page": page, "per_page": limit}
            if name:
                params_dict["name"] = name
            result = _cf_request("GET", "/zones", params=params_dict)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_zone":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_zone":
            if not name:
                raise ValueError("name required for create_zone")
            acc_id = account_id or _get_account_id()
            payload = {"name": name, "account": {"id": acc_id}}
            if data:
                payload.update(_parse_json(data, {}))
            result = _cf_request("POST", "/zones", data=payload)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "delete_zone":
            zid = _get_zone_id(zone_id)
            result = _cf_request("DELETE", f"/zones/{zid}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "zone_settings":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/settings")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "update_zone_setting":
            zid = _get_zone_id(zone_id)
            if not name or not value:
                raise ValueError("name and value required for update_zone_setting")
            result = _cf_request("PATCH", f"/zones/{zid}/settings/{name}", data={"value": _parse_json(value, value)})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === DNS RECORDS ===
        if action == "list_dns_records":
            zid = _get_zone_id(zone_id)
            params_dict = {"page": page, "per_page": limit}
            if record_type:
                params_dict["type"] = record_type
            if name:
                params_dict["name"] = name
            result = _cf_request("GET", f"/zones/{zid}/dns_records", params=params_dict)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_dns_record":
            zid = _get_zone_id(zone_id)
            if not record_id:
                raise ValueError("record_id required for get_dns_record")
            result = _cf_request("GET", f"/zones/{zid}/dns_records/{record_id}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_dns_record":
            zid = _get_zone_id(zone_id)
            if not record_type or not name or not content:
                raise ValueError("record_type, name, and content required for create_dns_record")
            payload = {
                "type": record_type,
                "name": name,
                "content": content,
                "ttl": ttl,
                "proxied": proxied,
            }
            if priority is not None:
                payload["priority"] = priority
            result = _cf_request("POST", f"/zones/{zid}/dns_records", data=payload)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "update_dns_record":
            zid = _get_zone_id(zone_id)
            if not record_id:
                raise ValueError("record_id required for update_dns_record")
            payload = {}
            if record_type:
                payload["type"] = record_type
            if name:
                payload["name"] = name
            if content:
                payload["content"] = content
            payload["ttl"] = ttl
            payload["proxied"] = proxied
            if priority is not None:
                payload["priority"] = priority
            result = _cf_request("PATCH", f"/zones/{zid}/dns_records/{record_id}", data=payload)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "delete_dns_record":
            zid = _get_zone_id(zone_id)
            if not record_id:
                raise ValueError("record_id required for delete_dns_record")
            result = _cf_request("DELETE", f"/zones/{zid}/dns_records/{record_id}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "export_dns":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/dns_records/export")
            return {
                "status": "success",
                "content": [{"text": str(result)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === WORKERS ===
        if action == "list_workers":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/workers/scripts")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_worker":
            acc_id = account_id or _get_account_id()
            if not worker_name:
                raise ValueError("worker_name required for get_worker")
            result = _cf_request("GET", f"/accounts/{acc_id}/workers/scripts/{worker_name}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2) if isinstance(result, dict) else str(result)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "deploy_worker":
            acc_id = account_id or _get_account_id()
            if not worker_name:
                raise ValueError("worker_name required for deploy_worker")
            
            # Get script content
            script_content = script
            if script_path:
                with open(script_path, "r") as f:
                    script_content = f.read()
            
            if not script_content:
                raise ValueError("script or script_path required for deploy_worker")
            
            # Simple script upload (no bindings)
            if not bindings:
                result = _cf_request(
                    "PUT",
                    f"/accounts/{acc_id}/workers/scripts/{worker_name}",
                    raw_body=script_content.encode("utf-8"),
                    content_type="application/javascript"
                )
            else:
                # Multipart upload with bindings
                import uuid
                boundary = f"----WebKitFormBoundary{uuid.uuid4().hex[:16]}"
                
                bindings_data = _parse_json(bindings, [])
                metadata = {"main_module": "worker.js", "bindings": bindings_data}
                
                body_parts = []
                body_parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="metadata"\r\nContent-Type: application/json\r\n\r\n{json.dumps(metadata)}')
                body_parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="worker.js"; filename="worker.js"\r\nContent-Type: application/javascript\r\n\r\n{script_content}')
                body_parts.append(f'--{boundary}--')
                
                body = "\r\n".join(body_parts).encode("utf-8")
                
                result = _cf_request(
                    "PUT",
                    f"/accounts/{acc_id}/workers/scripts/{worker_name}",
                    raw_body=body,
                    content_type=f"multipart/form-data; boundary={boundary}"
                )
            
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "worker_name": worker_name,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "delete_worker":
            acc_id = account_id or _get_account_id()
            if not worker_name:
                raise ValueError("worker_name required for delete_worker")
            result = _cf_request("DELETE", f"/accounts/{acc_id}/workers/scripts/{worker_name}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "list_worker_routes":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/workers/routes")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_worker_route":
            zid = _get_zone_id(zone_id)
            if not content or not worker_name:
                raise ValueError("content (pattern) and worker_name required for create_worker_route")
            result = _cf_request("POST", f"/zones/{zid}/workers/routes", data={"pattern": content, "script": worker_name})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === WORKERS KV ===
        if action == "list_kv_namespaces":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/storage/kv/namespaces", params={"page": page, "per_page": limit})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_kv_namespace":
            acc_id = account_id or _get_account_id()
            if not name:
                raise ValueError("name required for create_kv_namespace")
            result = _cf_request("POST", f"/accounts/{acc_id}/storage/kv/namespaces", data={"title": name})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "delete_kv_namespace":
            acc_id = account_id or _get_account_id()
            if not namespace_id:
                raise ValueError("namespace_id required for delete_kv_namespace")
            result = _cf_request("DELETE", f"/accounts/{acc_id}/storage/kv/namespaces/{namespace_id}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "list_kv_keys":
            acc_id = account_id or _get_account_id()
            if not namespace_id:
                raise ValueError("namespace_id required for list_kv_keys")
            params_dict = {"limit": limit}
            if keys_prefix:
                params_dict["prefix"] = keys_prefix
            result = _cf_request("GET", f"/accounts/{acc_id}/storage/kv/namespaces/{namespace_id}/keys", params=params_dict)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_kv_value":
            acc_id = account_id or _get_account_id()
            if not namespace_id or not key:
                raise ValueError("namespace_id and key required for get_kv_value")
            result = _cf_request("GET", f"/accounts/{acc_id}/storage/kv/namespaces/{namespace_id}/values/{key}")
            return {
                "status": "success",
                "content": [{"text": str(result)}],
                "action": action,
                "key": key,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "put_kv_value":
            acc_id = account_id or _get_account_id()
            if not namespace_id or not key or value is None:
                raise ValueError("namespace_id, key, and value required for put_kv_value")
            result = _cf_request(
                "PUT",
                f"/accounts/{acc_id}/storage/kv/namespaces/{namespace_id}/values/{key}",
                raw_body=value.encode("utf-8"),
                content_type="text/plain"
            )
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "key": key,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "delete_kv_value":
            acc_id = account_id or _get_account_id()
            if not namespace_id or not key:
                raise ValueError("namespace_id and key required for delete_kv_value")
            result = _cf_request("DELETE", f"/accounts/{acc_id}/storage/kv/namespaces/{namespace_id}/values/{key}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "key": key,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === D1 DATABASE ===
        if action == "list_d1_databases":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/d1/database", params={"page": page, "per_page": limit})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_d1_database":
            acc_id = account_id or _get_account_id()
            if not database_name:
                raise ValueError("database_name required for create_d1_database")
            result = _cf_request("POST", f"/accounts/{acc_id}/d1/database", data={"name": database_name})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "delete_d1_database":
            acc_id = account_id or _get_account_id()
            if not database_id:
                raise ValueError("database_id required for delete_d1_database")
            result = _cf_request("DELETE", f"/accounts/{acc_id}/d1/database/{database_id}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "d1_query":
            acc_id = account_id or _get_account_id()
            if not database_id or not sql:
                raise ValueError("database_id and sql required for d1_query")
            result = _cf_request("POST", f"/accounts/{acc_id}/d1/database/{database_id}/query", data={"sql": sql})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === R2 STORAGE ===
        if action == "list_r2_buckets":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/r2/buckets")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", {}).get("buckets", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_r2_bucket":
            acc_id = account_id or _get_account_id()
            if not bucket_name:
                raise ValueError("bucket_name required for create_r2_bucket")
            result = _cf_request("POST", f"/accounts/{acc_id}/r2/buckets", data={"name": bucket_name})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "delete_r2_bucket":
            acc_id = account_id or _get_account_id()
            if not bucket_name:
                raise ValueError("bucket_name required for delete_r2_bucket")
            result = _cf_request("DELETE", f"/accounts/{acc_id}/r2/buckets/{bucket_name}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === PAGES ===
        if action == "list_pages_projects":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/pages/projects")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_pages_project":
            acc_id = account_id or _get_account_id()
            if not project_name:
                raise ValueError("project_name required for get_pages_project")
            result = _cf_request("GET", f"/accounts/{acc_id}/pages/projects/{project_name}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_pages_project":
            acc_id = account_id or _get_account_id()
            if not project_name:
                raise ValueError("project_name required for create_pages_project")
            payload = {"name": project_name, "production_branch": production_branch or "main"}
            if data:
                payload.update(_parse_json(data, {}))
            result = _cf_request("POST", f"/accounts/{acc_id}/pages/projects", data=payload)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "delete_pages_project":
            acc_id = account_id or _get_account_id()
            if not project_name:
                raise ValueError("project_name required for delete_pages_project")
            result = _cf_request("DELETE", f"/accounts/{acc_id}/pages/projects/{project_name}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "list_pages_deployments":
            acc_id = account_id or _get_account_id()
            if not project_name:
                raise ValueError("project_name required for list_pages_deployments")
            result = _cf_request("GET", f"/accounts/{acc_id}/pages/projects/{project_name}/deployments")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === CLOUDFLARE AI ===
        if action == "list_ai_models":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/ai/models/search")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "ai_text_generation":
            acc_id = account_id or _get_account_id()
            model_name = model or "@cf/meta/llama-2-7b-chat-int8"
            
            if messages:
                payload = {"messages": _parse_json(messages, [])}
            elif prompt:
                payload = {"prompt": prompt}
            else:
                raise ValueError("prompt or messages required for ai_text_generation")
            
            result = _cf_request("POST", f"/accounts/{acc_id}/ai/run/{model_name}", data=payload)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "model": model_name,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "ai_text_embedding":
            acc_id = account_id or _get_account_id()
            model_name = model or "@cf/baai/bge-base-en-v1.5"
            if not prompt:
                raise ValueError("prompt required for ai_text_embedding")
            result = _cf_request("POST", f"/accounts/{acc_id}/ai/run/{model_name}", data={"text": prompt})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)[:8000]}],
                "action": action,
                "model": model_name,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "ai_translation":
            acc_id = account_id or _get_account_id()
            model_name = model or "@cf/meta/m2m100-1.2b"
            if not prompt:
                raise ValueError("prompt required for ai_translation")
            payload = {"text": prompt}
            if data:
                payload.update(_parse_json(data, {}))
            result = _cf_request("POST", f"/accounts/{acc_id}/ai/run/{model_name}", data=payload)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "model": model_name,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "ai_summarization":
            acc_id = account_id or _get_account_id()
            model_name = model or "@cf/facebook/bart-large-cnn"
            if not prompt:
                raise ValueError("prompt required for ai_summarization")
            result = _cf_request("POST", f"/accounts/{acc_id}/ai/run/{model_name}", data={"input_text": prompt})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "model": model_name,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === TUNNELS ===
        if action == "list_tunnels":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/cfd_tunnel", params={"page": page, "per_page": limit})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_tunnel":
            acc_id = account_id or _get_account_id()
            if not tunnel_id:
                raise ValueError("tunnel_id required for get_tunnel")
            result = _cf_request("GET", f"/accounts/{acc_id}/cfd_tunnel/{tunnel_id}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_tunnel":
            acc_id = account_id or _get_account_id()
            if not tunnel_name:
                raise ValueError("tunnel_name required for create_tunnel")
            payload = {"name": tunnel_name, "config_src": config_src or "cloudflare"}
            if tunnel_secret:
                payload["tunnel_secret"] = tunnel_secret
            result = _cf_request("POST", f"/accounts/{acc_id}/cfd_tunnel", data=payload)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "delete_tunnel":
            acc_id = account_id or _get_account_id()
            if not tunnel_id:
                raise ValueError("tunnel_id required for delete_tunnel")
            result = _cf_request("DELETE", f"/accounts/{acc_id}/cfd_tunnel/{tunnel_id}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_tunnel_token":
            acc_id = account_id or _get_account_id()
            if not tunnel_id:
                raise ValueError("tunnel_id required for get_tunnel_token")
            result = _cf_request("GET", f"/accounts/{acc_id}/cfd_tunnel/{tunnel_id}/token")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "list_tunnel_connections":
            acc_id = account_id or _get_account_id()
            if not tunnel_id:
                raise ValueError("tunnel_id required for list_tunnel_connections")
            result = _cf_request("GET", f"/accounts/{acc_id}/cfd_tunnel/{tunnel_id}/connections")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_tunnel_config":
            acc_id = account_id or _get_account_id()
            if not tunnel_id:
                raise ValueError("tunnel_id required for get_tunnel_config")
            result = _cf_request("GET", f"/accounts/{acc_id}/cfd_tunnel/{tunnel_id}/configurations")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "update_tunnel_config":
            acc_id = account_id or _get_account_id()
            if not tunnel_id or not data:
                raise ValueError("tunnel_id and data required for update_tunnel_config")
            result = _cf_request("PUT", f"/accounts/{acc_id}/cfd_tunnel/{tunnel_id}/configurations", data=_parse_json(data))
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === FIREWALL ===
        if action == "list_firewall_rules":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/firewall/rules", params={"page": page, "per_page": limit})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_firewall_rule":
            zid = _get_zone_id(zone_id)
            if not expression or not rule_action:
                raise ValueError("expression and rule_action required for create_firewall_rule")
            
            # First create the filter
            filter_result = _cf_request("POST", f"/zones/{zid}/filters", data=[{"expression": expression}])
            if not filter_result.get("success"):
                return {
                    "status": "error",
                    "content": [{"text": json.dumps(filter_result, indent=2)}],
                    "action": action,
                    "ms": int((time.time() - t0) * 1000),
                }
            
            filter_id = filter_result["result"][0]["id"]
            
            # Then create the rule
            rule_data = [{"filter": {"id": filter_id}, "action": rule_action}]
            if description:
                rule_data[0]["description"] = description
            
            result = _cf_request("POST", f"/zones/{zid}/firewall/rules", data=rule_data)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "delete_firewall_rule":
            zid = _get_zone_id(zone_id)
            if not rule_id:
                raise ValueError("rule_id required for delete_firewall_rule")
            result = _cf_request("DELETE", f"/zones/{zid}/firewall/rules/{rule_id}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === ACCESS (Zero Trust) ===
        if action == "list_access_apps":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/access/apps")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "list_access_groups":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/access/groups")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === CACHE ===
        if action == "purge_cache_all":
            zid = _get_zone_id(zone_id)
            result = _cf_request("POST", f"/zones/{zid}/purge_cache", data={"purge_everything": True})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "purge_cache_urls":
            zid = _get_zone_id(zone_id)
            if not purge_urls:
                raise ValueError("purge_urls required for purge_cache_urls")
            urls = _parse_json(purge_urls, [])
            result = _cf_request("POST", f"/zones/{zid}/purge_cache", data={"files": urls})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "purged_count": len(urls),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "purge_cache_tags":
            zid = _get_zone_id(zone_id)
            if not purge_tags:
                raise ValueError("purge_tags required for purge_cache_tags")
            tags = _parse_json(purge_tags, [])
            result = _cf_request("POST", f"/zones/{zid}/purge_cache", data={"tags": tags})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "purged_tags": len(tags),
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === SSL/TLS ===
        if action == "get_ssl_settings":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/settings/ssl")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "update_ssl_settings":
            zid = _get_zone_id(zone_id)
            if not value:
                raise ValueError("value required for update_ssl_settings (off, flexible, full, strict)")
            result = _cf_request("PATCH", f"/zones/{zid}/settings/ssl", data={"value": value})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "list_ssl_certificates":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/ssl/certificate_packs")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === PAGE RULES ===
        if action == "list_page_rules":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/pagerules")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_page_rule":
            zid = _get_zone_id(zone_id)
            if not data:
                raise ValueError("data (JSON with targets and actions) required for create_page_rule")
            result = _cf_request("POST", f"/zones/{zid}/pagerules", data=_parse_json(data))
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "delete_page_rule":
            zid = _get_zone_id(zone_id)
            if not rule_id:
                raise ValueError("rule_id required for delete_page_rule")
            result = _cf_request("DELETE", f"/zones/{zid}/pagerules/{rule_id}")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === ANALYTICS ===
        if action == "get_zone_analytics":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/analytics/dashboard", params={"since": "-10080", "continuous": "true"})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)[:8000]}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "get_dns_analytics":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/dns_analytics/report")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)[:8000]}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === LOAD BALANCING ===
        if action == "list_load_balancers":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/load_balancers")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "list_lb_pools":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/load_balancers/pools")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "list_lb_monitors":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/load_balancers/monitors")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === RATE LIMITING ===
        if action == "list_rate_limits":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/rate_limits")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_rate_limit":
            zid = _get_zone_id(zone_id)
            if not data:
                raise ValueError("data required for create_rate_limit")
            result = _cf_request("POST", f"/zones/{zid}/rate_limits", data=_parse_json(data))
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === EMAIL ROUTING ===
        if action == "get_email_routing":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/email/routing")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "list_email_rules":
            zid = _get_zone_id(zone_id)
            result = _cf_request("GET", f"/zones/{zid}/email/routing/rules")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === QUEUES ===
        if action == "list_queues":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/queues")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_queue":
            acc_id = account_id or _get_account_id()
            if not name:
                raise ValueError("name required for create_queue")
            result = _cf_request("POST", f"/accounts/{acc_id}/queues", data={"queue_name": name})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === HYPERDRIVE ===
        if action == "list_hyperdrives":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/hyperdrive/configs")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_hyperdrive":
            acc_id = account_id or _get_account_id()
            if not name or not data:
                raise ValueError("name and data (origin config) required for create_hyperdrive")
            payload = {"name": name}
            payload.update(_parse_json(data, {}))
            result = _cf_request("POST", f"/accounts/{acc_id}/hyperdrive/configs", data=payload)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === VECTORIZE ===
        if action == "list_vectorize_indexes":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/vectorize/indexes")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        if action == "create_vectorize_index":
            acc_id = account_id or _get_account_id()
            if not name or not data:
                raise ValueError("name and data (config) required for create_vectorize_index")
            payload = {"name": name}
            payload.update(_parse_json(data, {}))
            result = _cf_request("POST", f"/accounts/{acc_id}/vectorize/indexes", data=payload)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === DURABLE OBJECTS ===
        if action == "list_durable_objects":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/workers/durable_objects/namespaces")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === IMAGES ===
        if action == "list_images":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/images/v1", params={"page": page, "per_page": limit})
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", {}).get("images", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === STREAM ===
        if action == "list_stream_videos":
            acc_id = account_id or _get_account_id()
            result = _cf_request("GET", f"/accounts/{acc_id}/stream")
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "count": len(result.get("result", [])),
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === GENERIC API CALL ===
        if action == "api_call":
            if not content:
                raise ValueError("content (endpoint path) required for api_call")
            method_type = name or "GET"
            params_dict = _parse_json(params, None)
            data_dict = _parse_json(data, None)
            result = _cf_request(method_type.upper(), content, data=data_dict, params=params_dict)
            return {
                "status": "success" if result.get("success") else "error",
                "content": [{"text": json.dumps(_redact(result), indent=2)}],
                "action": action,
                "endpoint": content,
                "ms": int((time.time() - t0) * 1000),
            }
        
        # === UNKNOWN ACTION ===
        return {
            "status": "error",
            "content": [{
                "text": f"Unknown action: {action}. Valid actions: {', '.join(sorted(list(VALID_ACTIONS)))}"
            }],
            "action": action,
            "ms": int((time.time() - t0) * 1000),
        }
    
    except Exception as e:
        return {
            "status": "error",
            "content": [{"text": f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"}],
            "action": action,
            "ms": int((time.time() - t0) * 1000),
        }


if __name__ == "__main__":
    # Test basic functionality
    print("Testing use_cloudflare tool...")
    
    # List accounts (requires valid credentials)
    result = use_cloudflare(action="list_accounts")
    print(f"Result: {result['content'][0]['text'][:500]}...")
