import os
from automation_server_client import AutomationServerConfig

from pytest import fixture

@fixture(autouse=True)
def local_environment() -> None:
    
    os.environ["ATS_URL"] = "http://localhost:8000"

    AutomationServerConfig.init_from_environment()


