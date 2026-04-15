#  Copyright 2026 GÉANT.
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

from orchestrator.db import ProcessStepTable, ProcessTable, db, transactional
from orchestrator.workflow import ProcessStatus, StepStatus
from structlog import get_logger
from tabulate import tabulate

from orchestrator_shell.state import sorted_processes, state

logger = get_logger(__name__)


def indexed_process_list(processes: list[ProcessTable]) -> str:
    """Return tabulated, indexed list of processes."""
    return tabulate(
        [
            (
                process.workflow_name,
                process.created_by,
                process.last_status,
                process.last_step,
                process.started_at,
                process.last_modified_at,
            )
            for process in processes
        ],
        tablefmt="plain",
        disable_numparse=True,
        showindex=True,
    )


def query_db() -> list[ProcessTable]:
    """Return sorted list of processes from the database."""
    return sorted_processes(ProcessTable.query.all())


def filtered_processes(regular_expression: str, processes: list[ProcessTable]) -> list[ProcessTable]:
    """Return filtered list of processes."""
    pattern = re.compile(regular_expression, flags=re.IGNORECASE)
    return list(filter(lambda process: pattern.search(process.workflow_name + process.created_by), processes))


def details(process: ProcessTable) -> list[tuple[str, str]]:
    """Return list of tuples with process details."""
    return [
        ("workflow_name", str(process.workflow_name)),
        ("assignee", process.assignee),
        ("created_by", process.created_by),
        ("last_status", process.last_status),
        ("last_step", process.last_step),
        ("process_id", process.process_id),
        ("started_at", process.started_at),
    ]


def process_list() -> str:
    """Add list of the ten most recent processes to the state and return this list tabulated and indexed."""
    state.processes = query_db()[-10:]
    state.filtered_processes = None
    return indexed_process_list(state.processes)


def process_search(regular_expression: str) -> str:
    """Add list of filtered processes to the state and return this list tabulated and indexed."""
    state.processes = query_db()
    state.filtered_processes = filtered_processes(regular_expression, state.processes)
    return indexed_process_list(state.filtered_processes)


def process_select(index: int) -> str:
    """Implementation of the 'process select' subcommand."""
    if not state.filtered_processes:
        state.process_index = index
    else:
        state.process_index = state.processes.index(state.filtered_processes[index])
    return state.summary


def process_details() -> str:
    """Implementation of the 'process details' subcommand."""
    return tabulate(details(state.selected_process), tablefmt="plain")


def process_leapfrog() -> str:
    """Implementation of the 'process leapfrog' subcommand."""
    with transactional(db, logger):
        related_steps: list[ProcessStepTable] = sorted(
            ProcessStepTable.query.filter(ProcessStepTable.process_id == state.selected_process.process_id).all(),
            key=lambda step: step.completed_at,
        )
        last_successful_step = next(
            (step for step in reversed(related_steps) if step.status == StepStatus.SUCCESS), None
        )
        if not last_successful_step:
            return "ERROR: Cannot leapfrog a process that has not had a single successful step"
        last_step = related_steps[-1]

        # Copy state from last successful step
        last_step.state = last_successful_step.state

        # Mark the current step as success
        last_step.status = StepStatus.SUCCESS

        # Mark the process as failed
        state.selected_process.last_status = ProcessStatus.FAILED

        return f"Process {state.selected_process.process_id} has been leapfrogged, please retry the process."
