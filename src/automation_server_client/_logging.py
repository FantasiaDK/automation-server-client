import logging
import requests
import traceback

from typing import Dict, Any
from datetime import datetime
from ._config import AutomationServerConfig


# Custom HTTP Handler for logging
class AutomationServerLoggingHandler(logging.Handler):
    """Module-level shared logging handler instance used by the server package."""

    def __init__(self):
        """Logging handler that posts structured logs to the automation server.

        The handler uses ``AutomationServerConfig.session`` and ``url`` to
        determine if logs should be transmitted. It keeps a mutable
        ``workitem_id`` that can be set by the workqueue / workitem lifecycle
        helpers so logs include work item context.
        """

        super().__init__()
        self.workitem_id = None
        self.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))

    def emit(self, record):
        """Emit a LogRecord by POSTing it to the server's audit-logs endpoint.

        The method is intentionally best-effort: if the configuration is not
        present or the HTTP POST fails, the error is printed and processing
        continues.
        """

        log_record = self._format_log_record(record)

        if AutomationServerConfig.session is None or AutomationServerConfig.url == "":
            return

        try:
            response = requests.post(
                f"{AutomationServerConfig.url}/audit-logs",
                headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
                json=log_record,
                timeout=10,
            )
            response.raise_for_status()

        except requests.RequestException as e:
            # Handle any exceptions that occur when sending the log
            print(
                f"Failed to send log to {AutomationServerConfig.url}/sessions/"
                f"{AutomationServerConfig.session}/log: {e}"
            )

    def start_workitem(self, workitem_id: int):
        """Mark a work item as active for subsequent log records."""

        self.workitem_id = workitem_id

    def end_workitem(self):
        """Clear any active work item context."""

        self.workitem_id = None

    def _format_log_record(self, record: logging.LogRecord) -> Dict[str, Any]:
        """
        Convert LogRecord to api format.
        """
        # Extract structured data from record.__dict__ (from extra parameter)
        structured_data = {}

        # Get all extra fields (anything not in standard LogRecord attributes)
        standard_attrs = {
            "asctimename",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "lineno",
            "funcName",
            "name",
            "created",
            "msecs",
            "relativeCreated",
            "taskNamethread",
            "taskName",
            "thread",
            "threadName",
            "processName",
            "process",
            "exc_info",
            "exc_text",
            "stack_info",
            "message",
        }

        for key, value in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                structured_data[key] = value

        # Handle exception information
        exception_type = None
        exception_message = None
        traceback_text = None

        if record.exc_info:
            exception_type = record.exc_info[0].__name__
            exception_message = str(record.exc_info[1])
            traceback_text = "".join(traceback.format_exception(*record.exc_info))

        return {
            "session_id": AutomationServerConfig.session,
            "workitem_id": self.workitem_id,  # Now uses instance variable
            "message": record.getMessage(),
            "level": record.levelname,
            "logger_name": record.name,
            "module": record.module if hasattr(record, "module") else record.filename,
            "function_name": record.funcName,
            "line_number": record.lineno,
            "exception_type": exception_type,
            "exception_message": exception_message,
            "traceback": traceback_text,
            "structured_data": structured_data if structured_data else None,
            "event_timestamp": datetime.fromtimestamp(record.created).isoformat(),
        }

ats_logging_handler = AutomationServerLoggingHandler()
