from dataclasses import dataclass
from typing import Final, final


@dataclass
@final
class Team:
    id: Final[str]
    title: Final[str]
    url: Final[str]
