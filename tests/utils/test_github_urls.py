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
import pytest

from utils.github_urls import DEFAULT_SERVER_URL, blob_url, server_url

# server_url


def test_server_url_defaults_to_github_com():
    # Act & Assert
    assert server_url("") == DEFAULT_SERVER_URL == "https://github.com"


@pytest.mark.parametrize(
    "override, expected",
    [
        ("https://ghe.example", "https://ghe.example"),
        ("https://ghe.example/", "https://ghe.example"),
        ("http://ghe.example:8080/github/", "http://ghe.example:8080/github"),
        (" https://ghe.example/ \n", "https://ghe.example"),
    ],
    ids=["override", "trailing-slash", "http-port-and-prefix", "surrounding-whitespace"],
)
def test_server_url_returns_the_override_without_a_trailing_slash(override, expected):
    # Act & Assert
    assert server_url(override) == expected


@pytest.mark.parametrize("override", ["ghe.example", "ftp://ghe.example", "https://", "  "])
def test_server_url_rejects_a_value_that_is_not_an_http_url(override):
    # Act & Assert
    with pytest.raises(ValueError, match=r"must be an http\(s\) URL, got"):
        server_url(override)


# blob_url


def test_blob_url_is_the_permalink_at_the_commit():
    # Act & Assert
    assert blob_url("https://github.com", "org", "repo", "abc123", "features/a.feature") == (
        "https://github.com/org/repo/blob/abc123/features/a.feature"
    )


def test_blob_url_percent_encodes_the_path_but_keeps_its_slashes():
    # Act & Assert
    assert blob_url("https://ghe.example", "org", "repo", "abc123", "my features/a b.feature") == (
        "https://ghe.example/org/repo/blob/abc123/my%20features/a%20b.feature"
    )
