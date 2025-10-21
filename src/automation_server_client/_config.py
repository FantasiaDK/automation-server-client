import os
from dotenv import load_dotenv


class AutomationServerConfig:
    """Global configuration holder populated from environment variables.

    Attributes are class-level so they act as a simple singleton used across
    the library. Call :py:meth:`init_from_environment` during startup to load
    values from a `.env` file and the process environment.
    """
    token: str = ""
    url: str = ""
    session: str | None = None
    resource: str | None = None
    process: str | None = None

    workqueue_override: int | None = None

    @staticmethod
    def init_from_environment():
        """Load configuration from environment and `.env` file.

        Reads ATS_* environment variables and assigns class attributes. Raises
        ``ValueError`` when `ATS_URL` is not present, because the client
        cannot operate without a base URL.
        """
        load_dotenv()

        AutomationServerConfig.url = (
            os.environ["ATS_URL"] if "ATS_URL" in os.environ else ""
        )
        AutomationServerConfig.token = (
            os.environ["ATS_TOKEN"] if "ATS_TOKEN" in os.environ else ""
        )
        AutomationServerConfig.session = os.environ.get("ATS_SESSION")
        AutomationServerConfig.resource = os.environ.get("ATS_RESOURCE")
        AutomationServerConfig.process = os.environ.get("ATS_PROCESS")

        # Convert workqueue_override to int if present
        workqueue_override_str = os.environ.get("ATS_WORKQUEUE_OVERRIDE")
        AutomationServerConfig.workqueue_override = (
            int(workqueue_override_str) if workqueue_override_str else None
        )

        if AutomationServerConfig.url == "":
            raise ValueError("ATS_URL is not set in the environment")
