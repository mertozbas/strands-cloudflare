#!/usr/bin/env python3
"""
Universal Cloudflare Tool for Strands Agents

A dynamic tool for interacting with ALL Cloudflare services using the official
cloudflare-python SDK. No hardcoded endpoints - directly maps to SDK methods.

Licensed under the Apache License, Version 2.0
"""

from __future__ import annotations

import json
import os
import time
import traceback
from typing import Any, Dict, Optional

from strands import tool

# Sensitive keys to redact from output
SENSITIVE_KEYS = {
    "api_key",
    "api_token",
    "auth_key",
    "auth_token",
    "secret",
    "password",
    "private_key",
    "certificate",
    "tunnel_secret",
}


def _redact(obj: Any) -> Any:
    """Recursively redact sensitive data from output."""
    if isinstance(obj, dict):
        return {
            k: (
                "***REDACTED***"
                if any(s in str(k).lower() for s in ["secret", "key", "token", "password"])
                else _redact(v)
            )
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact(x) for x in obj]
    return obj


def _to_dict(obj: Any) -> Any:
    """Convert SDK objects to dictionaries recursively."""
    from datetime import datetime, date

    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    # Handle datetime objects - convert to ISO format string
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_dict(item) for item in obj]
    if hasattr(obj, "model_dump"):
        # model_dump may return datetimes too, so recurse
        return _to_dict(obj.model_dump())
    if hasattr(obj, "__dict__"):
        return {k: _to_dict(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    return str(obj)


def _parse_params(params: Optional[str]) -> Dict[str, Any]:
    """Parse JSON params string to dict."""
    if not params:
        return {}
    if isinstance(params, dict):
        return params
    try:
        return json.loads(params)
    except json.JSONDecodeError:
        return {}


def _get_client():
    """Get Cloudflare client using official SDK."""
    try:
        from cloudflare import Cloudflare
    except ImportError:
        raise ImportError("cloudflare package required. Install with: pip install cloudflare")

    api_token = os.getenv("CLOUDFLARE_API_TOKEN") or os.getenv("CF_API_TOKEN")
    api_key = os.getenv("CLOUDFLARE_API_KEY") or os.getenv("CF_API_KEY")
    email = os.getenv("CLOUDFLARE_EMAIL") or os.getenv("CF_EMAIL")

    if api_token:
        return Cloudflare(api_token=api_token)
    elif api_key and email:
        return Cloudflare(api_key=api_key, api_email=email)
    return Cloudflare()


def _resolve_path(client: Any, path: str) -> Any:
    """Resolve a dot-separated path on the client object."""
    obj = client
    for part in path.split("."):
        if not hasattr(obj, part):
            available = [a for a in dir(obj) if not a.startswith("_")]
            raise AttributeError(f"'{part}' not found. Available: {available}")
        obj = getattr(obj, part)
    return obj


def _list_services(client: Any, path: str = "") -> Dict[str, Any]:
    """List available services/methods at a given path."""
    try:
        obj = _resolve_path(client, path) if path else client
    except AttributeError:
        obj = client

    # Just list attribute names without deep inspection to avoid circular imports
    attrs = [a for a in dir(obj) if not a.startswith("_")]
    return {"available": attrs, "path": path or "root"}


@tool
def use_cloudflare(
    service: str,
    operation: str,
    params: Optional[str] = None,
    account_id: Optional[str] = None,
    zone_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Universal Cloudflare client - dynamically calls any SDK method.

    This tool provides direct access to the entire cloudflare-python SDK.
    Specify the service path and operation, and it calls the corresponding
    SDK method with your parameters.

    Args:
        service: SDK service path (e.g., "zones", "dns.records", "workers.scripts",
                 "kv.namespaces", "d1.database", "r2.buckets", "zero_trust.tunnels").
                 Use "_" to list all top-level services.
        operation: Method to call (e.g., "list", "get", "create", "delete", "update").
                   Use "_" to list available operations for the service.
        params: JSON string of parameters for the operation.
                Common params are auto-injected (account_id, zone_id).
        account_id: Cloudflare account ID (or set CLOUDFLARE_ACCOUNT_ID env var)
        zone_id: Cloudflare zone ID (or set CLOUDFLARE_ZONE_ID env var)

    Returns:
        Dict with status, content, and execution time.

    Environment Variables:
        - CLOUDFLARE_API_TOKEN: API Token (recommended)
        - CLOUDFLARE_API_KEY + CLOUDFLARE_EMAIL: Global API Key
        - CLOUDFLARE_ACCOUNT_ID: Default account ID
        - CLOUDFLARE_ZONE_ID: Default zone ID

    Examples:
        # List all services
        use_cloudflare(service="_", operation="_")

        # List zones
        use_cloudflare(service="zones", operation="list")

        # Get specific zone
        use_cloudflare(service="zones", operation="get", zone_id="abc123")

        # List DNS records
        use_cloudflare(service="dns.records", operation="list", zone_id="abc123")

        # Create DNS record
        use_cloudflare(
            service="dns.records",
            operation="create",
            zone_id="abc123",
            params='{"type": "A", "name": "www", "content": "192.0.2.1", "proxied": true}'
        )

        # List Workers
        use_cloudflare(service="workers.scripts", operation="list", account_id="xyz")

        # List KV namespaces
        use_cloudflare(service="kv.namespaces", operation="list", account_id="xyz")

        # Query D1 database
        use_cloudflare(
            service="d1.database",
            operation="query",
            account_id="xyz",
            params='{"database_id": "db-id", "sql": "SELECT * FROM users"}'
        )

        # List Cloudflare Tunnels
        use_cloudflare(service="zero_trust.tunnels", operation="list", account_id="xyz")

        # Run AI model
        use_cloudflare(
            service="ai",
            operation="run",
            account_id="xyz",
            params='{"model_name": "@cf/meta/llama-2-7b-chat-int8", "prompt": "Hello"}'
        )

        # Purge cache
        use_cloudflare(
            service="cache",
            operation="purge",
            zone_id="abc123",
            params='{"purge_everything": true}'
        )

    Service Reference (common paths):
        - zones: Zone management
        - dns.records: DNS record management
        - workers.scripts: Worker scripts
        - workers.routes: Worker routes
        - kv.namespaces: KV storage
        - kv.namespaces.keys: KV keys
        - kv.namespaces.values: KV values
        - d1.database: D1 SQL databases
        - r2.buckets: R2 object storage
        - pages.projects: Pages projects
        - zero_trust.tunnels: Cloudflare Tunnels
        - zero_trust.access.applications: Access apps
        - firewall.rules: Firewall rules
        - cache: Cache operations
        - ssl.certificate_packs: SSL certificates
        - load_balancers: Load balancers
        - ai: Workers AI
        - queues: Queues
        - vectorize.indexes: Vectorize
        - images.v1: Cloudflare Images
        - stream: Cloudflare Stream
    """
    t0 = time.time()

    try:
        client = _get_client()

        # Handle discovery requests
        if service == "_" or operation == "_":
            path = "" if service == "_" else service
            services = _list_services(client, path)
            return {
                "status": "success",
                "content": [{"json": {"service": path or "root", "ms": int((time.time() - t0) * 1000), **services}}],
            }

        # Build parameters
        call_params = _parse_params(params)

        # Only inject IDs if explicitly provided (not from env) to avoid param name mismatches
        # SDK uses various names: account_id, account, zone_id, zone, etc.
        if account_id:
            call_params["account_id"] = account_id
        if zone_id:
            call_params["zone_id"] = zone_id

        # Resolve service path and get operation
        service_obj = _resolve_path(client, service)

        if not hasattr(service_obj, operation):
            available = [
                a for a in dir(service_obj) if not a.startswith("_") and callable(getattr(service_obj, a, None))
            ]
            raise AttributeError(f"Operation '{operation}' not found on '{service}'. Available: {available}")

        method = getattr(service_obj, operation)

        # Call the method
        result = method(**call_params)

        # Handle iterators/generators (pagination)
        if hasattr(result, "__iter__") and not isinstance(result, (str, dict, list)):
            result = list(result)

        # Convert to dict for JSON serialization
        result_dict = _to_dict(result)

        return {
            "status": "success",
            "content": [
                {
                    "json": {
                        "service": service,
                        "operation": operation,
                        "ms": int((time.time() - t0) * 1000),
                        "result": _redact(result_dict),
                    }
                }
            ],
        }

    except Exception as e:
        return {
            "status": "error",
            "content": [{"text": f"{type(e).__name__}: {e}\n\n{traceback.format_exc()}"}],
        }


if __name__ == "__main__":
    # Quick test
    print("Testing use_cloudflare dynamic tool...")

    # List available services
    result = use_cloudflare(service="_", operation="_")
    print(f"Root services:\n{result['content'][0]['text'][:1000]}")
