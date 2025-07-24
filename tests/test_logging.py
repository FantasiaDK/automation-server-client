from datetime import datetime
from logging import LogRecord
import logging
from  automation_server_client._logging import ats_logging_handler
import httpx

base_url = "http://localhost/api"


def test_basic_create_log_entry():
    log_data = {
        "event_timestamp": datetime.now().isoformat(),
        "message": "Test log entry",
        "level": "INFO",
        "logger_name": "test_logger",
    }

    with httpx.Client() as client:
        response = client.post(f"{base_url}/audit-logs", json=log_data)

    assert response.status_code == 204

def test_format_log_record():

    # Need to get a record from the logging system
    record = LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="tests/test_logging.py",
        lineno=42,
        msg="This is a test log message",
        args=(),
        exc_info=None,
    )
    
    formatted_log = ats_logging_handler._format_log_record(record)

    assert isinstance(formatted_log, dict)
    assert "event_timestamp" in formatted_log
    assert "message" in formatted_log
    assert formatted_log["message"] == "This is a test log message"
    assert formatted_log["level"] == "INFO"
    assert formatted_log["logger_name"] == "test_logger"
    assert "structured_data" in formatted_log
    assert isinstance(formatted_log["structured_data"], dict)
#    assert "session_id" in formatted_log["structured_data"]
#    assert formatted_log["structured_data"]["session_id"] is not None

def test_server_accepts_record():

    # Need to get a record from the logging system
    record = LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="tests/test_logging.py",
        lineno=42,
        msg="This is a test log message",
        args=(),
        exc_info=None,
    )
    
    formatted_log = ats_logging_handler._format_log_record(record)

    with httpx.Client() as client:
        response = client.post(f"{base_url}/audit-logs", json=formatted_log)

    assert response.status_code == 204
