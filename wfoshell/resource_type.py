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


from orchestrator.db import SubscriptionInstanceValueTable, db, transactional
from structlog import get_logger
from tabulate import tabulate

from wfoshell.state import state

logger = get_logger(__name__)


def resource_type_table(resource_types: list[SubscriptionInstanceValueTable]) -> str:
    """Return indexed table of resource types."""
    return tabulate(
        [
            [index, resource_type.resource_type.resource_type, resource_type.value]
            for index, resource_type in enumerate(resource_types)
        ],
        tablefmt="plain",
        disable_numparse=True,
    )


def details(resource_type: SubscriptionInstanceValueTable | None) -> list[tuple[str, str]]:
    """Return list of tuples with resource type detail information."""
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
    """Implementation of the 'resource_type list' subcommand."""
    return resource_type_table(state.selected_resource_types)


def resource_type_select(index: int) -> str:
    """Implementation of the 'resource_type select' subcommand."""
    state.resource_type_index = index
    return tabulate(state.summary, tablefmt="plain")


def resource_type_details() -> str:
    """Implementation of the 'resource_type details' subcommand."""
    return tabulate(details(state.selected_resource_type), tablefmt="plain")


def resource_type_update(new_value: str) -> None:
    """Implementation of the 'resource_type update' subcommand."""
    with transactional(db, logger):
        if state.selected_resource_type is not None:
            state.selected_resource_type.value = new_value
