"""
Integration tests for use_cloudflare tool.

These tests require valid API credentials and make real API calls.
Skip these tests if credentials are not available.

To run: 
  CLOUDFLARE_API_TOKEN=xxx CLOUDFLARE_ACCOUNT_ID=xxx pytest tests/test_integration.py -v
"""

import json
import os
import pytest
from strands_cloudflare import use_cloudflare


# Skip all tests if no credentials
pytestmark = pytest.mark.skipif(
    not os.getenv("CLOUDFLARE_API_TOKEN") and not (
        os.getenv("CLOUDFLARE_API_KEY") and os.getenv("CLOUDFLARE_EMAIL")
    ),
    reason="CLOUDFLARE_API_TOKEN or CLOUDFLARE_API_KEY+EMAIL required for integration tests"
)


class TestZones:
    """Integration tests for zone endpoints."""

    def test_list_zones(self):
        result = use_cloudflare(action="list_zones")
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text or "Authentication" in error_text:
                pytest.skip("Invalid API credentials")
            pytest.fail(f"Unexpected error: {error_text}")
        
        assert result["status"] == "success"
        data = json.loads(result["content"][0]["text"])
        
        # API returns 'result' key
        assert "result" in data
        assert isinstance(data["result"], list)

    def test_list_zones_with_status_filter(self):
        result = use_cloudflare(
            action="list_zones",
            params='{"status": "active"}'
        )
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text or "Authentication" in error_text:
                pytest.skip("Invalid API credentials")
        
        assert result["status"] == "success"


class TestDNS:
    """Integration tests for DNS endpoints."""

    @pytest.fixture
    def zone_id(self):
        zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
        if not zone_id:
            # Try to get first zone
            result = use_cloudflare(action="list_zones")
            if result["status"] == "success":
                data = json.loads(result["content"][0]["text"])
                # API returns 'result' key
                if data.get("result"):
                    return data["result"][0]["id"]
        return zone_id

    def test_list_dns_records(self, zone_id):
        if not zone_id:
            pytest.skip("No zone_id available")
        
        result = use_cloudflare(action="list_dns_records", zone_id=zone_id)
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text or "403" in error_text:
                pytest.skip("Invalid credentials or permissions")
        
        assert result["status"] == "success"
        data = json.loads(result["content"][0]["text"])
        assert "result" in data

    def test_list_dns_records_with_type_filter(self, zone_id):
        if not zone_id:
            pytest.skip("No zone_id available")
        
        result = use_cloudflare(
            action="list_dns_records", 
            zone_id=zone_id,
            params='{"type": "A"}'
        )
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text or "403" in error_text:
                pytest.skip("Invalid credentials or permissions")
        
        assert result["status"] == "success"


class TestWorkers:
    """Integration tests for Workers endpoints."""

    @pytest.fixture
    def account_id(self):
        return os.getenv("CLOUDFLARE_ACCOUNT_ID")

    def test_list_workers(self, account_id):
        if not account_id:
            pytest.skip("CLOUDFLARE_ACCOUNT_ID required")
        
        result = use_cloudflare(action="list_workers", account_id=account_id)
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text or "403" in error_text:
                pytest.skip("Invalid credentials or no workers permissions")
        
        assert result["status"] == "success"


class TestKV:
    """Integration tests for KV endpoints."""

    @pytest.fixture
    def account_id(self):
        return os.getenv("CLOUDFLARE_ACCOUNT_ID")

    def test_list_kv_namespaces(self, account_id):
        if not account_id:
            pytest.skip("CLOUDFLARE_ACCOUNT_ID required")
        
        result = use_cloudflare(action="list_kv_namespaces", account_id=account_id)
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text or "403" in error_text:
                pytest.skip("Invalid credentials or no KV permissions")
        
        assert result["status"] == "success"


class TestD1:
    """Integration tests for D1 endpoints."""

    @pytest.fixture
    def account_id(self):
        return os.getenv("CLOUDFLARE_ACCOUNT_ID")

    def test_list_d1_databases(self, account_id):
        if not account_id:
            pytest.skip("CLOUDFLARE_ACCOUNT_ID required")
        
        result = use_cloudflare(action="list_d1_databases", account_id=account_id)
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text or "403" in error_text:
                pytest.skip("Invalid credentials or no D1 permissions")
        
        assert result["status"] == "success"


class TestR2:
    """Integration tests for R2 endpoints."""

    @pytest.fixture
    def account_id(self):
        return os.getenv("CLOUDFLARE_ACCOUNT_ID")

    def test_list_r2_buckets(self, account_id):
        if not account_id:
            pytest.skip("CLOUDFLARE_ACCOUNT_ID required")
        
        result = use_cloudflare(action="list_r2_buckets", account_id=account_id)
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text or "403" in error_text:
                pytest.skip("Invalid credentials or no R2 permissions")
        
        assert result["status"] == "success"


class TestPages:
    """Integration tests for Pages endpoints."""

    @pytest.fixture
    def account_id(self):
        return os.getenv("CLOUDFLARE_ACCOUNT_ID")

    def test_list_pages_projects(self, account_id):
        if not account_id:
            pytest.skip("CLOUDFLARE_ACCOUNT_ID required")
        
        result = use_cloudflare(action="list_pages_projects", account_id=account_id)
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text or "403" in error_text:
                pytest.skip("Invalid credentials or no Pages permissions")
        
        assert result["status"] == "success"


class TestSSL:
    """Integration tests for SSL endpoints."""

    @pytest.fixture
    def zone_id(self):
        zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
        if not zone_id:
            result = use_cloudflare(action="list_zones")
            if result["status"] == "success":
                data = json.loads(result["content"][0]["text"])
                if data.get("result"):
                    return data["result"][0]["id"]
        return zone_id

    def test_get_ssl_settings(self, zone_id):
        if not zone_id:
            pytest.skip("No zone_id available")
        
        result = use_cloudflare(action="zone_settings", zone_id=zone_id)
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text or "403" in error_text:
                pytest.skip("Invalid credentials or permissions")
        
        assert result["status"] == "success"


class TestCache:
    """Integration tests for Cache endpoints."""

    @pytest.fixture
    def zone_id(self):
        zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
        if not zone_id:
            result = use_cloudflare(action="list_zones")
            if result["status"] == "success":
                data = json.loads(result["content"][0]["text"])
                if data.get("result"):
                    return data["result"][0]["id"]
        return zone_id

    def test_get_cache_settings(self, zone_id):
        if not zone_id:
            pytest.skip("No zone_id available")
        
        # Use zone_settings to get cache related settings
        result = use_cloudflare(action="zone_settings", zone_id=zone_id)
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text or "403" in error_text:
                pytest.skip("Invalid credentials or permissions")
        
        assert result["status"] == "success"


class TestFirewall:
    """Integration tests for Firewall endpoints."""

    @pytest.fixture
    def zone_id(self):
        zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
        if not zone_id:
            result = use_cloudflare(action="list_zones")
            if result["status"] == "success":
                data = json.loads(result["content"][0]["text"])
                if data.get("result"):
                    return data["result"][0]["id"]
        return zone_id

    def test_list_firewall_rules(self, zone_id):
        if not zone_id:
            pytest.skip("No zone_id available")
        
        result = use_cloudflare(action="list_firewall_rules", zone_id=zone_id)
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text or "403" in error_text:
                pytest.skip("Invalid credentials or permissions")
        
        assert result["status"] == "success"


class TestUser:
    """Integration tests for User endpoints."""

    def test_get_user(self):
        result = use_cloudflare(action="get_user")
        
        if result["status"] == "error":
            error_text = result["content"][0]["text"]
            if "401" in error_text:
                pytest.skip("Invalid API credentials")
        
        assert result["status"] == "success"
        data = json.loads(result["content"][0]["text"])
        # get_user returns user data directly (no 'result' wrapper)
        # Check for common user fields
        assert "id" in data or "email" in data or "result" in data


class TestAnalytics:
    """Integration tests for Analytics endpoints."""

    @pytest.fixture
    def zone_id(self):
        zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
        if not zone_id:
            result = use_cloudflare(action="list_zones")
            if result["status"] == "success":
                data = json.loads(result["content"][0]["text"])
                if data.get("result"):
                    return data["result"][0]["id"]
        return zone_id

    def test_get_analytics(self, zone_id):
        if not zone_id:
            pytest.skip("No zone_id available")
        
        result = use_cloudflare(action="get_analytics", zone_id=zone_id)
        
        # Analytics can fail for various reasons (free plan, no data, etc.)
        if result["status"] == "error":
            error_text = result["content"][0]["text"] or ""
            # Skip if any common error condition
            if any(skip_cond in error_text.lower() for skip_cond in [
                "401", "403", "404", "not found", "not available", 
                "plan", "null", "none", "permission"
            ]) or error_text.strip() == "null":
                pytest.skip("Analytics not available for this zone/plan")
        
        # If we get here with error and null content, still skip
        if result["status"] == "error":
            content_text = result["content"][0]["text"]
            if content_text is None or content_text.strip() in ["null", ""]:
                pytest.skip("Analytics returned no data (possibly free plan)")
        
        assert result["status"] == "success"
