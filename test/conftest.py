# Copyright 2026 SURF, GÉANT.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Test fixtures: the shell tests run without a database."""

from collections.abc import Generator
from contextlib import contextmanager

import pytest
from orchestrator.core.db import SubscriptionInstanceTable

from orchestrator.shell import process, resource_type, subscripition
from test import factories


@contextmanager
def _no_transaction(*_args: object, **_kwargs: object) -> Generator[None]:
    """Stand-in for orchestrator-core's ``transactional``, which commits a real session."""
    yield


@pytest.fixture(autouse=True)
def without_database(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the transaction manager and the queries so commands do not need a database."""
    monkeypatch.setattr(resource_type, "transactional", _no_transaction)
    monkeypatch.setattr(subscripition, "transactional", _no_transaction)
    monkeypatch.setattr(process, "transactional", _no_transaction)
    monkeypatch.setattr(subscripition, "query_db", list)
    monkeypatch.setattr(process, "query_db", list)


@pytest.fixture
def node_product_block() -> SubscriptionInstanceTable:
    """Return a node product block with ``node_name`` set and ``node_description`` unset."""
    block = factories.product_block("Node", "node_name", "node_description")
    return factories.subscription_instance(block, "si-1", factories.value(block.resource_types[0], "amsterdam-1"))
