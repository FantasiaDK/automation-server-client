import logging
import pytest # noqa: F401

from . import local_environment  # noqa: F401

def test_logging_setup_httpx(caplog, local_environment):

    # Check info logging in general
    
    logger = logging.getLogger("httpx")
    
    logger.info("Test log message")

    # Assert log content is empty since httpx is set to WARNING
    assert "" in caplog.text
    
    logger.warning("Warning message")
    
    assert "Warning message" in caplog.text   
    assert any(record.levelname == "WARNING" for record in caplog.records)
    assert any(record.name == "httpx" for record in caplog.records)