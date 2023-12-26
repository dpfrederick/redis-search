from datetime import datetime

from pydantic.v1 import BaseModel

from .team import Team


class Source(BaseModel):
    team: Team
    title: str
    path: str
    last_updated: datetime
    url: str
    file_type: str

    @property
    def id(self) -> int:
        return hash(self.url + str(self.last_updated))
