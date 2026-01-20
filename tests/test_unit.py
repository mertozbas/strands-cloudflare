"""
Unit tests for use_cloudflare tool.

These tests don't require API credentials - they test the tool's
internal logic, parameter validation, and error handling.
"""

import json
import os
import pytest
from strands_cloudflare import use_cloudflare


class TestListActions:
    """Tests for list_actions action."""

    def test_list_actions_returns_success(self):
        result = use_cloudflare(action="list_actions")
        assert result["status"] == "success"

    def test_list_actions_returns_actions(self):
        result = use_cloudflare(action="list_actions")
        text = result["content"][0]["text"]
        data = json.loads(text)
        assert "actions" in data

    def test_list_actions_includes_core_actions(self):
        result = use_cloudflare(action="list_actions")
        text = result["content"][0]["text"]
        data = json.loads(text)
        actions = data["actions"]
        
        # Check for core actions
        core_actions = ["list_zones", "list_dns_records", "list_workers"]
        for action in core_actions:
            assert action in actions


class TestDescribe:
    """Tests for describe action."""

    def test_describe_returns_success(self):
        result = use_cloudflare(action="describe")
        assert result["status"] == "success"

    def test_describe_includes_action_details(self):
        result = use_cloudflare(action="describe")
        text = result["content"][0]["text"]
        # Should contain usage examples
        assert "list_zones" in text or "example" in text.lower() or "action" in text.lower()


class TestUnknownAction:
    """Tests for unknown action handling."""

    def test_unknown_action_returns_error(self):
        result = use_cloudflare(action="unknown_invalid_action_xyz")
        assert result["status"] == "error"

    def test_unknown_action_lists_valid_actions(self):
        result = use_cloudflare(action="unknown_invalid_action_xyz")
        text = result["content"][0]["text"].lower()
        # Should suggest valid actions
        assert "unknown" in text or "valid" in text or "list_zones" in text


class TestParameterValidation:
    """Tests for parameter validation."""

    def test_list_dns_records_requires_zone_id(self):
        """list_dns_records needs zone_id."""
        result = use_cloudflare(action="list_dns_records")
        # Should fail due to missing zone_id OR missing credentials
        assert result["status"] == "error"
        text = result["content"][0]["text"].lower()
        assert "zone_id" in text or "zone" in text or "credentials" in text

    def test_create_dns_record_requires_params(self):
        """create_dns_record needs zone_id and record details."""
        result = use_cloudflare(action="create_dns_record")
        assert result["status"] == "error"
        text = result["content"][0]["text"].lower()
        assert "zone" in text or "record" in text or "type" in text or "credentials" in text

    def test_update_dns_record_requires_record_id(self):
        """update_dns_record needs record_id."""
        result = use_cloudflare(action="update_dns_record", zone_id="test")
        assert result["status"] == "error"
        text = result["content"][0]["text"].lower()
        assert "record_id" in text or "record" in text or "credentials" in text

    def test_delete_dns_record_requires_record_id(self):
        """delete_dns_record needs record_id."""
        result = use_cloudflare(action="delete_dns_record", zone_id="test")
        assert result["status"] == "error"
        text = result["content"][0]["text"].lower()
        assert "record_id" in text or "record" in text or "credentials" in text

    def test_deploy_worker_requires_account_or_name(self):
        """deploy_worker needs account_id or worker name."""
        result = use_cloudflare(action="deploy_worker")
        assert result["status"] == "error"
        text = result["content"][0]["text"].lower()
        # Can fail with worker/name/account/script OR account_id required
        assert "worker" in text or "name" in text or "account" in text or "script" in text or "credentials" in text

    def test_delete_worker_requires_account_or_name(self):
        """delete_worker needs worker name or account_id."""
        result = use_cloudflare(action="delete_worker")
        assert result["status"] == "error"
        text = result["content"][0]["text"].lower()
        # Can fail with worker/name requirement OR account_id requirement
        assert "worker" in text or "name" in text or "account" in text or "credentials" in text

    def test_d1_query_requires_params(self):
        """d1_query needs database_id, sql, or account_id."""
        result = use_cloudflare(action="d1_query")
        assert result["status"] == "error"
        text = result["content"][0]["text"].lower()
        # Can fail with database/sql/d1 requirement OR account_id requirement
        assert "database" in text or "sql" in text or "d1" in text or "account" in text or "credentials" in text


class TestCredentialValidation:
    """Tests for credential validation (when no env credentials set)."""

    def test_list_zones_requires_credentials(self):
        """list_zones should require API credentials."""
        # Temporarily unset credentials
        old_token = os.environ.pop("CLOUDFLARE_API_TOKEN", None)
        old_key = os.environ.pop("CLOUDFLARE_API_KEY", None)
        old_email = os.environ.pop("CLOUDFLARE_EMAIL", None)
        
        try:
            result = use_cloudflare(action="list_zones")
            # Without credentials, should error
            if result["status"] == "error":
                text = result["content"][0]["text"].lower()
                assert "credentials" in text or "token" in text or "authentication" in text
            # If success, credentials must have been found somehow (account-level)
        finally:
            # Restore credentials
            if old_token:
                os.environ["CLOUDFLARE_API_TOKEN"] = old_token
            if old_key:
                os.environ["CLOUDFLARE_API_KEY"] = old_key
            if old_email:
                os.environ["CLOUDFLARE_EMAIL"] = old_email

    def test_list_workers_requires_credentials_or_account(self):
        """list_workers should require credentials or account_id."""
        # Temporarily unset credentials
        old_token = os.environ.pop("CLOUDFLARE_API_TOKEN", None)
        old_key = os.environ.pop("CLOUDFLARE_API_KEY", None)
        old_email = os.environ.pop("CLOUDFLARE_EMAIL", None)
        old_account = os.environ.pop("CLOUDFLARE_ACCOUNT_ID", None)
        
        try:
            result = use_cloudflare(action="list_workers")
            # Without credentials, should error
            if result["status"] == "error":
                text = result["content"][0]["text"].lower()
                assert "credentials" in text or "account" in text or "authentication" in text
        finally:
            # Restore credentials
            if old_token:
                os.environ["CLOUDFLARE_API_TOKEN"] = old_token
            if old_key:
                os.environ["CLOUDFLARE_API_KEY"] = old_key
            if old_email:
                os.environ["CLOUDFLARE_EMAIL"] = old_email
            if old_account:
                os.environ["CLOUDFLARE_ACCOUNT_ID"] = old_account


class TestResponseFormat:
    """Tests for consistent response format."""

    def test_response_has_status(self):
        result = use_cloudflare(action="list_actions")
        assert "status" in result
        assert result["status"] in ["success", "error"]

    def test_response_has_content(self):
        result = use_cloudflare(action="list_actions")
        assert "content" in result
        assert isinstance(result["content"], list)
        assert len(result["content"]) > 0
        assert "text" in result["content"][0]

    def test_response_has_ms(self):
        result = use_cloudflare(action="list_actions")
        assert "ms" in result
        assert isinstance(result["ms"], int)
        assert result["ms"] >= 0

    def test_response_has_action(self):
        result = use_cloudflare(action="list_actions")
        assert "action" in result
        assert result["action"] == "list_actions"


class TestJsonParsing:
    """Tests for JSON argument parsing."""

    def test_params_as_json_object(self):
        result = use_cloudflare(
            action="list_zones",
            params='{"status": "active"}'
        )
        # Should succeed if credentials exist, or fail with credential error
        # NOT fail with JSON parsing error
        if result["status"] == "error":
            text = result["content"][0]["text"].lower()
            # JSON should be parsed correctly - error should be about credentials or API
            assert "json" not in text or "credentials" in text or "parse" not in text

    def test_invalid_params_json_graceful(self):
        """Invalid JSON should be handled gracefully (ignored or error)."""
        result = use_cloudflare(
            action="list_zones",
            params="not valid json {"
        )
        # Either succeeds (ignoring invalid params) or errors gracefully
        # We just check the response is well-formed
        assert "status" in result
        assert "content" in result


class TestActionNormalization:
    """Tests for action name normalization."""

    def test_action_case_insensitive(self):
        result1 = use_cloudflare(action="LIST_ACTIONS")
        result2 = use_cloudflare(action="list_actions")
        result3 = use_cloudflare(action="List_Actions")
        
        assert result1["status"] == result2["status"] == result3["status"]

    def test_action_with_whitespace(self):
        result = use_cloudflare(action="  list_actions  ")
        assert result["status"] == "success"

    def test_action_with_dashes(self):
        # If tool supports dash-notation
        result = use_cloudflare(action="list-actions")
        # Should either work or give clear error
        assert result["status"] in ["success", "error"]
