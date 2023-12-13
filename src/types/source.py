from dataclasses import dataclass
from datetime import datetime
from typing import Final, final

from .team import Team


@dataclass
@final
class Source:
    team: Final[Team]
    title: Final[str]
    path: Final[str]
    last_updated: Final[datetime]
    url: Final[str]
    file_type: Final[str]

    @property
    def id(self) -> int:
        return hash(self.url + str(self.last_updated))
