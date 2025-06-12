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
This module contains all constants and enums used across the project.
"""
from enum import Enum

VERBOSE_LOGGING = "VERBOSE_LOGGING"

# doc-issues mode Action inputs
DOC_ISSUES_PROJECT_STATE_MINING = "DOC_ISSUES_PROJECT_STATE_MINING"
DOC_ISSUES_REPOSITORIES = "DOC_ISSUES_REPOSITORIES"

# Supported issue labels
DOC_USER_STORY_LABEL = "DocumentedUserStory"
DOC_FEATURE_LABEL = "DocumentedFeature"
DOC_FUNCTIONALITY_LABEL = "DocumentedFunctionality"
SUPPORTED_ISSUE_LABELS = [DOC_USER_STORY_LABEL, DOC_FEATURE_LABEL, DOC_FUNCTIONALITY_LABEL]


# Collector regimes
class Mode(Enum):
    DOC_ISSUES = "DOC_ISSUES"


# Regime output paths
DOC_ISSUES_OUTPUT_PATH = "./output/doc-issues"


# GitHub API constants
ISSUES_PER_PAGE_LIMIT = 100
ISSUE_STATE_ALL = "all"
PROJECTS_FROM_REPO_QUERY = """
                query {{
                  repository(owner: "{organization_name}", name: "{repository_name}") {{
                    projectsV2(first: 100) {{
                      nodes {{
                        id
                        number
                        title
                      }}
                    }}
                  }}
                }}
                """
ISSUES_FROM_PROJECT_QUERY = """
                query {{
                  node(id: "{project_id}") {{
                    ... on ProjectV2 {{
                      items(first: {issues_per_page}, {after_argument}) {{
                        pageInfo {{
                          endCursor
                          hasNextPage
                        }}
                        nodes {{
                          content {{
                              ... on Issue {{
                                title
                                state
                                number
                                repository {{
                                  name
                                  owner {{
                                    login
                                  }}
                                }}
                              }}
                            }}
                          fieldValues(first: 100) {{
                            nodes {{
                              __typename
                              ... on ProjectV2ItemFieldSingleSelectValue {{
                                name
                              }}
                            }}
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
                """
PROJECT_FIELD_OPTIONS_QUERY = """
                query {{
                  repository(owner: "{organization_name}", name: "{repository_name}") {{
                    projectV2(number: {project_number}) {{
                      title
                      fields(first: 100) {{
                        nodes {{
                          ... on ProjectV2SingleSelectField {{
                            name
                            options {{
                              name
                            }}
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
                """
