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
"""Tests for the state that the shell commands share."""

from datetime import datetime

import pytest

from orchestrator.shell.state import (
    State,
    all_resource_types,
    sorted_processes,
    sorted_product_blocks,
    sorted_resource_types,
    sorted_subscriptions,
)
from test import factories


def test_selected_subscription_requires_an_index() -> None:
    """Reading the selected subscription without a selection is an error, not a silent first item."""
    with pytest.raises(IndexError, match="subscription_index not set"):
        _ = State().selected_subscription


def test_selected_product_block_requires_an_index() -> None:
    """Reading the selected product block without a selection is an error."""
    with pytest.raises(IndexError, match="product_block_index not set"):
        _ = State().selected_product_block


def test_selected_resource_type_requires_an_index() -> None:
    """Reading the selected resource type without a selection is an error."""
    with pytest.raises(IndexError, match="resource_type_index not set"):
        _ = State().selected_resource_type


def test_empty_state_has_no_summary_lines() -> None:
    """An empty state prints an empty table instead of raising."""
    assert State().summary == ""
    assert "number of subscriptions" in State().details


def test_all_resource_types_adds_unset_optional_resource_types() -> None:
    """Defined resource types without a value are listed as ``None`` before the set ones."""
    block = factories.product_block("Node", "node_name", "node_status", "node_description")
    instance = factories.subscription_instance(
        block,
        "si-1",
        factories.value(block.resource_types[0], "amsterdam-1"),
        factories.value(block.resource_types[1], "active"),
    )

    result = all_resource_types(instance)

    by_name = {rt.resource_type.resource_type: rt for rt in result}
    assert set(by_name) == {"node_name", "node_status", "node_description"}
    assert by_name["node_name"].value == "amsterdam-1"
    assert by_name["node_status"].value == "active"
    assert by_name["node_description"].value is None
    assert by_name["node_description"].subscription_instance_value_id is None


def test_all_resource_types_prefers_the_set_value() -> None:
    """A resource type that has a value is not duplicated in the unset form."""
    block = factories.product_block("Node", "node_name")
    instance = factories.subscription_instance(block, "si-1", factories.value(block.resource_types[0], "rome-1"))

    result = all_resource_types(instance)

    assert len(result) == 1
    assert result[0].value == "rome-1"


def test_sorted_subscriptions_orders_by_start_date() -> None:
    """Subscriptions without a start date come first; the rest are ordered by their start date."""
    early = factories.subscription("early", "early", start_date=datetime(2024, 1, 1))
    late = factories.subscription("late", "late", start_date=datetime(2025, 1, 1))
    undated = factories.subscription("undated", "undated")

    assert [s.subscription_id for s in sorted_subscriptions([late, early])] == ["early", "late"]
    assert [s.subscription_id for s in sorted_subscriptions([undated])] == ["undated"]


def test_sorted_subscriptions_put_undated_subscriptions_first() -> None:
    """Pins the current behaviour, which contradicts the docstring: ``str(None)`` sorts before any date.

    Changing it to sort undated subscriptions last changes what the shell lists first, so it needs a
    deliberate decision; see the rollout report.
    """
    dated = factories.subscription("dated", "dated", start_date=datetime(2024, 1, 1))
    undated = factories.subscription("undated", "undated")

    assert [s.subscription_id for s in sorted_subscriptions([dated, undated])] == ["undated", "dated"]


def test_sorted_product_blocks_orders_by_name() -> None:
    """Product blocks are listed alphabetically by product block name."""
    node = factories.subscription_instance(factories.product_block("Node"), "node")
    port = factories.subscription_instance(factories.product_block("Port"), "port")

    assert [i.product_block.name for i in sorted_product_blocks([port, node])] == ["Node", "Port"]


def test_sorted_resource_types_orders_by_name() -> None:
    """Resource types are listed alphabetically by resource type name."""
    block = factories.product_block("Node", "site_id", "ims_id", "node_name")
    values = [factories.value(rt, "1") for rt in block.resource_types]

    assert [v.resource_type.resource_type for v in sorted_resource_types(values)] == ["ims_id", "node_name", "site_id"]


def test_sorted_processes_orders_by_started_at() -> None:
    """Processes are ordered by their start timestamp."""
    first = factories.process("first", "create_node", datetime(2024, 1, 1))
    second = factories.process("second", "create_node", datetime(2024, 2, 1))

    assert [p.process_id for p in sorted_processes([second, first])] == ["first", "second"]


def test_summary_follows_the_selection_chain() -> None:
    """The summary names the selected subscription, product block and resource type."""
    block = factories.product_block("Node", "node_name")
    instance = factories.subscription_instance(block, "si-1", factories.value(block.resource_types[0], "amsterdam-1"))
    state = State(
        subscriptions=[factories.subscription("sub-1", "node amsterdam-1", instance)],
        subscription_index=0,
        product_block_index=0,
        resource_type_index=0,
    )

    summary = state.summary

    assert "subscription" in summary
    assert "node amsterdam-1" in summary
    assert "product block" in summary
    assert "resource_type" in summary
    assert "amsterdam-1" in summary


def test_summary_marks_an_unset_resource_type() -> None:
    """An unset resource type is shown as such instead of by its (missing) value id."""
    block = factories.product_block("Node", "node_name")
    instance = factories.subscription_instance(block, "si-1")
    state = State(
        subscriptions=[factories.subscription("sub-1", "node", instance)],
        subscription_index=0,
        product_block_index=0,
        resource_type_index=0,
    )

    assert "<unset or non-scalar>" in state.summary
