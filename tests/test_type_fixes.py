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


def test_config_type_annotations():
    """Test that all config attributes have correct types after initialization"""
    os.environ["ATS_URL"] = "http://localhost:8000"
    os.environ["ATS_TOKEN"] = "test_token"
    os.environ["ATS_SESSION"] = "test_session"
    os.environ["ATS_WORKQUEUE_OVERRIDE"] = "999"
    
    AutomationServerConfig.init_from_environment()
    
    # String fields
    assert isinstance(AutomationServerConfig.url, str)
    assert isinstance(AutomationServerConfig.token, str)
    
    # String or None fields
    assert isinstance(AutomationServerConfig.session, str) or AutomationServerConfig.session is None
    
    # Int or None fields
    assert isinstance(AutomationServerConfig.workqueue_override, int) or AutomationServerConfig.workqueue_override is None
    assert isinstance(AutomationServerConfig.workitem_id, int) or AutomationServerConfig.workitem_id is None


def test_workitem_id_assignment():
    """Test that workitem_id can be assigned int values"""
    # This should not raise any type errors at runtime
    AutomationServerConfig.workitem_id = 123
    assert AutomationServerConfig.workitem_id == 123
    
    AutomationServerConfig.workitem_id = None  
    assert AutomationServerConfig.workitem_id is None