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


from orchestrator.db import SubscriptionInstanceTable
from tabulate import tabulate

from wfoshell.resource_type import resource_type_table
from wfoshell.state import all_resource_types, state


def product_block_table(product_blocks: list[SubscriptionInstanceTable]) -> str:
    """Return indexed table of product blocks."""
    max_rt_width = max([len(rt.resource_type.resource_type) for pb in product_blocks for rt in all_resource_types(pb)])
    return tabulate(
        [
            [
                tabulate(
                    [
                        ["name", product_block.product_block.name],
                        ["resource types", resource_type_table(all_resource_types(product_block), max_rt_width)],
                    ],
                    tablefmt="plain",
                )
            ]
            for product_block in product_blocks
        ],
        tablefmt="plain",
        disable_numparse=True,
        showindex=True,
    )


def details_product_block(product_block: SubscriptionInstanceTable) -> list[tuple[str, str]]:
    """Return list of tuples with product block details only."""
    return [
        ("name", product_block.product_block.name),
        ("subscription_instance_id", product_block.subscription_instance_id),
        ("subscription_id", product_block.subscription_id),
        ("product_block_id", product_block.product_block_id),
        ("label", product_block.label),
    ]


def details_resource_types(product_block: SubscriptionInstanceTable) -> list[tuple[str, str]]:
    """Return list of tuples with resource type details only."""
    return [
        ("resource types", resource_type_table(all_resource_types(product_block))),
    ]


def details_depends_on(product_block: SubscriptionInstanceTable) -> list[tuple[str, str]]:
    """Return list of tuples with depends on details only."""
    return [
        ("depends_on", product_block_table(product_block.depends_on) if product_block.depends_on else ""),
    ]


def details_in_use_by(product_block: SubscriptionInstanceTable) -> list[tuple[str, str]]:
    """Return list of tuples with in use by details only."""
    return [
        ("in_use_by", product_block_table(product_block.in_use_by) if product_block.in_use_by else ""),
    ]


def details_all(product_block: SubscriptionInstanceTable) -> list[tuple[str, str]]:
    """Return list of tuples with all product block details."""
    return (
        details_product_block(product_block)
        + details_resource_types(product_block)
        + details_depends_on(product_block)
        + details_in_use_by(product_block)
    )


def product_block_list() -> str:
    """Implementation of the 'product_block list' subcommand."""
    return product_block_table(state.selected_product_blocks)


def product_block_select(index: int) -> str:
    """Implementation of the 'product_block select' subcommand."""
    state.product_block_index = index
    state.resource_type_index = None
    return state.summary


def product_block_details(
    product_block_only: bool, resource_types_only: bool, depends_on_only: bool, in_use_by_only: bool
) -> str:
    """Implementation of the 'product_block details' subcommand."""
    if product_block_only:
        return tabulate(details_product_block(state.selected_product_block), tablefmt="plain")
    elif resource_types_only:  # noqa: RET505
        return tabulate(details_resource_types(state.selected_product_block), tablefmt="plain")
    elif depends_on_only:
        return tabulate(details_depends_on(state.selected_product_block), tablefmt="plain")
    elif in_use_by_only:
        return tabulate(details_in_use_by(state.selected_product_block), tablefmt="plain")
    else:
        return tabulate(details_all(state.selected_product_block), tablefmt="plain")


def product_block_depends_on(index: int) -> str:
    """Implementation of the 'product_block depends_on' subcommand."""
    depends_on_product_block = state.selected_product_block.depends_on[index]
    state.subscription_index = state.subscriptions.index(depends_on_product_block.subscription)
    # note that the selected_product_blocks list below is of the subscription selected just above
    state.product_block_index = state.selected_product_blocks.index(depends_on_product_block)
    state.resource_type_index = None
    return state.summary


def product_block_in_use_by(index: int) -> str:
    """Implementation of the 'product_block in_use_by' subcommand."""
    in_use_by_product_block = state.selected_product_block.in_use_by[index]
    state.subscription_index = state.subscriptions.index(in_use_by_product_block.subscription)
    # note that the selected_product_blocks list below is of the subscription selected just above
    state.product_block_index = state.selected_product_blocks.index(in_use_by_product_block)
    state.resource_type_index = None
    return state.summary
