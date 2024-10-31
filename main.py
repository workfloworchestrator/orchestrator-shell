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

from cmd import Cmd
from readline import read_history_file, set_history_length, write_history_file

from orchestrator.db import init_database
from tabulate import tabulate

from wfoshell.product_block import (
    product_block_arguments,
    product_block_details,  # noqa: F401
    product_block_list,  # noqa: F401
    product_block_search,  # noqa: F401
    product_block_select,  # noqa: F401
)
from wfoshell.resource_type import (
    resource_type_arguments,
    resource_type_details,  # noqa: F401
    resource_type_list,  # noqa: F401
    resource_type_search,  # noqa: F401
    resource_type_select,  # noqa: F401
    resource_type_update,  # noqa: F401
)
from wfoshell.settings import settings
from wfoshell.state import state_summary
from wfoshell.subscripition import (
    subscription_arguments,
    subscription_details,  # noqa: F401
    subscription_list,  # noqa: F401
    subscription_search,  # noqa: F401
    subscription_select,  # noqa: F401
)


def complete(commands: list[str], text: str) -> list[str]:
    """Return list of commands that start with text."""
    return [command for command in commands if command.startswith(text)]


class WFOshell(Cmd):
    """WorkFlow Orchestrator shell."""

    intro = "Welcome to the WFO shell.\n" "Type help or ? to list commands."

    def __init__(self) -> None:
        """WFO shell initialisation."""
        super().__init__()
        self.prompt = "(wfo) "
        init_database(settings)  # type: ignore[arg-type]

    def preloop(self) -> None:
        """Load history before command loop starts."""
        if settings.WFOSHELL_HISTFILE.exists():
            read_history_file(settings.WFOSHELL_HISTFILE)

    def emptyline(self) -> bool:
        """Show state summary (instead of repeating last command)."""
        print(tabulate(state_summary(), tablefmt="plain"))
        return False

    def postloop(self) -> None:
        """Save history after command loop finishes."""
        set_history_length(settings.WFOSHELL_HISTFILE_SIZE)
        write_history_file(settings.WFOSHELL_HISTFILE)

    def do_exit(self, arg: str) -> bool:  # noqa: ARG002
        """Exit the WFO shell."""
        print("exiting WFO shell ...")
        return True

    #
    # 'subscription' command
    #
    def help_subscription(self) -> None:
        """Help text for 'subscription' command."""
        print(f"subscription [{'|'.join(subscription_arguments())}]")

    def complete_subscription(self, text: str, line: str, begidx: int, endidx: int) -> list[str]:  # noqa: ARG002
        """Return a list of possible completions for 'subscription' subcommands."""
        return complete(subscription_arguments(), text)

    def do_subscription(self, arg: str) -> None:
        """Call 'subscription' subcommand implementation function."""
        if len(args := arg.split()) and args[0] in subscription_arguments():
            globals()["subscription_" + args[0]](args)
        else:
            self.help_subscription()

    #
    # 'product_block' command
    #
    def help_product_block(self) -> None:
        """Help text for 'product_block' command."""
        print(f"subscription [{'|'.join(product_block_arguments())}]")

    def complete_product_block(self, text: str, line: str, begidx: int, endidx: int) -> list[str]:  # noqa: ARG002
        """Return a list of possible completions for 'product_block' subcommands."""
        return complete(product_block_arguments(), text)

    def do_product_block(self, arg: str) -> None:
        """Call 'product_block' subcommand implementation function."""
        if len(args := arg.split()) and args[0] in product_block_arguments():
            globals()["product_block_" + args[0]](args)
        else:
            self.help_product_block()

    #
    # 'resource_type' command
    #
    def help_resource_type(self) -> None:
        """Help text for 'resource_type' command."""
        print(f"subscription [{'|'.join(resource_type_arguments())}]")

    def complete_resource_type(self, text: str, line: str, begidx: int, endidx: int) -> list[str]:  # noqa: ARG002
        """Return a list of possible completions for 'resource_type' subcommands."""
        return complete(resource_type_arguments(), text)

    def do_resource_type(self, arg: str) -> None:
        """Call 'resource_type' subcommand implementation function."""
        if len(args := arg.split()) and args[0] in resource_type_arguments():
            globals()["resource_type_" + args[0]](args)
        else:
            self.help_resource_type()


if __name__ == "__main__":
    shell = WFOshell()
    shell.cmdloop()
