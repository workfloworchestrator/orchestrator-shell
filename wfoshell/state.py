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
    subscription_index: int | None = None
    product_block_index: int | None = None
    resource_type_index: int | None = None

    @property
    def selected_subscription(self) -> SubscriptionTable:
        """Return the subscription indexed by subscription_index."""
        if self.subscription_index is not None:
            return self.subscriptions[self.subscription_index]
        raise IndexError("subscription_index not set")

    @property
    def selected_product_blocks(self) -> list[SubscriptionInstanceTable]:
        """Return the list of product blocks for the subscription indexed by subscription_index."""
        return (
            (
                sorted(
                    self.selected_subscription.instances,
                    key=lambda subscription_instance: subscription_instance.product_block.name,
                )
            )
            if self.subscription_index is not None
            else []
        )

    @property
    def selected_product_block(self) -> SubscriptionInstanceTable:
        """Return the product block indexed by product_block_index."""
        if self.product_block_index is not None:
            return self.selected_product_blocks[self.product_block_index]
        raise IndexError("product_block_index not set")

    @property
    def selected_resource_types(self) -> list[SubscriptionInstanceValueTable]:
        """Return the list of resource types for the product block indexed by product_block_index."""
        return (
            sorted(
                self.selected_product_block.values,
                key=lambda subscription_instance_value: subscription_instance_value.resource_type.resource_type,
            )
            if self.product_block_index is not None
            else []
        )

    @property
    def selected_resource_type(self) -> SubscriptionInstanceValueTable:
        """Return the resource type indexed by resource_type_index."""
        if self.resource_type_index is not None:
            return self.selected_resource_types[self.resource_type_index]
        raise IndexError("resource_type_index not set")

    @property
    def summary(self) -> list[tuple[str, str, str]]:
        """Generate a list of tuples with a summary of the subscription, product block and resource type state."""
        summary = []
        if self.subscription_index is not None:
            summary.append(
                (
                    "subscription",
                    self.selected_subscription.description,
                    self.selected_subscription.subscription_id,
                )
            )
        if self.product_block_index is not None:
            summary.append(
                (
                    "product block",
                    self.selected_product_block.product_block.name,
                    self.selected_product_block.subscription_instance_id,
                ),
            )
        if self.resource_type_index is not None:
            summary.append(
                (
                    "resource_type",
                    self.selected_resource_type.resource_type.resource_type,
                    self.selected_resource_type.subscription_instance_value_id,
                ),
            )
        return summary


state = State()
