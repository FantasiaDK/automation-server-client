from datetime import datetime
import os

import pytest
from automation_server_client._server import AutomationServer


def test_add_workqueue_item(ats: AutomationServer):
    workqueue = ats.workqueue()
    assert workqueue is not None

    data = {
        "event_timestamp": datetime.now().isoformat(),
        "message": "Test log entry",
        "level": "INFO",
        "logger_name": "test_logger",
    }

    workitem = workqueue.add_item(data, reference="test_reference")

    assert workitem is not None


def test_workitem_next(ats: AutomationServer):
    workqueue = ats.workqueue()
    assert workqueue is not None

    data = {
        "event_timestamp": datetime.now().isoformat(),
        "message": "Test log entry",
        "level": "INFO",
        "logger_name": "test_logger",
    }

    workitem = workqueue.add_item(data, reference="test_reference")
    
    item = next(workqueue)
    with item:
        assert item.id == workitem.id
        assert item.data == workitem.data
        assert item.reference == workitem.reference

def test_workqueue_empty_iterator(ats: AutomationServer):
    workqueue = ats.workqueue()
    assert workqueue is not None

    # Ensure the workqueue is empty
    workqueue.clear_workqueue()

    with pytest.raises(StopIteration):
        next(workqueue)  # Should raise StopIteration since the queue is empty

def test_workqueue_multiple_items(ats: AutomationServer):
    workqueue = ats.workqueue()
    assert workqueue is not None

    for i in range(5):
        data = {
            "event_timestamp": datetime.now().isoformat(),
            "message": f"Test log entry {i}",
            "level": "INFO",
            "logger_name": "test_logger",
        }
        workqueue.add_item(data, reference=f"test_reference_{i}")

    # Iterate through the workqueue and check items
    for i, item in enumerate(workqueue):
        with item:
            assert item.data["message"] == f"Test log entry {i}"
            assert item.reference == f"test_reference_{i}"
    
    assert i == 4  # Ensure we iterated through all 5 items
