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

from wfoshell.product_block import product_block_table
from wfoshell.state import state

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
    """Return sorted and filtered list of subscriptions from the database and also store in the state."""
    pattern = re.compile(regular_expression, flags=re.IGNORECASE)
    state.subscriptions = sorted(
        filter(
            lambda subscription: pattern.search(subscription.description),
            SubscriptionTable.query.all(),
        ),
        key=lambda subscription: subscription.description,
    )
    return state.subscriptions


def details(subscription: SubscriptionTable) -> list[tuple[str, str]]:
    """Return list of tuples with subscription detail information."""
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
        ("product block(s)", product_block_table(state.selected_product_blocks)),
    ]


def subscription_list() -> str:
    """Return tabulated and indexed list of all subscriptions from the database."""
    return indexed_subscription_list(query_db())


def subscription_search(regular_expression: str) -> str:
    """Return a tabulated and indexed list of subscriptions matching regular_expression and also store in the state."""
    return indexed_subscription_list(
        query_db(regular_expression=regular_expression),
    )


def subscription_select(index: int) -> str:
    """Implementation of the 'subscription select' subcommand."""
    state.subscription_index = index
    state.product_block_index = None
    state.resource_type_index = None
    return tabulate(state.summary, tablefmt="plain")


def subscription_details() -> str:
    """Implementation of the 'subscription details' subcommand."""
    return tabulate(details(state.selected_subscription), tablefmt="plain")


def subscription_update(field: str, new_value: str | bool | datetime | None) -> None:
    """Implementation of the 'subscription update' subcommand."""
    with transactional(db, logger):
        setattr(state.selected_subscription, field, new_value)
