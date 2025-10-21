import logging

from ._config import AutomationServerConfig
from ._logging import ats_logging_handler
from ._models import Session, Process, Workqueue


class AutomationServer:
    """Entrypoint for interacting with the automation server.

    Typical usage is to call :py:meth:`from_environment` which will load
    configuration, attach the HTTP logging handler and return a configured
    instance. Use :py:meth:`workqueue` to obtain a `Workqueue` model for the
    configured session/process.
    """

    session_id = None

    def __init__(self, session_id=None):
        """Create an AutomationServer instance.

        Args:
            session_id: Optional session id to attach; when provided the
                instance will fetch the session and process and determine the
                workqueue id. If omitted, the instance operates without a
                session context.
        """
        # store provided session_id on the instance for later use
        self.session_id = session_id
        self.workqueue_id = None

        self.url = AutomationServerConfig.url
        self.token = AutomationServerConfig.token

        if session_id is not None:
            self.session = Session.get_session(session_id)
            self.process = Process.get_process(self.session.process_id)
            if self.process.workqueue_id is not None:
                self.workqueue_id = self.process.workqueue_id
        else:
            self.session = None
            self.process = None

        if AutomationServerConfig.workqueue_override is not None:
            self.workqueue_id = AutomationServerConfig.workqueue_override

    def workqueue(self):
        """Return the configured `Workqueue` model.

        Raises:
            ValueError: If no workqueue id is configured on this instance.
        """

        if self.workqueue_id is None:
            raise ValueError("workqueue_id is not set")

        return Workqueue.get_workqueue(self.workqueue_id)

    @staticmethod
    def from_environment():
        """Create an AutomationServer configured from environment variables.

        This will call :py:meth:`AutomationServerConfig.init_from_environment`,
        register the module logging handler on the root logger and return a
        configured instance bound to the `ATS_SESSION` value (if any).
        """

        AutomationServerConfig.init_from_environment()

        root_logger = logging.getLogger()
        root_logger.addHandler(ats_logging_handler)

        return AutomationServer(AutomationServerConfig.session)

    def __str__(self):
        return f"AutomationServer(url={self.url}, session = {self.session}, process = {self.process}, workqueue_id={self.workqueue_id})"


class WorkItemError(Exception):
    """Generic error raised for work item related failures.

    Currently unused but kept for API compatibility with older versions of the
    library.
    """
