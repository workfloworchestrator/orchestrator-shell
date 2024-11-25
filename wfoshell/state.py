#  Copyright 2024 SURF.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from dataclasses import dataclass, field

from orchestrator.db import SubscriptionInstanceTable, SubscriptionInstanceValueTable, SubscriptionTable


@dataclass
class State:
    """State that is shared between the WFO shell commands."""

    subscriptions: list[SubscriptionTable] = field(default_factory=list)
    # product_blocks: list[SubscriptionInstanceTable] = field(default_factory=list)
    # resource_types: list[SubscriptionInstanceValueTable] = field(default_factory=list)
    # selected_subscription: SubscriptionTable | None = None
    # selected_product_block: SubscriptionInstanceTable | None = None
    # selected_resource_type: SubscriptionInstanceValueTable | None = None
    subscription_index: int | None = None
    product_block_index: int | None = None
    resource_type_index: int | None = None


state = State()


def state_summary() -> list[tuple[str, str, str]]:
    """Generate a list of tuples with a summary of the subscription, product block and resource type state."""
    if state.subscriptions[state.subscription_index]:
        summary = [
            (
                (
                    "subscription",
                    selected_subscription().description,
                    selected_subscription().subscription_id,
                )
            ),
        ]
        if state.product_block_index is not None:
            summary.append(
                (
                    "product block",
                    selected_product_block().product_block.name,
                    selected_product_block().subscription_instance_id,
                ),
            )
            if state.resource_type_index is not None:
                summary.append(
                    (
                        "resource_type",
                        selected_resource_type().resource_type.resource_type,
                        selected_resource_type().subscription_instance_value_id,
                    ),
                )
        return summary
    return []


def selected_subscription() -> SubscriptionTable | None:
    return None if state.subscription_index is None else state.subscriptions[state.subscription_index]


def selected_product_blocks() -> list[SubscriptionInstanceTable]:
    return (
        []
        if state.subscription_index is None
        else (
            sorted(
                selected_subscription().instances,
                key=lambda subscription_instance: subscription_instance.product_block.name,
            )
        )
    )


def selected_product_block() -> SubscriptionInstanceTable | None:
    return None if state.product_block_index is None else selected_product_blocks()[state.product_block_index]


def selected_resource_types() -> list[SubscriptionInstanceValueTable]:
    return (
        []
        if state.product_block_index is None
        else sorted(
            selected_product_block().values,
            key=lambda subscription_instance_value: subscription_instance_value.resource_type.resource_type,
        )
    )


def selected_resource_type() -> SubscriptionInstanceValueTable | None:
    return None if state.resource_type_index is None else selected_resource_types()[state.resource_type_index]
