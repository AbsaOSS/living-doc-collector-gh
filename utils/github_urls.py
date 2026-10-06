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
This module is the only one that holds GitHub addresses: the server the configured repositories live on, and a
source file's commit permalink on it.
"""

from urllib.parse import quote, urlparse

DEFAULT_SERVER_URL = "https://github.com"


def server_url(override: str) -> str:
    """
    The GitHub server the configured repositories live on.

    @param override: The `github-server-url` input, e.g. a GitHub Enterprise Server URL; empty for the default.
    @return: The override without a trailing `/`, or `https://github.com` when it is empty.
    @raise ValueError: When the override is not an http(s) URL.
    """
    if not override:
        return DEFAULT_SERVER_URL
    parsed = urlparse(override)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"must be an http(s) URL, got {override!r}")
    return override.rstrip("/")


def blob_url(server: str, org: str, repo: str, sha: str, rel_path: str) -> str:
    """
    The permalink of a file at one commit.

    @param server: The GitHub server, as `server_url` returns it.
    @param org: The repository's organization.
    @param repo: The repository's name.
    @param sha: The commit the file is read at.
    @param rel_path: The file's `/`-separated path from the repository root.
    @return: `<server>/<org>/<repo>/blob/<sha>/<rel_path>`, the path percent-encoded.
    """
    return f"{server}/{org}/{repo}/blob/{sha}/{quote(rel_path)}"
