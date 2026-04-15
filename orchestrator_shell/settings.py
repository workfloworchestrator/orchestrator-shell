#  Copyright 2024-2026 SURF, GÉANT.
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

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """WFO Shell settings."""

    ORCHESTRATOR_SHELL_HISTFILE: Path = Path("~/.orchestrator_shell_history").expanduser()
    ORCHESTRATOR_SHELL_HISTFILE_SIZE: int = 1000


settings = Settings()
