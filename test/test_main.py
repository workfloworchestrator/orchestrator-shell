# Copyright 2026 SURF, GÉANT.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for command dispatch and argument handling of the shell.

The shell itself is not constructed: ``OrchestratorShell.__init__`` opens the database. The command
functions only use the output methods of ``Cmd``, so a ``Cmd`` instance with replaced output methods
is enough to exercise the real argument parsers and the guards in front of every command.
"""

import importlib
from datetime import datetime

import pytest
from cmd2 import Cmd

import orchestrator.shell
from orchestrator.shell import process, product_block, resource_type, subscripition
from orchestrator.shell.state import State
from test import factories

# ``orchestrator.shell.main`` is the console-script function exported by the package, so the module is
# taken from ``sys.modules`` instead of from ``from orchestrator.shell import main``.
shell_main = importlib.import_module("orchestrator.shell.main")


class RecordingShell(shell_main.OrchestratorShell):
    """The real shell, with its output methods replaced by recorders.

    The constructor below runs cmd2's own ``Cmd.__init__`` instead of ``OrchestratorShell.__init__``:
    the latter ends in ``init_database``, which needs a PostgreSQL server. Everything the commands use
    -- the command table from this class, the parsers and the prompt -- comes from that base setup.
    """

    def __init__(self) -> None:
        """Set up the shell without touching the database."""
        self.output: list[str] = []
        self.warnings: list[str] = []
        Cmd.__init__(self, persistent_history_file="", persistent_history_length=10)
        self.prompt = "(wfo) "

    def poutput(self, msg: str = "", *, end: str = "\n") -> None:  # noqa: ARG002
        """Record normal output; the line ending does not matter in a test."""
        self.output.append(msg)

    def pfeedback(self, msg: str, *, end: str = "\n") -> None:  # noqa: ARG002
        """Record informational output; the line ending does not matter in a test."""
        self.output.append(msg)

    def pwarning(self, msg: str, *, end: str = "\n") -> None:  # noqa: ARG002
        """Record warnings; the line ending does not matter in a test."""
        self.warnings.append(msg)


@pytest.fixture
def node_state(monkeypatch: pytest.MonkeyPatch) -> State:
    """Point every command module at one state with a selected subscription and product block."""
    block = factories.product_block("Node", "ims_id", "node_name")
    instance = factories.subscription_instance(
        block,
        "si-1",
        factories.value(block.resource_types[0], "3"),
        factories.value(block.resource_types[1], "amsterdam-1"),
    )
    state = State(
        subscriptions=[factories.subscription("sub-1", "node amsterdam-1", instance)],
        subscription_index=0,
        product_block_index=0,
    )
    for module in (shell_main, subscripition, product_block, resource_type, process):
        monkeypatch.setattr(module, "state", state)
    return state


@pytest.fixture
def shell() -> RecordingShell:
    """Return a shell that records its output."""
    return RecordingShell()


@pytest.mark.usefixtures("node_state")
def test_subscription_list_warns_to_use_search(shell: RecordingShell) -> None:
    """Listing subscriptions explains that only the ten most recent are shown."""
    shell.do_subscription("list")

    assert shell.output
    assert "ten most recent subscriptions" in shell.output[0]


def test_subscription_details_needs_a_selection(shell: RecordingShell, node_state: State) -> None:
    """Details without a selected subscription warns instead of raising."""
    node_state.subscription_index = None

    shell.do_subscription("details")

    assert shell.warnings == ["first select a subscription"]


@pytest.mark.usefixtures("node_state")
def test_subscription_details_prints_the_fields(shell: RecordingShell) -> None:
    """Details of the selected subscription print its description and id."""
    shell.do_subscription("details")

    assert "node amsterdam-1" in shell.output[0]
    assert "sub-1" in shell.output[0]


@pytest.mark.usefixtures("node_state")
def test_subscription_select_rejects_an_index_out_of_range(shell: RecordingShell) -> None:
    """Selecting a subscription outside the list warns with the valid range."""
    shell.do_subscription("select 5")

    assert shell.warnings == ["selected subscription index not between 0 and 0"]


def test_subscription_update_parses_insync(shell: RecordingShell, node_state: State) -> None:
    """The truthy spellings of insync are accepted and applied."""
    shell.do_subscription("update insync yes")

    assert node_state.selected_subscription.insync is True
    assert shell.warnings == []


def test_subscription_update_rejects_an_unknown_boolean(shell: RecordingShell, node_state: State) -> None:
    """An unknown spelling of a boolean warns and changes nothing."""
    shell.do_subscription("update insync maybe")

    assert shell.warnings == ["expected y, yes, true, n, no or false"]
    assert node_state.selected_subscription.insync is False


def test_subscription_update_parses_a_date(shell: RecordingShell, node_state: State) -> None:
    """A date field accepts an ISO date and stores it timezone-aware."""
    shell.do_subscription("update start_date 2025-01-02T03:04:05")

    start_date = node_state.selected_subscription.start_date
    assert start_date == datetime(2025, 1, 2, 3, 4, 5, tzinfo=start_date.tzinfo)
    assert start_date.tzinfo is not None


def test_subscription_update_rejects_an_invalid_date(shell: RecordingShell, node_state: State) -> None:
    """An unparseable date warns and leaves the field alone."""
    shell.do_subscription("update start_date yesterday")

    assert shell.warnings
    assert node_state.selected_subscription.start_date is None


def test_subscription_update_clears_a_date_with_an_empty_value(shell: RecordingShell, node_state: State) -> None:
    """An empty date value clears the field."""
    node_state.selected_subscription.start_date = datetime(2025, 1, 1)

    shell.do_subscription('update start_date ""')

    assert node_state.selected_subscription.start_date is None


def test_product_block_needs_a_subscription(shell: RecordingShell, node_state: State) -> None:
    """Product block commands warn until a subscription is selected."""
    node_state.subscription_index = None

    shell.do_product_block("list")

    assert shell.warnings == ["first select a subscription"]


@pytest.mark.usefixtures("node_state")
def test_product_block_select_out_of_range(shell: RecordingShell) -> None:
    """Selecting a product block outside the list warns with the valid range."""
    shell.do_product_block("select 2")

    assert shell.warnings == ["selected product_block index not between 0 and 0"]


@pytest.mark.usefixtures("node_state")
def test_product_block_depends_on_without_dependencies(shell: RecordingShell) -> None:
    """Following depends_on without any dependency warns."""
    shell.do_product_block("depends_on 0")

    assert shell.warnings == ["no depend on product blocks"]


@pytest.mark.usefixtures("node_state")
def test_resource_type_list_prints_the_sorted_resource_types(shell: RecordingShell) -> None:
    """The resource type list is ordered by name."""
    shell.do_resource_type("list")

    lines = shell.output[0].splitlines()
    assert lines[0].startswith("0  ims_id")
    assert lines[1].startswith("1  node_name")


@pytest.mark.usefixtures("node_state")
def test_resource_type_details_needs_a_selection(shell: RecordingShell) -> None:
    """Details without a selected resource type warns."""
    shell.do_resource_type("details")

    assert shell.warnings == ["first select a resource_type"]


def test_resource_type_update_changes_the_value(shell: RecordingShell, node_state: State) -> None:
    """Updating a selected resource type through the command changes its value."""
    shell.do_resource_type("select 1")
    shell.do_resource_type("update rome-1")

    assert node_state.selected_resource_type.value == "rome-1"


def test_state_summary_is_silent_without_a_selection(shell: RecordingShell, node_state: State) -> None:
    """The summary prints nothing when nothing is selected."""
    node_state.subscription_index = None
    node_state.product_block_index = None
    node_state.resource_type_index = None

    shell.do_state("summary")

    assert shell.output == []


@pytest.mark.usefixtures("node_state")
def test_state_details_prints_the_counts(shell: RecordingShell) -> None:
    """The state details report the number of subscriptions."""
    shell.do_state("details")

    assert "number of subscriptions" in shell.output[0]


@pytest.mark.usefixtures("node_state")
def test_process_select_needs_a_list_first(shell: RecordingShell) -> None:
    """Selecting a process before listing any warns."""
    shell.do_process("select 0")

    assert shell.warnings == ["list or search for processes first"]


@pytest.mark.usefixtures("node_state")
def test_process_leapfrog_needs_a_selection(shell: RecordingShell) -> None:
    """Leapfrogging without a selected process warns."""
    shell.do_process("leapfrog")

    assert shell.warnings == ["first select a process"]


def test_process_leapfrog_refuses_a_non_resumable_process(shell: RecordingShell, node_state: State) -> None:
    """Leapfrogging a process in a non-resumable state is refused before touching the database."""
    node_state.processes = [factories.process("p-1", "create_node", datetime(2025, 1, 1), last_status="completed")]
    node_state.process_index = 0

    shell.do_process("leapfrog")

    assert shell.warnings == ["selected process is not resumable"]


def test_module_entry_point_starts_the_shell(monkeypatch: pytest.MonkeyPatch) -> None:
    """The console script builds a shell and starts its command loop.

    The generated ``orchestrator-shell`` script imports ``main`` from the package, so the package
    attribute is what the test replaces.
    """
    calls: list[str] = []

    class FakeShell:
        def cmdloop(self) -> None:
            calls.append("cmdloop")

    monkeypatch.setattr(orchestrator.shell, "OrchestratorShell", FakeShell)

    orchestrator.shell.main()

    assert calls == ["cmdloop"]
