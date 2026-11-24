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
"""Tests for listing, searching and inspecting processes."""

from datetime import datetime

import pytest

from orchestrator.shell import process
from orchestrator.shell.state import State
from test import factories


def test_indexed_process_list_shows_the_process_columns() -> None:
    """The list shows workflow name, creator, status, step and timestamps behind an index."""
    created = factories.process("p-1", "create_node", datetime(2025, 1, 1), last_status="completed")

    table = process.indexed_process_list([created])

    assert table.startswith("0  create_node")
    assert "completed" in table


def test_filter_matches_workflow_name_and_creator() -> None:
    """The search matches the workflow name and the creator, ignoring case."""
    mine = factories.process("p-1", "create_node", datetime(2025, 1, 1))
    other = factories.process("p-2", "modify_node", datetime(2025, 1, 2))
    other.created_by = "someone-else"

    assert [p.process_id for p in process.filtered_processes("CREATE", [mine, other])] == ["p-1"]
    assert [p.process_id for p in process.filtered_processes("SOMEONE", [mine, other])] == ["p-2"]


def test_details_report_the_process_fields() -> None:
    """The details report the workflow name and the identifiers of the process."""
    created = factories.process("p-1", "create_node", datetime(2025, 1, 1))

    rows = dict(process.details(created))

    assert rows["workflow_name"] == "create_node"
    assert rows["process_id"] == "p-1"
    assert rows["created_by"] == "test"


def test_process_list_keeps_the_ten_most_recent_processes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Listing keeps the ten newest processes in the state and forgets an earlier filter."""
    processes = [factories.process(f"p-{number}", "create_node", datetime(2025, 1, 1, number)) for number in range(12)]
    state = State(filtered_processes=[])
    monkeypatch.setattr(process, "query_db", lambda: processes)
    monkeypatch.setattr(process, "state", state)

    table = process.process_list()

    assert [p.process_id for p in state.processes] == [f"p-{number}" for number in range(2, 12)]
    assert state.filtered_processes is None
    assert table.startswith("0  create_node")


def test_process_search_stores_the_filtered_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Searching keeps both the full and the filtered list in the state."""
    processes = [
        factories.process("p-1", "create_node", datetime(2025, 1, 1)),
        factories.process("p-2", "modify_node", datetime(2025, 1, 2)),
    ]
    state = State()
    monkeypatch.setattr(process, "query_db", lambda: processes)
    monkeypatch.setattr(process, "state", state)

    process.process_search("modify")

    assert [p.process_id for p in state.processes] == ["p-1", "p-2"]
    assert state.filtered_processes is not None
    assert [p.process_id for p in state.filtered_processes] == ["p-2"]


def test_select_maps_a_filtered_index_back_to_the_full_list(monkeypatch: pytest.MonkeyPatch) -> None:
    """Selecting a search result selects that process in the unfiltered list."""
    processes = [
        factories.process("p-1", "create_node", datetime(2025, 1, 1)),
        factories.process("p-2", "modify_node", datetime(2025, 1, 2)),
    ]
    state = State(processes=processes, filtered_processes=[processes[1]])
    monkeypatch.setattr(process, "state", state)

    process.process_select(0)

    assert state.process_index == 1


def test_select_without_a_filter_uses_the_list_index(monkeypatch: pytest.MonkeyPatch) -> None:
    """Selecting on the plain list sets the index directly."""
    processes = [factories.process("p-1", "create_node", datetime(2025, 1, 1))]
    state = State(processes=processes)
    monkeypatch.setattr(process, "state", state)

    process.process_select(0)

    assert state.process_index == 0
