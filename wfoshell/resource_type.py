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

from orchestrator.db import (
    SubscriptionInstanceValueTable,
    db,
    transactional,
)
from structlog import get_logger
from tabulate import tabulate

from wfoshell.state import state, state_summary

logger = get_logger(__name__)


def format_table(resource_types: list[SubscriptionInstanceValueTable]) -> str:
    """Output indexed list of resource types stored in state."""
    return tabulate(
        [
            (
                subscription_instance_value.resource_type.resource_type,
                subscription_instance_value.value,
                subscription_instance_value.subscription_instance_value_id,
            )
            for subscription_instance_value in resource_types
        ],
        tablefmt="plain",
        disable_numparse=True,
        showindex=True,
    )


def query_db(regular_expression: str = ".*") -> list[SubscriptionInstanceValueTable]:
    """Get list of filtered resource types of the select product block from the database.

    Return a sorted and filtered list of all resource types of the selected product block from the database, and
    add this list to the state, so it can be referenced by other subcommands.
    """
    pattern = re.compile(regular_expression, flags=re.IGNORECASE)
    if state.selected_product_block is None:
        state.resource_types = []
    else:
        state.resource_types = sorted(
            filter(
                lambda resource_type: pattern.search(resource_type.resource_type.resource_type),
                SubscriptionInstanceValueTable.query.filter(
                    SubscriptionInstanceValueTable.subscription_instance_id
                    == state.selected_product_block.subscription_instance_id,
                ).all(),
            ),
            key=lambda subscription_instance_value: subscription_instance_value.resource_type.resource_type,
        )
    return state.resource_types


def details(resource_type: SubscriptionInstanceValueTable | None) -> list[tuple[str, str]]:
    """Generate list of tuples with resource type detail information."""
    # Use this for unset optional resource types?
    #
    # resource_types = sorted(
    #     (
    #         {rt.resource_type: None for rt in subscription_instance.product_block.resource_types}
    #         | {v.resource_type.resource_type: v.value for v in subscription_instance.values}
    #     ).items()
    # )
    if resource_type is None:
        return []
    return [
        ("subscription_instance_value_id", resource_type.subscription_instance_value_id),
        ("subscription_instance_id", resource_type.subscription_instance_id),
        ("resource_type_id", resource_type.resource_type_id),
        ("resource_type", resource_type.resource_type.resource_type),
        ("value", resource_type.value),
    ]


def resource_type_list() -> str:
    """Resource type 'list' subcommand.

    List the resource types of the selected product block.
    Add the list of resource types to the state, so it can be referenced by the 'select' subcommand.
    Return a tabulated and index list of resource types for the selected product block.
    """
    return format_table(query_db())


def resource_type_search(regular_expression: str) -> str:
    """Resource type 'search' subcommand.

    Find resource types on the selected product block whose name matches the supplied search string.
    Add the matching list of resource types to the state, so it can be referenced by the 'select' subcommand.
    Return a tabulated and indexed list of resource type for the selected product block.
    """
    return format_table(query_db(regular_expression=regular_expression))


def resource_type_select(index: int) -> str:
    """Resource type 'select' subcommand.

    Select a specific resource type after listing or searching resource types.
    Add the selected resource type to the state, so it can be referenced by the 'details' and 'update' subcommands.
    Return a tabulated state summary.
    """
    state.selected_resource_type = state.resource_types[index]
    return tabulate(state_summary(), tablefmt="plain")


def resource_type_details() -> str:
    """Resource type 'details' subcommand.

    Show details of the selected resource type.
    Return the tabulated details of the selected resource type.
    """
    return tabulate(details(state.selected_resource_type), tablefmt="plain")


def resource_type_update(new_value: str) -> None:
    """Resource type 'update' subcommand.

    Update the selected resource type with new_value in the database.
    """
    with transactional(db, logger):
        if state.selected_resource_type is not None:
            state.selected_resource_type.value = new_value
