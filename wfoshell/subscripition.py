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
from datetime import datetime

from orchestrator.db import SubscriptionTable, db, transactional
from structlog import get_logger
from tabulate import tabulate

import wfoshell.resource_type
from wfoshell.product_block import product_block_table
from wfoshell.state import state, state_summary, selected_product_blocks, selected_subscription

logger = get_logger(__name__)


def indexed_subscription_list(subscriptions: list[SubscriptionTable]) -> str:
    """Return tabulated indexed list of subscriptions."""
    return tabulate(
        [(subscription.description, subscription.subscription_id) for subscription in subscriptions],
        tablefmt="plain",
        disable_numparse=True,
        showindex=True,
    )


def query_db(regular_expression: str = ".*") -> list[SubscriptionTable]:
    """Get list of filtered subscriptions from the database.

    Return a sorted and filtered list of all subscriptions from the database, and
    add this list to the state, so it can be referenced by other subcommands.
    """
    pattern = re.compile(regular_expression, flags=re.IGNORECASE)
    state.subscriptions = sorted(
        filter(
            lambda subscription: pattern.search(subscription.description),
            SubscriptionTable.query.all(),
        ),
        key=lambda subscription: subscription.description,
    )
    return state.subscriptions


def details(subscription) -> list[tuple[str, str]]:
    """Generate list of tuples with subscription detail information."""
    if subscription is None:
        return []
    return [
        ("description", subscription.description),
        ("subscription_id", subscription.subscription_id),
        ("status", subscription.status),
        ("product_id", subscription.product_id),
        ("customer_id", subscription.customer_id),
        ("insync", subscription.insync),
        ("start_date", subscription.start_date),
        ("end_date", subscription.end_date),
        ("note", subscription.note),
        ("product block(s)", product_block_table(selected_product_blocks())),
    ]


def subscription_list() -> str:
    """Return a tabulated and indexed list of all subscriptions from the database."""
    return indexed_subscription_list(query_db())


def subscription_search(regular_expression: str) -> str:
    """Subscription 'search' subcommand.

    Find subscriptions stored in the database whose description matches the supplied search string.
    Add the matching list of subscriptions to the state, so it can be referenced by the 'select' subcommand.
    Return a tabulated and indexed subscription list.
    """
    return indexed_subscription_list(
        query_db(regular_expression=regular_expression),
    )


def subscription_select(index: int) -> str:
    """Subscription 'select' subcommand.

    Select a specific subscription after listing or searching subscriptions.
    Add the selected subscription to the state, so it can be referenced by the 'product_block' command.
    Return a tabulated state summary.
    """
    state.subscription_index = index
    state.product_block_index = None
    state.resource_type_index = None
    return tabulate(state_summary(), tablefmt="plain")


def subscription_details() -> str:
    """Subscription 'details' subcommand.

    Show details of the selected subscription.
    Return the tabulated details of the selected subscription.
    """
    return tabulate(details(selected_subscription()), tablefmt="plain")


def subscription_update(field: str, new_value: str | bool | datetime | None) -> None:
    """Subscription 'update' subcommand.

    Update subscription `field` with `new_value`.
    Return a tabulated state summary.
    """
    with transactional(db, logger):
        setattr(selected_subscription(), field, new_value)
