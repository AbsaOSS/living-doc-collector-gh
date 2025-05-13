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
This module contains the main script for the Living Documentation Generator GH Action.
It sets up logging, loads action inputs, generates the documentation, and sets the output
for the GH Action.
"""

import logging
import sys

from action_inputs import ActionInputs
from doc_issues.collector import GHDocIssuesCollector
from living_doc_utilities.logging_config import setup_logging
from utils.constants import OUTPUT_PATH
from utils.github_project_queries import validate_query_formats
from utils.utils import set_action_output, make_absolute_path


def run() -> None:
    """
    The main function is to run the Living Documentation (Liv-Doc) Collector for GitHub.

    @return: None
    """
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Liv-Doc collector for GitHub - starting.")

    if not ActionInputs().validate_user_configuration():
        logger.info("Liv-Doc collector for GitHub - user configuration validation failed.")
        sys.exit(1)

    if not validate_query_formats():
        logger.info("Liv-Doc collector for GitHub - query format validation failed.")
        sys.exit(1)

    output_path: str = make_absolute_path(OUTPUT_PATH)
    all_modes_success: bool = True

    if ActionInputs.is_doc_issues_mode_enabled():
        logger.info("Liv-Doc collector for GitHub - Starting the `doc-issues` mode.")

        # Generate the Living documentation
        if GHDocIssuesCollector(output_path).collect():
            logger.info("Liv-Doc collector for GitHub - `doc-issues` mode completed successfully.")
        else:
            logger.info("Liv-Doc collector for GitHub - `doc-issues` mode failed.")
            all_modes_success = False
    else:
        logger.info("Liv-Doc collector for GitHub - `doc-issues` mode disabled.")

    # Set the output for the GitHub Action
    set_action_output("output-path", output_path)
    logger.info("Liv-Doc collector for GitHub - root output path set to `%s`.", output_path)

    logger.info("Liv-Doc collector for GitHub - ending.")

    if not all_modes_success:
        sys.exit(1)


if __name__ == "__main__":
    run()
