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

from orchestrator.db import (
    SubscriptionInstanceValueTable,
    db,
    transactional,
)
from structlog import get_logger
from tabulate import tabulate

from wfoshell.state import state, state_summary

logger = get_logger(__name__)


def resource_type_arguments() -> list[str]:
    """List of possible 'resource_type' subcommands."""
    return ["list", "search", "select", "details", "update"]


def resource_type_list(args: list[str]) -> None:
    """Resource type 'list' subcommand.

    List the resource types of the selected product block.
    Add the list of resource types to the state, so it can be referenced by the 'select' subcommand.
    """
    if len(args) != 1:
        print("subcommand does not take parameters")
    elif not state.selected_product_block:
        print("first select a product block")
    else:
        state.resource_types = sorted(
            SubscriptionInstanceValueTable.query.filter(
                SubscriptionInstanceValueTable.subscription_instance_id
                == state.selected_product_block.subscription_instance_id,
            ).all(),
            key=lambda subscription_instance_value: subscription_instance_value.resource_type.resource_type,
        )
        subscription_instance_value_details = [
            (
                subscription_instance_value.resource_type.resource_type,
                subscription_instance_value.value,
                subscription_instance_value.subscription_instance_value_id,
            )
            for subscription_instance_value in state.resource_types
        ]
        print(tabulate(subscription_instance_value_details, tablefmt="plain", disable_numparse=True, showindex=True))


def resource_type_select(args: list[str]) -> None:
    """Resource type 'select' subcommand.

    Select a specific resource type after listing or searching resource types.
    Add the selected resource type to the state, so it can be referenced by the 'details' and 'update' subcommands.
    """
    if len(args) != 2:
        print("specify resource_type index")
    elif not args[1].isdecimal():
        print(f"'{args[1]}' is not an decimal")
    elif not (number_of_resource_types := len(state.resource_types)):
        print("list or search for resource_types first")
    elif (selected := int(args[1])) >= number_of_resource_types:
        print(f"selected resource_type index not between 0 and {number_of_resource_types - 1}")
    else:
        state.selected_resource_type = state.resource_types[selected]
        print(tabulate(state_summary(), tablefmt="plain"))


def resource_type_search(args: list[str]) -> None:  # noqa: ARG001
    """Resource type 'search' subcommand.

    Find resource types on the selected product block whose name matches the supplied search string.
    Add the matching list of resource types to the state, so it can be referenced by the 'select' subcommand.
    """
    print("resource_type search not implemented yet")


def details(resource_type: SubscriptionInstanceValueTable) -> list[tuple[str, str]]:
    """Generate list of tuples with resource type detail information."""
    # Use this for unset optional resource types?
    #
    # resource_types = sorted(
    #     (
    #         {rt.resource_type: None for rt in subscription_instance.product_block.resource_types}
    #         | {v.resource_type.resource_type: v.value for v in subscription_instance.values}
    #     ).items()
    # )
    return [
        ("subscription_instance_value_id", resource_type.subscription_instance_value_id),
        ("subscription_instance_id", resource_type.subscription_instance_id),
        ("resource_type_id", resource_type.resource_type_id),
        ("resource_type", resource_type.resource_type.resource_type),
        ("value", resource_type.value),
    ]


def resource_type_details(args: list[str]) -> None:
    """Resource type 'details' subcommand.

    Show details of the selected resource type.
    """
    if len(args) != 1:
        print("subcommand does not take parameters")
    elif not state.selected_resource_type:
        print("first select a resource type")
    else:
        print(tabulate(details(state.selected_resource_type), tablefmt="plain"))


def resource_type_update(args: list[str]) -> None:
    """Resource type 'update' subcommand.

    Ask for a new value and update the selected resource type in the database.
    """
    if len(args) != 1:
        print("subcommand does not take parameters")
    elif not state.selected_resource_type:
        print("first select a resource type")
    else:
        new_value = input(f"new '{state.selected_resource_type.resource_type.resource_type}' value> ")
        with transactional(db, logger):
            state.selected_resource_type.value = new_value
