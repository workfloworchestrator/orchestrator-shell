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

from orchestrator.db import SubscriptionTable
from tabulate import tabulate

from wfoshell.state import state, state_summary


def subscription_arguments() -> list[str]:
    """List of possible 'subscription' subcommands."""
    return ["list", "search", "select", "details"]


def subscription_list(args: list[str]) -> None:  # noqa: ARG001
    """Subscription 'list' subcommand.

    List all possible subscriptions stored in the database.
    Add the list of subscriptions to the state, so it can be referenced by the 'select' subcommand.
    """
    if len(args) != 1:
        print("subcommand does not take parameters")
    else:
        state.subscriptions = sorted(
            SubscriptionTable.query.all(),
            key=lambda subscription: subscription.description,
        )
        details = [(subscription.description, subscription.subscription_id) for subscription in state.subscriptions]
        print(tabulate(details, tablefmt="plain", disable_numparse=True, showindex=True))


def subscription_select(args: list[str]) -> None:
    """Subscription 'select' subcommand.

    Select a specific subscription after listing or searching subscriptions.
    Add the selected subscription to the state, so it can be referenced by the 'product_block' command.
    """
    if len(args) != 2:
        print("specify subscription index")
    elif not args[1].isdecimal():
        print(f"'{args[1]}' is not an decimal")
    elif not (number_of_subscriptions := len(state.subscriptions)):
        print("list or search for subscriptions first")
    elif (selected := int(args[1])) >= number_of_subscriptions:
        print(f"selected subscription index not between 0 and {number_of_subscriptions - 1}")
    else:
        state.selected_subscription = state.subscriptions[selected]
        print(tabulate(state_summary(), tablefmt="plain"))


def subscription_search(args: list[str]) -> None:  # noqa: ARG001
    """Subscription 'search' subcommand.

    Find subscriptions stored in the database whose description matches the supplied search string.
    Add the matching list of subscriptions to the state, so it can be referenced by the 'select' subcommand.
    """
    print("subscription search not implemented yet")


def details(subscription: SubscriptionTable) -> list[tuple[str, str]]:
    """Generate list of tuples with subscription detail information."""
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
    ]


def subscription_details(args: list[str]) -> None:
    """Subscription 'details' subcommand.

    Show details of the selected subscription.
    """
    if len(args) != 1:
        print("subcommand does not take parameters")
    elif not state.selected_subscription:
        print("first select a subscription")
    else:
        print(tabulate(details(state.selected_subscription), tablefmt="plain"))
