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
This module contains the Living Documentation Collector for GitHub class, which is responsible for collecting
of the Living Documentation related data from GitHub.
"""

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from typing import Callable

from github import Github, Auth
from github.Issue import Issue

from living_doc_utilities.decorators import safe_call_decorator
from living_doc_utilities.github.rate_limiter import GithubRateLimiter
from living_doc_utilities.model.feature_issue import FeatureIssue
from living_doc_utilities.model.functionality_issue import FunctionalityIssue
from living_doc_utilities.model.issues import Issues
from living_doc_utilities.model.user_story_issue import UserStoryIssue

from action_inputs import ActionInputs
from doc_issues.github_projects import GitHubProjects
from doc_issues.model.consolidated_issue import ConsolidatedIssue
from doc_issues.model.github_project import GitHubProject
from doc_issues.model.project_issue import ProjectIssue
from utils.constants import (
    ISSUES_PER_PAGE_LIMIT,
    ISSUE_STATE_ALL,
    SUPPORTED_ISSUE_LABELS,
    DOC_USER_STORY_LABEL,
    DOC_FEATURE_LABEL,
    DOC_FUNCTIONALITY_LABEL,
)

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class GHDocIssuesCollector:
    """
    A class representing the Living Documentation Collector for GitHub.
    The class uses several helper methods to fetch required data from GitHub, consolidate the data, and
    generate the output in JSON format.
    """

    def __init__(self, output_path: str):
        github_token = ActionInputs.get_github_token()

        self.__output_path = os.path.join(output_path, "doc-issues")
        self.__github_instance: Github = Github(
            auth=Auth.Token(token=github_token), per_page=ISSUES_PER_PAGE_LIMIT, verify=False
        )
        self.__github_projects_instance: GitHubProjects = GitHubProjects(token=github_token)
        self.__rate_limiter: GithubRateLimiter = GithubRateLimiter(self.__github_instance)
        self.__safe_call: Callable = safe_call_decorator(self.__rate_limiter)

    def collect(self) -> bool:
        """
        Collect 'doc-issues' GitHub data and export the output.

        @return: True if collection is successful, False otherwise (error occurred).
        """
        self._clean_output_directory()
        logger.debug("'doc-issues' mode output directory cleaned.")

        # Data mine GitHub issues with defined labels from all repositories
        logger.info("Fetching repository GitHub issues - started.")
        repository_issues: dict[str, list[Issue]] = self._fetch_github_issues()
        # Note: got a dict of the list of issues for each repository (key is repository id)
        logger.info("Fetching repository GitHub issues - finished.")

        # Data mine GitHub project's issues
        logger.info("Fetching GitHub project data - started.")
        project_issues: dict[str, list[ProjectIssue]] = self._fetch_github_project_issues()
        # Note: got dict of project issues with unique string key, defying the issue
        logger.info("Fetching GitHub project data - finished.")

        # Consolidate all issue data together
        logger.info("Issue and project data consolidation - started.")
        consolidated_issues: dict[str, ConsolidatedIssue] = self._consolidate_issues_data(
            repository_issues, project_issues
        )
        logger.info("Issue and project data consolidation - finished.")

        # persist the consolidated issues
        logger.info("Exporting consolidated issues - started.")
        without_error = self._store_consolidated_issues(consolidated_issues)
        logger.info("Exporting consolidated issues - finished.")

        if not without_error:
            return False

        return True

    def _clean_output_directory(self) -> None:
        """
        Clean the output directory from the previous run.

        @return: None
        """
        if os.path.exists(self.__output_path):
            shutil.rmtree(self.__output_path)
        os.makedirs(self.__output_path)

    def _fetch_github_issues(self) -> dict[str, list[Issue]]:
        """
        Fetch GitHub repository issues using the GitHub library. Only issues with correct labels are fetched.
        All repository issues are fetched if no labels are defined in the configuration.

        @return: A dictionary containing repository issue objects with a unique key.
        """
        issues: dict[str, list[Issue]] = {}
        total_issues_number = 0

        # Run the fetching logic for every config repository
        # Here is no need for catching an exception, because get_repositories
        # is static, and it was handled when validating user configuration.
        for config_repository in ActionInputs.get_repositories():
            repository_id = f"{config_repository.organization_name}/{config_repository.repository_name}"

            repository = self.__safe_call(self.__github_instance.get_repo)(repository_id)
            if repository is None:
                return {}

            logger.info("Fetching repository GitHub issues - from `%s`.", repository.full_name)

            issues[repository_id] = []
            for label in SUPPORTED_ISSUE_LABELS:
                logger.debug("Fetching issues with label `%s`.", label)
                issues[repository_id].extend(
                    self.__safe_call(repository.get_issues)(state=ISSUE_STATE_ALL, labels=[label])
                )
            amount_of_issues_per_repo = len(issues[repository_id])

            # Accumulate the count of issues
            total_issues_number += amount_of_issues_per_repo
            logger.info(
                "Fetching repository GitHub issues - fetched `%i` repository issues (%s).",
                amount_of_issues_per_repo,
                repository.full_name,
            )

        logger.info(
            "Fetching repository GitHub issues - loaded `%i` repository issues in total.",
            total_issues_number,
        )
        return issues

    def _fetch_github_project_issues(self) -> dict[str, list[ProjectIssue]]:
        """
        Fetch GitHub project issues using the GraphQL API.

        @return: A dictionary containing project issue objects with unique key.
        """
        if not ActionInputs.is_project_state_mining_enabled():
            logger.info("Fetching GitHub project data - project mining is not allowed.")
            return {}

        logger.debug("Project data mining allowed.")

        # Mine project issues for every repository
        all_project_issues: dict[str, list[ProjectIssue]] = {}

        # Here is no need for catching the exception, because get_repositories
        # is static, and it was handled when validating user configuration.
        for config_repository in ActionInputs.get_repositories():
            repository_id = f"{config_repository.organization_name}/{config_repository.repository_name}"
            projects_title_filter = config_repository.projects_title_filter
            logger.debug("Filtering projects: %s. If filter is empty, fetching all.", projects_title_filter)

            repository = self.__safe_call(self.__github_instance.get_repo)(repository_id)
            if repository is None:
                return {}

            # Fetch all projects_buffer attached to the repository
            logger.debug("Fetching GitHub project data - looking for repository `%s` projects.", repository_id)
            projects: list[GitHubProject] = self.__safe_call(self.__github_projects_instance.get_repository_projects)(
                repository=repository, projects_title_filter=projects_title_filter
            )

            if projects:
                logger.info(
                    "Fetching GitHub project data - for repository `%s` found `%i` project/s.",
                    repository.full_name,
                    len(projects),
                )
            else:
                logger.info(
                    "Fetching GitHub project data - no project data found for repository `%s`.", repository.full_name
                )

            # Update every project with project issue-related data
            for project in projects:
                logger.info("Fetching GitHub project data - fetching project data from `%s`.", project.title)
                project_issues: list[ProjectIssue] = self.__safe_call(
                    self.__github_projects_instance.get_project_issues
                )(project=project)

                for project_issue in project_issues:
                    key = Issues.make_issue_key(
                        project_issue.organization_name,
                        project_issue.repository_name,
                        project_issue.number,
                    )

                    # If the key is unique, add the project issue to the dictionary
                    if key not in all_project_issues:
                        all_project_issues[key] = [project_issue]
                    else:
                        # If the project issue key is already present, add another project data from other projects
                        all_project_issues[key].append(project_issue)
                logger.info(
                    "Fetching GitHub project data - successfully fetched project data from `%s`.", project.title
                )

        return all_project_issues

    @staticmethod
    def _consolidate_issues_data(
        repository_issues: dict[str, list[Issue]], project_issues: dict[str, list[ProjectIssue]]
    ) -> dict[str, ConsolidatedIssue]:
        """
        Consolidate the fetched issues and extra project data into a single consolidated object.

        @param repository_issues: A dictionary containing repository issue objects with a unique key.
        @param project_issues: A dictionary containing project issue objects with a unique key.
        @return: A dictionary containing all consolidated issues.
        """

        consolidated_issues = {}

        # Create a ConsolidatedIssue object for each repository issue
        for repository_id in repository_issues.keys():
            for repository_issue in repository_issues[repository_id]:
                repo_id_parts = repository_id.split("/")
                unique_key = Issues.make_issue_key(repo_id_parts[0], repo_id_parts[1], repository_issue.number)
                if unique_key not in consolidated_issues:
                    consolidated_issues[unique_key] = ConsolidatedIssue(
                        repository_id=repository_id, repository_issue=repository_issue
                    )

                    labels = consolidated_issues[unique_key].labels
                    issue_type = "Issue"

                    if DOC_USER_STORY_LABEL in labels:
                        issue_type = UserStoryIssue.__name__
                    elif DOC_FEATURE_LABEL in labels:
                        issue_type = FeatureIssue.__name__
                    elif DOC_FUNCTIONALITY_LABEL in labels:
                        issue_type = FunctionalityIssue.__name__

                    consolidated_issues[unique_key].issue_type = issue_type
                else:
                    logger.error(
                        "Issue with key `%s` already consolidated. Multiple Living-Doc labels `%s` might be used.",
                        unique_key,
                        repository_issue.labels,
                    )
                    consolidated_issues[unique_key].errors["multiple_labels"] = (
                        "Multiple Living-Doc labels found for the same issue. "
                        "Please use only one Living-Doc label per issue."
                    )

        # Update consolidated issue structures with project data
        logger.debug("Updating consolidated issue structure with project data.")
        for key, consolidated_issue in consolidated_issues.items():
            if key in project_issues:
                for project_issue in project_issues[key]:
                    consolidated_issue.update_with_project_data(project_issue.project_status)

        logger.info(
            "Issue and project data consolidation - consolidated `%i` repository issues with extra project data.",
            len(consolidated_issues),
        )
        return consolidated_issues

    def _store_consolidated_issues(self, consolidated_issues: dict[str, ConsolidatedIssue]) -> bool:
        """
        Store the consolidated issues in JSON format with audit enrichment.

        @param consolidated_issues: A dictionary containing all consolidated issues.
        @return: True if successful, False otherwise.
        """
        issues: Issues = Issues()
        invalid_issue_detected = False

        for key, item in consolidated_issues.items():
            issue = item.convert_to_issue_for_persist()

            if not issue.is_valid_issue():
                logger.error(
                    "Issue with key `%s` is not valid (Repository ID, title and issue_number have to be defined)."
                    " Skipping issue.",
                    key,
                )
                invalid_issue_detected = True
                continue

            issues.add_issue(
                key=key,
                issue=issue,
            )

        output_file_path = os.path.join(self.__output_path, "doc-issues.json")
        logger.info("Exporting consolidated issues - exporting to `%s`.", output_file_path)

        # Save with audit enrichment
        self._save_issues_with_audit_data(output_file_path, issues, consolidated_issues)

        if any(len(issue.errors) > 0 for issue in issues.issues.values()) or invalid_issue_detected:
            logger.error("Exporting consolidated issues - some issues have errors.")
            return False

        return True

    def _save_issues_with_audit_data(
        self,
        file_path: str,
        issues: Issues,
        consolidated_issues: dict[str, ConsolidatedIssue],
    ) -> None:
        """
        Save issues to JSON with audit enrichment and file-level metadata.

        @param file_path: Path to save the JSON file.
        @param issues: Issues object containing base issue data.
        @param consolidated_issues: Consolidated issues with audit data.
        @return: None
        """
        # Build issue data with audit enrichment
        issues_data = {}
        for key, issue in issues.issues.items():
            issue_dict = issue.to_dict()

            # Add audit data from consolidated issue
            if key in consolidated_issues:
                audit_data = consolidated_issues[key].get_audit_data()
                issue_dict.update(audit_data)

            issues_data[key] = issue_dict

        # Wrap with file-level metadata
        output_data = {
            "metadata": self._get_file_metadata(),
            "issues": issues_data,
        }

        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)

    def _get_file_metadata(self) -> dict:
        """
        Generate file-level metadata (provenance, run info).

        @return: Dictionary containing file metadata.
        """
        metadata = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": "1.0",
            "generator": {
                "name": "AbsaOSS/living-doc-collector-gh",
                "version": self._get_action_version(),
            },
        }

        # Add source info
        source_info = {}
        repositories = ActionInputs.get_repositories()
        if repositories:
            # Use the first repository as the primary source for metadata
            source_info["repositories"] = [f"{repo.organization_name}/{repo.repository_name}" for repo in repositories]
        metadata["source"] = source_info

        # Add run info (from GitHub Actions environment)
        run_info = {}
        github_env_vars = {
            "workflow": os.getenv("GITHUB_WORKFLOW"),
            "run_id": os.getenv("GITHUB_RUN_ID"),
            "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
            "actor": os.getenv("GITHUB_ACTOR"),
            "ref": os.getenv("GITHUB_REF"),
            "sha": os.getenv("GITHUB_SHA"),
        }

        # Only add non-None values
        for key, value in github_env_vars.items():
            if value:
                run_info[key] = value

        if run_info:
            metadata["run"] = run_info

        # Add non-sensitive inputs
        inputs_info = {
            "project_state_mining_enabled": ActionInputs.is_project_state_mining_enabled(),
        }
        metadata["inputs"] = inputs_info

        return metadata

    @staticmethod
    def _get_action_version() -> str:
        """
        Get the action version from environment or package.

        @return: Version string.
        """
        # Try to get from GitHub Actions ref (e.g., refs/tags/v1.0.0)
        github_ref = os.getenv("GITHUB_ACTION_REF", "")
        if github_ref:
            return github_ref

        # Try to get from SHA
        github_sha = os.getenv("GITHUB_SHA", "")
        if github_sha:
            return github_sha[:7]  # Short SHA

        return "unknown"
