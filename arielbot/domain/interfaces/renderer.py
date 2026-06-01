from abc import ABC, abstractmethod
from typing import List, Tuple


class DynRenderer(ABC):
    @abstractmethod
    async def render(self, dynamic: object) -> bytes:
        ...


class SubListRenderer(ABC):
    @abstractmethod
    async def render(self, data: List[Tuple[str, str, bool, bool]]) -> bytes:
        ...


class HelpRenderer(ABC):
    @abstractmethod
    async def render(self) -> bytes:
        ...