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

import re

from orchestrator.db import SubscriptionInstanceTable
from tabulate import tabulate

import wfoshell
import wfoshell.state
from wfoshell.state import state, state_summary, selected_product_blocks, selected_product_block


def product_block_table(product_blocks) -> str:
    """Return indexed table of product blocks."""
    return tabulate(
        [
            [
                tabulate(
                    [
                        ["name", product_block.product_block.name],
                        ["resource types", wfoshell.resource_type.resource_type_table(product_block.values)],
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


def details(product_block: SubscriptionInstanceTable | None) -> list[tuple[str, str]]:
    """Generate list of tuples with product block detail information."""
    if product_block is None:
        return []
    return [
        ("subscription_instance_id", product_block.subscription_instance_id),
        ("subscription_id", product_block.subscription_id),
        ("product_block_id", product_block.product_block_id),
        ("name", product_block.product_block.name),
        ("label", product_block.label),
        ("depends_on", product_block_table(product_block.depends_on)),
        ("in_use_by", product_block_table(product_block.in_use_by)),
    ]


def product_block_list() -> str:
    """Product block 'list' subcommand.

    List the product blocks of the selected subscription.
    Add the list of product blocks to the state, so it can be referenced by the 'select' subcommand.
    Return a tabulated and index list of product blocks for the selected subscription.
    """
    return product_block_table(selected_product_blocks())


def product_block_select(index: int) -> str:
    """Product block 'select' subcommand.

    Select a specific product block after listing or searching product blocks.
    Add the selected product block to the state, so it can be referenced by the 'resource_type' command.
    Return a tabulated state summary.
    """
    state.product_block_index = index
    state.resource_type_index = None
    return tabulate(state_summary(), tablefmt="plain")


def product_block_details() -> str:
    """Product block 'details' subcommand.

    Show details of the selected product block.
    Return the tabulated details of the selected product block.
    """
    return tabulate(details(selected_product_block()), tablefmt="plain")
