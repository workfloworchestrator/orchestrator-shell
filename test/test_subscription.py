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
"""Tests for listing, searching, selecting and updating subscriptions."""

import re
from datetime import datetime, timezone

import pytest
from orchestrator.core.db import SubscriptionInstanceTable, SubscriptionTable

from orchestrator.shell import subscripition
from orchestrator.shell.state import State
from test import factories


@pytest.fixture
def node_subscription(node_product_block: SubscriptionInstanceTable) -> SubscriptionTable:
    """Return a subscription with one node product block."""
    return factories.subscription("sub-1", "node amsterdam-1", node_product_block)


def test_indexed_subscription_list_shows_description_and_id(node_subscription: SubscriptionTable) -> None:
    """The list shows the description and the subscription id behind an index."""
    table = subscripition.indexed_subscription_list([node_subscription])

    assert table.startswith("0  node amsterdam-1")
    assert "sub-1" in table


def test_filter_is_case_insensitive_and_matches_substrings() -> None:
    """The search matches anywhere in the description, ignoring case."""
    subscriptions = [
        factories.subscription("1", "port 10G paris-1 ethernet-1/5"),
        factories.subscription("2", "node rome-1 (staged)"),
        factories.subscription("3", "core link 100G paris-1"),
    ]

    assert [s.subscription_id for s in subscripition.filtered_subscriptions("PARIS", subscriptions)] == ["1", "3"]
    assert [s.subscription_id for s in subscripition.filtered_subscriptions("^node", subscriptions)] == ["2"]


def test_filter_rejects_an_invalid_regular_expression() -> None:
    """A broken expression raises instead of silently returning everything."""
    with pytest.raises(re.error):
        subscripition.filtered_subscriptions("([", [])


def test_select_without_a_filter_uses_the_list_index(monkeypatch: pytest.MonkeyPatch) -> None:
    """Selecting on the plain list sets the index directly and clears the deeper selection."""
    subscriptions = [factories.subscription("1", "first"), factories.subscription("2", "second")]
    state = State(subscriptions=list(subscriptions), product_block_index=0, resource_type_index=0)
    monkeypatch.setattr(subscripition, "state", state)

    summary = subscripition.subscription_select(1)

    assert state.subscription_index == 1
    assert state.product_block_index is None
    assert state.resource_type_index is None
    assert "second" in summary


def test_select_with_a_filter_maps_back_to_the_full_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Selecting a search result selects that subscription in the unfiltered list."""
    subscriptions = [factories.subscription("1", "first"), factories.subscription("2", "second")]
    state = State(
        subscriptions=list(subscriptions),
        filtered_subscriptions=[subscriptions[1]],
    )
    monkeypatch.setattr(subscripition, "state", state)

    subscripition.subscription_select(0)

    assert state.subscription_index == 1


def test_details_report_the_subscription_fields(node_subscription: SubscriptionTable) -> None:
    """The subscription-only details contain every reported field."""
    rows = dict(subscripition.details_subscription_only(node_subscription))

    assert rows["description"] == "node amsterdam-1"
    assert rows["subscription_id"] == "sub-1"
    assert rows["status"] == "active"
    assert rows["insync"] is False


def test_details_product_blocks_only(monkeypatch: pytest.MonkeyPatch, node_subscription: SubscriptionTable) -> None:
    """The product-block details render the product blocks of the selected subscription."""
    state = State(subscriptions=[node_subscription], subscription_index=0)
    monkeypatch.setattr(subscripition, "state", state)

    rows = dict(subscripition.details_product_blocks_only())

    assert "Node" in rows["product block(s)"]


def test_details_product_blocks_only_of_a_subscription_without_product_blocks(
    monkeypatch: pytest.MonkeyPatch, node_subscription: SubscriptionTable
) -> None:
    """A subscription without product blocks shows an empty list instead of raising ValueError."""
    node_subscription.instances = []
    state = State(subscriptions=[node_subscription], subscription_index=0)
    monkeypatch.setattr(subscripition, "state", state)

    rows = dict(subscripition.details_product_blocks_only())

    assert rows["product block(s)"] == ""


def test_update_changes_the_selected_field(
    monkeypatch: pytest.MonkeyPatch, node_subscription: SubscriptionTable
) -> None:
    """Updating a field sets it on the selected subscription."""
    state = State(subscriptions=[node_subscription], subscription_index=0)
    monkeypatch.setattr(subscripition, "state", state)

    subscripition.subscription_update("note", "touched by hand")

    assert node_subscription.note == "touched by hand"


def test_update_accepts_a_date(monkeypatch: pytest.MonkeyPatch, node_subscription: SubscriptionTable) -> None:
    """Updating a date field stores the parsed value."""
    state = State(subscriptions=[node_subscription], subscription_index=0)
    monkeypatch.setattr(subscripition, "state", state)
    end_date = datetime(2025, 12, 31, tzinfo=timezone.utc)

    subscripition.subscription_update("end_date", end_date)

    assert node_subscription.end_date == end_date
