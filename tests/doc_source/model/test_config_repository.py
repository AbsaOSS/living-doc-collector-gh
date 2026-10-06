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

from doc_source.model.config_repository import ConfigRepository


def test_load_from_json_with_us_paths_key_loads_correctly():
    # Arrange
    config_repository = ConfigRepository()
    repository_json = {
        "organization-name": "absa-group",
        "repository-name": "aul-ui",
        "us-paths": ["/path/to/checkout/aul-ui/playwright/features/liv_doc_us"],
        "func-paths": ["/path/to/checkout/aul-ui/playwright/features/liv_doc_func"],
        "pages-paths": ["/path/to/checkout/aul-ui/playwright/pages"],
    }

    # Act
    actual = config_repository.load_from_json(repository_json)

    # Assert
    assert actual is None
    assert config_repository.organization_name == "absa-group"
    assert config_repository.repository_name == "aul-ui"
    assert config_repository.paths == ["/path/to/checkout/aul-ui/playwright/features/liv_doc_us"]
    assert config_repository.func_paths == ["/path/to/checkout/aul-ui/playwright/features/liv_doc_func"]
    assert config_repository.pages_paths == ["/path/to/checkout/aul-ui/playwright/pages"]
    assert "aul-ui" in repr(config_repository)


def test_load_from_json_with_legacy_paths_key_loads_correctly():
    """'paths' is accepted as a backward-compatible alias for 'us-paths'."""
    # Arrange
    config_repository = ConfigRepository()
    repository_json = {
        "organization-name": "absa-group",
        "repository-name": "aul-ui",
        "paths": ["/path/to/checkout/aul-ui/playwright/features/**/*.feature"],
    }

    # Act
    config_repository.load_from_json(repository_json)

    # Assert
    assert config_repository.paths == ["/path/to/checkout/aul-ui/playwright/features/**/*.feature"]
    assert config_repository.func_paths == []
    assert config_repository.pages_paths == []


def test_load_from_json_prefers_us_paths_over_legacy_paths():
    # Arrange
    config_repository = ConfigRepository()
    repository_json = {
        "organization-name": "absa-group",
        "repository-name": "aul-ui",
        "us-paths": ["/canonical"],
        "paths": ["/legacy"],
    }

    # Act
    config_repository.load_from_json(repository_json)

    # Assert
    assert config_repository.paths == ["/canonical"]


def test_load_from_json_optional_paths_default_to_empty():
    # Arrange
    config_repository = ConfigRepository()
    repository_json = {
        "organization-name": "absa-group",
        "repository-name": "aul-ui",
        "us-paths": ["/path/to/us"],
    }

    # Act
    config_repository.load_from_json(repository_json)

    # Assert
    assert config_repository.paths == ["/path/to/us"]
    assert config_repository.func_paths == []
    assert config_repository.pages_paths == []


@pytest.mark.parametrize(
    "repository_json, reason",
    [
        ({"organization-name": "absa-group"}, "missing key `repository-name`"),
        ({"repository-name": "aul-ui"}, "missing key `organization-name`"),
        ({"organization-name": "absa-group", "repository-name": "aul-ui"}, "missing key `us-paths`"),
    ],
    ids=["no-repository-name", "no-organization-name", "no-us-paths-nor-paths"],
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
        ConfigRepository().load_from_json({**names, "us-paths": []})


def test_load_from_json_names_the_empty_repository_name():
    # Act & Assert
    with pytest.raises(ValueError) as error:
        ConfigRepository().load_from_json({"organization-name": "absa-group", "repository-name": "", "us-paths": []})
    assert str(error.value) == "`repository-name` must be a non-empty string with no `/`, got ''"


@pytest.mark.parametrize(
    "key, value",
    [
        ("us-paths", "/a/single/string"),
        ("us-paths", ["/ok", 7]),
        ("func-paths", None),
        ("pages-paths", {"path": "/x"}),
    ],
    ids=["us-paths-string", "us-paths-non-string-item", "func-paths-null", "pages-paths-object"],
)
def test_load_from_json_with_a_path_list_that_is_not_a_list_of_strings_raises_value_error(key, value):
    # Arrange
    repository_json = {"organization-name": "absa-group", "repository-name": "aul-ui", "us-paths": ["/us"], key: value}

    # Act & Assert
    with pytest.raises(ValueError) as error:
        ConfigRepository().load_from_json(repository_json)
    assert str(error.value) == f"`{key}` must be a list of path strings, got {value!r}"
