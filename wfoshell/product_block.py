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


def product_block_arguments() -> list[str]:
    """List of possible 'product_block' subcommands."""
    return ["list", "search", "select", "details"]


def output_product_block_list() -> None:
    """Output indexed list of product blocks stored in state."""
    details = [
        (product_block.product_block.name, product_block.subscription_instance_id)
        for product_block in state.product_blocks
    ]
    print(tabulate(details, tablefmt="plain", disable_numparse=True, showindex=True))


def product_block_list(args: list[str]) -> None:
    """Product block 'list' subcommand.

    List the product blocks of the selected subscription.
    Add the list of product blocks to the state, so it can be referenced by the 'select' subcommand.
    """
    if len(args) != 1:
        print("subcommand does not take parameters")
    elif not state.selected_subscription:
        print("first select a subscription")
    else:
        state.product_blocks = sorted(
            SubscriptionInstanceTable.query.filter(
                SubscriptionInstanceTable.subscription_id == state.selected_subscription.subscription_id,
            ).all(),
            key=lambda subscription_instance: subscription_instance.product_block.name,
        )
        output_product_block_list()


def product_block_select(args: list[str]) -> None:
    """Product block 'select' subcommand.

    Select a specific product block after listing or searching product blocks.
    Add the selected product block to the state, so it can be referenced by the 'resource_type' command.
    """
    if len(args) != 2:
        print("specify product_block index")
    elif not args[1].isdecimal():
        print(f"'{args[1]}' is not an decimal")
    elif not (number_of_product_blocks := len(state.product_blocks)):
        print("list or search for product_blocks first")
    elif (selected := int(args[1])) >= number_of_product_blocks:
        print(f"selected product_block index not between 0 and {number_of_product_blocks - 1}")
    else:
        state.selected_product_block = state.product_blocks[selected]
        state.selected_resource_type = None
        print(tabulate(state_summary(), tablefmt="plain"))


def product_block_search(args: list[str]) -> None:
    """Product block 'search' subcommand.

    Find product blocks on the selected subscription whose name matches the supplied search string.
    Add the matching list of product blocks to the state, so it can be referenced by the 'select' subcommand.
    """
    if len(args) != 2:
        print("specify search string")
    else:
        pattern = re.compile(args[1], flags=re.IGNORECASE)
        state.product_blocks = sorted(
            filter(
                lambda product_block: pattern.search(product_block.product_block.name),
                SubscriptionInstanceTable.query.filter(
                    SubscriptionInstanceTable.subscription_id == state.selected_subscription.subscription_id,
                ).all(),
            ),
            key=lambda subscription_instance: subscription_instance.product_block.name,
        )
        output_product_block_list()


def details(product_block: SubscriptionInstanceTable) -> list[tuple[str, str]]:
    """Generate list of tuples with product block detail information."""
    return [
        ("subscription_instance_id", product_block.subscription_instance_id),
        ("subscription_id", product_block.subscription_id),
        ("product_block_id", product_block.product_block_id),
        ("name", product_block.product_block.name),
        ("label", product_block.label),
    ]


def product_block_details(args: list[str]) -> None:
    """Product block 'details' subcommand.

    Show details of the selected product block.
    """
    if len(args) != 1:
        print("subcommand does not take parameters")
    elif not state.selected_product_block:
        print("first select a product block")
    else:
        print(tabulate(details(state.selected_product_block), tablefmt="plain"))
