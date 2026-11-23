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
"""Tests for listing, selecting and following product blocks."""

import pytest
from orchestrator.core.db import SubscriptionInstanceTable, SubscriptionTable

from orchestrator.shell import product_block
from orchestrator.shell.state import State
from test import factories


def _node_and_port() -> tuple[SubscriptionTable, SubscriptionTable, SubscriptionInstanceTable]:
    """Return a node and port subscription plus the port product block that depends on the node."""
    node_block = factories.product_block("Node", "node_name")
    node_instance = factories.subscription_instance(
        node_block, "node-si", factories.value(node_block.resource_types[0], "paris-1")
    )
    node = factories.subscription("node-sub", "node paris-1", node_instance)

    port_block = factories.product_block("Port", "port_name")
    port_instance = factories.subscription_instance(
        port_block, "port-si", factories.value(port_block.resource_types[0], "ethernet-1/5")
    )
    port_instance.depends_on = [node_instance]
    port_instance.subscription = factories.subscription("port-sub", "port paris-1", port_instance)
    return node, port_instance.subscription, port_instance


def test_product_block_table_lists_blocks_with_their_resource_types() -> None:
    """A product block is listed with its name and its resource types."""
    node, _, _ = _node_and_port()
    table = product_block.product_block_table(list(node.instances))

    assert table.startswith("0  name")
    assert "Node" in table
    assert "node_name" in table
    assert "paris-1" in table


def test_details_of_a_product_block() -> None:
    """The product block details report the identifiers of the product block."""
    node, _, _ = _node_and_port()

    rows = dict(product_block.details_product_block(node.instances[0]))

    assert rows["name"] == "Node"
    assert rows["subscription_instance_id"] == "node-si"
    assert rows["subscription_id"] == "node-sub"


def test_details_depends_on_is_empty_without_dependencies() -> None:
    """A product block without dependencies shows an empty depends_on."""
    node, _, _ = _node_and_port()

    rows = dict(product_block.details_depends_on(node.instances[0]))
    assert rows["depends_on"] == ""


def test_product_block_table_of_no_product_blocks_is_empty() -> None:
    """A subscription without product blocks renders an empty table instead of raising."""
    assert product_block.product_block_table([]) == ""


def test_product_block_table_of_blocks_without_resource_types() -> None:
    """A product block that defines no resource types is still listed instead of raising ValueError."""
    block = factories.product_block("Empty")
    instance = factories.subscription_instance(block, "si-1")

    table = product_block.product_block_table([instance])

    lines = table.splitlines()
    assert lines[0].startswith("0  name")
    assert lines[0].rstrip().endswith("Empty")
    assert lines[1].startswith("   resource types")


def test_details_all_combines_every_section() -> None:
    """The full details contain the product block, resource types and relations."""
    _, _, port_instance = _node_and_port()

    labels = [label for label, _ in product_block.details_all(port_instance)]

    assert labels == [
        "name",
        "subscription_instance_id",
        "subscription_id",
        "product_block_id",
        "label",
        "resource types",
        "depends_on",
        "in_use_by",
    ]


def test_details_in_use_by_lists_the_dependent_product_block() -> None:
    """A product block that another block depends on lists that block under in_use_by."""
    node, _, port_instance = _node_and_port()
    node_instance = node.instances[0]
    node_instance.in_use_by = [port_instance]

    rows = dict(product_block.details_in_use_by(node_instance))

    assert "Port" in rows["in_use_by"]
    assert "ethernet-1/5" in rows["in_use_by"]


def test_depends_on_navigates_to_the_depended_on_product_block(monkeypatch: pytest.MonkeyPatch) -> None:
    """Following depends_on selects the other subscription and product block."""
    node, port, _ = _node_and_port()
    state = State(subscriptions=[node, port], subscription_index=1, product_block_index=0)
    monkeypatch.setattr(product_block, "state", state)

    summary = product_block.product_block_depends_on(0)

    assert state.subscription_index == 0
    assert state.product_block_index == 0
    assert state.resource_type_index is None
    assert "node paris-1" in summary


def test_in_use_by_navigates_to_the_dependent_product_block(monkeypatch: pytest.MonkeyPatch) -> None:
    """Following in_use_by selects the other subscription and product block."""
    node, port, port_instance = _node_and_port()
    node.instances[0].in_use_by = [port_instance]
    state = State(subscriptions=[node, port], subscription_index=0, product_block_index=0)
    monkeypatch.setattr(product_block, "state", state)

    summary = product_block.product_block_in_use_by(0)

    assert state.subscription_index == 1
    assert state.product_block_index == 0
    assert "port paris-1" in summary


def test_select_resets_the_resource_type_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    """Selecting a product block clears the previously selected resource type."""
    node, _, _ = _node_and_port()
    state = State(subscriptions=[node], subscription_index=0, resource_type_index=3)
    monkeypatch.setattr(product_block, "state", state)

    product_block.product_block_select(0)

    assert state.product_block_index == 0
    assert state.resource_type_index is None
