from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from arielbot.domain.entities import SubTarget, SubChannel, BotStatus


class SubTargetRepository(ABC):
    @abstractmethod
    async def get(self, uid: str) -> Optional[SubTarget]:
        ...

    @abstractmethod
    async def save(self, uid: str, nickname: str, live_status: int) -> None:
        ...

    @abstractmethod
    async def update(self, nickname: str, live_status: int, uid: str) -> None:
        ...


class SubChannelRepository(ABC):
    @abstractmethod
    async def get(self, uid: str, group_id: int, bot_id: int) -> Optional[SubChannel]:
        ...

    @abstractmethod
    async def save(self, uid: str, group_id: int, bot_id: int) -> None:
        ...

    @abstractmethod
    async def update(self, live_active: int, dyn_active: int,
                     uid: str, group_id: int, bot_id: int) -> None:
        ...

    @abstractmethod
    async def delete(self, uid: str, group_id: int, bot_id: int) -> None:
        ...

    @abstractmethod
    async def find_push_targets_for_dyn(self, uid: str) -> List[Tuple[int, int]]:
        ...

    @abstractmethod
    async def find_push_targets_for_live(self, uid: str) -> List[Tuple[int, int]]:
        ...

    @abstractmethod
    async def find_live_check_uids(self) -> List[tuple]:
        ...

    @abstractmethod
    async def list_by_group(self, bot_id: int, group_id: int) -> List[tuple]:
        ...


class BotStatusRepository(ABC):
    @abstractmethod
    async def get(self, bot_id: int, group_id: int) -> Optional[BotStatus]:
        ...

    @abstractmethod
    async def save(self, bot_id: int, group_id: int,
                   push_active: int, bot_active: int) -> None:
        ...

    @abstractmethod
    async def update_push(self, bot_id: int, group_id: int, active: int) -> None:
        ...

    @abstractmethod
    async def update_active(self, bot_id: int, active: int) -> None:
        ...

    @abstractmethod
    async def list_all_bots(self) -> List[int]:
        ...


class CookieRepository(ABC):
    @abstractmethod
    async def get(self) -> Optional[tuple]:
        ...

    @abstractmethod
    async def save(self, cookie_blob: bytes, refresh_token: str) -> None:
        ...

    @abstractmethod
    async def update(self, cookie_blob: bytes, refresh_token: str,
                     old_refresh_token: str) -> None:
        ...

    @abstractmethod
    async def clear(self) -> None:
        ...


class DynCacheRepository(ABC):
    @abstractmethod
    async def exists(self, dyn_id: str) -> Optional[bytes]:
        ...

    @abstractmethod
    async def save(self, dyn_id: str, uname: str, content: bytes) -> None:
        ...

    @abstractmethod
    async def get_content(self, dyn_id: str) -> Optional[bytes]:
        ...