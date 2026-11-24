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
"""Tests for rendering and selecting resource types."""

import pytest

from orchestrator.shell import resource_type
from orchestrator.shell.state import State
from test import factories


def test_resource_type_table_aligns_on_width_and_marks_unset_values() -> None:
    """The table pads names to ``width`` and renders a missing value as ``<unset or non-scalar>``."""
    block = factories.product_block("Node", "ims_id", "node_name")
    set_value = factories.value(block.resource_types[0], "3")
    unset_value = factories.value(block.resource_types[1], None)

    table = resource_type.resource_type_table([set_value, unset_value], width=12)

    lines = table.splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("0  ims_id")
    assert lines[1].startswith("1  node_name")
    assert "<unset or non-scalar>" in lines[1]


def test_details_of_a_resource_type() -> None:
    """All identifiers of a resource type value are reported."""
    block = factories.product_block("Node", "node_name")
    set_value = factories.value(block.resource_types[0], "amsterdam-1", value_id="siv-1")

    rows = dict(resource_type.details(set_value))

    assert rows["resource_type"] == "node_name"
    assert rows["value"] == "amsterdam-1"
    assert rows["subscription_instance_value_id"] == "siv-1"
    assert rows["resource_type_id"] == set_value.resource_type_id


def test_select_indexes_into_the_sorted_resource_types(monkeypatch: pytest.MonkeyPatch) -> None:
    """Selecting by index picks from the sorted list, not the definition order."""
    block = factories.product_block("Node", "node_name", "ims_id")
    instance = factories.subscription_instance(
        block,
        "si-1",
        factories.value(block.resource_types[0], "amsterdam-1"),
        factories.value(block.resource_types[1], "3"),
    )
    state = State(
        subscriptions=[factories.subscription("sub-1", "node", instance)],
        subscription_index=0,
        product_block_index=0,
    )
    monkeypatch.setattr(resource_type, "state", state)

    resource_type.resource_type_select(0)

    assert state.resource_type_index == 0
    assert state.selected_resource_type.resource_type.resource_type == "ims_id"


def test_update_sets_the_value_of_a_selected_resource_type(monkeypatch: pytest.MonkeyPatch) -> None:
    """Updating a resource type that already has a value changes that value in place."""
    block = factories.product_block("Node", "node_status")
    existing = factories.value(block.resource_types[0], "staged")
    instance = factories.subscription_instance(block, "si-1", existing)
    state = State(
        subscriptions=[factories.subscription("sub-1", "node", instance)],
        subscription_index=0,
        product_block_index=0,
        resource_type_index=0,
    )
    monkeypatch.setattr(resource_type, "state", state)

    resource_type.resource_type_update("active")

    assert existing.value == "active"
    assert len(instance.values) == 1


def test_update_adds_a_value_to_an_unset_resource_type(monkeypatch: pytest.MonkeyPatch) -> None:
    """Updating a resource type without a value appends a new value to its product block."""
    block = factories.product_block("Node", "node_description")
    instance = factories.subscription_instance(block, "si-1")
    state = State(
        subscriptions=[factories.subscription("sub-1", "node", instance)],
        subscription_index=0,
        product_block_index=0,
        resource_type_index=0,
    )
    monkeypatch.setattr(resource_type, "state", state)

    resource_type.resource_type_update("Rome international exchange")

    assert len(instance.values) == 1
    assert instance.values[0].value == "Rome international exchange"
    assert instance.values[0].resource_type_id == block.resource_types[0].resource_type_id
