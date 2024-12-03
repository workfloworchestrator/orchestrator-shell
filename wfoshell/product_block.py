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


def details(product_block: SubscriptionInstanceTable) -> list[tuple[str, str]]:
    """Return list of tuples with product block detail information."""
    return [
        ("name", product_block.product_block.name),
        ("subscription_instance_id", product_block.subscription_instance_id),
        ("subscription_id", product_block.subscription_id),
        ("product_block_id", product_block.product_block_id),
        ("label", product_block.label),
        ("resource types", resource_type_table(all_resource_types(product_block))),
        ("depends_on", product_block_table(product_block.depends_on) if product_block.depends_on else ""),
        ("in_use_by", product_block_table(product_block.in_use_by) if product_block.in_use_by else ""),
    ]


def product_block_list() -> str:
    """Implementation of the 'product_block list' subcommand."""
    return product_block_table(state.selected_product_blocks)


def product_block_select(index: int) -> str:
    """Implementation of the 'product_block select' subcommand."""
    state.product_block_index = index
    state.resource_type_index = None
    return tabulate(state.summary, tablefmt="plain")


def product_block_details() -> str:
    """Implementation of the 'product_block details' subcommand."""
    return tabulate(details(state.selected_product_block), tablefmt="plain")


def product_block_depends_on(index: int) -> str:
    """Implementation of the 'product_block depends_on' subcommand."""
    depends_on_product_block = state.selected_product_block.depends_on[index]
    state.subscription_index = state.subscriptions.index(depends_on_product_block.subscription)
    # note that the selected_product_blocks list below is of the subscription selected just above
    state.product_block_index = state.selected_product_blocks.index(depends_on_product_block)
    state.resource_type_index = None
    return tabulate(state.summary, tablefmt="plain")


def product_block_in_use_by(index: int) -> str:
    """Implementation of the 'product_block in_use_by' subcommand."""
    in_use_by_product_block = state.selected_product_block.in_use_by[index]
    state.subscription_index = state.subscriptions.index(in_use_by_product_block.subscription)
    # note that the selected_product_blocks list below is of the subscription selected just above
    state.product_block_index = state.selected_product_blocks.index(in_use_by_product_block)
    state.resource_type_index = None
    return tabulate(state.summary, tablefmt="plain")
