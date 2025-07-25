import os
from automation_server_client import AutomationServerConfig


def test_workqueue_override_type_conversion():
    """Test that workqueue_override is properly converted from string to int"""
    # Set environment variable as string (how env vars always come in)
    os.environ["ATS_URL"] = "http://localhost:8000"
    os.environ["ATS_WORKQUEUE_OVERRIDE"] = "12345"

    AutomationServerConfig.init_from_environment()

    # Should be converted to int
    assert isinstance(AutomationServerConfig.workqueue_override, int)
    assert AutomationServerConfig.workqueue_override == 12345


def test_workqueue_override_none_when_not_set():
    """Test that workqueue_override is None when environment variable not set"""
    # Clear environment variable if it exists
    if "ATS_WORKQUEUE_OVERRIDE" in os.environ:
        del os.environ["ATS_WORKQUEUE_OVERRIDE"]

    os.environ["ATS_URL"] = "http://localhost:8000"

    AutomationServerConfig.init_from_environment()

    # Should be None when not set
    assert AutomationServerConfig.workqueue_override is None
