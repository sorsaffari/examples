#
# GRAKN.AI - THE KNOWLEDGE GRAPH
# Copyright (C) 2018 Grakn Labs Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

load("@bazel_tools//tools/build_defs/repo:git.bzl", "git_repository")

def graknlabs_grakn_core():
    git_repository(
        name = "graknlabs_grakn_core",
        remote = "https://github.com/graknlabs/grakn",
        commit = '9a84058f83e5ccdf910073ba966ca729f824ee6b' # sync-marker: do not remove this comment, this is used for sync-dependencies by @graknlabs_grakn_core
    )

def graknlabs_client_java():
     git_repository(
         name = "graknlabs_client_java",
         remote = "https://github.com/graknlabs/client-java",
         commit = '63aeec66bc19f8f1c4b6a278f0d90351aae4bafb' # sync-marker: do not remove this comment, this is used for sync-dependencies by @graknlabs_client_java
     )

def graknlabs_client_python():
     git_repository(
         name = "graknlabs_client_python",
         remote = "https://github.com/graknlabs/client-python",
         commit = '1a56d28e00cf599c9e92b442cb67e74c6b0c4d99' # sync-marker: do not remove this comment, this is used for sync-dependencies by @graknlabs_client_python
     )

def graknlabs_build_tools():
     git_repository(
         name = "graknlabs_build_tools",
         remote = "https://github.com/graknlabs/build-tools",
         commit = "c2952ec155c182aecb228ea5c0f79f893092d876", # sync-marker: do not remove this comment, this is used for sync-dependencies by @graknlabs_build_tools
     )