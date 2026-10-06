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
import re

import pytest

from ui_tests.model.config_repository import ConfigRepository


def test_load_from_json_with_valid_input_loads_correctly():
    # Arrange
    config_repository = ConfigRepository()
    repository_json = {
        "organization-name": "absa-group",
        "repository-name": "aul-ui",
        "paths": ["/path/to/checkout/aul-ui/playwright/features/**/*.feature"],
    }

    # Act
    actual = config_repository.load_from_json(repository_json)

    # Assert
    assert actual is None
    assert config_repository.organization_name == "absa-group"
    assert config_repository.repository_name == "aul-ui"
    assert config_repository.paths == ["/path/to/checkout/aul-ui/playwright/features/**/*.feature"]
    assert "aul-ui" in repr(config_repository)


@pytest.mark.parametrize(
    "repository_json, reason",
    [
        ({"organization-name": "absa-group"}, "missing key `repository-name`"),
        ({"repository-name": "aul-ui", "paths": []}, "missing key `organization-name`"),
        ({"organization-name": "absa-group", "repository-name": "aul-ui"}, "missing key `paths`"),
    ],
    ids=["no-repository-name", "no-organization-name", "no-paths"],
)
def test_load_from_json_with_a_missing_key_raises_value_error(repository_json, reason):
    # Act & Assert
    with pytest.raises(ValueError, match=f"^{re.escape(reason)}$"):
        ConfigRepository().load_from_json(repository_json)


def test_load_from_json_with_wrong_structure_input_raises_value_error():
    # Act & Assert
    with pytest.raises(ValueError, match=r"^the entry must be a JSON object, got 'not a dictionary'$"):
        ConfigRepository().load_from_json("not a dictionary")


@pytest.mark.parametrize(
    "names, reason",
    [
        ({"organization-name": 123, "repository-name": "aul-ui"}, "`organization-name` must be a non-empty"),
        ({"organization-name": "absa-group", "repository-name": ""}, "`repository-name` must be a non-empty"),
        ({"organization-name": "absa-group", "repository-name": None}, "`repository-name` must be a non-empty"),
        ({"organization-name": "absa/group", "repository-name": "aul-ui"}, "`organization-name` must be a non-empty"),
    ],
    ids=["int-organization", "empty-repository", "null-repository", "slash-in-organization"],
)
def test_load_from_json_with_a_name_that_is_not_a_non_empty_string_raises_value_error(names, reason):
    # Act & Assert
    with pytest.raises(ValueError, match=f"^{re.escape(reason)}"):
        ConfigRepository().load_from_json({**names, "paths": []})


@pytest.mark.parametrize("paths", ["/a/single/string", ["/ok", 7], None], ids=["string", "non-string-item", "null"])
def test_load_from_json_with_paths_that_is_not_a_list_of_strings_raises_value_error(paths):
    # Arrange
    repository_json = {"organization-name": "absa-group", "repository-name": "aul-ui", "paths": paths}

    # Act & Assert
    with pytest.raises(ValueError) as error:
        ConfigRepository().load_from_json(repository_json)
    assert str(error.value) == f"`paths` must be a list of path strings, got {paths!r}"
