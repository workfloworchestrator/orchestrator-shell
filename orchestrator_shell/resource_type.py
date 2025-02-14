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


import tabulate
from orchestrator.db import SubscriptionInstanceValueTable, db, transactional
from structlog import get_logger

from orchestrator_shell.state import sorted_resource_types, state

logger = get_logger(__name__)
tabulate.PRESERVE_WHITESPACE = True


def resource_type_table(resource_types: list[SubscriptionInstanceValueTable], width: int = 0) -> str:
    """Return indexed table of resource types, with name optionally aligned on width."""
    return tabulate.tabulate(
        [
            [
                resource_type.resource_type.resource_type.ljust(width),
                resource_type.value if resource_type.value is not None else "<unset or non-scalar>",
            ]
            for resource_type in sorted_resource_types(resource_types)
        ],
        tablefmt="plain",
        disable_numparse=True,
        showindex=True,
    )


def details(resource_type: SubscriptionInstanceValueTable | None) -> list[tuple[str, str]]:
    """Return list of tuples with resource type detail information."""
    if resource_type is None:
        return []
    return [
        ("resource_type", resource_type.resource_type.resource_type),
        ("value", resource_type.value),
        ("subscription_instance_value_id", resource_type.subscription_instance_value_id),
        ("subscription_instance_id", resource_type.subscription_instance_id),
        ("resource_type_id", resource_type.resource_type_id),
    ]


def resource_type_list() -> str:
    """Implementation of the 'resource_type list' subcommand."""
    return resource_type_table(state.selected_resource_types)


def resource_type_select(index: int) -> str:
    """Implementation of the 'resource_type select' subcommand."""
    state.resource_type_index = index
    return state.summary


def resource_type_details() -> str:
    """Implementation of the 'resource_type details' subcommand."""
    return tabulate.tabulate(details(state.selected_resource_type), tablefmt="plain")


def resource_type_update(new_value: str) -> None:
    """Implementation of the 'resource_type update' subcommand."""
    with transactional(db, logger):
        if state.selected_resource_type.value is None:
            # add previously unset resource type to list of product block values
            state.selected_product_block.values.append(
                SubscriptionInstanceValueTable(
                    resource_type_id=state.selected_resource_type.resource_type.resource_type_id, value=new_value
                )
            )
        else:
            # otherwise just update the existing resource type value
            state.selected_resource_type.value = new_value
