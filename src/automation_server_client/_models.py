import logging
import requests
import urllib.parse

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict

from ._config import AutomationServerConfig
from ._logging import ats_logging_handler


class Session(BaseModel):
    """Represents a session on the automation server.

    Fields mirror the server JSON for a session. Use
    :py:meth:`get_session` to fetch a session by id.
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    process_id: int
    resource_id: int
    dispatched_at: datetime
    status: str
    stop_requested: bool
    deleted: bool
    parameters: str
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def get_session(session_id):
        """Fetch a session from the automation server by id.

        Args:
            session_id: Numeric session identifier.

        Returns:
            Session: Parsed `Session` model.

        Raises:
            requests.HTTPError: If the request fails (non-2xx).
        """
        response = requests.get(
            f"{AutomationServerConfig.url}/sessions/{session_id}",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            timeout=10
        )
        response.raise_for_status()

        return Session.model_validate(response.json())


class Process(BaseModel):
    """Represents a process definition retrieved from the server.

    Use :py:meth:`get_process` to load a process by id.
    """
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    description: str
    requirements: str
    target_type: str
    target_source: str
    target_credentials_id: int | None = None
    credentials_id: int | None = None
    workqueue_id: int | None = None
    deleted: bool
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def get_process(process_id):
        """Fetch a process from the automation server by id.

        Args:
            process_id: Numeric process identifier.

        Returns:
            Process: Parsed `Process` model.

        Raises:
            requests.HTTPError: If the request fails (non-2xx).
        """
        response = requests.get(
            f"{AutomationServerConfig.url}/processes/{process_id}",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            timeout=10
        )
        response.raise_for_status()

        return Process.model_validate(response.json())


class WorkItemStatus(str, Enum):
    """Enumeration of possible work item statuses used by the API."""
    NEW = "new"
    IN_PROGRESS = "in progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING_USER_ACTION = "pending user action"

class Workqueue(BaseModel):
    """Represents a workqueue and provides helpers to manipulate items.

    The class implements iterator protocol to fetch next items using the
    server `/workqueues/{id}/next_item` endpoint and includes convenience
    methods like `add_item`, `clear_workqueue` and `get_item_by_reference`.
    """

    model_config = ConfigDict(extra="ignore")
    id: int
    name: str
    description: str
    enabled: bool
    deleted: bool
    created_at: datetime
    updated_at: datetime

    def add_item(self, data: dict, reference: str):
        """Add a new work item to this workqueue.

        Args:
            data: The payload for the work item (will be stored as JSON).
            reference: Human-readable reference used to identify the item.

        Returns:
            WorkItem: The created work item returned by the server.
        """
        response = requests.post(
            f"{AutomationServerConfig.url}/workqueues/{self.id}/add",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            json={"data": data, "reference": reference},
            timeout=10
        )
        response.raise_for_status()

        return WorkItem.model_validate(response.json())

    @staticmethod
    def get_workqueue(workqueue_id):
        """Retrieve workqueue metadata by id.

        Args:
            workqueue_id: Numeric workqueue identifier.

        Returns:
            Workqueue: Parsed `Workqueue` model.
        """
        response = requests.get(
            f"{AutomationServerConfig.url}/workqueues/{workqueue_id}",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            timeout=10
        )
        response.raise_for_status()

        return Workqueue.model_validate(response.json())

    def clear_workqueue(
        self, workitem_status: WorkItemStatus = None, days_older_than=None
    ):
        """Clear items from the workqueue using the server-side clear endpoint.

        Args:
            workitem_status: Optional status filter for items to clear.
            days_older_than: Optional integer specifying age filter in days.
        """
        response = requests.post(
            f"{AutomationServerConfig.url}/workqueues/{self.id}/clear",
            json={
                "workitem_status": workitem_status,
                "days_older_than": days_older_than,
            },
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            timeout=10
        )
        response.raise_for_status()

    def get_item_by_reference(
        self, reference: str, status: WorkItemStatus = None
    ) -> list["WorkItem"]:
        """Retrieve work items from the workqueue by their reference identifier.

        This method queries the automation server to find all work items that match
        the specified reference string. The reference is typically used as a unique
        identifier or business key for work items, making this method useful for
        duplicate checking, status verification, or retrieving specific items.

        Args:
            reference (str): The reference identifier to search for. The reference
                will be URL-encoded automatically to handle special characters.
            status (WorkItemStatus, optional): If provided, filters results to only
                include items with the specified status. Defaults to None (no filtering).

        Returns:
            list[WorkItem]: A list of WorkItem objects that match the reference.
                Returns an empty list if no matching items are found.

        Raises:
            requests.HTTPError: If the API request fails (e.g., network error,
                authentication failure, or server error).

        Example:
            >>> workqueue = Workqueue.get_workqueue(123)
            >>> # Find all items with reference "INV-2023-001"
            >>> items = workqueue.get_item_by_reference("INV-2023-001")
            >>>
            >>> # Find only completed items with the reference
            >>> completed_items = workqueue.get_item_by_reference(
            ...     "INV-2023-001",
            ...     WorkItemStatus.COMPLETED
            ... )
            >>>
            >>> # Check for duplicates before adding a new item
            >>> existing = workqueue.get_item_by_reference("new-ref")
            >>> if not existing:
            ...     workqueue.add_item({"data": "value"}, "new-ref")
        """
        url = f"{AutomationServerConfig.url}/workqueues/{self.id}/by_reference/"
        url += f"{urllib.parse.quote(reference)}"
        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            params={"status": status} if status else None,
            timeout=10
        )
        response.raise_for_status()

        items = response.json()
        return [WorkItem(**item) for item in items]

    def __iter__(self):
        return self

    def __next__(self):
        """Iterator protocol: fetch the next available work item.

        When no items are available the server returns HTTP 204 and this
        method raises StopIteration.

        Returns:
            WorkItem: Next available work item.
        """

        ats_logging_handler.end_workitem()
        response = requests.get(
            f"{AutomationServerConfig.url}/workqueues/{self.id}/next_item",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            timeout=10
        )

        if response.status_code == 204:
            raise StopIteration

        response.raise_for_status()

        workitem = WorkItem.model_validate(response.json())

        ats_logging_handler.start_workitem(workitem.id)

        return workitem


class WorkItem(BaseModel):
    """Model for a work item returned by the automation server.

    Provides methods to update payload and status and implements a
    context-manager API so processing code can use `with work_item:` to
    automatically set log context and handle status transitions.
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    data: dict
    reference: str
    locked: bool
    status: str
    message: str
    workqueue_id: int
    created_at: datetime
    updated_at: datetime

    # def __init__(self, **data):
    #     """Initialize a WorkItem instance.

    #     The ``__init__`` simply forwards to Pydantic's initializer and exists to
    #     keep the explicit constructor from being removed if custom logic is
    #     later needed.
    #     """

    #     super().__init__(**data)

    def update(self, data: dict):
        """Update the work item's data on the server and locally.

        Args:
            data: New payload to store in the work item.
        """

        response = requests.put(
            f"{AutomationServerConfig.url}/workitems/{self.id}",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            json={"data": data, "reference": self.reference},
            timeout=10
        )
        response.raise_for_status()
        self.data = data

    def __enter__(self):
        """Enter work item processing context.

        The context manager signals the logging handler that this work item is
        active. Use as: ``with work_item:``
        """

        logger = logging.getLogger("ats")
        logger.debug("Processing %s", self)

        ats_logging_handler.start_workitem(self.id)

        return self

    def __exit__(self, exc_type, exc_value, _traceback):
        """Exit work item processing context.

        If an exception occurred the work item will be marked as failed; if the
        work item is still in progress it will be marked completed when the
        context exits without exception.
        """

        logger = logging.getLogger("ats")
        if exc_type:
            logger.error("An error occurred while processing %s: %s", self, exc_value)
            self.fail(str(exc_value))

        logger.debug("Finished processing %s", self)
        ats_logging_handler.end_workitem()

        # If we are working on an item that is in progress, we will mark it as completed
        if self.status == "in progress":
            self.complete("Completed")

    def __str__(self) -> str:
        """Human-readable representation used in logs and debugging."""

        return f"WorkItem(id={self.id}, reference={self.reference}, data={self.data})"

    def fail(self, message):
        """Mark the work item as failed with an optional message."""

        self.update_status("failed", message)

    def complete(self, message):
        """Mark the work item as completed with an optional message."""

        self.update_status("completed", message)

    def pending_user(self, message):
        """Set the work item status to pending user action with a message."""

        self.update_status("pending user action", message)

    def update_status(self, status, message: str = ""):
        """Send a status update for this work item to the server.

        Args:
            status: New status string.
            message: Optional message describing the status change.
        """

        response = requests.put(
            f"{AutomationServerConfig.url}/workitems/{self.id}/status",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            json={"status": status, "message": message},
            timeout=10
        )
        response.raise_for_status()
        self.status = status
        self.message = message


class Credential(BaseModel):
    """Represents a named credential stored on the automation server.

    Use :py:meth:`get_credential` to retrieve a credential by name.
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    data: dict
    username: str
    password: str
    deleted: bool
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def get_credential(credential: str) -> "Credential":
        """Retrieve a credential by its name (URL-encoded).

        Args:
            credential: Name of the credential to look up.

        Returns:
            Credential: Parsed `Credential` model.
        """

        response = requests.get(
            f"{AutomationServerConfig.url}/credentials/by_name/{urllib.parse.quote(credential)}",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            timeout=10
        )
        response.raise_for_status()

        return Credential.model_validate(response.json())


class Asset(BaseModel):
    """Represents an asset stored on the automation server.

    Use :py:meth:`get_asset` to retrieve an asset by name.
    """

    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    data: dict
    deleted: bool
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def get_asset(asset: str) -> "Asset":
        """Retrieve an asset by its name (URL-encoded).

        Args:
            asset: Name of the asset to look up.

        Returns:
            Asset: Parsed `Asset` model.
        """

        response = requests.get(
            f"{AutomationServerConfig.url}/assets/by_name/{urllib.parse.quote(asset)}",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            timeout=10
        )
        response.raise_for_status()

        return Asset.model_validate(response.json())
    
    
    @staticmethod
    def get_asset(asset: str) -> "Asset":
        """Retrieve an asset by its name (URL-encoded).

        Args:
            asset: Name of the asset to look up.
            environment: Name of the environment to filter by.

        Returns:
            Asset: Parsed `Asset` model.
        """
        response = requests.get(
            f"{AutomationServerConfig.url}/assets/by_name/{urllib.parse.quote(asset)}",
            headers={"Authorization": f"Bearer {AutomationServerConfig.token}"},
            timeout=10
        )
        response.raise_for_status()

        return Asset.model_validate(response.json())
