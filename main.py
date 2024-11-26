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

from argparse import Namespace
from datetime import datetime

from cmd2 import Cmd, Cmd2ArgumentParser, Statement, with_argparser
from orchestrator.db import init_database

import wfoshell.product_block
import wfoshell.resource_type
import wfoshell.state
import wfoshell.subscripition
from wfoshell.settings import settings
from wfoshell.state import state


class WFOshell(Cmd):
    """WorkFlow Orchestrator shell."""

    intro = "Welcome to the WFO shell.\n" "Type help or ? to list commands."

    def __init__(self) -> None:
        """WFO shell initialisation."""
        super().__init__(
            persistent_history_file=str(settings.WFOSHELL_HISTFILE),
            persistent_history_length=settings.WFOSHELL_HISTFILE_SIZE,
        )
        self.prompt = "(wfo) "
        self.hidden_commands.extend(["alias", "edit", "macro", "run_pyscript", "run_script", "shell", "shortcuts"])
        init_database(settings)  # type: ignore[arg-type]

    def do_exit(self, line: Statement) -> bool:  # noqa: ARG002
        """Exit the application."""
        return True

    # subcommand functions for the subscription command
    def subscription_list(self, args: Namespace) -> None:  # noqa: ARG002
        """List subcommand of subscription command."""
        self.poutput(wfoshell.subscripition.subscription_list())

    def subscription_search(self, args: Namespace) -> None:
        """Search subcommand of subscription command."""
        self.poutput(wfoshell.subscripition.subscription_search(args.regular_expression))

    def subscription_select(self, args: Namespace) -> None:
        """Select subcommand of subscription command."""
        if not (number_of_subscriptions := len(state.subscriptions)):
            self.pwarning("list or search for subscriptions first")
        elif not 0 <= args.index < number_of_subscriptions:
            self.pwarning(f"selected subscription index not between 0 and {number_of_subscriptions - 1}")
        else:
            self.poutput(wfoshell.subscripition.subscription_select(args.index))

    def subscription_details(self, args: Namespace) -> None:  # noqa: ARG002
        """Details subcommand of subscription command."""
        if state.subscription_index is None:
            self.pwarning("first select a subscription")
        else:
            self.poutput(wfoshell.subscripition.subscription_details())

    def subscription_update(self, args: Namespace) -> None:  # noqa: C901
        """Update subcommand of subscription command."""
        if state.subscription_index is None:
            self.pwarning("first select a subscription")
            return
        if args.field in ["insync"]:
            if args.new_value.lower() in ["y", "yes", "true"]:
                args.new_value = True
            elif args.new_value.lower() in ["n", "no", "false"]:
                args.new_value = False
            else:
                self.pwarning("expected y, yes, true, n, no or false")
                return
        if args.field in ["start_date", "end_date"]:
            if args.new_value == "":
                args.new_value = None
            else:
                try:
                    args.new_value = datetime.fromisoformat(args.new_value)
                except ValueError as value_error:
                    self.pwarning(str(value_error))
                    return
                if args.new_value.tzinfo is None:
                    args.new_value = args.new_value.astimezone()
        wfoshell.subscripition.subscription_update(args.field, args.new_value)

    # subscription (sub)commands argument parsers
    s_parser = Cmd2ArgumentParser()
    s_subparser = s_parser.add_subparsers(title="subscription subcommands")
    s_list_parser = s_subparser.add_parser("list")
    s_list_parser.set_defaults(func=subscription_list)
    s_search_parser = s_subparser.add_parser("search")
    s_search_parser.add_argument("regular_expression", type=str, help="match description on regular expression")
    s_search_parser.set_defaults(func=subscription_search)
    s_select_parser = s_subparser.add_parser("select")
    s_select_parser.add_argument("index", type=int, help="select by index number")
    s_select_parser.set_defaults(func=subscription_select)
    s_details_parser = s_subparser.add_parser("details")
    s_details_parser.set_defaults(func=subscription_details)
    s_update_parser = s_subparser.add_parser("update")
    s_update_parser.add_argument(
        "field",
        choices=[
            "description",
            "status",
            "customer_id",
            "insync",
            "start_date",
            "end_date",
            "note",
        ],
        help="subscription field",
    )
    s_update_parser.add_argument("new_value", type=str, help="new value for selected subscription field")
    s_update_parser.set_defaults(func=subscription_update)

    # subscription command
    @with_argparser(s_parser)
    def do_subscription(self, args: Namespace) -> None:
        """Subscription related commands."""
        if func := getattr(args, "func", None):
            func(self, args)
        else:
            self.do_help("subscription")

    # subcommand functions for the product_block command
    def product_block_list(self, args: Namespace) -> None:  # noqa: ARG002
        """List subcommand of product_block command."""
        if state.subscription_index is None:
            self.pwarning("first select a subscription")
        else:
            self.poutput(wfoshell.product_block.product_block_list())

    def product_block_select(self, args: Namespace) -> None:
        """Select subcommand of product_block command."""
        if not (number_of_product_blocks := len(state.selected_product_blocks)):
            self.pwarning("list or search for product_blocks first")
        elif not 0 <= args.index < number_of_product_blocks:
            self.pwarning(f"selected product_block index not between 0 and {number_of_product_blocks - 1}")
        else:
            self.poutput(wfoshell.product_block.product_block_select(args.index))

    def product_block_details(self, args: Namespace) -> None:  # noqa: ARG002
        """Details subcommand of product_block command."""
        if state.product_block_index is None:
            self.pwarning("first select a product_block")
        else:
            self.poutput(wfoshell.product_block.product_block_details())

    def product_block_depends_on(self, args: Namespace) -> None:
        """Depends_on subcommand of product_block command."""
        if state.product_block_index is None:
            self.pwarning("first select a product block")
        elif not 0 <= args.index < (number_of_depends_on := len(state.selected_product_block.depends_on)):
            self.pwarning(f"selected product_block index not between 0 and {number_of_depends_on - 1}")
        else:
            self.poutput(wfoshell.product_block.product_block_depends_on(args.index))

    def product_block_in_use_by(self, args: Namespace) -> None:
        """In_use_by subcommand of product_block command."""
        if state.product_block_index is None:
            self.pwarning("first select a product block")
        elif not 0 <= args.index < (number_of_in_use_by := len(state.selected_product_block.in_use_by)):
            self.pwarning(f"selected product_block index not between 0 and {number_of_in_use_by - 1}")
        else:
            self.poutput(wfoshell.product_block.product_block_in_use_by(args.index))

    # product_block (sub)commands argument parsers
    pb_parser = Cmd2ArgumentParser()
    pb_subparser = pb_parser.add_subparsers(title="product_block subcommands")
    pb_list_parser = pb_subparser.add_parser("list")
    pb_list_parser.set_defaults(func=product_block_list)
    pb_select_parser = pb_subparser.add_parser("select")
    pb_select_parser.add_argument("index", type=int, help="select by index number")
    pb_select_parser.set_defaults(func=product_block_select)
    pb_details_parser = pb_subparser.add_parser("details")
    pb_details_parser.set_defaults(func=product_block_details)
    pb_depends_on_parser = pb_subparser.add_parser("depends_on")
    pb_depends_on_parser.add_argument("index", type=int, help="select by index number")
    pb_depends_on_parser.set_defaults(func=product_block_depends_on)
    pb_is_use_by_parser = pb_subparser.add_parser("in_use_by")
    pb_is_use_by_parser.add_argument("index", type=int, help="select by index number")
    pb_is_use_by_parser.set_defaults(func=product_block_in_use_by)

    # product_block command
    @with_argparser(pb_parser)
    def do_product_block(self, args: Namespace) -> None:
        """Product_block related commands."""
        if func := getattr(args, "func", None):
            func(self, args)
        else:
            self.do_help("product_block")

    # subcommand functions for the resource_type command
    def resource_type_list(self, args: Namespace) -> None:  # noqa: ARG002
        """List subcommand of resource_type command."""
        if state.product_block_index is None:
            self.pwarning("first select a product block")
        else:
            self.poutput(wfoshell.resource_type.resource_type_list())

    def resource_type_select(self, args: Namespace) -> None:
        """Select subcommand of resource_type command."""
        if not (number_of_resource_types := len(state.selected_resource_types)):
            self.pwarning("list or search for resource_types first")
        elif not 0 <= args.index < number_of_resource_types:
            self.pwarning(f"selected resource_type index not between 0 and {number_of_resource_types - 1}")
        else:
            self.poutput(wfoshell.resource_type.resource_type_select(args.index))

    def resource_type_details(self, args: Namespace) -> None:  # noqa: ARG002
        """Details subcommand of resource_type command."""
        if state.resource_type_index is None:
            self.pwarning("first select a resource_type")
        else:
            self.poutput(wfoshell.resource_type.resource_type_details())

    def resource_type_update(self, args: Namespace) -> None:
        """Update subcommand of resource_type command."""
        if state.resource_type_index is None:
            self.pwarning("first select a resource_type")
        else:
            wfoshell.resource_type.resource_type_update(args.new_value)

    # resource_type (sub)commands argument parsers
    rt_parser = Cmd2ArgumentParser()
    rt_subparser = rt_parser.add_subparsers(title="resource_type subcommands")
    rt_list_parser = rt_subparser.add_parser("list")
    rt_list_parser.set_defaults(func=resource_type_list)
    rt_select_parser = rt_subparser.add_parser("select")
    rt_select_parser.add_argument("index", type=int, help="select by index number")
    rt_select_parser.set_defaults(func=resource_type_select)
    rt_details_parser = rt_subparser.add_parser("details")
    rt_details_parser.set_defaults(func=resource_type_details)
    rt_update_parser = rt_subparser.add_parser("update")
    rt_update_parser.add_argument("new_value", type=str, help="new value for selected resource type")
    rt_update_parser.set_defaults(func=resource_type_update)

    # resource_type command
    @with_argparser(rt_parser)
    def do_resource_type(self, args: Namespace) -> None:
        """resource_type related commands."""
        if func := getattr(args, "func", None):
            func(self, args)
        else:
            self.do_help("resource_type")


if __name__ == "__main__":
    shell = WFOshell()
    shell.cmdloop()
