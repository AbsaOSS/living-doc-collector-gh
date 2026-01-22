#
# Copyright 2025 ABSA Group Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
This module contains a data container for Consolidated Issue, which holds all the essential logic.
"""

import logging
from typing import Optional, Any

from living_doc_utilities.factory.issue_factory import IssueFactory
from living_doc_utilities.model.issue import Issue
from living_doc_utilities.model.project_status import ProjectStatus

from github.Issue import Issue as GitHubIssue
from github.GithubException import GithubException

logger = logging.getLogger(__name__)


class ConsolidatedIssue:
    """
    A class representing a consolidated issue from the repository and project data.
    It provides methods for updating project data and generating page filenames and
    properties to access consolidated issue details.
    """

    def __init__(self, repository_id: str, repository_issue: Optional[GitHubIssue] = None):
        # save issue from repository (got from GitHub library & keep connection to repository for lazy loading)
        # Warning: several issue properties require additional API calls - use wisely to keep low API usage
        self.__issue: Optional[GitHubIssue] = repository_issue
        self.__repository_id: str = repository_id

        self.issue_type: str = "Issue"

        # Extra project data (optionally provided from the GithubProjects class)
        self.__linked_to_project: bool = False
        self.__project_issue_statuses: list[ProjectStatus] = []

        # Labels of the issue - saved during mining to reduce API calls and protect against rate limits
        self.__issue_labels: list[str] = []

        self.__errors: dict[str, str] = {}

        # Audit-related data (cached to reduce API calls)
        self.__audit_data_fetched: bool = False
        self.__created_by: Optional[str] = None
        self.__closed_by: Optional[str] = None
        self.__comments_count: int = 0
        self.__last_commented_at: Optional[str] = None
        self.__last_commented_by: Optional[str] = None
        self.__audit_events: list[dict[str, Any]] = []

    # Issue properties
    @property
    def number(self) -> int:
        """Getter of the issue number."""
        return self.__issue.number if self.__issue else 0

    @property
    def repository_id(self) -> str:
        """Getter of the repository id."""
        return self.__repository_id

    @property
    def organization_name(self) -> str:
        """Getter of the organization where the issue was fetched from."""
        parts = self.__repository_id.split("/")
        return parts[0] if len(parts) == 2 else ""

    @property
    def repository_name(self) -> str:
        """Getter of the repository name where the issue was fetched from."""
        parts = self.__repository_id.split("/")
        return parts[1] if len(parts) == 2 else ""

    @property
    def title(self) -> str:
        """Getter of the issue title."""
        return self.__issue.title if self.__issue else ""

    @property
    def state(self) -> str:
        """Getter of the issue state."""
        return self.__issue.state if self.__issue else ""

    @property
    def created_at(self) -> str:
        """Getter of the info when issue was created."""
        return str(self.__issue.created_at) if self.__issue else ""

    @property
    def updated_at(self) -> str:
        """Getter of the info when issue was updated"""
        return str(self.__issue.updated_at) if self.__issue else ""

    @property
    def closed_at(self) -> str:
        """Getter of the info when issue was closed."""
        return str(self.__issue.closed_at) if self.__issue else ""

    @property
    def html_url(self) -> str:
        """Getter of the issue GitHub HTML URL."""
        return self.__issue.html_url if self.__issue else ""

    @property
    def body(self) -> str:
        """Getter of the issue description."""
        return self.__issue.body if self.__issue else ""

    @property
    def labels(self) -> list[str]:
        """Getter of the issue labels."""
        if self.__issue_labels:
            return self.__issue_labels

        if self.__issue:
            self.__issue_labels = [label.name for label in self.__issue.labels]
        return self.__issue_labels

    # Project properties
    @property
    def linked_to_project(self) -> bool:
        """Getter of the info if the issue is linked to a project."""
        return self.__linked_to_project

    @property
    def project_issue_statuses(self) -> list[ProjectStatus]:
        """Getter of the project issue statuses."""
        return self.__project_issue_statuses

    @property
    def errors(self) -> dict[str, str]:
        """Getter of the errors that occurred during the issue processing."""
        return self.__errors

    # Audit properties
    @property
    def created_by(self) -> Optional[str]:
        """Getter of the user who created the issue."""
        self._ensure_audit_data_fetched()
        return self.__created_by

    @property
    def closed_by(self) -> Optional[str]:
        """Getter of the user who closed the issue."""
        self._ensure_audit_data_fetched()
        return self.__closed_by

    @property
    def comments_count(self) -> int:
        """Getter of the number of comments on the issue."""
        self._ensure_audit_data_fetched()
        return self.__comments_count

    @property
    def last_commented_at(self) -> Optional[str]:
        """Getter of the timestamp of the last comment."""
        self._ensure_audit_data_fetched()
        return self.__last_commented_at

    @property
    def last_commented_by(self) -> Optional[str]:
        """Getter of the user who last commented on the issue."""
        self._ensure_audit_data_fetched()
        return self.__last_commented_by

    @property
    def audit_events(self) -> list[dict[str, Any]]:
        """Getter of audit events (label, assignment, milestone changes)."""
        self._ensure_audit_data_fetched()
        return self.__audit_events

    def _ensure_audit_data_fetched(self) -> None:
        """
        Ensure audit data is fetched from the GitHub API (lazy loading).
        This method fetches data only once and caches it.
        """
        if self.__audit_data_fetched or not self.__issue:
            return

        self.__audit_data_fetched = True

        try:
            # Fetch creator
            if self.__issue.user:
                self.__created_by = self.__issue.user.login

            # Fetch closed_by
            if self.__issue.closed_by:
                self.__closed_by = self.__issue.closed_by.login

            # Fetch comments info
            self.__comments_count = self.__issue.comments

            # Fetch last comment info
            if self.__comments_count > 0:
                try:
                    comments = list(self.__issue.get_comments())
                    if comments:
                        last_comment = comments[-1]
                        self.__last_commented_at = str(last_comment.created_at) if last_comment.created_at else None
                        self.__last_commented_by = last_comment.user.login if last_comment.user else None
                except (GithubException, AttributeError, TypeError) as e:
                    logger.debug(
                        "Could not fetch comments for issue #%s: %s",
                        self.number,
                        str(e),
                    )

            # Fetch timeline events for audit trail
            self.__audit_events = self._fetch_audit_events()

        except (GithubException, AttributeError, TypeError) as e:
            logger.warning(
                "Could not fetch complete audit data for issue #%s: %s",
                self.number,
                str(e),
            )

    def _fetch_audit_events(self) -> list[dict[str, Any]]:
        """
        Fetch audit events from the issue timeline (label changes, assignments, milestones).

        @return: List of audit event dictionaries.
        """
        events: list[dict[str, Any]] = []
        if not self.__issue:
            return events

        try:
            timeline = self.__issue.get_timeline()
            for event in timeline:
                event_data = self._parse_timeline_event(event)
                if event_data:
                    events.append(event_data)
        except (GithubException, AttributeError, TypeError) as e:
            logger.debug(
                "Could not fetch timeline events for issue #%s (may lack permissions): %s",
                self.number,
                str(e),
            )

        return events

    def _parse_timeline_event(self, event: Any) -> Optional[dict[str, Any]]:
        """
        Parse a timeline event into a structured audit event.

        @param event: The timeline event from GitHub API.
        @return: Parsed event dictionary or None if not relevant.
        """
        try:
            event_type = event.event if hasattr(event, "event") else None
            if not event_type:
                return None

            # Filter for audit-relevant events
            relevant_events = {
                "labeled",
                "unlabeled",
                "assigned",
                "unassigned",
                "milestoned",
                "demilestoned",
                "reopened",
                "closed",
            }

            if event_type not in relevant_events:
                return None

            event_data: dict[str, Any] = {
                "action": event_type,
                "timestamp": str(event.created_at) if hasattr(event, "created_at") else None,
            }

            # Add actor info
            if hasattr(event, "actor") and event.actor:
                event_data["actor"] = event.actor.login

            # Add event-specific details
            if event_type in ("labeled", "unlabeled") and hasattr(event, "label"):
                event_data["label"] = event.label.name if event.label else None
            elif event_type in ("assigned", "unassigned") and hasattr(event, "assignee"):
                event_data["assignee"] = event.assignee.login if event.assignee else None
            elif event_type in ("milestoned", "demilestoned") and hasattr(event, "milestone"):
                event_data["milestone"] = event.milestone.title if event.milestone else None

            return event_data

        except (AttributeError, TypeError) as e:
            logger.debug("Could not parse timeline event: %s", str(e))
            return None

    def update_with_project_data(self, project_issue_status: ProjectStatus) -> None:
        """
        Update the consolidated issue with Project Status data.

        @param project_issue_status: The extra issue project data per project.
        @return: None
        """
        self.__linked_to_project = True
        self.__project_issue_statuses.append(project_issue_status)

    def get_audit_data(self) -> dict[str, Any]:
        """
        Get audit-related data as a dictionary for persistence.

        @return: Dictionary containing audit fields.
        """
        audit_data: dict[str, Any] = {}

        # Add creator info
        if self.created_by:
            audit_data["created_by"] = self.created_by

        # Add closer info
        if self.closed_by:
            audit_data["closed_by"] = self.closed_by

        # Add comments summary
        if self.comments_count > 0:
            audit_data["comments_count"] = self.comments_count
        if self.last_commented_at:
            audit_data["last_commented_at"] = self.last_commented_at
        if self.last_commented_by:
            audit_data["last_commented_by"] = self.last_commented_by

        # Add audit events
        if self.audit_events:
            audit_data["audit_events"] = self.audit_events

        return audit_data

    def convert_to_issue_for_persist(self) -> Issue:
        """
        Convert the consolidated issue to a standard Issue object for persistence.

        @return: The converted Issue.
        """
        values: dict[str, Any] = {
            Issue.REPOSITORY_ID: self.repository_id,
            Issue.TITLE: self.title,
            Issue.ISSUE_NUMBER: self.number,
        }

        issue = IssueFactory.get(self.issue_type, values)
        issue.state = self.state
        issue.created_at = self.created_at
        issue.updated_at = self.updated_at
        issue.closed_at = self.closed_at
        issue.html_url = self.html_url
        issue.body = self.body
        issue.labels = self.labels

        issue.linked_to_project = self.linked_to_project
        issue.project_statuses = self.project_issue_statuses

        issue.add_errors(errors=self.errors)

        return issue
