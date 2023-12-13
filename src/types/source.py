from dataclasses import dataclass
from datetime import datetime

# from hashlib import _Hash
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

    # @property
    # def id(self) -> _Hash:
    #     return _Hash(self.url, self.last_updated)
