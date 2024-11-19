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

from wfoshell.state import state, state_summary


def format_table(product_blocks: list[SubscriptionInstanceTable]) -> str:
    """Return indexed table of product blocks."""
    return tabulate(
        [
            (product_block.product_block.name, product_block.subscription_instance_id)
            for product_block in product_blocks
        ],
        tablefmt="plain",
        disable_numparse=True,
        showindex=True,
    )


def query_db(regular_expression: str = ".*") -> list[SubscriptionInstanceTable]:
    """Get list of filtered product blocks of the select subscription from the database.

    Return a sorted and filtered list of all product blocks of the selected subscription from the database, and
    add this list to the state, so it can be referenced by other subcommands.
    """
    pattern = re.compile(regular_expression, flags=re.IGNORECASE)
    if state.selected_subscription is None:
        state.product_blocks = []
    else:
        state.product_blocks = sorted(
            filter(
                lambda product_block: pattern.search(product_block.product_block.name),
                SubscriptionInstanceTable.query.filter(
                    SubscriptionInstanceTable.subscription_id == state.selected_subscription.subscription_id,
                ).all(),
            ),
            key=lambda subscription_instance: subscription_instance.product_block.name,
        )
    return state.product_blocks


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
    ]


def product_block_list() -> str:
    """Product block 'list' subcommand.

    List the product blocks of the selected subscription.
    Add the list of product blocks to the state, so it can be referenced by the 'select' subcommand.
    Return a tabulated and index list of product blocks for the selected subscription.
    """
    return format_table(query_db())


def product_block_search(regular_expression: str) -> str:
    """Product block 'search' subcommand.

    Find product blocks on the selected subscription whose name matches the supplied search string.
    Add the matching list of product blocks to the state, so it can be referenced by the 'select' subcommand.
    Return a tabulated and indexed list of product blocks for the selected subscription.
    """
    return format_table(query_db(regular_expression=regular_expression))


def product_block_select(index: int) -> str:
    """Product block 'select' subcommand.

    Select a specific product block after listing or searching product blocks.
    Add the selected product block to the state, so it can be referenced by the 'resource_type' command.
    Return a tabulated state summary.
    """
    state.selected_product_block = state.product_blocks[index]
    state.selected_resource_type = None
    return tabulate(state_summary(), tablefmt="plain")


def product_block_details() -> str:
    """Product block 'details' subcommand.

    Show details of the selected product block.
    Return the tabulated details of the selected product block.
    """
    return tabulate(details(state.selected_product_block), tablefmt="plain")
